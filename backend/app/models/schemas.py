"""
Pydantic models describing every shape that crosses the API boundary.

Design principle (see spec §64 "Data Honesty"): almost every numeric
field is Optional. A missing value is serialized as `null` and the
frontend renders that as "N/A" / "No Data" — we never invent a number
to fill a gap.
"""
from __future__ import annotations

from typing import List, Literal, Optional

from pydantic import BaseModel, Field

DriverStateLabel = Literal["CALM", "ELEVATED", "STRESSED", "FATIGUE-LIKE"]


# ---------------------------------------------------------------- meta
class MeetingSummary(BaseModel):
    meeting_key: int
    meeting_name: Optional[str] = None
    country_name: Optional[str] = None
    circuit_short_name: Optional[str] = None
    year: Optional[int] = None
    date_start: Optional[str] = None


class SessionSummary(BaseModel):
    session_key: int
    meeting_key: Optional[int] = None
    session_name: Optional[str] = None
    session_type: Optional[str] = None
    date_start: Optional[str] = None
    date_end: Optional[str] = None
    country_name: Optional[str] = None
    circuit_short_name: Optional[str] = None
    year: Optional[int] = None


class DriverSummary(BaseModel):
    driver_number: int
    full_name: Optional[str] = None
    name_acronym: Optional[str] = None
    team_name: Optional[str] = None
    team_colour: Optional[str] = None
    headshot_url: Optional[str] = None


# ---------------------------------------------------------------- laps
class LapEntry(BaseModel):
    lap_number: int
    lap_duration: Optional[float] = None
    duration_sector_1: Optional[float] = None
    duration_sector_2: Optional[float] = None
    duration_sector_3: Optional[float] = None
    is_pit_out_lap: Optional[bool] = None
    delta_to_previous: Optional[float] = None
    delta_to_best: Optional[float] = None


# ------------------------------------------------------------- location
class LocationPoint(BaseModel):
    date: Optional[str] = None
    x: Optional[float] = None
    y: Optional[float] = None
    lap_number: Optional[int] = None


class PositionEntry(BaseModel):
    date: Optional[str] = None
    position: Optional[int] = None


# --------------------------------------------------------- race control
class RaceControlEvent(BaseModel):
    date: Optional[str] = None
    category: Optional[str] = None
    flag: Optional[str] = None
    message: Optional[str] = None
    lap_number: Optional[int] = None


class WeatherSample(BaseModel):
    date: Optional[str] = None
    air_temperature: Optional[float] = None
    track_temperature: Optional[float] = None
    humidity: Optional[float] = None
    wind_speed: Optional[float] = None
    rainfall: Optional[float] = None


class StintEntry(BaseModel):
    stint_number: Optional[int] = None
    compound: Optional[str] = None
    lap_start: Optional[int] = None
    lap_end: Optional[int] = None
    tyre_age_at_start: Optional[int] = None


class RadioClip(BaseModel):
    date: Optional[str] = None
    recording_url: Optional[str] = None
    lap_number: Optional[int] = None
    source: Literal["openf1", "upload", "demo"] = "openf1"


# ----------------------------------------------------------------- audio
class TranscriptSegment(BaseModel):
    start: float
    end: float
    text: str


class AudioResult(BaseModel):
    source: Literal["openf1", "upload", "demo"]
    duration: Optional[float] = None
    transcript: Optional[str] = None
    segments: List[TranscriptSegment] = Field(default_factory=list)


class VocalFeatures(BaseModel):
    speech_rate_wpm: Optional[float] = None
    speech_rate_delta_pct: Optional[float] = None
    energy: Optional[Literal["LOW", "MODERATE", "HIGH"]] = None
    voice_activity: Optional[Literal["LOW", "MODERATE", "HIGH"]] = None
    pitch_variation_pct: Optional[float] = None


class DriverState(BaseModel):
    label: DriverStateLabel
    confidence: float
    is_demo: bool = False


# --------------------------------------------------------------- analyze
class AnalyzeAudioResponse(BaseModel):
    audio: AudioResult
    driver_state: DriverState
    vocal_features: VocalFeatures
    model_source: Literal["custom_model", "demo"]


class StateBucketStat(BaseModel):
    state: DriverStateLabel
    average_lap_time: Optional[float] = None
    sample_count: int = 0


class AssociationAnalysis(BaseModel):
    association: Optional[str] = None
    sample_count: int = 0
    buckets: List[StateBucketStat] = Field(default_factory=list)


class RaceSnapshot(BaseModel):
    current_lap: Optional[int] = None
    total_laps: Optional[int] = None
    lap_time: Optional[float] = None
    previous_lap: Optional[float] = None
    best_lap: Optional[float] = None
    delta_to_previous: Optional[float] = None
    position: Optional[int] = None
    starting_position: Optional[int] = None


class SessionAnalysisResponse(BaseModel):
    driver: DriverSummary
    session: SessionSummary
    audio: AudioResult
    driver_state: DriverState
    vocal_features: VocalFeatures
    race: RaceSnapshot
    laps: List[LapEntry] = Field(default_factory=list)
    location: List[LocationPoint] = Field(default_factory=list)
    race_control: List[RaceControlEvent] = Field(default_factory=list)
    weather: List[WeatherSample] = Field(default_factory=list)
    stints: List[StintEntry] = Field(default_factory=list)
    radio_clips: List[RadioClip] = Field(default_factory=list)
    analysis: AssociationAnalysis
    is_demo: bool = False


class AnalyzeSessionRequest(BaseModel):
    session_key: int
    driver_number: int
    radio_source: Literal["openf1", "upload"] = "openf1"


class HealthResponse(BaseModel):
    status: str
    demo_mode: bool
    openf1_reachable: Optional[bool] = None
