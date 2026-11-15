import type { ReactNode } from "react";
import { Navigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

export function RequireAuth({ children }: { children: ReactNode }) {
  const { user, loading } = useAuth();
  if (loading) return null;
  if (!user) return <Navigate to="/login" replace />;
  return <>{children}</>;
}

export function RequireCustomer({ children }: { children: ReactNode }) {
  const { user, loading } = useAuth();
  if (loading) return null;
  if (!user) return <Navigate to="/login" replace />;
  if (user.role !== "CUSTOMER") return <Navigate to="/staff" replace />;
  return <>{children}</>;
}

export function RequireStaff({ children, perm }: { children: ReactNode; perm?: string }) {
  const { user, loading, hasPerm } = useAuth();
  if (loading) return null;
  if (!user) return <Navigate to="/login" replace />;
  if (user.role === "CUSTOMER") return <Navigate to="/account" replace />;
  if (perm && !hasPerm(perm)) return <Navigate to="/staff" replace />;
  return <>{children}</>;
}
