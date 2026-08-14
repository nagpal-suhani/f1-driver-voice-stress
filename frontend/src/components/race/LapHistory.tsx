import { useState } from "react";
import type { LapEntry } from "../../types/api";
import { DataPanel, formatDelta, formatLapTime } from "../common/DataPanel";
import clsx from "clsx";

interface Props {
  laps: LapEntry[];
  onSelectLap?: (lap: LapEntry) => void;
}

export default function LapHistory({ laps, onSelectLap }: Props) {
  const [selected, setSelected] = useState<number | null>(null);
  const recent = laps.slice(-8);

  return (
    <DataPanel title="Lap History">
      <div className="overflow-x-auto">
        <table className="w-full text-xs">
          <thead>
            <tr className="label-micro text-muted/70 border-b border-line">
              <th className="text-left py-1.5 font-normal">Lap</th>
              <th className="text-right py-1.5 font-normal">Time</th>
              <th className="text-right py-1.5 font-normal">Delta</th>
            </tr>
          </thead>
          <tbody>
            {recent.map((lap) => (
              <tr
                key={lap.lap_number}
                onClick={() => {
                  setSelected(lap.lap_number);
                  onSelectLap?.(lap);
                }}
                className={clsx(
                  "cursor-pointer border-b border-line/50 hover:bg-surface-2 transition-colors",
                  selected === lap.lap_number && "bg-accent/10"
                )}
              >
                <td className="py-1.5 num-display">{lap.lap_number}</td>
                <td className="py-1.5 num-display text-right">{formatLapTime(lap.lap_duration)}</td>
                <td
                  className={clsx(
                    "py-1.5 num-display text-right",
                    (lap.delta_to_previous ?? 0) > 0 ? "text-accent" : "text-emerald-400"
                  )}
                >
                  {formatDelta(lap.delta_to_previous)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </DataPanel>
  );
}
