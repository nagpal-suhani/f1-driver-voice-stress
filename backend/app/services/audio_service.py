"""
Audio Service.

Owns everything related to a raw audio file: validation, temporary
storage, running it through the external model API, and cleaning up.
Nothing here talks to OpenF1 or builds HTTP responses — see
`app/api/routes/analysis.py` for that.

Temporary files are written under a system temp dir and removed after
processing (do not permanently store audio unless required).
"""
from __future__ import annotations

import os
import tempfile
import uuid
from typing import Any, Dict, Optional

from fastapi import UploadFile

from app.core.config import get_settings
from app.models.schemas import AudioResult, DriverState, TranscriptSegment, VocalFeatures
from app.services import demo_data, model_service
from app.services.model_service import ModelUnavailable

settings = get_settings()

ALLOWED_EXTENSIONS = {".mp3", ".wav", ".m4a", ".ogg", ".webm", ".flac"}


class InvalidAudioError(Exception):
    pass


def validate_upload(file: UploadFile, size_bytes: int) -> None:
    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise InvalidAudioError(f"Unsupported audio format '{ext or 'unknown'}'.")
    max_bytes = settings.max_audio_mb * 1024 * 1024
    if size_bytes > max_bytes:
        raise InvalidAudioError(f"Audio file exceeds the maximum allowed size ({settings.max_audio_mb} MB).")
    if size_bytes == 0:
        raise InvalidAudioError("Uploaded audio file is empty.")


async def save_temp_file(file: UploadFile) -> str:
    ext = os.path.splitext(file.filename or "")[1].lower() or ".wav"
    tmp_dir = tempfile.gettempdir()
    tmp_path = os.path.join(tmp_dir, f"radio_{uuid.uuid4().hex}{ext}")
    contents = await file.read()
    with open(tmp_path, "wb") as fh:
        fh.write(contents)
    return tmp_path


def cleanup_temp_file(path: Optional[str]) -> None:
    if path and os.path.exists(path):
        try:
            os.remove(path)
        except OSError:
            pass


def _duration_seconds(audio_path: str) -> Optional[float]:
    try:
        import soundfile as sf  # lazy import — optional dependency

        info = sf.info(audio_path)
        return round(info.frames / info.samplerate, 2) if info.samplerate else None
    except Exception:  # noqa: BLE001 — duration is a nice-to-have, not required
        return None


async def analyze_audio_file(
    audio_path: str,
    context: Optional[Dict[str, Any]] = None,
    original_filename: Optional[str] = None,
) -> tuple[AudioResult, DriverState, VocalFeatures, str]:
    """
    Sends the audio (+ optional F1 context) to your external model API
    via model_service.analyze_audio(), and maps the response into our
    schemas. Falls back to demo data if the API is unconfigured,
    unreachable, or returns something unusable — never raises to the
    caller in that case.
    """
    duration = _duration_seconds(audio_path)

    if settings.demo_mode:
        return _demo_result(duration)

    ctx = context or model_service.build_context(
        audio_filename=original_filename,
        duration_seconds=duration,
        source="upload",
    )

    try:
        result = model_service.analyze_audio(audio_path, ctx)

        segments = [
            TranscriptSegment(start=s.get("start", 0.0), end=s.get("end", 0.0), text=s.get("text", ""))
            for s in result.transcription.segments
        ]
        audio_result = AudioResult(
            source="upload",
            duration=duration,
            transcript=result.transcription.text or None,
            segments=segments,
        )
        driver_state = DriverState(
            label=result.vocal_state.label,  # type: ignore[arg-type]
            confidence=round(result.vocal_state.confidence, 3),
            is_demo=False,
        )
        vocal_features = VocalFeatures(
            speech_rate_wpm=result.vocal_features.speech_rate_wpm,
            speech_rate_delta_pct=None,  # requires a session baseline your API isn't given here
            energy=result.vocal_features.energy,  # type: ignore[arg-type]
            voice_activity=result.vocal_features.voice_activity,  # type: ignore[arg-type]
            pitch_variation_pct=result.vocal_features.pitch_variation_pct,
        )
        return audio_result, driver_state, vocal_features, "custom_model"

    except ModelUnavailable:
        return _demo_result(duration)


def demo_result(duration: Optional[float] = None) -> tuple[AudioResult, DriverState, VocalFeatures, str]:
    """Public entry point for callers that need demo audio/state without a real file (e.g. session-level placeholder)."""
    return _demo_result(duration)


def _demo_result(duration: Optional[float]) -> tuple[AudioResult, DriverState, VocalFeatures, str]:
    demo_audio = demo_data.demo_audio_result()
    if duration:
        demo_audio["duration"] = duration
    audio_result = AudioResult(**demo_audio)
    driver_state = DriverState(**demo_data.demo_driver_state())
    vocal_features = VocalFeatures(**demo_data.demo_vocal_features())
    return audio_result, driver_state, vocal_features, "demo"
