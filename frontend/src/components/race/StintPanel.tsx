import type { StintEntry } from "../../types/api";
import { DataPanel } from "../common/DataPanel";

interface Props {
  stints: StintEntry[];
  currentLap?: number | null;
}

export default function StintPanel({ stints, currentLap }: Props) {
  if (stints.length === 0) {
    return (
      <DataPanel title="Tyre / Stint">
        <p className="text-sm text-muted">No stint data available.</p>
      </DataPanel>
    );
  }

  const active =
    stints.find((s) => currentLap != null && s.lap_start != null && s.lap_end != null && currentLap >= s.lap_start && currentLap <= s.lap_end) ||
    stints[stints.length - 1];

  const age = active.tyre_age_at_start != null && active.lap_start != null && currentLap != null
    ? active.tyre_age_at_start + (currentLap - active.lap_start)
    : null;

  return (
    <DataPanel title="Tyre / Stint">
      <div className="flex items-center justify-between">
        <div>
          <div className="label-micro mb-1">Compound</div>
          <div className="font-display uppercase text-xl font-semibold">{active.compound || "N/A"}</div>
        </div>
        <div className="text-right">
          <div className="label-micro mb-1">Stint</div>
          <div className="num-display text-xl">{active.stint_number ?? "N/A"}</div>
        </div>
      </div>
      <div className="mt-3 pt-3 border-t border-line label-micro text-muted">
        Age: <span className="text-offwhite num-display">{age != null ? `${age} laps` : "N/A"}</span>
      </div>
    </DataPanel>
  );
}
