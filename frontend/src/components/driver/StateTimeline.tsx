import type { DriverStateLabel } from "../../types/api";
import { DataPanel } from "../common/DataPanel";

interface StatePoint {
  lap: number;
  state: DriverStateLabel;
}

interface Props {
  points: StatePoint[];
}

const STATE_ORDER: DriverStateLabel[] = ["FATIGUE-LIKE", "CALM", "ELEVATED", "STRESSED"];
const STATE_COLOR: Record<DriverStateLabel, string> = {
  CALM: "#8a8f98",
  ELEVATED: "#e18f00",
  STRESSED: "#e10600",
  "FATIGUE-LIKE": "#5a6ee1",
};

export default function StateTimeline({ points }: Props) {
  if (points.length <= 1) {
    return (
      <DataPanel title="Driver State Timeline">
        <p className="text-sm text-muted">Single sample analysis — insufficient data for a full timeline.</p>
        {points.length === 1 && (
          <div className="mt-3 flex items-center gap-2">
            <span className="w-2 h-2 rounded-full" style={{ background: STATE_COLOR[points[0].state] }} />
            <span className="text-xs text-offwhite">
              Lap {points[0].lap} — {points[0].state}
            </span>
          </div>
        )}
      </DataPanel>
    );
  }

  const width = 100;
  const laneHeight = 22;
  const minLap = Math.min(...points.map((p) => p.lap));
  const maxLap = Math.max(...points.map((p) => p.lap));
  const span = Math.max(1, maxLap - minLap);

  return (
    <DataPanel title="Driver State Timeline">
      <div className="relative" style={{ height: STATE_ORDER.length * laneHeight + 20 }}>
        {STATE_ORDER.map((label, i) => (
          <div
            key={label}
            className="absolute left-0 right-0 flex items-center label-micro text-muted/70"
            style={{ top: i * laneHeight }}
          >
            <span className="w-24 shrink-0">{label}</span>
            <div className="flex-1 h-px bg-line" />
          </div>
        ))}
        <svg viewBox={`0 0 ${width} ${STATE_ORDER.length * laneHeight}`} className="absolute left-24 right-0 top-0 h-full" preserveAspectRatio="none">
          <polyline
            fill="none"
            stroke="#e10600"
            strokeWidth="1.5"
            points={points
              .map((p) => {
                const x = ((p.lap - minLap) / span) * width;
                const y = STATE_ORDER.indexOf(p.state) * laneHeight + laneHeight / 2;
                return `${x},${y}`;
              })
              .join(" ")}
          />
          {points.map((p, i) => {
            const x = ((p.lap - minLap) / span) * width;
            const y = STATE_ORDER.indexOf(p.state) * laneHeight + laneHeight / 2;
            return <circle key={i} cx={x} cy={y} r="2" fill={STATE_COLOR[p.state]} />;
          })}
        </svg>
      </div>
      <div className="flex justify-between mt-2 label-micro text-muted/50">
        <span>LAP {minLap}</span>
        <span>LAP {maxLap}</span>
      </div>
    </DataPanel>
  );
}
