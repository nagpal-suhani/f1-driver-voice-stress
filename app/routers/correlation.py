from typing import List, Optional

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/api/correlation", tags=["correlation"])


class LapTime(BaseModel):
    lap_number: int
    lap_time_seconds: float


class StressEvent(BaseModel):
    """One radio call's worth of data. `lap_number` is how we line it
    up against lap_times -- for the demo you can just hardcode which
    lap each pre-recorded clip 'happened' near."""

    lap_number: int
    mood: str
    arousal: float
    valence: float
    dominance: float
    transcript: Optional[str] = None


class CorrelationRequest(BaseModel):
    lap_times: List[LapTime]
    stress_events: List[StressEvent]


@router.post("/merge")
async def merge_stress_and_laps(payload: CorrelationRequest):
    """
    Combines lap times with stress events for the same laps, and
    flags laps that were slower than the driver's average -- this is
    the data the frontend chart consumes directly.
    """
    stress_by_lap = {event.lap_number: event for event in payload.stress_events}

    if not payload.lap_times:
        return {"average_lap_time": 0, "laps": []}

    avg_lap_time = sum(l.lap_time_seconds for l in payload.lap_times) / len(
        payload.lap_times
    )

    laps = []
    for lap in payload.lap_times:
        event = stress_by_lap.get(lap.lap_number)
        delta = round(lap.lap_time_seconds - avg_lap_time, 3)
        laps.append(
            {
                "lap_number": lap.lap_number,
                "lap_time_seconds": lap.lap_time_seconds,
                "delta_from_avg": delta,
                "slower_than_avg": delta > 0,
                "mood": event.mood if event else None,
                "arousal": event.arousal if event else None,
                "transcript": event.transcript if event else None,
            }
        )

    return {
        "average_lap_time": round(avg_lap_time, 3),
        "laps": laps,
    }