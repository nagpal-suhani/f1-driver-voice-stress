import { motion } from "framer-motion";
import type { DriverStateLabel } from "../../types/api";

interface Props {
  state: DriverStateLabel;
  teamColour?: string | null;
}

// Every visual trait — eyebrow angle, eye openness, mouth curve, jitter,
// breathing speed, glow colour — is driven by the estimated state, so
// the face actually reads as an emotion rather than a static prop.
const STATE_CONFIG: Record<
  DriverStateLabel,
  {
    glow: string;
    accent: string;
    breath: number;
    jitter: number;
    browLeft: string; // path 'd' for left eyebrow
    browRight: string;
    mouth: string; // path 'd' for mouth
    eyeOpen: number; // 0-1, eyelid height multiplier
    blinkSpeed: number;
  }
> = {
  CALM: {
    glow: "rgba(138,143,152,0.3)",
    accent: "#9aa0aa",
    breath: 3.6,
    jitter: 0.4,
    browLeft: "M78 84 Q90 80 102 84",
    browRight: "M138 84 Q150 80 162 84",
    mouth: "M96 138 Q120 148 144 138",
    eyeOpen: 1,
    blinkSpeed: 4.2,
  },
  ELEVATED: {
    glow: "rgba(225,143,0,0.32)",
    accent: "#e18f00",
    breath: 2.4,
    jitter: 1.1,
    browLeft: "M78 80 Q90 74 104 80",
    browRight: "M136 80 Q150 74 162 80",
    mouth: "M94 140 Q120 132 146 140",
    eyeOpen: 1.15,
    blinkSpeed: 2.6,
  },
  STRESSED: {
    glow: "rgba(225,6,0,0.45)",
    accent: "#e10600",
    breath: 1.3,
    jitter: 2.6,
    browLeft: "M78 86 Q92 76 106 86",
    browRight: "M134 86 Q148 76 162 86",
    mouth: "M96 144 Q120 136 144 144",
    eyeOpen: 0.85,
    blinkSpeed: 1.4,
  },
  "FATIGUE-LIKE": {
    glow: "rgba(90,110,225,0.32)",
    accent: "#5a6ee1",
    breath: 4.8,
    jitter: 0.25,
    browLeft: "M78 88 Q90 86 104 90",
    browRight: "M136 90 Q150 86 162 88",
    mouth: "M98 140 Q120 136 142 140",
    eyeOpen: 0.4,
    blinkSpeed: 5.5,
  },
};

// A layered SVG "digital twin" face — not a full WebGL 3D model, but an
// expressive, state-reactive avatar: eyebrow angle, eye openness, and
// mouth curve all change with the estimated vocal state, plus a
// breathing/jitter/glow reaction, so the emotion is actually legible.
export default function DriverAvatar({ state, teamColour }: Props) {
  const cfg = STATE_CONFIG[state] ?? STATE_CONFIG.CALM;
  const teamAccent = teamColour ? `#${teamColour.replace("#", "")}` : null;

  return (
    <div
      className="fixed bottom-2 md:bottom-4 left-0 z-20 pointer-events-none flex justify-center lg:justify-start"
      style={{ width: "min(70vw, 100%)" }}
    >
      <div className="relative flex flex-col items-center lg:ml-[13%]" style={{ width: "min(60%, 200px)" }}>
        <motion.div
          className="absolute -bottom-2 w-32 h-32 rounded-full blur-2xl"
          style={{ background: cfg.glow }}
          animate={{ opacity: [0.35, 0.65, 0.35], scale: [0.9, 1.06, 0.9] }}
          transition={{ duration: cfg.breath, repeat: Infinity, ease: "easeInOut" }}
        />

        <motion.svg
          viewBox="0 0 240 260"
          className="relative w-40 md:w-48 drop-shadow-2xl"
          animate={{ y: [0, -4, 0], rotate: [-cfg.jitter, cfg.jitter, -cfg.jitter] }}
          transition={{ duration: cfg.breath, repeat: Infinity, ease: "easeInOut" }}
        >
          <defs>
            <linearGradient id="busttone" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#3a3e46" />
              <stop offset="100%" stopColor="#1b1e23" />
            </linearGradient>
            <radialGradient id="facetone" cx="45%" cy="35%" r="70%">
              <stop offset="0%" stopColor="#585d68" />
              <stop offset="100%" stopColor="#2a2d33" />
            </radialGradient>
          </defs>

          {/* shoulders / racing suit */}
          <path
            d="M30 260 C30 190 70 168 120 168 C170 168 210 190 210 260 Z"
            fill="url(#busttone)"
            stroke="#6a6e78"
            strokeWidth="1.5"
          />
          <path d="M90 172 L120 190 L150 172 L150 158 L90 158 Z" fill={teamAccent || cfg.accent} opacity="0.85" />

          {/* head */}
          <ellipse cx="120" cy="102" rx="60" ry="66" fill="url(#facetone)" stroke="#6a6e78" strokeWidth="2" />

          {/* eyebrows — angle carries most of the emotional read */}
          <motion.path
            d={cfg.browLeft}
            stroke={cfg.accent}
            strokeWidth="4"
            strokeLinecap="round"
            fill="none"
            animate={{ d: cfg.browLeft }}
            transition={{ duration: 0.6 }}
          />
          <motion.path
            d={cfg.browRight}
            stroke={cfg.accent}
            strokeWidth="4"
            strokeLinecap="round"
            fill="none"
            animate={{ d: cfg.browRight }}
            transition={{ duration: 0.6 }}
          />

          {/* eyes — openness + blink driven by state */}
          {[92, 148].map((cx) => (
            <motion.ellipse
              key={cx}
              cx={cx}
              cy="104"
              rx="9"
              ry={7 * cfg.eyeOpen}
              fill="#0c0d10"
              stroke={cfg.accent}
              strokeWidth="1.5"
              animate={{ ry: [7 * cfg.eyeOpen, 0.8, 7 * cfg.eyeOpen] }}
              transition={{ duration: cfg.blinkSpeed, repeat: Infinity, repeatDelay: cfg.blinkSpeed * 1.4, ease: "easeInOut" }}
            />
          ))}
          {[92, 148].map((cx) => (
            <circle key={`pupil-${cx}`} cx={cx} cy="104" r="2.6" fill={cfg.accent} />
          ))}

          {/* mouth — curve flips from a gentle smile (CALM) to a tight
              line (STRESSED) to a flat downturn (FATIGUE-LIKE) */}
          <motion.path
            d={cfg.mouth}
            stroke={cfg.accent}
            strokeWidth="3.5"
            strokeLinecap="round"
            fill="none"
            animate={{ d: cfg.mouth }}
            transition={{ duration: 0.6 }}
          />

          {/* jaw / cheek shading for depth */}
          <path d="M64 112 C64 138 88 156 120 156 C152 156 176 138 176 112" fill="none" stroke="#6a6e78" strokeWidth="1" opacity="0.4" />
        </motion.svg>

        <motion.div
          className="mt-1 w-2 h-2 rounded-full"
          style={{ background: cfg.accent }}
          animate={{ opacity: [0.4, 1, 0.4] }}
          transition={{ duration: cfg.breath, repeat: Infinity, ease: "easeInOut" }}
        />
      </div>
    </div>
  );
}
