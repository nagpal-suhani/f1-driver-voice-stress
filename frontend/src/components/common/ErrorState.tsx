import { AlertTriangle } from "lucide-react";

interface Props {
  message: string;
  onRetry?: () => void;
}

export default function ErrorState({ message, onRetry }: Props) {
  return (
    <div className="panel px-5 py-4 flex items-start gap-3 border-accent-dim/60">
      <AlertTriangle className="w-4 h-4 text-accent shrink-0 mt-0.5" />
      <div className="flex-1">
        <p className="text-sm text-offwhite/90">{message}</p>
        {onRetry && (
          <button onClick={onRetry} className="btn-ghost mt-3 !px-4 !py-2">
            Retry
          </button>
        )}
      </div>
    </div>
  );
}
