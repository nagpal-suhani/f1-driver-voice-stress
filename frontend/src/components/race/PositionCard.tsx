import type { RaceSnapshot } from "../../types/api";
import { DataPanel, TelemetryMetric } from "../common/DataPanel";

interface Props {
  race: RaceSnapshot;
}

export default function PositionCard({ race }: Props) {
  const delta =
    race.position != null && race.starting_position != null ? race.starting_position - race.position : null;

  return (
    <DataPanel title="Position">
      <div className="grid grid-cols-3 gap-3">
        <TelemetryMetric label="Current" value={race.position != null ? `P${race.position}` : null} size="md" tone="accent" />
        <TelemetryMetric label="Starting" value={race.starting_position != null ? `P${race.starting_position}` : null} size="md" />
        <TelemetryMetric
          label="Delta"
          value={delta != null ? `${delta > 0 ? "+" : ""}${delta}` : null}
          size="md"
          tone={delta != null && delta > 0 ? "accent" : "default"}
        />
      </div>
    </DataPanel>
  );
}
