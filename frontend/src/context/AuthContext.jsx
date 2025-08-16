import React, { createContext, useContext, useState, useEffect } from "react";
import { loginUser, signupUser } from "../api";

const AuthContext = createContext();

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  // On mount, check for token and set authenticated state
  useEffect(() => {
    const token = localStorage.getItem("token");
    if (token) {
      try {
        const payload = JSON.parse(atob(token.split('.')[1]));
        // Optionally check token expiration
        if (payload.exp && Date.now() / 1000 < payload.exp) {
          setIsAuthenticated(true);
          setUser({ id: payload.user_id, name: payload.name });
        } else {
          setIsAuthenticated(false);
          setUser(null);
        }
      } catch {
        setIsAuthenticated(false);
        setUser(null);
      }
    } else {
      setIsAuthenticated(false);
      setUser(null);
    }
  }, []);

  const login = async (email, password) => {
    setLoading(true);
    setError("");
    try {
      const res = await loginUser(email, password);
      setUser(res.user);
      if (res.token) {
        localStorage.setItem("token", res.token);
        // Set authenticated state
        try {
          const payload = JSON.parse(atob(res.token.split('.')[1]));
          if (payload.exp && Date.now() / 1000 < payload.exp) {
            setIsAuthenticated(true);
            setUser({ id: payload.user_id, name: payload.name });
          }
        } catch {}
      }
      return true;
    } catch (err) {
      setError(err?.response?.data?.detail || "Login failed");
      return false;
    } finally {
      setLoading(false);
    }
  };

  const signup = async (email, password) => {
    setLoading(true);
    setError("");
    try {
      const res = await signupUser({ email, password });
      setUser(res.user);
      if (res.token) {
        localStorage.setItem("token", res.token);
        // Set authenticated state
        try {
          const payload = JSON.parse(atob(res.token.split('.')[1]));
          if (payload.exp && Date.now() / 1000 < payload.exp) {
            setIsAuthenticated(true);
            setUser({ id: payload.user_id, name: payload.name });
          }
        } catch {}
      }
      return true;
    } catch (err) {
      setError(err?.response?.data?.detail || "Signup failed");
      return false;
    } finally {
      setLoading(false);
    }
  };

  const logout = () => {
    setUser(null);
    setIsAuthenticated(false);
    localStorage.removeItem("token");
  };

  return (
    <AuthContext.Provider
      value={{ user, isAuthenticated, loading, error, login, signup, logout }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}
