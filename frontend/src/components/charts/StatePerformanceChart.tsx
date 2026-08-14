import type { AssociationAnalysis } from "../../types/api";
import { DataPanel, formatLapTime } from "../common/DataPanel";

interface Props {
  analysis: AssociationAnalysis;
}

export default function StatePerformanceChart({ analysis }: Props) {
  return (
    <DataPanel title="State / Performance Overview">
      {analysis.sample_count < 2 ? (
        <p className="text-sm text-muted">Insufficient observations.</p>
      ) : (
        <>
          {analysis.buckets.map((b, i) => (
            <div key={i} className="flex items-center justify-between py-1.5 border-b border-line/50 last:border-0">
              <span className="text-xs uppercase text-muted">{b.state}</span>
              <span className="num-display text-sm">{formatLapTime(b.average_lap_time)}</span>
              <span className="label-micro text-muted/60">n={b.sample_count}</span>
            </div>
          ))}
          <p className="text-[11px] text-muted/70 mt-3 leading-relaxed">{analysis.association}</p>
        </>
      )}
    </DataPanel>
  );
}
