import os
import json
from modules.llm import GroqLLM
from modules.db_handling import Database
from routes.auth import get_current_user
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse

router = APIRouter(prefix="/reports", tags=["Reports"])
groq_llm = GroqLLM(api_key=os.getenv("GROQ_API_KEY"))
db = Database()


def _format_transcript(transcript: list) -> str:
    lines = []
    for entry in transcript:
        speaker = entry.get("speaker", "Unknown")
        text = entry.get("text", "")
        ts = entry.get("timestamp", 0)
        lines.append(f"[{ts:.1f}s] {speaker}: {text}")
    return "\n".join(lines)


@router.post("/generate")
async def generate_report(data: dict):
    transcript = data.get("transcript", [])
    session_id = data.get("session_id")

    if not transcript:
        raise HTTPException(status_code=400, detail="Transcript is required")

    if isinstance(transcript, list):
        transcript = _format_transcript(transcript)

    async def generate():
        buffer = []
        try:
            for chunk in groq_llm.llm(transcript):
                if chunk:
                    buffer.append(chunk)
                    yield f"data: {json.dumps({'content': chunk})}\n\n"

            content = "".join(buffer)
            if session_id:
                report_id = db.create_report(session_id, content)
                yield f"data: {json.dumps({'done': True, 'report_id': report_id})}\n\n"
            else:
                yield f"data: {json.dumps({'done': True})}\n\n"
        except Exception as e:
            print(f"Error in LLM generation: {e}")
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")


@router.get("/")
async def list_reports(status: str = None, user: dict = Depends(get_current_user)):
    reports_list = db.get_user_reports(user["id"], status=status)
    return {"reports": reports_list}


@router.get("/{report_id}")
async def get_report(report_id: int, user: dict = Depends(get_current_user)):
    report = db.get_report_with_session(report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    if report["user_id"] != user["id"]:
        raise HTTPException(status_code=403, detail="Not your report")
    return report


@router.put("/{report_id}")
async def update_report(
    report_id: int, data: dict, user: dict = Depends(get_current_user)
):
    report = db.get_report_with_session(report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    if report["user_id"] != user["id"]:
        raise HTTPException(status_code=403, detail="Not your report")
    content = data.get("content", report["content"])
    status = data.get("status")
    db.update_report(report_id, content, status=status)
    return {"message": "Report updated"}


@router.delete("/{report_id}")
async def delete_report(report_id: int, user: dict = Depends(get_current_user)):
    report = db.get_report_with_session(report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    if report["user_id"] != user["id"]:
        raise HTTPException(status_code=403, detail="Not your report")
    db.delete_report(report_id)
    return {"message": "Report deleted"}
