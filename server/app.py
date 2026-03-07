import os
import io
import json
import uuid
import torch
from typing import Dict
from scipy.io import wavfile
from datetime import datetime
from dotenv import load_dotenv
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from modules.llm import GroqLLM
from modules.stt import WhisperSTT
from models.audio_session import Session
from modules.silence_detector import SilenceDetector
from utils.processors import process_webm_bytes

load_dotenv('../.env')

# Global variables
sessions: Dict[str, Session] = {}

# Initialize modules
silence_detector = SilenceDetector()
whisper_stt = WhisperSTT(api_key=os.getenv("GROQ_API_KEY"))
groq_llm = GroqLLM(api_key=os.getenv("GROQ_API_KEY"))


@asynccontextmanager
async def lifespan(app: FastAPI):
    sessions.clear()
    yield
    sessions.clear()


app = FastAPI(title="MARGe API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==== REST ENDPOINTS ====
@app.get("/")
async def root():
    return {"message": "MARGe API - Medical Appointment Report Generator"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}


@app.post("/appointment/start")
async def start_appointment(data: dict):
    session_id = str(uuid.uuid4())
    language = data.get("language", "en")
    
    sessions[session_id] = Session(
        id=session_id,
        language=language,
        started_at=datetime.now().isoformat()
    )
    
    return {"session_id": session_id, "status": "started", "language": language}


@app.post("/appointment/end", responses={404: {"description": "Session not found"}})
async def end_appointment(data: dict):
    session_id = data.get("session_id")
    
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = sessions[session_id]
    transcript = session.transcript
    
    del sessions[session_id]
    
    return {
        "session_id": session_id,
        "transcript": transcript,
        "status": "ended"
    }


@app.post("/report/generate", responses={400: {"description": "Transcript is required"}})
async def generate_report(data: dict):
    transcript = data.get("transcript", [])
    
    if not transcript:
        raise HTTPException(status_code=400, detail="Transcript is required")
    
    transcript_text = "\n".join([item.get("text", "") for item in transcript])
    
    async def generate():
        for chunk in groq_llm.llm(transcript_text, is_full=True):
            yield f"data: {json.dumps({'content': chunk})}\n\n"
        yield f"data: {json.dumps({'done': True})}\n\n"
    
    return generate()


# ===== WEB SOCKETS =====
@app.websocket("/ws/audio/{session_id}")
async def websocket_audio(websocket: WebSocket, session_id: str):
    if session_id not in sessions:
        await websocket.close(code=4004, reason="Session not found")
        return
    
    session = sessions[session_id]
    await websocket.accept()
    
    silence_threshold = 5
    overlap_seconds = 2
    
    accumulated_audio = None
    
    try:
        while True:
            data = await websocket.receive_bytes()
            
            # Convert WebM to audio tensor
            audio_tensor = process_webm_bytes(data, session.sample_rate)
            
            if audio_tensor is None:
                await websocket.send_json({"type": "error", "message": "Failed to process audio"})
                continue
            
            # Append to accumulated audio
            if accumulated_audio is None:
                accumulated_audio = audio_tensor
            else:
                accumulated_audio = torch.cat([accumulated_audio, audio_tensor], dim=1)
            
            # Run VAD on accumulated audio
            timestamps = silence_detector.get_timestamps_from_tensor(accumulated_audio, session.sample_rate)
            
            # Check for silence gaps
            current_audio_duration = accumulated_audio.shape[1] / session.sample_rate
            
            if len(timestamps) > 0:
                last_timestamp = timestamps[-1]
                speech_end = last_timestamp.get('end', 0)
                
                # Calculate silence since last speech
                silence_since_speech = current_audio_duration - speech_end
                
                if silence_since_speech >= silence_threshold:
                    # Create chunk with overlap
                    chunk_start = max(0, speech_end - overlap_seconds)
                    chunk_end = current_audio_duration
                    
                    # Extract chunk
                    start_sample = int(chunk_start * session.sample_rate)
                    end_sample = int(chunk_end * session.sample_rate)
                    audio_chunk = accumulated_audio[:, start_sample:end_sample]
                    
                    # Save to BytesIO (in-memory) and transcribe
                    audio_buffer = io.BytesIO()
                    audio_np = audio_chunk.squeeze().numpy()
                    wavfile.write(audio_buffer, session.sample_rate, audio_np)
                    audio_buffer.seek(0)
                    
                    result = whisper_stt.stt(audio_buffer, language=session.language)
                    result_dict = json.loads(result)
                    text = result_dict.get("text", "")
                    
                    if text.strip():
                        session.transcript.append({
                            "text": text,
                            "timestamp": chunk_start,
                            "chunk_start": chunk_start,
                            "chunk_end": chunk_end
                        })
                        
                        await websocket.send_json({
                            "type": "transcript",
                            "text": text,
                            "timestamp": chunk_start
                        })
                    
                    # Reset accumulated audio (keep a small buffer for overlap)
                    keep_duration = overlap_seconds + 1
                    keep_samples = int(keep_duration * session.sample_rate)
                    if accumulated_audio.shape[1] > keep_samples:
                        accumulated_audio = accumulated_audio[:, -keep_samples:]
                    else:
                        accumulated_audio = None
            
            await websocket.send_json({
                "type": "ack",
                "duration": current_audio_duration,
                "transcripts_count": len(session.transcript)
            })
            
    except WebSocketDisconnect:
        pass
    except Exception as e:
        try:
            await websocket.send_json({"type": "error", "message": str(e)})
        except Exception:
            pass
        await websocket.close(code=1011)