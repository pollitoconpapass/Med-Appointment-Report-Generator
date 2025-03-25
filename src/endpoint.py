import os
import shutil
import uvicorn
import assemblyai as aai
from dotenv import load_dotenv
from fastapi import FastAPI, UploadFile, File, HTTPException


app = FastAPI()

# === ELEMENTAL DATA ===
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))
aai.settings.api_key = os.getenv("ASSEMBLY_API_KEY")


@app.post("/transcribe")
async def transcribe_audio(language_code: str, num_speakers: int, file: UploadFile = File(...)):    
    # start = time.time()

    file_location = f"../audios/{file.filename}"
    with open(file_location, "wb") as f:
        shutil.copyfileobj(file.file, f)
    
    try:
        # === FOR IDENTIFYING SPEAKERS ===
        config = aai.TranscriptionConfig(
            speaker_labels=True, 
            language_code=language_code, 
            speakers_expected=num_speakers
        )
        transcriber = aai.Transcriber()
        transcript = transcriber.transcribe(
            file_location,
            config=config
        )
        
        # Collect transcription results
        transcription_results = [
            {"speaker": utterance.speaker, "text": utterance.text}
            for utterance in transcript.utterances
        ]

        # print(f"TIME TAKEN: {time.time() - start} seconds\n")
        return { "transcription": transcription_results }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        os.remove(file_location)


if __name__ == "__main__":
    uvicorn.run(app, host="localhost", port=8000)
