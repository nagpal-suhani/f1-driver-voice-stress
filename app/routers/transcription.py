"""
Speech-to-text endpoints, adapted from the teammate's standalone STT
service (main.py + stt_pipeline.py) into a router that plugs into the
shared app -- same pattern as app/routers/stress.py.

NOTE on the upload field name: the original standalone service used
`file` as the form field name. This router uses `audio` instead, to
match the field name the stress endpoint already uses -- so the
frontend can send the exact same form field to either endpoint (or
both, via the combined /api/process endpoint). Tell your teammate if
their code/tests reference `file` directly.
"""

import os
import tempfile
import time
import uuid

from fastapi import APIRouter, File, HTTPException, UploadFile, status
from starlette.concurrency import run_in_threadpool

from app.services import stt_pipeline
from app.services.output_writer import save_json

router = APIRouter(prefix="/api/transcribe", tags=["transcription"])

MAX_FILE_SIZE_MB = 25
ALLOWED_EXTENSIONS = {".wav", ".mp3", ".m4a", ".flac", ".ogg", ".webm"}


def _validate_upload(file: UploadFile) -> str:
    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Unsupported file type '{ext}'. Allowed: {sorted(ALLOWED_EXTENSIONS)}",
        )
    return ext


async def _save_upload_to_temp(file: UploadFile, ext: str) -> str:
    """Stream the upload to a temp file, enforcing a max size limit
    while reading (rather than after loading it all into memory)."""
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


async def _run(file: UploadFile, apply_preprocessing: bool) -> dict:
    ext = _validate_upload(file)
    temp_path = await _save_upload_to_temp(file, ext)
    request_id = str(uuid.uuid4())[:8]

    try:
        start = time.time()
        # transcribe_audio is CPU-bound and blocking (audio DSP + model
        # inference) -- run it in a threadpool so it doesn't block the
        # event loop and stall other requests/health checks.
        result = await run_in_threadpool(
            stt_pipeline.transcribe_audio, temp_path, apply_preprocessing
        )
        elapsed = time.time() - start
        result["request_id"] = request_id
        result["processing_time_sec"] = round(elapsed, 2)
    except FileNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Transcription failed: {e}",
        )
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

    output_path = save_json(result, request_id, "transcript")
    result["output_file"] = output_path
    return result


@router.post("")
async def transcribe(audio: UploadFile = File(...)):
    """
    Upload a radio audio clip, get back the full structured transcript:
    full text, timestamped segments, per-word confidence, and any
    low-confidence words worth flagging in the UI.
    Applies bandpass filtering + normalization before transcribing.
    Also saves the result under output_data/{request_id}_transcript.json.
    """
    return await _run(audio, apply_preprocessing=True)


@router.post("/raw")
async def transcribe_raw(audio: UploadFile = File(...)):
    """Same as /api/transcribe but skips the bandpass/normalize
    preprocessing step -- useful for comparing against clean
    (non-radio) audio."""
    return await _run(audio, apply_preprocessing=False)


@router.get("/status")
async def transcription_status():
    """Lets the frontend check if the Whisper model has finished
    loading yet (it loads in the background at startup -- see main.py)."""
    model_ready = "model" in stt_pipeline._model_cache
    return {"model_loaded": model_ready}