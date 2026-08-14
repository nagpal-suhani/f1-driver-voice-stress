import type { LapEntry } from "../../types/api";
import { DataPanel } from "../common/DataPanel";

interface Props {
  currentLap?: LapEntry;
  bestLap?: LapEntry;
}

function fmt(v?: number | null): string {
  return v == null ? "N/A" : v.toFixed(3);
}

export default function SectorTimes({ currentLap, bestLap }: Props) {
  const sectors: { label: string; current?: number | null; best?: number | null }[] = [
    { label: "S1", current: currentLap?.duration_sector_1, best: bestLap?.duration_sector_1 },
    { label: "S2", current: currentLap?.duration_sector_2, best: bestLap?.duration_sector_2 },
    { label: "S3", current: currentLap?.duration_sector_3, best: bestLap?.duration_sector_3 },
  ];

  return (
    <DataPanel title="Sector Performance">
      <table className="w-full text-xs">
        <thead>
          <tr className="label-micro text-muted/70 border-b border-line">
            <th className="text-left py-1.5 font-normal">Sector</th>
            <th className="text-right py-1.5 font-normal">Current</th>
            <th className="text-right py-1.5 font-normal">Best</th>
            <th className="text-right py-1.5 font-normal">Delta</th>
          </tr>
        </thead>
        <tbody>
          {sectors.map((s) => {
            const delta = s.current != null && s.best != null ? s.current - s.best : null;
            return (
              <tr key={s.label} className="border-b border-line/50">
                <td className="py-1.5">{s.label}</td>
                <td className="py-1.5 num-display text-right">{fmt(s.current)}</td>
                <td className="py-1.5 num-display text-right text-muted">{fmt(s.best)}</td>
                <td className={`py-1.5 num-display text-right ${delta && delta > 0 ? "text-accent" : "text-emerald-400"}`}>
                  {delta == null ? "N/A" : `${delta > 0 ? "+" : ""}${delta.toFixed(3)}`}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </DataPanel>
  );
}
