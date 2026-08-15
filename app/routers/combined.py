"""
This is the endpoint the frontend should actually call: one audio
upload in, both models run (concurrently), two JSON files saved to
output_data/ sharing the same request_id, both results returned in
one response.
"""

import asyncio
import os
import tempfile
import time
import uuid

from fastapi import APIRouter, File, HTTPException, UploadFile
from starlette.concurrency import run_in_threadpool

from app.models.emotion_model import (
    TARGET_SAMPLE_RATE,
    predict_arousal_dominance_valence,
)
from app.services.audio_utils import load_and_resample
from app.services.mood_mapping import map_to_mood, mood_explanation
from app.services.output_writer import save_json
from app.services.stt_pipeline import transcribe_audio

router = APIRouter(prefix="/api/process", tags=["combined"])


def _run_stress(raw_bytes: bytes) -> dict:
    """Blocking stress-analysis work, meant to run inside a threadpool."""
    audio_array = load_and_resample(raw_bytes)
    arousal, dominance, valence = predict_arousal_dominance_valence(
        audio_array, TARGET_SAMPLE_RATE
    )
    mood = map_to_mood(arousal, valence, dominance)
    return {
        "arousal": round(float(arousal), 3),
        "dominance": round(float(dominance), 3),
        "valence": round(float(valence), 3),
        "mood": mood,
        "explanation": mood_explanation(arousal, valence, dominance, mood),
    }


def _run_transcription(temp_path: str) -> dict:
    """Blocking transcription work, meant to run inside a threadpool."""
    return transcribe_audio(temp_path, apply_preprocessing=True)


@router.post("")
async def process_audio(audio: UploadFile = File(...)):
    """
    Upload ONE audio clip. Runs the stress model and the transcription
    model on it concurrently, saves each result as its own JSON file
    under output_data/ (named {request_id}_stress.json and
    {request_id}_transcript.json), and returns both in one response.

    This is the endpoint the frontend should call for the main "play
    a radio clip, see mood + transcript + lap chart" flow -- rather
    than calling /api/stress/analyze and /api/transcribe separately.
    """
    if audio.content_type is None or not audio.content_type.startswith("audio"):
        raise HTTPException(status_code=400, detail="Please upload an audio file")

    raw_bytes = await audio.read()
    if not raw_bytes:
        raise HTTPException(status_code=400, detail="Empty file")

    request_id = str(uuid.uuid4())[:8]

    # stt_pipeline needs a real file on disk; write the upload once and
    # let both branches read from it (the stress branch works off the
    # raw bytes directly, no temp file needed for that side).
    suffix = os.path.splitext(audio.filename or "")[1] or ".wav"
    fd, temp_path = tempfile.mkstemp(suffix=suffix, prefix="process_")
    os.close(fd)
    with open(temp_path, "wb") as f:
        f.write(raw_bytes)

    start = time.time()
    try:
        # Run both models concurrently in separate threadpool workers --
        # they're independent (different models, different memory) so
        # this overlaps their runtime instead of doing them back to back.
        stress_result, transcript_result = await asyncio.gather(
            run_in_threadpool(_run_stress, raw_bytes),
            run_in_threadpool(_run_transcription, temp_path),
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Processing failed: {exc}")
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

    stress_result["request_id"] = request_id
    transcript_result["request_id"] = request_id

    stress_path = save_json(stress_result, request_id, "stress")
    transcript_path = save_json(transcript_result, request_id, "transcript")

    return {
        "request_id": request_id,
        "processing_time_sec": round(time.time() - start, 2),
        "stress": stress_result,
        "transcript": transcript_result,
        "output_files": {
            "stress_json": stress_path,
            "transcript_json": transcript_path,
        },
    }