"""
External Model API Client.

This is the ONLY file that talks to your AI model API. It sends the
radio audio clip plus F1 session/driver/lap context as a single
multipart request, and expects one JSON response back containing the
transcript AND the vocal-state classification together.

============================================================
REQUEST — what this backend sends to `MODEL_API_URL`
============================================================
POST {MODEL_API_URL}
Headers:
    Authorization: Bearer {MODEL_API_KEY}

Multipart form-data body:
    audio     — the raw audio file (mp3/wav/m4a/ogg/webm/flac)
    context   — a JSON string (see shape below), sent as a plain form field

`context` JSON shape:
{
  "session": {
    "session_key": 9159,
    "session_name": "Race",
    "session_type": "Race",
    "circuit_short_name": "Silverstone",
    "country_name": "United Kingdom",
    "year": 2025
  },
  "driver": {
    "driver_number": 44,
    "full_name": "Driver Name",
    "team_name": "Team Name"
  },
  "lap_context": {
    "lap_number": 19,          // nullable — the lap nearest this radio clip, if known
    "lap_time": 91.482,        // nullable
    "delta_to_previous": 0.577 // nullable
  },
  "audio_meta": {
    "filename": "radio_clip.wav",
    "duration_seconds": 6.8,   // nullable — best-effort, may be null
    "source": "upload"         // "upload" | "openf1"
  }
}

Any field you don't have context for is sent as `null` — never
fabricated. If you don't need the F1 context at all, your API can just
ignore the `context` field.

============================================================
RESPONSE — what this backend expects back from your API
============================================================
200 OK, JSON body:
{
  "transcript": {
    "text": "The rear is moving quite a lot through Turn 7.",
    "segments": [                        // optional — [] if you don't have timestamps
      {"start": 0.0, "end": 2.4, "text": "The rear is moving quite a lot"},
      {"start": 2.4, "end": 4.8, "text": "through Turn 7."}
    ]
  },
  "vocal_state": {
    "label": "STRESSED",                 // MUST be one of: CALM | ELEVATED | STRESSED | FATIGUE-LIKE
    "confidence": 0.87                   // 0.0 - 1.0
  },
  "vocal_features": {                    // optional block — omit fields you can't support, don't fabricate
    "speech_rate_wpm": 168.0,
    "energy": "HIGH",                    // "LOW" | "MODERATE" | "HIGH"
    "voice_activity": "HIGH",            // "LOW" | "MODERATE" | "HIGH"
    "pitch_variation_pct": 8.0
  }
}

`vocal_features` and `transcript.segments` are optional — omit fields
you don't have rather than inventing values; the frontend renders
missing fields as "N/A".

If your API call fails (network error, non-200 status, malformed
response, or missing required fields), this module raises
`ModelUnavailable` and the caller (`audio_service.py`) automatically
falls back to demo data — the app never crashes on a model failure.
============================================================
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import httpx

from app.core.config import get_settings

settings = get_settings()

VALID_LABELS = {"CALM", "ELEVATED", "STRESSED", "FATIGUE-LIKE"}


class ModelUnavailable(Exception):
    """Raised when the external model API can't be reached or returns
    something we can't use. Caught by audio_service.py to trigger the
    demo-data fallback."""


@dataclass
class TranscriptionResult:
    text: str
    segments: List[dict] = field(default_factory=list)


@dataclass
class VocalStateResult:
    label: str
    confidence: float


@dataclass
class VocalFeaturesResult:
    speech_rate_wpm: Optional[float] = None
    energy: Optional[str] = None
    voice_activity: Optional[str] = None
    pitch_variation_pct: Optional[float] = None


@dataclass
class ExternalAnalysisResult:
    transcription: TranscriptionResult
    vocal_state: VocalStateResult
    vocal_features: VocalFeaturesResult


def is_configured() -> bool:
    return bool(settings.model_api_url)


def build_context(
    session: Optional[Dict[str, Any]] = None,
    driver: Optional[Dict[str, Any]] = None,
    lap_context: Optional[Dict[str, Any]] = None,
    audio_filename: Optional[str] = None,
    duration_seconds: Optional[float] = None,
    source: str = "upload",
) -> Dict[str, Any]:
    """Assembles the `context` JSON object described in the module
    docstring. Any piece the caller doesn't have is sent as null rather
    than guessed."""
    return {
        "session": session,
        "driver": driver,
        "lap_context": lap_context,
        "audio_meta": {
            "filename": audio_filename,
            "duration_seconds": duration_seconds,
            "source": source,
        },
    }


def analyze_audio(audio_path: str, context: Dict[str, Any]) -> ExternalAnalysisResult:
    """
    Sends the audio file + context to MODEL_API_URL and parses the
    response into the dataclasses above. Raises ModelUnavailable on
    any failure — never lets an exception from httpx/json bubble up
    to the route handler.
    """
    if not is_configured():
        raise ModelUnavailable("MODEL_API_URL is not configured (set it in backend/.env).")

    headers = {"Authorization": f"Bearer {settings.model_api_key}"} if settings.model_api_key else {}

    try:
        with open(audio_path, "rb") as audio_file:
            files = {"audio": (audio_path.split("/")[-1], audio_file, "application/octet-stream")}
            data = {"context": json.dumps(context)}
            with httpx.Client(timeout=settings.model_api_timeout_seconds) as client:
                resp = client.post(settings.model_api_url, headers=headers, files=files, data=data)
                resp.raise_for_status()
                payload = resp.json()
    except (httpx.HTTPError, OSError, ValueError) as exc:
        raise ModelUnavailable(f"External model API call failed: {exc}") from exc

    return _parse_response(payload)


def _parse_response(payload: Dict[str, Any]) -> ExternalAnalysisResult:
    transcript_block = payload.get("transcript") or {}
    vocal_state_block = payload.get("vocal_state") or {}
    vocal_features_block = payload.get("vocal_features") or {}

    text = transcript_block.get("text")
    if not isinstance(text, str) or not text.strip():
        raise ModelUnavailable("External model API response missing 'transcript.text'.")

    label = vocal_state_block.get("label")
    if label not in VALID_LABELS:
        raise ModelUnavailable(
            f"External model API returned an invalid vocal_state.label: {label!r} "
            f"(must be one of {sorted(VALID_LABELS)})."
        )

    try:
        confidence = float(vocal_state_block.get("confidence"))
    except (TypeError, ValueError) as exc:
        raise ModelUnavailable("External model API response missing/invalid 'vocal_state.confidence'.") from exc

    segments = transcript_block.get("segments") or []
    if not isinstance(segments, list):
        segments = []

    return ExternalAnalysisResult(
        transcription=TranscriptionResult(text=text, segments=segments),
        vocal_state=VocalStateResult(label=label, confidence=confidence),
        vocal_features=VocalFeaturesResult(
            speech_rate_wpm=vocal_features_block.get("speech_rate_wpm"),
            energy=vocal_features_block.get("energy"),
            voice_activity=vocal_features_block.get("voice_activity"),
            pitch_variation_pct=vocal_features_block.get("pitch_variation_pct"),
        ),
    )
