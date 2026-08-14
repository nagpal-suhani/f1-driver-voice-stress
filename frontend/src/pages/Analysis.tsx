import { useEffect, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { motion } from "framer-motion";
import Navbar from "../components/common/Navbar";
import LoadingState from "../components/common/LoadingState";
import ErrorState from "../components/common/ErrorState";
import DriverAvatar from "../components/driver/DriverAvatar";
import DriverStatePanel from "../components/driver/DriverStatePanel";
import TranscriptPanel from "../components/driver/TranscriptPanel";
import RadioTimeline from "../components/driver/RadioTimeline";
import StateTimeline from "../components/driver/StateTimeline";
import RaceHeader from "../components/race/RaceHeader";
import LapPerformance from "../components/race/LapPerformance";
import LapHistory from "../components/race/LapHistory";
import SectorTimes from "../components/race/SectorTimes";
import PositionCard from "../components/race/PositionCard";
import RaceControlTimeline from "../components/race/RaceControlTimeline";
import WeatherPanel from "../components/race/WeatherPanel";
import StintPanel from "../components/race/StintPanel";
import PerformanceChart from "../components/charts/PerformanceChart";
import StatePerformanceChart from "../components/charts/StatePerformanceChart";
import TrackMap from "../components/map/TrackMap";
import { useAnalysis } from "../hooks/useAnalysis";
import type { LapEntry } from "../types/api";

export default function Analysis() {
  const [params] = useSearchParams();
  const navigate = useNavigate();
  const { data, loading, stageIndex, error, run } = useAnalysis();
  const [activeRadioIndex, setActiveRadioIndex] = useState<number | null>(null);
  const [selectedLap, setSelectedLap] = useState<LapEntry | null>(null);

  const sessionKey = params.get("session_key");
  const driverNumber = params.get("driver_number");
  const radioSource = (params.get("radio_source") as "openf1" | "upload") || "openf1";

  useEffect(() => {
    if (!sessionKey || !driverNumber) {
      navigate("/");
      return;
    }
    run(Number(sessionKey), Number(driverNumber), radioSource);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [sessionKey, driverNumber]);

  if (loading || (!data && !error)) {
    return <LoadingState stageIndex={stageIndex} />;
  }

  if (error || !data) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-void grid-overlay px-6">
        <div className="max-w-sm w-full">
          <ErrorState
            message={error || "Unable to load analysis."}
            onRetry={() => sessionKey && driverNumber && run(Number(sessionKey), Number(driverNumber), radioSource)}
          />
        </div>
      </div>
    );
  }

  const currentLapEntry = selectedLap || data.laps[data.laps.length - 1];
  const bestLapEntry = data.laps.reduce<LapEntry | undefined>((best, l) => {
    if (l.lap_duration == null) return best;
    if (!best || (best.lap_duration != null && l.lap_duration < best.lap_duration)) return l;
    return best;
  }, undefined);

  // Single classified sample in this prototype -> one state timeline
  // point at the driver's current lap (spec §23 "single sample analysis").
  const statePoints = [{ lap: data.race.current_lap ?? data.laps[data.laps.length - 1]?.lap_number ?? 1, state: data.driver_state.label }];

  return (
    <div className="min-h-screen bg-void grid-overlay">
      <Navbar />
      <div className="pt-14 flex flex-col lg:flex-row">
        {/* LEFT: Driver Intelligence */}
        <motion.section
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.5 }}
          className="lg:w-[72%] relative px-5 md:px-8 py-6 space-y-5 pb-56 lg:pb-72"
        >
          <div className="label-micro text-accent mb-1">DRIVER INTELLIGENCE</div>
          <DriverStatePanel driverState={data.driver_state} vocalFeatures={data.vocal_features} />
          <TranscriptPanel audio={data.audio} />
          <div className="grid md:grid-cols-2 gap-5">
            <RadioTimeline clips={data.radio_clips} activeIndex={activeRadioIndex} onSelect={setActiveRadioIndex} />
            <StateTimeline points={statePoints} />
          </div>
        </motion.section>

        {/* RIGHT: Race Intelligence */}
        <motion.aside
          initial={{ opacity: 0, x: 16 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.55, delay: 0.1 }}
          className="lg:w-[28%] border-t lg:border-t-0 lg:border-l border-line px-5 md:px-6 py-6 space-y-5"
        >
          <div className="label-micro text-accent mb-1">RACE INTELLIGENCE</div>
          {data.is_demo && (
            <div className="label-micro text-muted/50 border border-line px-2 py-1 inline-block">DEMO DATA</div>
          )}
          <RaceHeader session={data.session} driver={data.driver} />
          <LapPerformance race={data.race} />
          <SectorTimes currentLap={currentLapEntry} bestLap={bestLapEntry} />
          <PositionCard race={data.race} />
          <TrackMap location={data.location} />
          <LapHistory laps={data.laps} onSelectLap={setSelectedLap} />
          <PerformanceChart laps={data.laps} />
          <StatePerformanceChart analysis={data.analysis} />
          <RaceControlTimeline events={data.race_control} />
          <WeatherPanel samples={data.weather} />
          <StintPanel stints={data.stints} currentLap={data.race.current_lap} />
        </motion.aside>
      </div>

      <DriverAvatar state={data.driver_state.label} teamColour={data.driver.team_colour} />
    </div>
  );
}
