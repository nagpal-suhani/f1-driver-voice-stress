from __future__ import annotations

from typing import List

from fastapi import APIRouter

from app.core.config import get_settings
from app.models.schemas import RadioClip
from app.services import demo_data, openf1_service
from app.services.openf1_service import OpenF1Error

router = APIRouter(tags=["radio"])
settings = get_settings()


@router.get("/sessions/{session_key}/radio/{driver_number}", response_model=List[RadioClip])
async def get_radio(session_key: int, driver_number: int):
    """
    Mode A/B fallback (spec §6): if OpenF1 has no team-radio recordings
    for this session/driver, we return an empty list — NOT an error.
    The frontend then offers "Upload driver radio" instead of treating
    the absence as an application failure.
    """
    if settings.demo_mode or session_key >= demo_data.DEMO_SESSION_KEY:
        return demo_data.demo_radio_clips()

    try:
        raw = await openf1_service.list_team_radio(session_key, driver_number)
    except OpenF1Error:
        return []

    return [
        RadioClip(
            date=r.get("date"),
            recording_url=r.get("recording_url"),
            lap_number=r.get("lap_number"),
            source="openf1",
        )
        for r in raw
    ]
