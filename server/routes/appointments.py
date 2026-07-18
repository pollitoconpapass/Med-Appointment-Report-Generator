import uuid
import asyncio
from datetime import datetime
from models.audio_session import Session, active_sessions
from fastapi import APIRouter, Depends, HTTPException
from modules.db_handling import Database
from routes.auth import get_optional_user

db = Database()
router = APIRouter(prefix="/appointments", tags=["Appointments"])


@router.post("/start")
async def start_appointment(
    data: dict,
    user: dict | None = Depends(get_optional_user),
):
    session_id = str(uuid.uuid4())
    language = data.get("language", "en")
    num_speakers = data.get("num_speakers", 2)
    min_speakers = data.get("min_speakers")
    max_speakers = data.get("max_speakers")

    active_sessions[session_id] = Session(
        id=session_id,
        language=language,
        started_at=datetime.now().isoformat(),
        num_speakers=num_speakers,
        min_speakers=min_speakers,
        max_speakers=max_speakers,
    )

    db.create_session(
        session_id=session_id,
        user_id=user["id"] if user else None,
        language=language,
        num_speakers=num_speakers,
        min_speakers=min_speakers,
        max_speakers=max_speakers,
        started_at=datetime.now().isoformat(),
    )

    return {"session_id": session_id, "status": "started", "language": language}


@router.post("/end")
async def end_appointment(data: dict):
    session_id = data.get("session_id")

    if session_id not in active_sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    session = active_sessions[session_id]

    wait_time = 0
    while session.is_active and wait_time < 120:
        await asyncio.sleep(0.5)
        wait_time += 0.5

    transcript = session.transcript

    if transcript:
        db.add_transcriptions_bulk(session_id, transcript)

    db.end_session(session_id)
    del active_sessions[session_id]

    return {
        "session_id": session_id,
        "transcript": transcript,
        "status": "ended",
    }
