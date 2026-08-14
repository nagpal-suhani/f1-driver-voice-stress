export type DriverStateLabel = "CALM" | "ELEVATED" | "STRESSED" | "FATIGUE-LIKE";

export interface MeetingSummary {
  meeting_key: number;
  meeting_name?: string | null;
  country_name?: string | null;
  circuit_short_name?: string | null;
  year?: number | null;
  date_start?: string | null;
}

export interface SessionSummary {
  session_key: number;
  meeting_key?: number | null;
  session_name?: string | null;
  session_type?: string | null;
  date_start?: string | null;
  date_end?: string | null;
  country_name?: string | null;
  circuit_short_name?: string | null;
  year?: number | null;
}

export interface DriverSummary {
  driver_number: number;
  full_name?: string | null;
  name_acronym?: string | null;
  team_name?: string | null;
  team_colour?: string | null;
  headshot_url?: string | null;
}

export interface LapEntry {
  lap_number: number;
  lap_duration?: number | null;
  duration_sector_1?: number | null;
  duration_sector_2?: number | null;
  duration_sector_3?: number | null;
  is_pit_out_lap?: boolean | null;
  delta_to_previous?: number | null;
  delta_to_best?: number | null;
}

export interface LocationPoint {
  date?: string | null;
  x?: number | null;
  y?: number | null;
  lap_number?: number | null;
}

export interface RaceControlEvent {
  date?: string | null;
  category?: string | null;
  flag?: string | null;
  message?: string | null;
  lap_number?: number | null;
}

export interface WeatherSample {
  date?: string | null;
  air_temperature?: number | null;
  track_temperature?: number | null;
  humidity?: number | null;
  wind_speed?: number | null;
  rainfall?: number | null;
}

export interface StintEntry {
  stint_number?: number | null;
  compound?: string | null;
  lap_start?: number | null;
  lap_end?: number | null;
  tyre_age_at_start?: number | null;
}

export interface RadioClip {
  date?: string | null;
  recording_url?: string | null;
  lap_number?: number | null;
  source: "openf1" | "upload" | "demo";
}

export interface TranscriptSegment {
  start: number;
  end: number;
  text: string;
}

export interface AudioResult {
  source: "openf1" | "upload" | "demo";
  duration?: number | null;
  transcript?: string | null;
  segments: TranscriptSegment[];
}

export interface VocalFeatures {
  speech_rate_wpm?: number | null;
  speech_rate_delta_pct?: number | null;
  energy?: "LOW" | "MODERATE" | "HIGH" | null;
  voice_activity?: "LOW" | "MODERATE" | "HIGH" | null;
  pitch_variation_pct?: number | null;
}

export interface DriverState {
  label: DriverStateLabel;
  confidence: number;
  is_demo: boolean;
}

export interface StateBucketStat {
  state: DriverStateLabel;
  average_lap_time?: number | null;
  sample_count: number;
}

export interface AssociationAnalysis {
  association?: string | null;
  sample_count: number;
  buckets: StateBucketStat[];
}

export interface RaceSnapshot {
  current_lap?: number | null;
  total_laps?: number | null;
  lap_time?: number | null;
  previous_lap?: number | null;
  best_lap?: number | null;
  delta_to_previous?: number | null;
  position?: number | null;
  starting_position?: number | null;
}

export interface SessionAnalysisResponse {
  driver: DriverSummary;
  session: SessionSummary;
  audio: AudioResult;
  driver_state: DriverState;
  vocal_features: VocalFeatures;
  race: RaceSnapshot;
  laps: LapEntry[];
  location: LocationPoint[];
  race_control: RaceControlEvent[];
  weather: WeatherSample[];
  stints: StintEntry[];
  radio_clips: RadioClip[];
  analysis: AssociationAnalysis;
  is_demo: boolean;
}

export interface AnalyzeAudioResponse {
  audio: AudioResult;
  driver_state: DriverState;
  vocal_features: VocalFeatures;
  model_source: "huggingface" | "demo" | "fallback";
}

export interface HealthResponse {
  status: string;
  demo_mode: boolean;
  openf1_reachable?: boolean | null;
  hf_model_configured: boolean;
}

export interface SetupConfig {
  year: number;
  meeting: MeetingSummary | null;
  session: SessionSummary | null;
  driver: DriverSummary | null;
  radioSource: "openf1" | "upload";
  uploadedFile: File | null;
  analysisMode: "historical" | "live";
}
