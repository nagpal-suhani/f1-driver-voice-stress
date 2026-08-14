import type {
  AnalyzeAudioResponse,
  DriverSummary,
  HealthResponse,
  LapEntry,
  LocationPoint,
  MeetingSummary,
  RaceControlEvent,
  RadioClip,
  SessionAnalysisResponse,
  SessionSummary,
  StintEntry,
  WeatherSample,
} from "../types/api";

// The frontend only ever talks to our own FastAPI server. Secrets
// (Hugging Face token, OpenF1 credentials if ever required) live in
// backend/.env and never reach this file.
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

export class ApiError extends Error {
  status?: number;
  constructor(message: string, status?: number) {
    super(message);
    this.status = status;
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let res: Response;
  try {
    res = await fetch(`${API_BASE_URL}${path}`, init);
  } catch (err) {
    throw new ApiError("Unable to reach the analysis server. Confirm the backend is running.");
  }
  if (!res.ok) {
    let detail = `Request failed (${res.status})`;
    try {
      const body = await res.json();
      detail = body.detail || detail;
    } catch {
      /* ignore parse errors */
    }
    throw new ApiError(detail, res.status);
  }
  return res.json() as Promise<T>;
}

export const api = {
  health: () => request<HealthResponse>("/api/health"),

  getMeetings: (year: number) => request<MeetingSummary[]>(`/api/meetings?year=${year}`),

  getSessions: (year?: number, meetingKey?: number) => {
    const params = new URLSearchParams();
    if (year) params.set("year", String(year));
    if (meetingKey) params.set("meeting_key", String(meetingKey));
    return request<SessionSummary[]>(`/api/sessions?${params.toString()}`);
  },

  getSessionDrivers: (sessionKey: number) => request<DriverSummary[]>(`/api/sessions/${sessionKey}/drivers`),

  getLaps: (sessionKey: number, driverNumber: number) =>
    request<LapEntry[]>(`/api/sessions/${sessionKey}/laps/${driverNumber}`),

  getLocation: (sessionKey: number, driverNumber: number) =>
    request<LocationPoint[]>(`/api/sessions/${sessionKey}/location/${driverNumber}`),

  getRaceControl: (sessionKey: number) => request<RaceControlEvent[]>(`/api/sessions/${sessionKey}/race-control`),

  getWeather: (sessionKey: number) => request<WeatherSample[]>(`/api/sessions/${sessionKey}/weather`),

  getStints: (sessionKey: number, driverNumber: number) =>
    request<StintEntry[]>(`/api/sessions/${sessionKey}/stints/${driverNumber}`),

  getRadio: (sessionKey: number, driverNumber: number) =>
    request<RadioClip[]>(`/api/sessions/${sessionKey}/radio/${driverNumber}`),

  analyzeAudio: (file: File, context?: Record<string, unknown>) => {
    const form = new FormData();
    form.append("file", file);
    if (context) form.append("context", JSON.stringify(context));
    return request<AnalyzeAudioResponse>("/api/analyze-audio", { method: "POST", body: form });
  },

  analyzeSession: (sessionKey: number, driverNumber: number, radioSource: "openf1" | "upload") =>
    request<SessionAnalysisResponse>("/api/analyze-session", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ session_key: sessionKey, driver_number: driverNumber, radio_source: radioSource }),
    }),
};
