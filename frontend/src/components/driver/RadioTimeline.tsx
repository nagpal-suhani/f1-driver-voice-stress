import type { RadioClip } from "../../types/api";
import { DataPanel } from "../common/DataPanel";
import clsx from "clsx";

interface Props {
  clips: RadioClip[];
  activeIndex: number | null;
  onSelect: (index: number) => void;
}

export default function RadioTimeline({ clips, activeIndex, onSelect }: Props) {
  if (clips.length === 0) {
    return (
      <DataPanel title="Radio Activity">
        <p className="text-sm text-muted">Radio recording unavailable for this session.</p>
      </DataPanel>
    );
  }

  const grouped = new Map<number, number[]>();
  clips.forEach((c, i) => {
    const lap = c.lap_number ?? 0;
    grouped.set(lap, [...(grouped.get(lap) || []), i]);
  });

  return (
    <DataPanel title="Radio Activity">
      <div className="space-y-2">
        {Array.from(grouped.entries())
          .sort((a, b) => a[0] - b[0])
          .map(([lap, indices]) => (
            <button
              key={lap}
              onClick={() => onSelect(indices[0])}
              className={clsx(
                "w-full flex items-center justify-between px-3 py-2 border transition-colors text-left",
                indices.includes(activeIndex ?? -1) ? "border-accent bg-accent/10" : "border-line hover:border-muted"
              )}
            >
              <span className="label-micro text-muted">LAP {lap || "—"}</span>
              <span className="flex gap-1">
                {indices.map((i) => (
                  <span key={i} className="w-1.5 h-1.5 rounded-full bg-accent" />
                ))}
              </span>
            </button>
          ))}
      </div>
    </DataPanel>
  );
}
