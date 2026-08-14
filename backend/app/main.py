"""
THE SILENT CO-DRIVER — FastAPI backend entrypoint.

Run with:
    uvicorn app.main:app --reload --port 8000

All secrets (model API keys, endpoints) live in `backend/.env` and are
never sent to the frontend. The React app only ever calls this
server; this server is the only thing that talks to OpenF1 and to
whatever models you plug into `app/services/model_service.py`.
"""
from __future__ import annotations

import logging

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routes import analysis, race_data, radio, sessions
from app.core.config import get_settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("silent_codriver")

settings = get_settings()

app = FastAPI(
    title="The Silent Co-Driver API",
    description="Race-engineering decision-support API: OpenF1 telemetry + AI-derived driver vocal state.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(sessions.router, prefix="/api")
app.include_router(race_data.router, prefix="/api")
app.include_router(radio.router, prefix="/api")
app.include_router(analysis.router, prefix="/api")


@app.exception_handler(Exception)
async def unhandled_exception_handler(request, exc):  # noqa: ANN001
    logger.exception("Unhandled error on %s", request.url)
    return JSONResponse(status_code=500, content={"detail": "Internal server error. Please try again."})


@app.get("/")
async def root():
    return {"service": "silent-codriver-api", "status": "running", "demo_mode": settings.demo_mode}
