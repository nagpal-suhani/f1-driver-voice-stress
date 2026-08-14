import { useMemo, useState } from "react";
import type { LocationPoint } from "../../types/api";
import { DataPanel } from "../common/DataPanel";

interface Props {
  location: LocationPoint[];
}

// OpenF1's `location` endpoint returns approximate car-relative x/y
// coordinates, not conventional GPS track-side geometry (spec §31).
// Rather than fabricate a basemap, we render the driver's actual
// coordinate path as an SVG trace — an honest, data-driven track
// visualization instead of a generic map tile the coordinates don't
// actually correspond to.
export default function TrackMap({ location }: Props) {
  const [scrubIndex, setScrubIndex] = useState<number | null>(null);

  const { path, bounds, points } = useMemo(() => {
    const pts = location.filter((p) => p.x != null && p.y != null);
    if (pts.length === 0) return { path: "", bounds: null, points: [] as LocationPoint[] };
    const xs = pts.map((p) => p.x as number);
    const ys = pts.map((p) => p.y as number);
    const minX = Math.min(...xs);
    const maxX = Math.max(...xs);
    const minY = Math.min(...ys);
    const maxY = Math.max(...ys);
    const pad = 20;
    const scaleX = (x: number) => ((x - minX) / (maxX - minX || 1)) * (400 - pad * 2) + pad;
    const scaleY = (y: number) => ((y - minY) / (maxY - minY || 1)) * (240 - pad * 2) + pad;
    const d = pts.map((p, i) => `${i === 0 ? "M" : "L"} ${scaleX(p.x as number)} ${scaleY(p.y as number)}`).join(" ");
    return { path: d, bounds: { scaleX, scaleY }, points: pts };
  }, [location]);

  if (points.length === 0) {
    return (
      <DataPanel title="Track Map">
        <p className="text-sm text-muted">No location data available for this session.</p>
      </DataPanel>
    );
  }

  const activePoint = scrubIndex != null ? points[scrubIndex] : points[points.length - 1];
  const activeXY = bounds && activePoint ? { x: bounds.scaleX(activePoint.x as number), y: bounds.scaleY(activePoint.y as number) } : null;

  return (
    <DataPanel title="Track Map">
      <svg viewBox="0 0 400 240" className="w-full h-48">
        <path d={path} fill="none" stroke="#2a2d33" strokeWidth="6" strokeLinecap="round" strokeLinejoin="round" />
        <path d={path} fill="none" stroke="#e10600" strokeWidth="1.5" strokeOpacity="0.7" strokeLinecap="round" strokeLinejoin="round" />
        {activeXY && <circle cx={activeXY.x} cy={activeXY.y} r="5" fill="#e10600" stroke="#fff" strokeWidth="1.5" />}
      </svg>
      <input
        type="range"
        min={0}
        max={points.length - 1}
        value={scrubIndex ?? points.length - 1}
        onChange={(e) => setScrubIndex(Number(e.target.value))}
        className="w-full mt-2 accent-accent"
      />
      <div className="flex justify-between label-micro text-muted/60 mt-1">
        <span>SESSION START</span>
        <span>{activePoint?.lap_number != null ? `LAP ${activePoint.lap_number}` : "LATEST"}</span>
      </div>
    </DataPanel>
  );
}
