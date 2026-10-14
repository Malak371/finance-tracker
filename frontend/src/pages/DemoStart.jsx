import { useEffect, useRef, useState } from "react";
import { Link, Navigate } from "react-router-dom";
import { requestDemoToken } from "../api/auth";
import { ErrorMessage, LoadingState } from "../components/ui";
import { useAuth } from "../context/AuthContext";

// /demo: a shareable link (README, CV) that opens a fresh demo account directly.
export default function DemoStart() {
  const { login } = useAuth();
  const [status, setStatus] = useState({ done: false, error: null });
  const started = useRef(false);

  useEffect(() => {
    // Guard against React StrictMode running the effect twice in development.
    if (started.current) return;
    started.current = true;
    requestDemoToken().then(
      (token) => {
        login(token);
        setStatus({ done: true, error: null });
      },
      (error) => setStatus({ done: false, error }),
    );
  }, [login]);

  if (status.done) return <Navigate to="/app" replace />;
  return (
    <div className="mx-auto flex min-h-screen max-w-md flex-col justify-center px-4">
      {status.error ? (
        <div className="space-y-4 text-center">
          <ErrorMessage error={status.error} />
          <Link to="/" className="text-sm font-medium text-emerald-700 hover:underline">
            Back to the home page
          </Link>
        </div>
      ) : (
        <LoadingState label="Setting up your demo with a year of sample data…" />
      )}
    </div>
  );
}
