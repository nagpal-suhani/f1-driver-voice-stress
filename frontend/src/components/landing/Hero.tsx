import { motion } from "framer-motion";

const container = {
  hidden: {},
  show: {
    transition: { staggerChildren: 0.14, delayChildren: 0.15 },
  },
};

const rise = {
  hidden: { opacity: 0, y: 26 },
  show: { opacity: 1, y: 0, transition: { duration: 0.8, ease: [0.16, 1, 0.3, 1] } },
};

export function HeroBackground() {
  return (
    <>
      {/* Cinematic backdrop — layered gradients + motion streaks stand
          in for a licensed race-photo hero (spec §8). Swap in a real
          image via `bg-hero` in index.css / an <img> layer when brand
          assets are finalized. */}
      <div className="absolute inset-0 -z-10 overflow-hidden bg-void">
        <div className="absolute inset-0 grid-overlay opacity-60" />
        <div
          className="absolute inset-0"
          style={{
            background:
              "radial-gradient(ellipse 90% 60% at 78% 15%, rgba(225,6,0,0.14), transparent 60%), radial-gradient(ellipse 70% 50% at 10% 90%, rgba(225,6,0,0.08), transparent 60%)",
          }}
        />
        {/* motion streaks */}
        <svg className="absolute inset-0 w-full h-full opacity-25" preserveAspectRatio="none">
          {Array.from({ length: 14 }).map((_, i) => (
            <line
              key={i}
              x1={`${-10 + i * 9}%`}
              y1="0%"
              x2={`${5 + i * 9}%`}
              y2="100%"
              stroke={i % 5 === 0 ? "#e10600" : "#3a3d45"}
              strokeWidth={i % 5 === 0 ? 1.4 : 0.6}
            />
          ))}
        </svg>
        <div className="absolute inset-0 bg-gradient-to-t from-void via-void/70 to-void/20" />
        <div className="absolute inset-0 bg-gradient-to-r from-void/95 via-void/40 to-transparent" />
        {/* subtle vignette */}
        <div
          className="absolute inset-0"
          style={{ boxShadow: "inset 0 0 220px 60px rgba(0,0,0,0.75)" }}
        />
      </div>
    </>
  );
}

export function HeroContent() {
  return (
      <motion.div variants={container} initial="hidden" animate="show" className="max-w-xl">
        <motion.div variants={rise} className="label-micro text-accent mb-5 flex items-center gap-2">
          <span className="w-6 h-px bg-accent" />
          RACE-ENGINEERING DECISION SUPPORT
        </motion.div>
        <motion.h1 variants={rise} className="font-display uppercase leading-[0.95] text-5xl md:text-6xl lg:text-7xl font-semibold">
          <span className="text-muted/60 text-2xl md:text-3xl block mb-2 tracking-widest">PROJECT NAME</span>
          Read the Driver.
          <br />
          <span className="text-accent">Understand</span> the Race.
        </motion.h1>
        <motion.p variants={rise} className="mt-6 text-muted text-base md:text-lg max-w-md leading-relaxed">
          Voice-derived driver state, aligned against objective session telemetry — so the
          engineer sees what changed, and when.
        </motion.p>
        <motion.div variants={rise} className="mt-8 flex items-center gap-6 label-micro text-muted/60">
          <span>VOICE</span>
          <span className="w-1 h-1 bg-accent rounded-full" />
          <span>VOCAL STATE</span>
          <span className="w-1 h-1 bg-accent rounded-full" />
          <span>RACE DATA</span>
          <span className="w-1 h-1 bg-accent rounded-full" />
          <span>TIME</span>
        </motion.div>
      </motion.div>
  );
}
