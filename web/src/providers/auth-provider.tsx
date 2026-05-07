"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useState,
  type ReactNode,
} from "react";
import { apiClient } from "@/lib/api";

export interface AuthUser {
  id: string;
  email: string;
  is_admin: boolean;
}

interface AuthState {
  user: AuthUser | null;
  token: string | null;
  isLoading: boolean;
  signIn: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string) => Promise<void>;
  signOut: () => void;
}

const AuthContext = createContext<AuthState | null>(null);

const TOKEN_KEY = "ocw_user_token";

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const fetchMe = useCallback(async (jwt: string) => {
    try {
      const { data } = await apiClient.get<AuthUser>("/users/me", {
        headers: { Authorization: `Bearer ${jwt}` },
        timeout: 5000, // Don't block the page if Railway is cold-starting
      });
      setUser(data);
    } catch {
      // Token invalid / expired
      localStorage.removeItem(TOKEN_KEY);
      setToken(null);
      setUser(null);
    }
  }, []);

  // Rehydrate from localStorage on mount
  useEffect(() => {
    const stored = localStorage.getItem(TOKEN_KEY);
    if (stored) {
      setToken(stored);
      fetchMe(stored).finally(() => setIsLoading(false));
    } else {
      setIsLoading(false);
    }
  }, [fetchMe]);

  const signIn = useCallback(async (email: string, password: string) => {
    const { data } = await apiClient.post<{ access_token: string }>(
      "/users/login",
      { email, password }
    );
    const jwt = data.access_token;
    localStorage.setItem(TOKEN_KEY, jwt);
    setToken(jwt);
    await fetchMe(jwt);
  }, [fetchMe]);

  const register = useCallback(async (email: string, password: string) => {
    const { data } = await apiClient.post<{ access_token: string }>(
      "/users/register",
      { email, password }
    );
    const jwt = data.access_token;
    localStorage.setItem(TOKEN_KEY, jwt);
    setToken(jwt);
    await fetchMe(jwt);
  }, [fetchMe]);

  const signOut = useCallback(() => {
    localStorage.removeItem(TOKEN_KEY);
    setToken(null);
    setUser(null);
  }, []);

  return (
    <AuthContext.Provider value={{ user, token, isLoading, signIn, register, signOut }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used inside AuthProvider");
  return ctx;
}
