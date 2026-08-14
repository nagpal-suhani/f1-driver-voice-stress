"""
Analysis Service.

Combines OpenF1 race data with the AI-derived driver state into the
single `SessionAnalysisResponse` the frontend renders. This is also
where the (careful, non-causal) state/performance association is
computed — see spec §35/§36/§66: we only ever describe *temporal
overlap*, never causation.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from app.models.schemas import (
    AssociationAnalysis,
    DriverSummary,
    LapEntry,
    LocationPoint,
    RaceControlEvent,
    RaceSnapshot,
    SessionSummary,
    StateBucketStat,
    StintEntry,
    WeatherSample,
)


def build_lap_entries(raw_laps: List[Dict[str, Any]]) -> List[LapEntry]:
    entries: List[LapEntry] = []
    best = None
    valid_times = [l.get("lap_duration") for l in raw_laps if l.get("lap_duration")]
    if valid_times:
        best = min(valid_times)

    prev_time: Optional[float] = None
    for lap in raw_laps:
        duration = lap.get("lap_duration")
        delta_prev = round(duration - prev_time, 3) if duration is not None and prev_time is not None else None
        delta_best = round(duration - best, 3) if duration is not None and best is not None else None
        entries.append(
            LapEntry(
                lap_number=lap.get("lap_number", 0),
                lap_duration=duration,
                duration_sector_1=lap.get("duration_sector_1"),
                duration_sector_2=lap.get("duration_sector_2"),
                duration_sector_3=lap.get("duration_sector_3"),
                is_pit_out_lap=lap.get("is_pit_out_lap"),
                delta_to_previous=delta_prev,
                delta_to_best=delta_best,
            )
        )
        if duration is not None:
            prev_time = duration
    return entries


def build_race_snapshot(laps: List[LapEntry], raw_positions: List[Dict[str, Any]], starting_position: Optional[int]) -> RaceSnapshot:
    if not laps:
        return RaceSnapshot()

    current = laps[-1]
    previous = laps[-2] if len(laps) > 1 else None
    best_lap_time = min((l.lap_duration for l in laps if l.lap_duration is not None), default=None)

    current_position = None
    if raw_positions:
        current_position = raw_positions[-1].get("position")

    return RaceSnapshot(
        current_lap=current.lap_number,
        total_laps=None,  # OpenF1 does not expose a canonical "total laps" field directly
        lap_time=current.lap_duration,
        previous_lap=previous.lap_duration if previous else None,
        best_lap=best_lap_time,
        delta_to_previous=current.delta_to_previous,
        position=current_position,
        starting_position=starting_position,
    )


def build_location_points(raw_location: List[Dict[str, Any]]) -> List[LocationPoint]:
    return [
        LocationPoint(date=p.get("date"), x=p.get("x"), y=p.get("y"), lap_number=p.get("lap_number"))
        for p in raw_location
    ]


def build_race_control(raw_events: List[Dict[str, Any]]) -> List[RaceControlEvent]:
    return [
        RaceControlEvent(
            date=e.get("date"),
            category=e.get("category"),
            flag=e.get("flag"),
            message=e.get("message"),
            lap_number=e.get("lap_number"),
        )
        for e in raw_events
    ]


def build_weather(raw_weather: List[Dict[str, Any]]) -> List[WeatherSample]:
    return [
        WeatherSample(
            date=w.get("date"),
            air_temperature=w.get("air_temperature"),
            track_temperature=w.get("track_temperature"),
            humidity=w.get("humidity"),
            wind_speed=w.get("wind_speed"),
            rainfall=w.get("rainfall"),
        )
        for w in raw_weather
    ]


def build_stints(raw_stints: List[Dict[str, Any]]) -> List[StintEntry]:
    return [
        StintEntry(
            stint_number=s.get("stint_number"),
            compound=s.get("compound"),
            lap_start=s.get("lap_start"),
            lap_end=s.get("lap_end"),
            tyre_age_at_start=s.get("tyre_age_at_start"),
        )
        for s in raw_stints
    ]


def build_driver_summary(raw_driver: Optional[Dict[str, Any]], fallback_number: int) -> DriverSummary:
    if not raw_driver:
        return DriverSummary(driver_number=fallback_number)
    return DriverSummary(
        driver_number=raw_driver.get("driver_number", fallback_number),
        full_name=raw_driver.get("full_name"),
        name_acronym=raw_driver.get("name_acronym"),
        team_name=raw_driver.get("team_name"),
        team_colour=raw_driver.get("team_colour"),
        headshot_url=raw_driver.get("headshot_url"),
    )


def build_session_summary(raw_session: Optional[Dict[str, Any]], fallback_key: int) -> SessionSummary:
    if not raw_session:
        return SessionSummary(session_key=fallback_key)
    return SessionSummary(
        session_key=raw_session.get("session_key", fallback_key),
        meeting_key=raw_session.get("meeting_key"),
        session_name=raw_session.get("session_name"),
        session_type=raw_session.get("session_type"),
        date_start=raw_session.get("date_start"),
        date_end=raw_session.get("date_end"),
        country_name=raw_session.get("country_name"),
        circuit_short_name=raw_session.get("circuit_short_name"),
        year=raw_session.get("year"),
    )


def compute_association(
    current_state_label: str,
    laps: List[LapEntry],
    radio_lap_numbers: List[int],
) -> AssociationAnalysis:
    """
    Minimal, honest state/performance overview (spec §36).

    We only have ONE classified vocal-state sample per analysis request
    in this prototype (a single radio clip -> one state label), so a
    statistically meaningful multi-bucket average is not available yet.
    Rather than fabricate confidence, we report what IS observable: the
    lap(s) nearest to when radio events occurred, worded as a temporal
    association, never causation.
    """
    if not laps or not radio_lap_numbers:
        return AssociationAnalysis(association=None, sample_count=0, buckets=[])

    lap_by_number = {l.lap_number: l for l in laps}
    nearby_deltas = [
        lap_by_number[n].delta_to_previous
        for n in radio_lap_numbers
        if n in lap_by_number and lap_by_number[n].delta_to_previous is not None
    ]

    if len(nearby_deltas) < 2:
        return AssociationAnalysis(
            association="Insufficient observations to establish a state/performance overview.",
            sample_count=len(nearby_deltas),
            buckets=[],
        )

    avg_delta = sum(nearby_deltas) / len(nearby_deltas)
    direction = "higher" if avg_delta > 0 else "lower"
    association = (
        f"Laps following radio activity show, on average, {direction} lap-time deltas "
        f"({avg_delta:+.3f}s vs. previous lap) during the sampled window. "
        f"This is a temporal association, not a causal claim."
    )
    bucket = StateBucketStat(
        state=current_state_label,  # type: ignore[arg-type]
        average_lap_time=round(
            sum(lap_by_number[n].lap_duration for n in radio_lap_numbers if n in lap_by_number and lap_by_number[n].lap_duration)
            / max(1, len([n for n in radio_lap_numbers if n in lap_by_number and lap_by_number[n].lap_duration])),
            3,
        )
        if any(n in lap_by_number and lap_by_number[n].lap_duration for n in radio_lap_numbers)
        else None,
        sample_count=len(nearby_deltas),
    )
    return AssociationAnalysis(association=association, sample_count=len(nearby_deltas), buckets=[bucket])
