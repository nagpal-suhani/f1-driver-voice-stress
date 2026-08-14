import { motion } from "framer-motion";
import { ANALYSIS_STAGES } from "../../hooks/useAnalysis";

interface Props {
  stageIndex: number;
}

export default function LoadingState({ stageIndex }: Props) {
  return (
    <div className="min-h-screen flex items-center justify-center bg-void grid-overlay">
      <div className="text-center">
        <motion.div
          className="w-10 h-10 border-2 border-accent border-t-transparent rounded-full mx-auto mb-8"
          animate={{ rotate: 360 }}
          transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
        />
        <div className="space-y-2">
          {ANALYSIS_STAGES.map((stage, i) => (
            <motion.p
              key={stage}
              initial={{ opacity: 0.2 }}
              animate={{ opacity: i === stageIndex ? 1 : i < stageIndex ? 0.35 : 0.15 }}
              className={`label-micro tracking-[0.25em] ${i === stageIndex ? "text-accent" : "text-muted"}`}
            >
              {stage}
            </motion.p>
          ))}
        </div>
      </div>
    </div>
  );
}
