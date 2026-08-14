import { useCallback, useState } from "react";
import { api, ApiError } from "../services/api";
import type { SessionAnalysisResponse } from "../types/api";

export const ANALYSIS_STAGES = [
  "CONNECTING TO SESSION",
  "LOADING DRIVER DATA",
  "LOADING LAP DATA",
  "LOADING RADIO",
  "TRANSCRIBING AUDIO",
  "ANALYZING VOCAL STATE",
  "ALIGNING RACE DATA",
  "INITIALIZING DRIVER MODEL",
] as const;

interface AnalysisState {
  data: SessionAnalysisResponse | null;
  loading: boolean;
  stageIndex: number;
  error: string | null;
}

export function useAnalysis() {
  const [state, setState] = useState<AnalysisState>({
    data: null,
    loading: false,
    stageIndex: 0,
    error: null,
  });

  const run = useCallback(async (sessionKey: number, driverNumber: number, radioSource: "openf1" | "upload") => {
    setState({ data: null, loading: true, stageIndex: 0, error: null });

    // Stage the UI forward while the real request is in flight — each
    // step corresponds to a real backend operation happening inside
    // analyze-session (session -> driver -> laps -> radio -> transcript
    // -> vocal state -> race alignment -> ready).
    const stageTimer = window.setInterval(() => {
      setState((s) => {
        if (s.stageIndex >= ANALYSIS_STAGES.length - 1) return s;
        return { ...s, stageIndex: s.stageIndex + 1 };
      });
    }, 420);

    try {
      const data = await api.analyzeSession(sessionKey, driverNumber, radioSource);
      window.clearInterval(stageTimer);
      setState({ data, loading: false, stageIndex: ANALYSIS_STAGES.length - 1, error: null });
    } catch (err) {
      window.clearInterval(stageTimer);
      const message = err instanceof ApiError ? err.message : "Analysis failed. Please retry.";
      setState({ data: null, loading: false, stageIndex: 0, error: message });
    }
  }, []);

  return { ...state, run };
}
