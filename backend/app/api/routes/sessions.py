from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query

from app.core.config import get_settings
from app.models.schemas import DriverSummary, MeetingSummary, SessionSummary
from app.services import demo_data, openf1_service
from app.services.openf1_service import OpenF1Error

router = APIRouter(tags=["sessions"])
settings = get_settings()


@router.get("/meetings", response_model=List[MeetingSummary])
async def get_meetings(year: int = Query(..., description="Season year, e.g. 2025")):
    if settings.demo_mode:
        return demo_data.demo_meetings()
    try:
        raw = await openf1_service.list_meetings(year)
    except OpenF1Error:
        # graceful fallback — never a blank page (spec §44)
        return demo_data.demo_meetings()
    if not raw:
        return []
    return raw


@router.get("/sessions", response_model=List[SessionSummary])
async def get_sessions(
    year: Optional[int] = Query(None),
    meeting_key: Optional[int] = Query(None),
):
    if settings.demo_mode:
        return demo_data.demo_sessions()
    try:
        raw = await openf1_service.list_sessions(year=year, meeting_key=meeting_key)
    except OpenF1Error:
        return demo_data.demo_sessions()
    return raw


@router.get("/sessions/{session_key}", response_model=SessionSummary)
async def get_session(session_key: int):
    if settings.demo_mode or session_key >= demo_data.DEMO_SESSION_KEY:
        return demo_data.DEMO_SESSION
    try:
        row = await openf1_service.get_session(session_key)
    except OpenF1Error:
        raise HTTPException(status_code=503, detail="Unable to retrieve session data.")
    if not row:
        raise HTTPException(status_code=404, detail="Session not found.")
    return row


@router.get("/sessions/{session_key}/drivers", response_model=List[DriverSummary])
async def get_session_drivers(session_key: int):
    if settings.demo_mode or session_key >= demo_data.DEMO_SESSION_KEY:
        return demo_data.demo_drivers()
    try:
        raw = await openf1_service.list_drivers(session_key)
    except OpenF1Error:
        return demo_data.demo_drivers()
    return raw or demo_data.demo_drivers()


@router.get("/drivers/{driver_number}", response_model=DriverSummary)
async def get_driver(driver_number: int, session_key: int = Query(...)):
    if settings.demo_mode or session_key >= demo_data.DEMO_SESSION_KEY:
        match = next((d for d in demo_data.demo_drivers() if d["driver_number"] == driver_number), demo_data.DEMO_DRIVER)
        return match
    try:
        row = await openf1_service.get_driver(session_key, driver_number)
    except OpenF1Error:
        raise HTTPException(status_code=503, detail="Unable to retrieve driver data.")
    if not row:
        raise HTTPException(status_code=404, detail="Driver not found.")
    return row
