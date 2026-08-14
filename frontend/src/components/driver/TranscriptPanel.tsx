import type { AudioResult } from "../../types/api";
import { DataPanel } from "../common/DataPanel";
import RadioPlayer from "./RadioPlayer";
import { useState } from "react";
import clsx from "clsx";

interface Props {
  audio: AudioResult;
}

export default function TranscriptPanel({ audio }: Props) {
  const [playhead, setPlayhead] = useState(0);

  return (
    <DataPanel title="Radio Transcript">
      <RadioPlayer src={audio.source === "upload" ? undefined : undefined} duration={audio.duration} onProgress={setPlayhead} />

      <div className="mt-4">
        {audio.segments.length > 0 ? (
          <p className="text-sm leading-relaxed">
            {audio.segments.map((seg, i) => {
              const active = playhead >= seg.start && playhead < seg.end;
              return (
                <span
                  key={i}
                  className={clsx(
                    "transition-colors duration-150",
                    active ? "text-offwhite bg-accent/20 px-0.5" : "text-muted"
                  )}
                >
                  {seg.text}{" "}
                </span>
              );
            })}
          </p>
        ) : audio.transcript ? (
          <p className="text-sm text-offwhite/90 leading-relaxed">&ldquo;{audio.transcript}&rdquo;</p>
        ) : (
          <p className="text-sm text-muted">No transcript available for this clip.</p>
        )}
      </div>

      <div className="flex items-center justify-between mt-4 pt-3 border-t border-line label-micro text-muted/70">
        <span>Duration: {audio.duration ? `${audio.duration.toFixed(1)}s` : "N/A"}</span>
        <span className="uppercase">{audio.source}</span>
      </div>
    </DataPanel>
  );
}
