import { Link } from "react-router-dom";
import { AlertTriangle } from "lucide-react";

export default function ErrorPage() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-void grid-overlay px-6">
      <div className="text-center max-w-sm">
        <AlertTriangle className="w-8 h-8 text-accent mx-auto mb-4" />
        <h1 className="font-display uppercase text-2xl font-semibold mb-2">Something Went Wrong</h1>
        <p className="text-sm text-muted mb-6">
          The console couldn&apos;t complete that request. Return home and try again.
        </p>
        <Link to="/" className="btn-command">
          RETURN HOME
        </Link>
      </div>
    </div>
  );
}
