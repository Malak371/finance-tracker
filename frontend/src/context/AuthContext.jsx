import { createContext, useState, useEffect, useContext } from "react";

const AuthContext = createContext();

export function AuthProvider({children}) {
    const [token, setToken] = useState(localStorage.getItem("token") || null);

    useEffect(() => {
        if (token) {
            localStorage.setItem("token", token);
        } else {
            localStorage.removeItem("token");
        }
    }, [token]);

    const login = (newToken) => {
        setToken(newToken);
    };

    const logout = () => {
        setToken(null);
    };

    return (
        <AuthContext.Provider value={{token, login, logout}}>
            {children}
        </AuthContext.Provider>
    );
}

export function useAuth() {
    return useContext(AuthContext);
}