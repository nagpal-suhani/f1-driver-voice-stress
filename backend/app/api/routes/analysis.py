from __future__ import annotations

import json
from typing import Any, Dict, Optional

import httpx
from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from app.core.config import get_settings
from app.models.schemas import (
    AnalyzeAudioResponse,
    AnalyzeSessionRequest,
    HealthResponse,
    RaceSnapshot,
    SessionAnalysisResponse,
)
from app.services import analysis_service, audio_service, demo_data, model_service, openf1_service
from app.services.audio_service import InvalidAudioError
from app.services.openf1_service import OpenF1Error

router = APIRouter(tags=["analysis"])
settings = get_settings()


@router.get("/health", response_model=HealthResponse)
async def health():
    openf1_ok = None
    if not settings.demo_mode:
        openf1_ok = await openf1_service.is_reachable()
    return HealthResponse(
        status="ok",
        demo_mode=settings.demo_mode,
        openf1_reachable=openf1_ok,
    )


@router.post("/analyze-audio", response_model=AnalyzeAudioResponse)
async def analyze_audio(file: UploadFile = File(...), context: Optional[str] = Form(None)):
    """
    Accepts an audio file plus an optional `context` form field (a JSON
    string — see app/services/model_service.py docstring for the exact
    shape) carrying whatever F1 session/driver/lap details the
    frontend already has for this clip. Both are forwarded to your
    external model API in a single request.
    """
    contents_preview = await file.read()
    size_bytes = len(contents_preview)
    await file.seek(0)

    try:
        audio_service.validate_upload(file, size_bytes)
    except InvalidAudioError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    parsed_context: Optional[Dict[str, Any]] = None
    if context:
        try:
            parsed_context = json.loads(context)
        except ValueError:
            raise HTTPException(status_code=400, detail="`context` must be valid JSON.")

    tmp_path = await audio_service.save_temp_file(file)
    try:
        audio_result, driver_state, vocal_features, model_source = await audio_service.analyze_audio_file(
            tmp_path, context=parsed_context, original_filename=file.filename
        )
    finally:
        audio_service.cleanup_temp_file(tmp_path)

    return AnalyzeAudioResponse(
        audio=audio_result,
        driver_state=driver_state,
        vocal_features=vocal_features,
        model_source=model_source,
    )


async def _download_openf1_clip(recording_url: str) -> Optional[str]:
    """Downloads an OpenF1 team-radio recording to a local temp file so
    it can be sent to the external model API. Returns None (never
    raises) if the download fails — caller treats that as 'no audio
    available' and falls back gracefully."""
    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            resp = await client.get(recording_url)
            resp.raise_for_status()
            contents = resp.content
    except httpx.HTTPError:
        return None

    import tempfile
    import uuid

    ext = ".mp3" if recording_url.lower().endswith(".mp3") else ".wav"
    tmp_path = f"{tempfile.gettempdir()}/openf1_radio_{uuid.uuid4().hex}{ext}"
    with open(tmp_path, "wb") as fh:
        fh.write(contents)
    return tmp_path


