import { Link, useLocation, useNavigate } from "react-router-dom";
import { requestToken } from "../api/auth";
import AuthForm from "../components/AuthForm";
import { useAuth } from "../context/AuthContext";

export default function Login() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const handleLogin = async ({ email, password }) => {
    login(await requestToken(email, password));
    // Return to the page that sent the visitor here, if any.
    navigate(location.state?.from?.pathname ?? "/app", { replace: true });
  };

  return (
    <AuthForm
      title="Welcome back"
      subtitle="Log in to see your spending."
      submitLabel="Log in"
      onSubmit={handleLogin}
      footer={
        <>
          New here?{" "}
          <Link to="/signup" className="font-medium text-emerald-700 hover:underline">
            Create an account
          </Link>
        </>
      }
    />
  );
}
