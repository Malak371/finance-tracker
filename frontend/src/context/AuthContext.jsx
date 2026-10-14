import { createContext, useCallback, useContext, useEffect, useState } from "react";
import api from "../api/api";

const AuthContext = createContext(null);

function readToken() {
  try {
    return localStorage.getItem("token");
  } catch {
    return null;
  }
}

export function AuthProvider({ children }) {
  const [token, setToken] = useState(readToken);

  const login = useCallback((newToken) => {
    localStorage.setItem("token", newToken);
    setToken(newToken);
  }, []);

  const logout = useCallback(() => {
    localStorage.removeItem("token");
    setToken(null);
  }, []);

  // An expired or revoked token anywhere in the app sends the user back to the login page.
  useEffect(() => {
    const id = api.interceptors.response.use(undefined, (error) => {
      const isLoginAttempt = error.config?.url?.startsWith("/auth/");
      if (error.response?.status === 401 && !isLoginAttempt) logout();
      return Promise.reject(error);
    });
    return () => api.interceptors.response.eject(id);
  }, [logout]);

  return <AuthContext.Provider value={{ token, login, logout }}>{children}</AuthContext.Provider>;
}

// eslint-disable-next-line react-refresh/only-export-components
export function useAuth() {
  return useContext(AuthContext);
}
