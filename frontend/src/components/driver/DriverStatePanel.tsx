import { motion } from "framer-motion";
import type { DriverState, VocalFeatures } from "../../types/api";
import { DataPanel, TelemetryMetric } from "../common/DataPanel";

const STATE_COLOR: Record<string, string> = {
  CALM: "text-muted",
  ELEVATED: "text-amber-500",
  STRESSED: "text-accent",
  "FATIGUE-LIKE": "text-blue-400",
};

interface Props {
  driverState: DriverState;
  vocalFeatures: VocalFeatures;
}

export default function DriverStatePanel({ driverState, vocalFeatures }: Props) {
  const color = STATE_COLOR[driverState.label] || "text-offwhite";

  return (
    <DataPanel
      title="Estimated Driver State"
      right={
        driverState.is_demo ? (
          <span className="label-micro text-muted/50 border border-line px-1.5 py-0.5">DEMO DATA</span>
        ) : null
      }
    >
      <div className="flex items-end justify-between mb-5">
        <motion.div
          key={driverState.label}
          initial={{ opacity: 0, y: 6 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4 }}
          className={`font-display uppercase text-4xl md:text-5xl font-semibold ${color}`}
        >
          {driverState.label}
        </motion.div>
        <TelemetryMetric label="Confidence" value={`${Math.round(driverState.confidence * 100)}`} unit="%" size="sm" />
      </div>

      <div className="grid grid-cols-2 gap-x-4 gap-y-4 pt-4 border-t border-line">
        <TelemetryMetric label="Vocal Energy" value={vocalFeatures.energy} size="sm" />
        <TelemetryMetric
          label="Speech Pace"
          value={
            vocalFeatures.speech_rate_delta_pct != null
              ? `${vocalFeatures.speech_rate_delta_pct > 0 ? "+" : ""}${vocalFeatures.speech_rate_delta_pct}`
              : vocalFeatures.speech_rate_wpm
              ? `${vocalFeatures.speech_rate_wpm}`
              : null
          }
          unit={vocalFeatures.speech_rate_delta_pct != null ? "%" : vocalFeatures.speech_rate_wpm ? "wpm" : undefined}
          size="sm"
        />
        <TelemetryMetric label="Voice Activity" value={vocalFeatures.voice_activity} size="sm" />
        <TelemetryMetric
          label="Pitch Variation"
          value={vocalFeatures.pitch_variation_pct != null ? `+${vocalFeatures.pitch_variation_pct}` : null}
          unit={vocalFeatures.pitch_variation_pct != null ? "%" : undefined}
          size="sm"
        />
      </div>

      <div className="mt-4 pt-4 border-t border-line flex items-center justify-between">
        <span className="label-micro">Heart Rate</span>
        <span className="text-sm text-muted num-display">— No sensor data</span>
      </div>

      <p className="text-[11px] text-muted/60 mt-4 leading-relaxed">
        Vocal-state estimate derived from radio audio. Not a medical or psychological diagnosis.
      </p>
    </DataPanel>
  );
}
