from fastapi import FastAPI
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
from models.audio_session import active_sessions

from routes.auth import router as auth_router
from routes.appointments import router as appointments_router
from routes.reports import router as reports_router
from routes.ws_audio import router as ws_audio_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    active_sessions.clear()
    yield
    active_sessions.clear()


app = FastAPI(title="MARGe API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:8000",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:8000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

PREFIX_API = "/api"

# ==== REST ENDPOINTS ====
@app.get(f"{PREFIX_API}/")
async def root():
    return {"message": "MARGe API - Medical Appointment Report Generator"}

@app.get(f"{PREFIX_API}/health")
async def health_check():
    return {"status": "healthy"}

app.include_router(auth_router, prefix=PREFIX_API)
app.include_router(appointments_router, prefix=PREFIX_API)
app.include_router(reports_router, prefix=PREFIX_API)
app.include_router(ws_audio_router)