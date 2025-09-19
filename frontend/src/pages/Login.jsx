import {useState} from "react";
import api from "../api/api";
import { useNavigate } from "react-router-dom";
import {useAuth} from "../context/AuthContext";

export default function Login() {
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const navigate = useNavigate();
    const {login} = useAuth();

    const handleLogin = async (e) => {
        e.preventDefault();
        try {
            const formData = new URLSearchParams();
            formData.append("username", email);
            formData.append("password", password);
            const res = await api.post("/auth/login", formData);
            login(res.data.access_token);
            navigate("/");
        } catch (err) {
            alert(err.response?.data?.detail || "Error logging in");
        }
    };

    return (
        <div className="flex h-screen items-center justify-center bg-gray-900">
      <form
        onSubmit={handleLogin}
        className="w-full max-w-md rounded-2xl bg-gray-800 p-8 shadow-lg shadow-cyan-500/50"
      >
        <h2 className="mb-6 text-center text-3xl font-bold text-cyan-400">
          Login
        </h2>

        <input
          type="email"
          placeholder="Email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          required
          className="mb-4 w-full rounded-lg bg-gray-700 px-4 py-2 text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-cyan-400 focus:ring-offset-1"
        />

        <input
          type="password"
          placeholder="Password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
          className="mb-6 w-full rounded-lg bg-gray-700 px-4 py-2 text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-cyan-400 focus:ring-offset-1"
        />

        <button
          type="submit"
          className="w-full rounded-lg bg-cyan-500 px-4 py-2 font-semibold text-gray-900 transition hover:bg-cyan-400"
        >
          Login
        </button>
      </form>
    </div>
    );
}