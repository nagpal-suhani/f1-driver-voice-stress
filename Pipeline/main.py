"""
The Silent Co-Driver — Speech-to-Text Backend (FastAPI)
----------------------------------------------------------
Wraps stt_pipeline.transcribe_audio() as an HTTP API so the frontend
and other team components (mood/stress model, lap-time correlation)
can call it directly.

Run locally:
    uvicorn main:app --host 0.0.0.0 --port 8000 --reload

Endpoints:
    GET  /health                 -> liveness/readiness check
    POST /transcribe             -> upload an audio file, get back the transcript JSON
    POST /transcribe/raw         -> same, but skips preprocessing (bandpass/normalize)

Interactive API docs (Swagger UI) are auto-served at /docs once running.
"""

import asyncio
import logging
import os
import tempfile
import time
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, File, HTTPException, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.concurrency import run_in_threadpool

from stt_pipeline import transcribe_audio, _get_model

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("stt-backend")

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

MAX_FILE_SIZE_MB = 25
ALLOWED_EXTENSIONS = {".wav", ".mp3", ".m4a", ".flac", ".ogg", ".webm"}


# ---------------------------------------------------------------------------
# App lifecycle — kick off model loading in the background at startup
# instead of blocking on it. Model loading (esp. first run, which downloads
# weights) can take anywhere from seconds to minutes depending on network
# conditions. Blocking startup on it means the whole server — including
# /health — is unreachable until it finishes. Loading it in the background
# lets uvicorn come up immediately; /health reports real readiness, and
# /transcribe will load-on-demand (and block only that request) if someone
# hits it before the background load finishes.
# ---------------------------------------------------------------------------

model_load_error: str | None = None


async def _load_model_background():
    global model_load_error
    logger.info("Loading speech-to-text model in background...")
    start = time.time()
    try:
        await run_in_threadpool(_get_model)
        logger.info(f"Model loaded in {time.time() - start:.1f}s")
    except Exception as e:
        model_load_error = str(e)
        logger.error(f"Model failed to load: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    asyncio.create_task(_load_model_background())
    yield
    logger.info("Shutting down.")


app = FastAPI(
    title="Silent Co-Driver — STT Service",
    description="Speech-to-text pipeline for driver radio audio",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS: wide open for hackathon purposes so the frontend (likely on a
# different port/origin during dev) can call this freely. Tighten
# allow_origins before any real deployment.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _validate_upload(file: UploadFile) -> str:
    """Check extension is supported. Returns the lowercase extension."""
    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Unsupported file type '{ext}'. Allowed: {sorted(ALLOWED_EXTENSIONS)}",
        )
    return ext


async def _save_upload_to_temp(file: UploadFile, ext: str) -> str:
    """Stream the upload to a temp file, enforcing a max size limit while
    reading (rather than after loading it all into memory)."""
    max_bytes = MAX_FILE_SIZE_MB * 1024 * 1024
    total = 0
    fd, path = tempfile.mkstemp(suffix=ext, prefix="radio_")

    try:
        with os.fdopen(fd, "wb") as out:
            while chunk := await file.read(1024 * 1024):
                total += len(chunk)
                if total > max_bytes:
                    raise HTTPException(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        detail=f"File exceeds {MAX_FILE_SIZE_MB}MB limit.",
                    )
                out.write(chunk)
    except HTTPException:
        os.remove(path)
        raise
    except Exception:
        os.remove(path)
        raise

    if total == 0:
        os.remove(path)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Uploaded file is empty.")

    return path


async def _run_transcription(file: UploadFile, apply_preprocessing: bool) -> dict:
    ext = _validate_upload(file)
    temp_path = await _save_upload_to_temp(file, ext)
    request_id = str(uuid.uuid4())[:8]

    try:
        logger.info(f"[{request_id}] Transcribing {file.filename} (preprocess={apply_preprocessing})")
        start = time.time()
        # transcribe_audio is CPU-bound and blocking (audio DSP + model
        # inference) — run it in a threadpool so it doesn't block the
        # event loop and stall other requests/health checks.
        result = await run_in_threadpool(transcribe_audio, temp_path, apply_preprocessing)
        elapsed = time.time() - start
        logger.info(f"[{request_id}] Done in {elapsed:.2f}s")
        result["request_id"] = request_id
        result["processing_time_sec"] = round(elapsed, 2)
        return result
    except FileNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.exception(f"[{request_id}] Transcription failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Transcription failed: {e}",
        )
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.get("/health")
async def health():
    """Liveness/readiness check. Reports whether the model is actually
    loaded, not just whether the process is up — a teammate's frontend
    can poll this before sending the first real request."""
    model_ready = "model" in __import__("stt_pipeline")._model_cache
    resp = {
        "status": "ok" if model_ready else ("error" if model_load_error else "starting"),
        "model_loaded": model_ready,
    }
    if model_load_error:
        resp["model_load_error"] = model_load_error
    return resp


@app.post("/transcribe")
async def transcribe(file: UploadFile = File(...)):
    """
    Upload a radio audio clip, get back the full structured transcript:
    full text, timestamped segments, per-word confidence, and any
    low-confidence words worth flagging in the UI.
    Applies bandpass filtering + normalization before transcribing.
    """
    result = await _run_transcription(file, apply_preprocessing=True)
    return JSONResponse(content=result)


@app.post("/transcribe/raw")
async def transcribe_raw(file: UploadFile = File(...)):
    """Same as /transcribe but skips the bandpass/normalize preprocessing
    step — useful for comparing against clean (non-radio) audio, or if a
    teammate wants to test preprocessing impact directly."""
    result = await _run_transcription(file, apply_preprocessing=False)
    return JSONResponse(content=result)


@app.get("/")
async def root():
    return {
        "service": "Silent Co-Driver STT",
        "docs": "/docs",
        "endpoints": ["/health", "/transcribe", "/transcribe/raw"],
    }
