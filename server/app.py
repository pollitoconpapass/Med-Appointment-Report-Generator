import os
import io
import time
import json
import uuid
import torch
import asyncio
import numpy as np
from typing import Dict
from scipy.io import wavfile
from datetime import datetime
from dotenv import load_dotenv
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from modules.llm import GroqLLM
from modules.stt import WhisperSTT
from models.audio_session import Session
from modules.silence_detector import SilenceDetector
from modules.speaker_diarization import SpeakerDiarization
from utils.processors import process_webm_bytes

load_dotenv('../.env')

# Global variables
sessions: Dict[str, Session] = {}

# Initialize modules
silence_detector = SilenceDetector()
whisper_stt = WhisperSTT(api_key=os.getenv("GROQ_API_KEY"))
groq_llm = GroqLLM(api_key=os.getenv("GROQ_API_KEY"))
speaker_diarization = SpeakerDiarization(api_key=os.getenv("HUGGING_FACE_API_KEY"))


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
    num_speakers = data.get("num_speakers", 2)
    min_speakers = data.get("min_speakers")
    max_speakers = data.get("max_speakers")
    
    sessions[session_id] = Session(
        id=session_id,
        language=language,
        started_at=datetime.now().isoformat(),
        num_speakers=num_speakers,
        min_speakers=min_speakers,
        max_speakers=max_speakers
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
    
    async def generate():
        try:
            for chunk in groq_llm.llm(transcript):
                if chunk:
                    yield f"data: {json.dumps({'content': chunk})}\n\n"
            yield f"data: {json.dumps({'done': True})}\n\n"
        except Exception as e:
            print(f"Error in LLM generation: {e}")
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
    
    return StreamingResponse(generate(), media_type="text/event-stream")


# ===== WEB SOCKETS =====
@app.websocket("/ws/audio/{session_id}")
async def websocket_audio(websocket: WebSocket, session_id: str):
    if session_id not in sessions:
        await websocket.close(code=4004, reason="Session not found")
        return
    
    session = sessions[session_id]
    await websocket.accept()
    
    silence_threshold = 2
    accumulated_audio = None
    
    async def process_audio_chunk(audio_chunk, current_duration):
        nonlocal accumulated_audio
        if audio_chunk is None or audio_chunk.shape[1] == 0:
            return

        print(f"\nProcessing audio chunk ({audio_chunk.shape[1] / session.sample_rate:.2f}s)...")
        start_time = time.time()
        
        # Run Diarization first to get speaker segments
        diarization_result = await asyncio.to_thread(
            speaker_diarization.diarize, 
            audio_chunk, 
            session.sample_rate,
            num_speakers=session.num_speakers,
            min_speakers=session.min_speakers,
            max_speakers=session.max_speakers
        )
        
        # Process each speaker segment separately
        chunk_start_offset = current_duration - (audio_chunk.shape[1] / session.sample_rate)
        
        for segment in diarization_result:
            seg_start = segment["start"]
            seg_end = segment["end"]
            speaker = segment["speaker"]
            
            # Extract speaker-specific audio segment
            start_sample = int(seg_start * session.sample_rate)
            end_sample = int(seg_end * session.sample_rate)
            speaker_audio = audio_chunk[:, start_sample:end_sample]
            
            if speaker_audio.shape[1] < session.sample_rate * 0.1:
                continue
            
            # Convert to BytesIO
            audio_buffer = io.BytesIO()
            audio_np = speaker_audio.squeeze().numpy()
            audio_int16 = (audio_np * 32767).astype(np.int16)
            wavfile.write(audio_buffer, session.sample_rate, audio_int16)
            audio_buffer.seek(0)
            audio_buffer.name = "audio.wav"
            
            # Run STT for this speaker segment
            result = await asyncio.to_thread(
                whisper_stt.stt, audio_buffer, language=session.language
            )
            
            if result and result.strip():
                abs_start = chunk_start_offset + seg_start
                abs_end = chunk_start_offset + seg_end
                
                session.transcript.append({
                    "speaker": speaker,
                    "text": result,
                    "timestamp": abs_start,
                    "chunk_start": abs_start,
                    "chunk_end": abs_end
                })
                
                try:
                    await websocket.send_json({
                        "type": "transcript",
                        "speaker": speaker,
                        "text": result,
                        "timestamp": abs_start
                    })
                except Exception:
                    # WebSocket might be closed during "final flush"
                    pass

        print(f"Diarization and transcription completed in {time.time() - start_time:.2f} seconds\n")
        
        # Reset webm_buffer to header only to keep it small
        if session.webm_header is not None:
            session.webm_buffer = bytearray(session.webm_header)
            session.last_processed_samples = session.header_samples

    try:
        while True:
            data = await websocket.receive_bytes()
            
            # Append to session-specific webm buffer
            if session.webm_header is None:
                session.webm_header = data
            
            session.webm_buffer.extend(data)
            
            # Convert WebM to audio tensor using the current buffer
            # Run in thread to avoid blocking the event loop heartbeats
            full_audio_tensor = await asyncio.to_thread(
                process_webm_bytes, bytes(session.webm_buffer), session_id, session.sample_rate
            )
            
            if full_audio_tensor is None:
                continue
            
            # Extract only the new part
            current_total_samples = full_audio_tensor.shape[1]
            
            # If this is the first successful decode and we just have the header, record its sample count
            if session.header_samples == 0 and session.webm_header is not None and len(session.webm_buffer) == len(session.webm_header):
                session.header_samples = current_total_samples

            new_samples_count = current_total_samples - session.last_processed_samples
            
            if new_samples_count <= 0:
                continue
                
            audio_tensor = full_audio_tensor[:, session.last_processed_samples:]
            session.last_processed_samples = current_total_samples
            
            # Append to accumulated audio (used for VAD and transcription)
            if accumulated_audio is None:
                accumulated_audio = audio_tensor
            else:
                accumulated_audio = torch.cat([accumulated_audio, audio_tensor], dim=1)
            
            # Run VAD in thread
            current_audio_duration = accumulated_audio.shape[1] / session.sample_rate
            timestamps = await asyncio.to_thread(
                silence_detector.get_timestamps_from_tensor, accumulated_audio, session.sample_rate
            )
            
            if len(timestamps) > 0:
                last_timestamp = timestamps[-1]
                speech_end = last_timestamp.get('end', 0)
                
                # Calculate silence since last speech
                silence_since_speech = current_audio_duration - speech_end
                
                if silence_since_speech >= silence_threshold:
                    print(f"\nSilence threshold met ({silence_since_speech:.2f}s), transcribing...")
                    await process_audio_chunk(accumulated_audio, current_audio_duration)
                    # Reset accumulated audio
                    accumulated_audio = None
            
            await websocket.send_json({
                "type": "ack",
                "duration": current_audio_duration,
                "transcripts_count": len(session.transcript)
            })
            
    except WebSocketDisconnect:
        print("WebSocket connection closed. Performing final flush...")
        if accumulated_audio is not None:
            # Calculate duration for the final chunk
            final_duration = accumulated_audio.shape[1] / session.sample_rate
            await process_audio_chunk(accumulated_audio, final_duration)
    except Exception as e:
        print(f"Error in websocket_audio: {e}")

        try:
            await websocket.send_json({"type": "error", "message": str(e)})
        except Exception:
            pass
        
        try:
            await websocket.close(code=1011)
        except Exception:
            pass
