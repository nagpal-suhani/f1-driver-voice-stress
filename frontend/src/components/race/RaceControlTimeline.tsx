import type { RaceControlEvent } from "../../types/api";
import { DataPanel } from "../common/DataPanel";

interface Props {
  events: RaceControlEvent[];
}

const FLAG_COLOR: Record<string, string> = {
  YELLOW: "#e1c200",
  GREEN: "#2fbf71",
  RED: "#e10600",
  BLUE: "#2f7fbf",
};

export default function RaceControlTimeline({ events }: Props) {
  if (events.length === 0) {
    return (
      <DataPanel title="Race Control">
        <p className="text-sm text-muted">No race control events for this session.</p>
      </DataPanel>
    );
  }

  return (
    <DataPanel title="Race Control">
      <div className="space-y-2 max-h-48 overflow-y-auto pr-1">
        {events.map((e, i) => (
          <div key={i} className="flex items-start gap-2 text-xs border-l-2 pl-2" style={{ borderColor: FLAG_COLOR[e.flag || ""] || "#2a2d33" }}>
            <div className="flex-1">
              <div className="flex items-center gap-2 label-micro text-muted/70">
                {e.lap_number != null && <span>LAP {e.lap_number}</span>}
                {e.category && <span>{e.category.toUpperCase()}</span>}
              </div>
              <p className="text-offwhite/90 mt-0.5">{e.message || "N/A"}</p>
            </div>
          </div>
        ))}
      </div>
    </DataPanel>
  );
}
