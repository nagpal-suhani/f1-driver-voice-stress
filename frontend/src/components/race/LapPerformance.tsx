import type { RaceSnapshot } from "../../types/api";
import { DataPanel, TelemetryMetric, formatLapTime, formatDelta } from "../common/DataPanel";

interface Props {
  race: RaceSnapshot;
}

export default function LapPerformance({ race }: Props) {
  return (
    <DataPanel title="Current Lap">
      <div className="flex items-baseline gap-2 mb-4">
        <span className="num-display text-4xl font-semibold">{race.current_lap ?? "N/A"}</span>
        <span className="text-muted text-lg">/ {race.total_laps ?? "N/A"}</span>
      </div>
      <TelemetryMetric label="Current Lap Time" value={formatLapTime(race.lap_time)} size="lg" tone="accent" />
      <div className="grid grid-cols-3 gap-3 mt-4 pt-4 border-t border-line">
        <TelemetryMetric label="Previous" value={formatLapTime(race.previous_lap)} size="sm" />
        <TelemetryMetric label="Best" value={formatLapTime(race.best_lap)} size="sm" />
        <TelemetryMetric
          label="Delta"
          value={formatDelta(race.delta_to_previous)}
          size="sm"
          tone={(race.delta_to_previous ?? 0) > 0 ? "accent" : "default"}
        />
      </div>
    </DataPanel>
  );
}
