import { motion } from "framer-motion";
import type { ReactNode } from "react";
import clsx from "clsx";

interface DataPanelProps {
  title: string;
  children: ReactNode;
  className?: string;
  right?: ReactNode;
}

export function DataPanel({ title, children, className, right }: DataPanelProps) {
  return (
    <motion.section
      initial={{ opacity: 0, y: 10 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: "-40px" }}
      transition={{ duration: 0.45, ease: "easeOut" }}
      className={clsx("panel panel-corner p-4", className)}
    >
      <div className="flex items-center justify-between mb-3">
        <h3 className="label-micro text-muted">{title}</h3>
        {right}
      </div>
      {children}
    </motion.section>
  );
}

interface TelemetryMetricProps {
  label: string;
  value: ReactNode;
  unit?: string;
  size?: "sm" | "md" | "lg";
  tone?: "default" | "accent" | "muted";
}

export function TelemetryMetric({ label, value, unit, size = "md", tone = "default" }: TelemetryMetricProps) {
  const sizeClass = size === "lg" ? "text-4xl" : size === "sm" ? "text-lg" : "text-2xl";
  const toneClass = tone === "accent" ? "text-accent" : tone === "muted" ? "text-muted" : "text-offwhite";
  return (
    <div>
      <div className="label-micro mb-1">{label}</div>
      <div className={clsx("num-display font-semibold", sizeClass, toneClass)}>
        {value === null || value === undefined || value === "" ? "N/A" : value}
        {unit && value !== null && value !== undefined && value !== "" ? (
          <span className="text-sm text-muted ml-1">{unit}</span>
        ) : null}
      </div>
    </div>
  );
}

export function formatLapTime(seconds?: number | null): string {
  if (seconds === null || seconds === undefined) return "N/A";
  const m = Math.floor(seconds / 60);
  const s = (seconds % 60).toFixed(3).padStart(6, "0");
  return `${m}:${s}`;
}

export function formatDelta(seconds?: number | null): string {
  if (seconds === null || seconds === undefined) return "N/A";
  const sign = seconds >= 0 ? "+" : "";
  return `${sign}${seconds.toFixed(3)}s`;
}
