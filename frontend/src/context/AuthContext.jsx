import React, { createContext, useContext, useState, useEffect } from "react";
import { loginUser, signupUser } from "../api";

const AuthContext = createContext();

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const login = async (email, password) => {
    setLoading(true);
    setError("");
    try {
      const res = await loginUser(email, password);
      setUser(res.user);
      if (res.token) {
        localStorage.setItem("token", res.token);
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
    localStorage.removeItem("token");
  };

  return (
    <AuthContext.Provider
      value={{ user, loading, error, login, signup, logout }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}
