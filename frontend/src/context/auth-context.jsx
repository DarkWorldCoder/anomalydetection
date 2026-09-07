import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from "react";

import { api } from "@/lib/api";

const TOKEN_KEY = "api-anomaly-token";
const AuthContext = createContext(null);

function readToken() {
  return localStorage.getItem(TOKEN_KEY) || sessionStorage.getItem(TOKEN_KEY);
}

function saveToken(token, remember) {
  localStorage.removeItem(TOKEN_KEY);
  sessionStorage.removeItem(TOKEN_KEY);
  (remember ? localStorage : sessionStorage).setItem(TOKEN_KEY, token);
}

function clearToken() {
  localStorage.removeItem(TOKEN_KEY);
  sessionStorage.removeItem(TOKEN_KEY);
}

export function AuthProvider({ children }) {
  const [token, setToken] = useState(readToken);
  const [user, setUser] = useState(null);
  const [isLoading, setIsLoading] = useState(Boolean(token));

  const clearSession = useCallback(() => {
    clearToken();
    setToken(null);
    setUser(null);
  }, []);

  useEffect(() => {
    if (!token) {
      setIsLoading(false);
      return;
    }

    let active = true;
    setIsLoading(true);
    api("/auth/me", { token })
      .then((currentUser) => {
        if (active) setUser(currentUser);
      })
      .catch(() => {
        if (active) clearSession();
      })
      .finally(() => {
        if (active) setIsLoading(false);
      });

    return () => {
      active = false;
    };
  }, [token, clearSession]);

  const login = useCallback(async ({ email, password, remember = false }) => {
    const data = await api("/auth/login", {
      method: "POST",
      body: { email, password },
    });
    saveToken(data.access_token, remember);
    setToken(data.access_token);
    setUser(data.user);
    return data.user;
  }, []);

  const register = useCallback(async ({ fullName, email, password, role }) => {
    return api("/auth/register", {
      method: "POST",
      body: { full_name: fullName, email, password, role },
    });
  }, []);

  const logout = useCallback(async () => {
    try {
      if (token) await api("/auth/logout", { token });
    } finally {
      clearSession();
    }
  }, [token, clearSession]);

  const updateProfile = useCallback(
    async ({ fullName, email }) => {
      const updatedUser = await api("/auth/me", {
        method: "PATCH",
        token,
        body: { full_name: fullName, email },
      });
      setUser(updatedUser);
      return updatedUser;
    },
    [token],
  );

  const value = useMemo(
    () => ({
      token,
      user,
      isLoading,
      isAuthenticated: Boolean(token && user),
      login,
      register,
      updateProfile,
      logout,
    }),
    [token, user, isLoading, login, register, updateProfile, logout],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) throw new Error("useAuth must be used within AuthProvider");
  return context;
}
