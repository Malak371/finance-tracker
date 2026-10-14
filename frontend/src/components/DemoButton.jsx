import { Sparkles } from "lucide-react";
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import api from "../api/api";
import { useAuth } from "../context/AuthContext";
import { Button, ErrorMessage } from "./ui";

export default function DemoButton() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const startDemo = async () => {
    setError(null);
    setLoading(true);
    try {
      const response = await api.post("/auth/demo");
      login(response.data.access_token);
      navigate("/", { replace: true });
    } catch (err) {
      setError(err);
      setLoading(false);
    }
  };

  return (
    <div className="space-y-3">
      <Button variant="secondary" className="w-full" onClick={startDemo} loading={loading}>
        {!loading && <Sparkles className="size-4 text-emerald-600" aria-hidden />}
        {loading ? "Setting up your demo…" : "Try the demo, no sign-up"}
      </Button>
      <ErrorMessage error={error} />
    </div>
  );
}
