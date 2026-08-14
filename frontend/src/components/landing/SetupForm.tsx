import { useEffect, useMemo, useState, type ChangeEvent } from "react";
import { motion } from "framer-motion";
import { ChevronDown, Loader2, Radio, Upload, X } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { useSessionData, useRadioAvailability } from "../../hooks/useSession";
import ErrorState from "../common/ErrorState";
import clsx from "clsx";

const CURRENT_YEAR = new Date().getFullYear();
const YEARS = Array.from({ length: 6 }, (_, i) => CURRENT_YEAR - i);

const rise = {
  hidden: { opacity: 0, x: 24 },
  show: { opacity: 1, x: 0, transition: { duration: 0.7, ease: [0.16, 1, 0.3, 1], delay: 0.35 } },
};

function Select({
  label,
  value,
  onChange,
  options,
  placeholder,
  loading,
  disabled,
}: {
  label: string;
  value: string;
  onChange: (v: string) => void;
  options: { value: string; label: string }[];
  placeholder: string;
  loading?: boolean;
  disabled?: boolean;
}) {
  return (
    <div>
      <label className="label-micro block mb-2">{label}</label>
      <div className="relative">
        <select
          className={clsx("field-shell appearance-none pr-9", disabled && "opacity-40 cursor-not-allowed")}
          value={value}
          disabled={disabled || loading}
          onChange={(e) => onChange(e.target.value)}
        >
          <option value="">{loading ? "LOADING..." : placeholder}</option>
          {options.map((o) => (
            <option key={o.value} value={o.value}>
              {o.label}
            </option>
          ))}
        </select>
        {loading ? (
          <Loader2 className="w-3.5 h-3.5 animate-spin absolute right-3 top-1/2 -translate-y-1/2 text-muted" />
        ) : (
          <ChevronDown className="w-3.5 h-3.5 absolute right-3 top-1/2 -translate-y-1/2 text-muted pointer-events-none" />
        )}
      </div>
    </div>
  );
}

function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
}

