import { Info } from "lucide-react";
import { startTransition } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { useApi } from "../hooks/useApi";

export default function DemoBanner() {
  const me = useApi("/auth/me");
  const { logout } = useAuth();
  const navigate = useNavigate();
  if (!me.data?.is_demo) return null;

  const signUp = () => {
    // Same transition for both updates, so the protected page doesn't redirect to /login first.
    startTransition(() => {
      navigate("/signup");
      logout();
    });
  };

  return (
    <div className="flex flex-wrap items-center gap-x-3 gap-y-1 bg-emerald-700 px-4 py-2 text-sm text-white">
      <Info className="size-4 shrink-0" aria-hidden />
      <p className="flex-1">
        <span className="sm:hidden">Demo account with sample data, deleted after 24 hours.</span>
        <span className="hidden sm:inline">
          You&apos;re exploring a demo account with a year of sample data. Change anything you like;
          it&apos;s deleted after 24 hours.
        </span>
      </p>
      <button type="button" onClick={signUp} className="font-semibold underline underline-offset-2">
        <span className="sm:hidden">Sign up</span>
        <span className="hidden sm:inline">Create your own account</span>
      </button>
    </div>
  );
}
