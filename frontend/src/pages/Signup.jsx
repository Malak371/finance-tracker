import { Link, useNavigate } from "react-router-dom";
import api from "../api/api";
import { requestToken } from "../api/auth";
import AuthForm from "../components/AuthForm";
import { useAuth } from "../context/AuthContext";

export default function Signup() {
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleSignup = async ({ email, password }) => {
    await api.post("/auth/signup", { email, password });
    login(await requestToken(email, password));
    navigate("/app", { replace: true });
  };

  return (
    <AuthForm
      title="Create your account"
      subtitle="Start tracking where your money goes."
      submitLabel="Sign up"
      passwordHint="At least 8 characters."
      onSubmit={handleSignup}
      footer={
        <>
          Already have an account?{" "}
          <Link to="/login" className="font-medium text-emerald-700 hover:underline">
            Log in
          </Link>
        </>
      }
    />
  );
}
