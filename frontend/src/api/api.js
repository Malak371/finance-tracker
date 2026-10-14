import axios from "axios";

const API_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

const api = axios.create({ baseURL: API_URL });

api.interceptors.request.use((config) => {
  const token = localStorage.getItem("token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Turns any API or network error into a message that can be shown to the user.
export function errorMessage(err, fallback = "Something went wrong. Please try again.") {
  const error = err?.response?.data?.error;
  if (error?.details?.length) {
    return error.details.map((d) => `${d.field}: ${d.message}`).join("\n");
  }
  if (error?.message) return error.message;
  if (err?.request && !err.response) return "Can't reach the server. Check your connection and try again.";
  return fallback;
}

export default api;
