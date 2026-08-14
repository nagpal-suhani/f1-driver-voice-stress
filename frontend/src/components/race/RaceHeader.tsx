import type { DriverSummary, SessionSummary } from "../../types/api";

interface Props {
  session: SessionSummary;
  driver: DriverSummary;
}

export default function RaceHeader({ session, driver }: Props) {
  const teamColour = driver.team_colour ? `#${driver.team_colour.replace("#", "")}` : "#e10600";

  return (
    <div className="panel panel-corner p-4" style={{ borderLeftColor: teamColour, borderLeftWidth: 3 }}>
      <div className="label-micro text-muted mb-1">
        {session.country_name || session.circuit_short_name || "GRAND PRIX"}
      </div>
      <h1 className="font-display uppercase text-xl font-semibold leading-tight">
        {session.circuit_short_name || session.country_name || "Unknown Circuit"}
      </h1>
      <div className="flex items-center justify-between mt-3 pt-3 border-t border-line">
        <div>
          <div className="label-micro">Session</div>
          <div className="text-sm text-offwhite">{session.session_name || session.session_type || "N/A"}</div>
        </div>
        <div className="text-right">
          <div className="label-micro">Driver</div>
          <div className="text-sm text-offwhite">
            #{driver.driver_number} {driver.name_acronym || ""}
          </div>
        </div>
      </div>
      <div className="mt-2 flex items-center gap-2">
        <span className="w-2 h-2" style={{ background: teamColour }} />
        <span className="text-xs text-muted">{driver.team_name || "Unknown Team"}</span>
      </div>
    </div>
  );
}
