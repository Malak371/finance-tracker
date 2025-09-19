import {Link, useNavigate} from "react-router-dom";
import {useAuth} from "../context/AuthContext";

export default function Navbar() {
    const {token, logout} = useAuth();
    const navigate = useNavigate();

    const handleLogout = () => {
        logout();
        navigate("/login");
    };

    return (
        <nav className="flex items-center justify-between bg-gray-900 px-6 py-4 shadow-lg shadow-cyan-500/30">
      <Link
        to="/"
        className="text-cyan-400 text-xl font-bold hover:text-cyan-300 transition-colors"
      >
        FinanceApp
      </Link>

      <div className="flex items-center space-x-6">
        {!token && (
          <>
            <Link
              to="/signup"
              className="text-gray-300 hover:text-cyan-400 transition-colors"
            >
              Signup
            </Link>
            <Link
              to="/login"
              className="text-gray-300 hover:text-cyan-400 transition-colors"
            >
              Login
            </Link>
          </>
        )}

        {token && (
          <button
            onClick={handleLogout}
            className="rounded-lg bg-cyan-500 px-4 py-2 font-semibold text-gray-900 transition hover:bg-cyan-400 hover:shadow-lg hover:shadow-cyan-500/50"
          >
            Logout
          </button>
        )}
      </div>
    </nav>
    );
}