import { createContext, useCallback, useContext, useEffect, useState, type ReactNode } from "react";
import { api, ApiError } from "../lib/api";

export interface Me {
  id: string;
  name: string;
  email: string;
  phone: string | null;
  role: "SUPER_ADMIN" | "ADMIN" | "OPERATIONS" | "STAFF" | "CUSTOMER";
  is_active: boolean;
  preferred_language: string;
  permissions: string[];
  customer_id?: string | null;
  notify_email?: boolean | null;
  notify_sms?: boolean | null;
  notify_whatsapp?: boolean | null;
}

interface AuthState {
  user: Me | null;
  loading: boolean;
  refresh: () => Promise<void>;
  login: (email: string, password: string) => Promise<Me>;
  logout: () => Promise<void>;
  hasPerm: (perm: string) => boolean;
  isStaff: boolean;
}

const AuthContext = createContext<AuthState | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<Me | null>(null);
  const [loading, setLoading] = useState(true);

  const refresh = useCallback(async () => {
    try {
      const me = await api.get<Me>("/api/auth/me");
      setUser(me);
    } catch {
      setUser(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  const login = useCallback(async (email: string, password: string) => {
    const me = await api.post<Me>("/api/auth/login", { email, password });
    setUser(me);
    return me;
  }, []);

  const logout = useCallback(async () => {
    try {
      await api.post("/api/auth/logout");
    } catch (e) {
      if (!(e instanceof ApiError)) throw e;
    }
    setUser(null);
  }, []);

  const hasPerm = useCallback((perm: string) => !!user?.permissions.includes(perm), [user]);
  const isStaff = !!user && user.role !== "CUSTOMER";

  return (
    <AuthContext.Provider value={{ user, loading, refresh, login, logout, hasPerm, isStaff }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthState {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
