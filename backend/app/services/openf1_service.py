"""
Thin, defensive client around the official OpenF1 API
(https://openf1.org/docs/). Only documented endpoints are used:

  /meetings  /sessions  /drivers  /laps  /location  /position
  /race_control  /weather  /stints  /team_radio  /session_result

Nothing here is proxied blindly to the frontend — routes in
`app/api/routes/` shape the response into our own schemas.

Historical OpenF1 endpoints do not require authentication today, so no
API key handling is invented here. If OpenF1 ever requires one, add it
via `Settings.openf1_api_key` and an Authorization header — do not
hardcode a fake requirement in the meantime.
"""
from __future__ import annotations

import time
from typing import Any, Dict, List, Optional

import httpx

from app.core.config import get_settings

settings = get_settings()

# very small in-memory TTL cache to avoid hammering OpenF1 for data that
# rarely changes within a demo session (sessions/drivers/laps lists).
_CACHE: Dict[str, tuple[float, Any]] = {}
_CACHE_TTL_SECONDS = 60


class OpenF1Error(Exception):
    """Raised when OpenF1 cannot be reached or returns something unusable."""


def _cache_get(key: str) -> Optional[Any]:
    entry = _CACHE.get(key)
    if not entry:
        return None
    ts, value = entry
    if time.time() - ts > _CACHE_TTL_SECONDS:
        _CACHE.pop(key, None)
        return None
    return value


def _cache_set(key: str, value: Any) -> None:
    _CACHE[key] = (time.time(), value)


async def _get(path: str, params: Optional[Dict[str, Any]] = None, use_cache: bool = True) -> List[Dict[str, Any]]:
    cache_key = f"{path}?{params}"
    if use_cache:
        cached = _cache_get(cache_key)
        if cached is not None:
            return cached

    url = f"{settings.openf1_base_url}{path}"
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(url, params=params or {})
            resp.raise_for_status()
            data = resp.json()
            if not isinstance(data, list):
                data = []
            if use_cache:
                _cache_set(cache_key, data)
            return data
    except (httpx.HTTPError, ValueError) as exc:
        raise OpenF1Error(f"OpenF1 request failed for {path}: {exc}") from exc


async def is_reachable() -> bool:
    try:
        await _get("/sessions", {"session_key": "latest"}, use_cache=False)
        return True
    except OpenF1Error:
        return False


# ------------------------------------------------------------ meetings
async def list_meetings(year: int) -> List[Dict[str, Any]]:
    return await _get("/meetings", {"year": year})


# ------------------------------------------------------------ sessions
async def list_sessions(year: Optional[int] = None, meeting_key: Optional[int] = None) -> List[Dict[str, Any]]:
    params: Dict[str, Any] = {}
    if year is not None:
        params["year"] = year
    if meeting_key is not None:
        params["meeting_key"] = meeting_key
    return await _get("/sessions", params)


async def get_session(session_key: int) -> Optional[Dict[str, Any]]:
    rows = await _get("/sessions", {"session_key": session_key})
    return rows[0] if rows else None


# ------------------------------------------------------------- drivers
async def list_drivers(session_key: int) -> List[Dict[str, Any]]:
    return await _get("/drivers", {"session_key": session_key})


async def get_driver(session_key: int, driver_number: int) -> Optional[Dict[str, Any]]:
    rows = await _get("/drivers", {"session_key": session_key, "driver_number": driver_number})
    return rows[0] if rows else None


# ---------------------------------------------------------------- laps
async def list_laps(session_key: int, driver_number: int) -> List[Dict[str, Any]]:
    rows = await _get("/laps", {"session_key": session_key, "driver_number": driver_number})
    return sorted(rows, key=lambda r: r.get("lap_number") or 0)


# ------------------------------------------------------------ location
async def list_location(session_key: int, driver_number: int, limit_recent: int = 1500) -> List[Dict[str, Any]]:
    rows = await _get("/location", {"session_key": session_key, "driver_number": driver_number})
    # Downsample defensively — OpenF1 location data can be very dense
    # (spec §60: never request/return huge unfiltered telemetry sets).
    if len(rows) > limit_recent:
        step = max(1, len(rows) // limit_recent)
        rows = rows[::step]
    return rows


# ------------------------------------------------------------ position
async def list_position(session_key: int, driver_number: int) -> List[Dict[str, Any]]:
    return await _get("/position", {"session_key": session_key, "driver_number": driver_number})


# -------------------------------------------------------- race control
async def list_race_control(session_key: int) -> List[Dict[str, Any]]:
    return await _get("/race_control", {"session_key": session_key})


# -------------------------------------------------------------- weather
async def list_weather(session_key: int) -> List[Dict[str, Any]]:
    return await _get("/weather", {"session_key": session_key})


# --------------------------------------------------------------- stints
async def list_stints(session_key: int, driver_number: int) -> List[Dict[str, Any]]:
    return await _get("/stints", {"session_key": session_key, "driver_number": driver_number})


# ----------------------------------------------------------- team_radio
async def list_team_radio(session_key: int, driver_number: int) -> List[Dict[str, Any]]:
    return await _get("/team_radio", {"session_key": session_key, "driver_number": driver_number})


# --------------------------------------------------------- session_result
async def list_session_result(session_key: int, driver_number: Optional[int] = None) -> List[Dict[str, Any]]:
    params: Dict[str, Any] = {"session_key": session_key}
    if driver_number is not None:
        params["driver_number"] = driver_number
    return await _get("/session_result", params)
