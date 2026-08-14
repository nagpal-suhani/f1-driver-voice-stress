import { Line, LineChart, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { LapEntry } from "../../types/api";
import { DataPanel } from "../common/DataPanel";

interface Props {
  laps: LapEntry[];
}

export default function PerformanceChart({ laps }: Props) {
  const valid = laps.filter((l) => l.lap_duration != null);
  if (valid.length === 0) {
    return (
      <DataPanel title="Lap Time Chart">
        <p className="text-sm text-muted">No lap time data available.</p>
      </DataPanel>
    );
  }

  const times = valid.map((l) => l.lap_duration as number);
  const best = Math.min(...times);
  const avg = times.reduce((a, b) => a + b, 0) / times.length;
  const data = valid.map((l) => ({ lap: l.lap_number, time: l.lap_duration }));

  return (
    <DataPanel title="Lap Time Chart">
      <div className="h-56">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={data} margin={{ top: 8, right: 8, left: -20, bottom: 0 }}>
            <XAxis dataKey="lap" tick={{ fill: "#8a8f98", fontSize: 10 }} axisLine={{ stroke: "#2a2d33" }} tickLine={false} />
            <YAxis
              domain={["dataMin - 0.5", "dataMax + 0.5"]}
              tick={{ fill: "#8a8f98", fontSize: 10 }}
              axisLine={{ stroke: "#2a2d33" }}
              tickLine={false}
              tickFormatter={(v) => v.toFixed(1)}
            />
            <Tooltip
              contentStyle={{ background: "#15171b", border: "1px solid #2a2d33", fontSize: 12 }}
              labelFormatter={(l) => `Lap ${l}`}
              formatter={(v: number) => [`${v.toFixed(3)}s`, "Lap Time"]}
            />
            <ReferenceLine y={best} stroke="#8a8f98" strokeDasharray="3 3" />
            <ReferenceLine y={avg} stroke="#3a3d45" strokeDasharray="2 4" />
            <Line type="monotone" dataKey="time" stroke="#e10600" strokeWidth={2} dot={false} />
          </LineChart>
        </ResponsiveContainer>
      </div>
      <div className="flex gap-4 label-micro text-muted/60 mt-1">
        <span>— Lap Time</span>
        <span>┄ Best</span>
        <span>┄ Average</span>
      </div>
    </DataPanel>
  );
}
