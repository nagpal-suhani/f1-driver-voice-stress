"""
Demo Data Service.

Used whenever DEMO_MODE=true, or whenever a live dependency (OpenF1,
your models in model_service.py, radio availability) fails or is
missing. The frontend behaves identically either way — every response
simply carries `is_demo: true` so nobody is misled about what's real.

Nothing here pretends to be biometric/medical data — see spec §19/§64.
"""
from __future__ import annotations

import math
import random
from typing import Any, Dict, List

DEMO_MEETING_KEY = 900001
DEMO_SESSION_KEY = 900101

DEMO_DRIVER = {
    "driver_number": 44,
    "full_name": "Demo Driver",
    "name_acronym": "DEM",
    "team_name": "Apex Racing",
    "team_colour": "E10600",
    "headshot_url": None,
}

DEMO_SESSION = {
    "session_key": DEMO_SESSION_KEY,
    "meeting_key": DEMO_MEETING_KEY,
    "session_name": "Race",
    "session_type": "Race",
    "date_start": "2025-07-06T14:00:00+00:00",
    "date_end": "2025-07-06T16:00:00+00:00",
    "country_name": "United Kingdom",
    "circuit_short_name": "Silverstone",
    "year": 2025,
}

DEMO_MEETING = {
    "meeting_key": DEMO_MEETING_KEY,
    "meeting_name": "British Grand Prix",
    "country_name": "United Kingdom",
    "circuit_short_name": "Silverstone",
    "year": 2025,
    "date_start": "2025-07-06T14:00:00+00:00",
}


def demo_meetings() -> List[Dict[str, Any]]:
    return [DEMO_MEETING]


def demo_sessions() -> List[Dict[str, Any]]:
    names = ["Practice 1", "Practice 2", "Practice 3", "Qualifying", "Race"]
    return [
        {**DEMO_SESSION, "session_key": DEMO_SESSION_KEY + i, "session_name": n, "session_type": n}
        for i, n in enumerate(names)
    ]


def demo_drivers() -> List[Dict[str, Any]]:
    roster = [
        (44, "Demo Driver", "DEM", "Apex Racing", "E10600"),
        (1, "Rival One", "RIV", "Vertex GP", "1E5BC6"),
        (16, "Rival Two", "RV2", "Meridian F1", "00A86B"),
        (63, "Rival Three", "RV3", "Titan Motorsport", "C9B037"),
    ]
    return [
        {
            "driver_number": n,
            "full_name": name,
            "name_acronym": acr,
            "team_name": team,
            "team_colour": colour,
            "headshot_url": None,
        }
        for n, name, acr, team, colour in roster
    ]


def demo_laps(total: int = 52) -> List[Dict[str, Any]]:
    base = 89.7
    laps = []
    random.seed(7)
    for lap in range(1, total + 1):
        wobble = random.uniform(-0.4, 0.9)
        # Model a mid-race "stress window" around laps 17-21 with a
        # small, honest performance dip — this is what the correlation
        # panel will surface as an "observed overlap", never a causal
        # claim.
        if 17 <= lap <= 21:
            wobble += 0.7
        lap_time = round(base + wobble, 3)
        s1 = round(lap_time * 0.325, 3)
        s2 = round(lap_time * 0.345, 3)
        s3 = round(lap_time - s1 - s2, 3)
        laps.append(
            {
                "lap_number": lap,
                "lap_duration": lap_time,
                "duration_sector_1": s1,
                "duration_sector_2": s2,
                "duration_sector_3": s3,
                "is_pit_out_lap": lap in (1, 28),
            }
        )
    return laps


def demo_location(total_points: int = 400) -> List[Dict[str, Any]]:
    # A stylised closed-loop path (not a real circuit trace) purely so
    # the track map has believable geometry in demo mode. Real sessions
    # use OpenF1's actual x/y telemetry instead.
    pts = []
    for i in range(total_points):
        t = (i / total_points) * 2 * math.pi
        x = 500 * math.cos(t) + 120 * math.cos(3 * t)
        y = 300 * math.sin(t) + 80 * math.sin(2 * t)
        pts.append({"date": None, "x": round(x, 1), "y": round(y, 1), "lap_number": (i % 52) + 1})
    return pts


def demo_race_control() -> List[Dict[str, Any]]:
    return [
        {"date": "2025-07-06T14:41:00+00:00", "category": "Flag", "flag": "YELLOW", "message": "Yellow flag sector 2", "lap_number": 12},
        {"date": "2025-07-06T14:55:00+00:00", "category": "SafetyCar", "flag": None, "message": "Safety car deployed", "lap_number": 18},
        {"date": "2025-07-06T14:59:00+00:00", "category": "SafetyCar", "flag": None, "message": "Safety car in this lap", "lap_number": 20},
        {"date": "2025-07-06T15:20:00+00:00", "category": "Flag", "flag": "GREEN", "message": "Track clear", "lap_number": 21},
    ]


def demo_weather() -> List[Dict[str, Any]]:
    return [
        {"date": "2025-07-06T14:00:00+00:00", "air_temperature": 22.4, "track_temperature": 34.1, "humidity": 48.0, "wind_speed": 2.1, "rainfall": 0.0},
        {"date": "2025-07-06T15:00:00+00:00", "air_temperature": 23.1, "track_temperature": 36.7, "humidity": 44.0, "wind_speed": 2.6, "rainfall": 0.0},
    ]


def demo_stints() -> List[Dict[str, Any]]:
    return [
        {"stint_number": 1, "compound": "MEDIUM", "lap_start": 1, "lap_end": 16, "tyre_age_at_start": 0},
        {"stint_number": 2, "compound": "HARD", "lap_start": 17, "lap_end": 38, "tyre_age_at_start": 0},
        {"stint_number": 3, "compound": "SOFT", "lap_start": 39, "lap_end": 52, "tyre_age_at_start": 0},
    ]


def demo_radio_clips() -> List[Dict[str, Any]]:
    return [
        {"date": "2025-07-06T14:22:00+00:00", "recording_url": None, "lap_number": 9, "source": "demo"},
        {"date": "2025-07-06T14:38:00+00:00", "recording_url": None, "lap_number": 17, "source": "demo"},
        {"date": "2025-07-06T14:41:00+00:00", "recording_url": None, "lap_number": 19, "source": "demo"},
        {"date": "2025-07-06T15:05:00+00:00", "recording_url": None, "lap_number": 27, "source": "demo"},
    ]


DEMO_TRANSCRIPT = "The rear is moving quite a lot through Turn 7, box is aware, keep pushing."


def demo_audio_result() -> Dict[str, Any]:
    return {
        "source": "demo",
        "duration": 6.8,
        "transcript": DEMO_TRANSCRIPT,
        "segments": [
            {"start": 0.0, "end": 2.4, "text": "The rear is moving quite a lot"},
            {"start": 2.4, "end": 4.1, "text": "through Turn 7,"},
            {"start": 4.1, "end": 6.8, "text": "box is aware, keep pushing."},
        ],
    }


def demo_driver_state() -> Dict[str, Any]:
    return {"label": "STRESSED", "confidence": 0.87, "is_demo": True}


def demo_vocal_features() -> Dict[str, Any]:
    return {
        "speech_rate_wpm": 168.0,
        "speech_rate_delta_pct": 14.0,
        "energy": "HIGH",
        "voice_activity": "HIGH",
        "pitch_variation_pct": 8.0,
    }
