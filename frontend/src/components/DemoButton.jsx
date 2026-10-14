import { Sparkles } from "lucide-react";
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { requestDemoToken } from "../api/auth";
import { useAuth } from "../context/AuthContext";
import SlowServerHint from "./SlowServerHint";
import { Button, ErrorMessage } from "./ui";

export default function DemoButton({
  variant = "secondary",
  label = "Try the demo, no sign-up",
  className = "",
}) {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleClick = async () => {
    setError(null);
    setLoading(true);
    try {
      login(await requestDemoToken());
      navigate("/app", { replace: true });
    } catch (err) {
      setError(err);
      setLoading(false);
    }
  };

  return (
    <div className="space-y-3">
      <Button
        variant={variant}
        className={`w-full ${className}`}
        onClick={handleClick}
        loading={loading}
      >
        {!loading && (
          <Sparkles
            className={`size-4 ${variant === "primary" ? "text-white" : "text-emerald-600"}`}
            aria-hidden
          />
        )}
        {loading ? "Setting up your demo…" : label}
      </Button>
      <SlowServerHint active={loading} />
      <ErrorMessage error={error} />
    </div>
  );
}
