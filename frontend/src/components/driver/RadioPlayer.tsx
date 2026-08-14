import { useEffect, useMemo, useRef, useState } from "react";
import { Pause, Play, Volume2 } from "lucide-react";

interface Props {
  src?: string | null;
  duration?: number | null;
  onProgress?: (currentTime: number) => void;
}

// A premium custom transport. When a real `src` (OpenF1 recording_url
// or an uploaded blob URL) is available we drive an actual <audio>
// element. When there's no playable source (demo mode / no clip
// selected yet) we still render the full UI with a simulated
// timeline so the interface never falls back to an ugly native
// control (spec §21).
export default function RadioPlayer({ src, duration, onProgress }: Props) {
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const [playing, setPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [speed, setSpeed] = useState(1);
  const [volume, setVolume] = useState(0.85);
  const simDuration = duration || 6.8;

  const bars = useMemo(() => {
    // deterministic pseudo-waveform so it doesn't jump every render
    let seed = 42;
    const rnd = () => {
      seed = (seed * 9301 + 49297) % 233280;
      return seed / 233280;
    };
    return Array.from({ length: 64 }, () => 0.2 + rnd() * 0.8);
  }, [src]);

  useEffect(() => {
    if (!playing) return;
    if (src && audioRef.current) return; // real element drives time via onTimeUpdate
    const id = window.setInterval(() => {
      setCurrentTime((t) => {
        const next = t + 0.2 * speed;
        if (next >= simDuration) {
          setPlaying(false);
          return 0;
        }
        onProgress?.(next);
        return next;
      });
    }, 200);
    return () => window.clearInterval(id);
  }, [playing, src, speed, simDuration, onProgress]);

  function togglePlay() {
    if (src && audioRef.current) {
      if (playing) audioRef.current.pause();
      else audioRef.current.play();
    }
    setPlaying((p) => !p);
  }

  const progressPct = Math.min(100, (currentTime / simDuration) * 100);

  return (
    <div className="border border-line bg-surface-2 p-4">
      {src && (
        <audio
          ref={audioRef}
          src={src}
          onTimeUpdate={(e) => {
            const t = e.currentTarget.currentTime;
            setCurrentTime(t);
            onProgress?.(t);
          }}
          onEnded={() => setPlaying(false)}
        />
      )}
      <div className="flex items-center gap-3">
        <button
          onClick={togglePlay}
          className="w-9 h-9 shrink-0 flex items-center justify-center bg-accent hover:bg-accent-dim transition-colors"
          aria-label={playing ? "Pause" : "Play"}
        >
          {playing ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4 ml-0.5" />}
        </button>

        <div className="flex-1 flex items-end gap-[2px] h-8 overflow-hidden">
          {bars.map((h, i) => {
            const barPct = (i / bars.length) * 100;
            const active = barPct <= progressPct;
            return (
              <div
                key={i}
                className={active ? "bg-accent" : "bg-line"}
                style={{ height: `${h * 100}%`, width: "2px", flexShrink: 0 }}
              />
            );
          })}
        </div>
      </div>

      <div className="flex items-center justify-between mt-3 text-[11px] num-display text-muted">
        <span>{formatTime(currentTime)}</span>
        <div className="flex items-center gap-3">
          <select
            value={speed}
            onChange={(e) => setSpeed(Number(e.target.value))}
            className="bg-transparent border border-line px-1.5 py-0.5 text-[10px]"
          >
            {[0.5, 1, 1.5, 2].map((s) => (
              <option key={s} value={s}>
                {s}x
              </option>
            ))}
          </select>
          <div className="flex items-center gap-1.5">
            <Volume2 className="w-3 h-3" />
            <input
              type="range"
              min={0}
              max={1}
              step={0.05}
              value={volume}
              onChange={(e) => {
                const v = Number(e.target.value);
                setVolume(v);
                if (audioRef.current) audioRef.current.volume = v;
              }}
              className="w-14 accent-accent"
            />
          </div>
        </div>
        <span>{formatTime(simDuration)}</span>
      </div>
    </div>
  );
}

function formatTime(s: number): string {
  const m = Math.floor(s / 60);
  const sec = Math.floor(s % 60);
  return `${m}:${sec.toString().padStart(2, "0")}`;
}