@router.post("/analyze-session", response_model=SessionAnalysisResponse)
async def analyze_session(payload: AnalyzeSessionRequest):
    session_key = payload.session_key
    driver_number = payload.driver_number
    is_demo = settings.demo_mode or session_key >= demo_data.DEMO_SESSION_KEY

    if is_demo:
        raw_session = demo_data.DEMO_SESSION
        raw_driver = next(
            (d for d in demo_data.demo_drivers() if d["driver_number"] == driver_number),
            demo_data.DEMO_DRIVER,
        )
        raw_laps = demo_data.demo_laps()
        raw_location = demo_data.demo_location()
        raw_race_control = demo_data.demo_race_control()
        raw_weather = demo_data.demo_weather()
        raw_stints = demo_data.demo_stints()
        raw_radio = demo_data.demo_radio_clips()
        starting_position = 8
        raw_positions = [{"position": 7}]
    else:
        try:
            raw_session = await openf1_service.get_session(session_key)
            raw_driver = await openf1_service.get_driver(session_key, driver_number)
            raw_laps = await openf1_service.list_laps(session_key, driver_number)
            raw_location = await openf1_service.list_location(session_key, driver_number)
            raw_race_control = await openf1_service.list_race_control(session_key)
            raw_weather = await openf1_service.list_weather(session_key)
            raw_stints = await openf1_service.list_stints(session_key, driver_number)
            raw_radio = await openf1_service.list_team_radio(session_key, driver_number)
            raw_positions = await openf1_service.list_position(session_key, driver_number)
            starting_position = None
        except OpenF1Error:
            raise HTTPException(status_code=503, detail="Unable to retrieve session data from OpenF1.")

    laps = analysis_service.build_lap_entries(raw_laps)
    race_snapshot: RaceSnapshot = analysis_service.build_race_snapshot(laps, raw_positions, starting_position)

    radio_clips = (
        demo_data.demo_radio_clips()
        if is_demo
        else [
            {
                "date": r.get("date"),
                "recording_url": r.get("recording_url"),
                "lap_number": r.get("lap_number"),
                "source": "openf1",
            }
            for r in raw_radio
        ]
    )
    radio_lap_numbers = [r["lap_number"] for r in radio_clips if r.get("lap_number") is not None]

    if is_demo:
        audio_result, driver_state, vocal_features, _model_source = audio_service.demo_result(None)
    else:
        # Real mode: analyze the most recent OpenF1 radio clip (if any)
        # through your external model API, using actual session/driver/
        # lap context. Falls back to a demo placeholder if there's no
        # clip, the download fails, or the model API is unavailable.
        analyzed = False
        if radio_clips:
            latest_clip = radio_clips[-1]
            recording_url = latest_clip.get("recording_url")
            if recording_url:
                tmp_path = await _download_openf1_clip(recording_url)
                if tmp_path:
                    clip_lap = latest_clip.get("lap_number")
                    matching_lap = next((l for l in laps if l.lap_number == clip_lap), None)
                    ctx = model_service.build_context(
                        session=raw_session,
                        driver=raw_driver,
                        lap_context={
                            "lap_number": clip_lap,
                            "lap_time": matching_lap.lap_duration if matching_lap else None,
                            "delta_to_previous": matching_lap.delta_to_previous if matching_lap else None,
                        },
                        audio_filename=recording_url.split("/")[-1],
                        duration_seconds=None,
                        source="openf1",
                    )
                    audio_result, driver_state, vocal_features, _model_source = await audio_service.analyze_audio_file(
                        tmp_path, context=ctx
                    )
                    audio_service.cleanup_temp_file(tmp_path)
                    analyzed = True

        if not analyzed:
            audio_result, driver_state, vocal_features, _model_source = audio_service.demo_result(None)
            driver_state.is_demo = True

    association = analysis_service.compute_association(driver_state.label, laps, radio_lap_numbers)

    return SessionAnalysisResponse(
        driver=analysis_service.build_driver_summary(raw_driver, driver_number),
        session=analysis_service.build_session_summary(raw_session, session_key),
        audio=audio_result,
        driver_state=driver_state,
        vocal_features=vocal_features,
        race=race_snapshot,
        laps=laps,
        location=analysis_service.build_location_points(raw_location),
        race_control=analysis_service.build_race_control(raw_race_control),
        weather=analysis_service.build_weather(raw_weather),
        stints=analysis_service.build_stints(raw_stints),
        radio_clips=[
            {
                "date": c.get("date"),
                "recording_url": c.get("recording_url"),
                "lap_number": c.get("lap_number"),
                "source": c.get("source", "openf1"),
            }
            for c in radio_clips
        ],
        analysis=association,
        is_demo=is_demo,
    )