export default function SetupForm() {
  const navigate = useNavigate();
  const {
    meetings,
    sessions,
    drivers,
    loadingMeetings,
    loadingSessions,
    loadingDrivers,
    meetingsError,
    sessionsError,
    driversError,
    loadMeetings,
    loadSessions,
    loadDrivers,
  } = useSessionData();

  const [year, setYear] = useState<number>(CURRENT_YEAR);
  const [meetingKey, setMeetingKey] = useState<string>("");
  const [sessionKey, setSessionKey] = useState<string>("");
  const [driverNumber, setDriverNumber] = useState<string>("");
  const [radioSource, setRadioSource] = useState<"openf1" | "upload">("openf1");
  const [file, setFile] = useState<File | null>(null);
  const [analysisMode, setAnalysisMode] = useState<"historical" | "live">("historical");

  const selectedSessionKeyNum = sessionKey ? Number(sessionKey) : null;
  const selectedDriverNum = driverNumber ? Number(driverNumber) : null;
  const { available: radioAvailable, checking: checkingRadio } = useRadioAvailability(
    selectedSessionKeyNum,
    selectedDriverNum
  );

  useEffect(() => {
    loadMeetings(year);
    setMeetingKey("");
    setSessionKey("");
    setDriverNumber("");
  }, [year, loadMeetings]);

  useEffect(() => {
    if (meetingKey) {
      loadSessions(year, Number(meetingKey));
      setSessionKey("");
      setDriverNumber("");
    }
  }, [meetingKey]); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    if (sessionKey) {
      loadDrivers(Number(sessionKey));
      setDriverNumber("");
    }
  }, [sessionKey]); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    if (radioAvailable === false) setRadioSource("upload");
  }, [radioAvailable]);

  const canSubmit = useMemo(() => {
    if (!sessionKey || !driverNumber) return false;
    if (radioSource === "upload" && !file) return false;
    return true;
  }, [sessionKey, driverNumber, radioSource, file]);

  function handleFileChange(e: ChangeEvent<HTMLInputElement>) {
    const f = e.target.files?.[0];
    if (!f) return;
    const ext = f.name.split(".").pop()?.toLowerCase();
    if (!["mp3", "wav", "m4a", "ogg", "webm", "flac"].includes(ext || "")) {
      alert("Unsupported audio format.");
      return;
    }
    setFile(f);
  }

  function handleSubmit() {
    if (!canSubmit || !sessionKey || !driverNumber) return;
    const params = new URLSearchParams({
      session_key: sessionKey,
      driver_number: driverNumber,
      radio_source: radioSource,
      mode: analysisMode,
    });
    navigate(`/analysis?${params.toString()}`, {
      state: { uploadedFileName: file?.name },
    });
  }

  return (
    <motion.div variants={rise} initial="hidden" animate="show" className="w-full max-w-sm">
      <div className="panel panel-corner p-6 md:p-7 bg-surface/90 backdrop-blur-sm">
        <div className="label-micro text-accent mb-5">SESSION CONFIGURATION</div>

        <div className="space-y-5">
          <Select
            label="Year"
            value={String(year)}
            onChange={(v) => setYear(Number(v))}
            options={YEARS.map((y) => ({ value: String(y), label: String(y) }))}
            placeholder="SELECT YEAR"
          />

          {meetingsError ? (
            <ErrorState message={meetingsError} onRetry={() => loadMeetings(year)} />
          ) : (
            <Select
              label="Grand Prix / Event"
              value={meetingKey}
              onChange={setMeetingKey}
              loading={loadingMeetings}
              options={meetings.map((m) => ({
                value: String(m.meeting_key),
                label: m.meeting_name || `Meeting ${m.meeting_key}`,
              }))}
              placeholder="SELECT EVENT"
            />
          )}

          {meetingKey &&
            (sessionsError ? (
              <ErrorState message={sessionsError} onRetry={() => loadSessions(year, Number(meetingKey))} />
            ) : (
              <Select
                label="Session"
                value={sessionKey}
                onChange={setSessionKey}
                loading={loadingSessions}
                options={sessions.map((s) => ({
                  value: String(s.session_key),
                  label: s.session_name || s.session_type || `Session ${s.session_key}`,
                }))}
                placeholder="SELECT SESSION"
              />
            ))}

          {sessionKey &&
            (driversError ? (
              <ErrorState message={driversError} onRetry={() => loadDrivers(Number(sessionKey))} />
            ) : (
              <Select
                label="Driver"
                value={driverNumber}
                onChange={setDriverNumber}
                loading={loadingDrivers}
                options={drivers.map((d) => ({
                  value: String(d.driver_number),
                  label: `#${d.driver_number} ${d.full_name || d.name_acronym || ""} — ${d.team_name || "Unknown Team"}`,
                }))}
                placeholder="SELECT DRIVER"
              />
            ))}

          {driverNumber && (
            <div>
              <label className="label-micro block mb-2">Radio Source</label>
              <div className="grid grid-cols-2 gap-2">
                <button
                  type="button"
                  disabled={radioAvailable === false}
                  onClick={() => setRadioSource("openf1")}
                  className={clsx(
                    "flex items-center justify-center gap-2 py-2.5 text-xs font-display uppercase tracking-wider border transition-colors",
                    radioSource === "openf1" ? "border-accent text-offwhite bg-accent/10" : "border-line text-muted",
                    radioAvailable === false && "opacity-30 cursor-not-allowed"
                  )}
                >
                  <Radio className="w-3.5 h-3.5" /> OpenF1 Radio
                </button>
                <button
                  type="button"
                  onClick={() => setRadioSource("upload")}
                  className={clsx(
                    "flex items-center justify-center gap-2 py-2.5 text-xs font-display uppercase tracking-wider border transition-colors",
                    radioSource === "upload" ? "border-accent text-offwhite bg-accent/10" : "border-line text-muted"
                  )}
                >
                  <Upload className="w-3.5 h-3.5" /> Upload Audio
                </button>
              </div>
              {checkingRadio && <p className="text-[11px] text-muted mt-2">Checking radio availability…</p>}
              {radioAvailable === false && (
                <p className="text-[11px] text-accent/90 mt-2">
                  Radio recording unavailable for this session. Upload driver radio instead.
                </p>
              )}
            </div>
          )}

          {driverNumber && radioSource === "upload" && (
            <div>
              <label className="label-micro block mb-2">Audio File</label>
              {!file ? (
                <label className="flex flex-col items-center justify-center gap-2 border border-dashed border-line py-6 cursor-pointer hover:border-muted transition-colors">
                  <Upload className="w-4 h-4 text-muted" />
                  <span className="text-xs text-muted">MP3 / WAV / M4A — click to browse</span>
                  <input type="file" accept=".mp3,.wav,.m4a,.ogg,.webm,.flac" className="hidden" onChange={handleFileChange} />
                </label>
              ) : (
                <div className="flex items-center justify-between border border-line px-3 py-2.5 bg-surface-2">
                  <div className="min-w-0">
                    <p className="text-xs text-offwhite truncate">{file.name}</p>
                    <p className="text-[10px] text-muted">{formatBytes(file.size)}</p>
                  </div>
                  <button onClick={() => setFile(null)} className="text-muted hover:text-accent shrink-0 ml-2">
                    <X className="w-3.5 h-3.5" />
                  </button>
                </div>
              )}
            </div>
          )}

          {driverNumber && (
            <div>
              <label className="label-micro block mb-2">Analysis Mode</label>
              <div className="grid grid-cols-2 gap-2">
                <button
                  type="button"
                  onClick={() => setAnalysisMode("historical")}
                  className={clsx(
                    "py-2.5 text-xs font-display uppercase tracking-wider border transition-colors",
                    analysisMode === "historical" ? "border-accent text-offwhite bg-accent/10" : "border-line text-muted"
                  )}
                >
                  Historical
                </button>
                <button
                  type="button"
                  disabled
                  title="Live mode requires compatible OpenF1 real-time access."
                  className="py-2.5 text-xs font-display uppercase tracking-wider border border-line text-muted/40 cursor-not-allowed"
                >
                  Live Monitoring
                </button>
              </div>
              <p className="text-[10px] text-muted/60 mt-2">Live mode requires compatible OpenF1 real-time access.</p>
            </div>
          )}

          <button onClick={handleSubmit} disabled={!canSubmit} className="btn-command w-full mt-2">
            INITIALIZE ANALYSIS
          </button>
        </div>
      </div>
    </motion.div>
  );
}
