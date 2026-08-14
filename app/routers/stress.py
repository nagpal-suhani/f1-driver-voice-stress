from fastapi import APIRouter, File, HTTPException, UploadFile

from app.models.emotion_model import (
    TARGET_SAMPLE_RATE,
    predict_arousal_dominance_valence,
)
from app.services.audio_utils import load_and_resample
from app.services.mood_mapping import map_to_mood, mood_explanation

router = APIRouter(prefix="/api/stress", tags=["stress"])


@router.post("/analyze")
async def analyze_stress(audio: UploadFile = File(...)):
    """
    Takes an uploaded audio clip, returns arousal/dominance/valence
    scores plus a mapped mood label (Calm / Stressed / Tired).

    This is independent of the speech-to-text endpoint -- your
    teammate's transcription endpoint and this one both take the
    same raw audio file, just processed by different models. The
    frontend calls both and displays them side by side.
    """
    if audio.content_type is None or not audio.content_type.startswith("audio"):
        raise HTTPException(status_code=400, detail="Please upload an audio file")

    raw_bytes = await audio.read()
    if not raw_bytes:
        raise HTTPException(status_code=400, detail="Empty file")

    try:
        audio_array = load_and_resample(raw_bytes)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Could not read audio: {exc}")

    try:
        arousal, dominance, valence = predict_arousal_dominance_valence(
            audio_array, TARGET_SAMPLE_RATE
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Model inference failed: {exc}")

    mood = map_to_mood(arousal, valence, dominance)

    return {
        "arousal": round(float(arousal), 3),
        "dominance": round(float(dominance), 3),
        "valence": round(float(valence), 3),
        "mood": mood,
        "explanation": mood_explanation(arousal, valence, dominance, mood),
    }