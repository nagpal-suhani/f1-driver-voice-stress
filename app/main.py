import asyncio
import logging
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.concurrency import run_in_threadpool

from app.routers import combined, correlation, stress, transcription
from app.services import stt_pipeline

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("silent-codriver")

stt_model_load_error: str | None = None


async def _load_stt_model_background():
    """The Whisper model download/load can take a while on first run --
    kick it off in the background at startup instead of blocking the
    whole server (including /health) until it finishes. If a request
    hits /api/transcribe before this finishes, transcribe_audio() will
    just load it on-demand at that point instead."""
    global stt_model_load_error
    logger.info("Loading speech-to-text model in background...")
    start = time.time()
    try:
        await run_in_threadpool(stt_pipeline._get_model)
        logger.info(f"STT model loaded in {time.time() - start:.1f}s")
    except Exception as e:
        stt_model_load_error = str(e)
        logger.error(f"STT model failed to load: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    asyncio.create_task(_load_stt_model_background())
    yield
    logger.info("Shutting down.")


app = FastAPI(title="Silent Co-Driver API", lifespan=lifespan)

# Wide-open CORS for hackathon speed. Tighten this if you have time.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(stress.router)
app.include_router(correlation.router)
app.include_router(transcription.router)
app.include_router(combined.router)



@app.get("/health")
async def health():
    stt_ready = "model" in stt_pipeline._model_cache
    resp = {
        "status": "ok",
        "stt_model_loaded": stt_ready,
    }
    if stt_model_load_error:
        resp["stt_model_load_error"] = stt_model_load_error
    return resp