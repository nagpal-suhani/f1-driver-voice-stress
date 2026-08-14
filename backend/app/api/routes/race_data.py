from __future__ import annotations

from typing import List

from fastapi import APIRouter

from app.core.config import get_settings
from app.models.schemas import LapEntry, LocationPoint, RaceControlEvent, StintEntry, WeatherSample
from app.services import analysis_service, demo_data, openf1_service
from app.services.openf1_service import OpenF1Error

router = APIRouter(tags=["race-data"])
settings = get_settings()


def _is_demo(session_key: int) -> bool:
    return settings.demo_mode or session_key >= demo_data.DEMO_SESSION_KEY


@router.get("/sessions/{session_key}/laps/{driver_number}", response_model=List[LapEntry])
async def get_laps(session_key: int, driver_number: int):
    if _is_demo(session_key):
        return analysis_service.build_lap_entries(demo_data.demo_laps())
    try:
        raw = await openf1_service.list_laps(session_key, driver_number)
    except OpenF1Error:
        return analysis_service.build_lap_entries(demo_data.demo_laps())
    if not raw:
        return []
    return analysis_service.build_lap_entries(raw)


@router.get("/sessions/{session_key}/location/{driver_number}", response_model=List[LocationPoint])
async def get_location(session_key: int, driver_number: int):
    if _is_demo(session_key):
        return analysis_service.build_location_points(demo_data.demo_location())
    try:
        raw = await openf1_service.list_location(session_key, driver_number)
    except OpenF1Error:
        return analysis_service.build_location_points(demo_data.demo_location())
    return analysis_service.build_location_points(raw)


@router.get("/sessions/{session_key}/race-control", response_model=List[RaceControlEvent])
async def get_race_control(session_key: int):
    if _is_demo(session_key):
        return analysis_service.build_race_control(demo_data.demo_race_control())
    try:
        raw = await openf1_service.list_race_control(session_key)
    except OpenF1Error:
        return analysis_service.build_race_control(demo_data.demo_race_control())
    return analysis_service.build_race_control(raw)


@router.get("/sessions/{session_key}/weather", response_model=List[WeatherSample])
async def get_weather(session_key: int):
    if _is_demo(session_key):
        return analysis_service.build_weather(demo_data.demo_weather())
    try:
        raw = await openf1_service.list_weather(session_key)
    except OpenF1Error:
        return analysis_service.build_weather(demo_data.demo_weather())
    return analysis_service.build_weather(raw)


@router.get("/sessions/{session_key}/stints/{driver_number}", response_model=List[StintEntry])
async def get_stints(session_key: int, driver_number: int):
    if _is_demo(session_key):
        return analysis_service.build_stints(demo_data.demo_stints())
    try:
        raw = await openf1_service.list_stints(session_key, driver_number)
    except OpenF1Error:
        return analysis_service.build_stints(demo_data.demo_stints())
    return analysis_service.build_stints(raw)
