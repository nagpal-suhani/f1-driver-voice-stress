import type { WeatherSample } from "../../types/api";
import { DataPanel, TelemetryMetric } from "../common/DataPanel";

interface Props {
  samples: WeatherSample[];
}

export default function WeatherPanel({ samples }: Props) {
  const latest = samples[samples.length - 1];
  if (!latest) {
    return (
      <DataPanel title="Weather">
        <p className="text-sm text-muted">No weather data available.</p>
      </DataPanel>
    );
  }

  return (
    <DataPanel title="Weather">
      <div className="grid grid-cols-2 gap-3">
        <TelemetryMetric label="Air Temp" value={latest.air_temperature} unit="°C" size="sm" />
        <TelemetryMetric label="Track Temp" value={latest.track_temperature} unit="°C" size="sm" />
        <TelemetryMetric label="Humidity" value={latest.humidity} unit="%" size="sm" />
        <TelemetryMetric label="Wind" value={latest.wind_speed} unit="m/s" size="sm" />
      </div>
    </DataPanel>
  );
}
