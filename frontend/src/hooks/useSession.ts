import { useCallback, useEffect, useState } from "react";
import { api, ApiError } from "../services/api";
import type { DriverSummary, MeetingSummary, SessionSummary } from "../types/api";

interface State {
  meetings: MeetingSummary[];
  sessions: SessionSummary[];
  drivers: DriverSummary[];
  loadingMeetings: boolean;
  loadingSessions: boolean;
  loadingDrivers: boolean;
  meetingsError: string | null;
  sessionsError: string | null;
  driversError: string | null;
}

const initialState: State = {
  meetings: [],
  sessions: [],
  drivers: [],
  loadingMeetings: false,
  loadingSessions: false,
  loadingDrivers: false,
  meetingsError: null,
  sessionsError: null,
  driversError: null,
};

export function useSessionData() {
  const [state, setState] = useState<State>(initialState);

  const loadMeetings = useCallback(async (year: number) => {
    setState((s) => ({ ...s, loadingMeetings: true, meetingsError: null, meetings: [], sessions: [], drivers: [] }));
    try {
      const meetings = await api.getMeetings(year);
      setState((s) => ({ ...s, meetings, loadingMeetings: false }));
    } catch (err) {
      const message = err instanceof ApiError ? err.message : "Unable to retrieve session data.";
      setState((s) => ({ ...s, loadingMeetings: false, meetingsError: message }));
    }
  }, []);

  const loadSessions = useCallback(async (year: number, meetingKey: number) => {
    setState((s) => ({ ...s, loadingSessions: true, sessionsError: null, sessions: [], drivers: [] }));
    try {
      const sessions = await api.getSessions(year, meetingKey);
      setState((s) => ({ ...s, sessions, loadingSessions: false }));
    } catch (err) {
      const message = err instanceof ApiError ? err.message : "Unable to retrieve session data.";
      setState((s) => ({ ...s, loadingSessions: false, sessionsError: message }));
    }
  }, []);

  const loadDrivers = useCallback(async (sessionKey: number) => {
    setState((s) => ({ ...s, loadingDrivers: true, driversError: null, drivers: [] }));
    try {
      const drivers = await api.getSessionDrivers(sessionKey);
      setState((s) => ({ ...s, drivers, loadingDrivers: false }));
    } catch (err) {
      const message = err instanceof ApiError ? err.message : "Unable to retrieve driver data.";
      setState((s) => ({ ...s, loadingDrivers: false, driversError: message }));
    }
  }, []);

  return { ...state, loadMeetings, loadSessions, loadDrivers };
}

export function useRadioAvailability(sessionKey: number | null, driverNumber: number | null) {
  const [available, setAvailable] = useState<boolean | null>(null);
  const [checking, setChecking] = useState(false);

  useEffect(() => {
    if (!sessionKey || !driverNumber) {
      setAvailable(null);
      return;
    }
    setChecking(true);
    api
      .getRadio(sessionKey, driverNumber)
      .then((clips) => setAvailable(clips.length > 0))
      .catch(() => setAvailable(false))
      .finally(() => setChecking(false));
  }, [sessionKey, driverNumber]);

  return { available, checking };
}
