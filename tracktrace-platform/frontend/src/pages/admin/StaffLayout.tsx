import { Link, Outlet, useNavigate } from "react-router-dom";
import { useAuth } from "../../context/AuthContext";
import { useSiteSettings } from "../../hooks/useSiteSettings";

const NAV = [
  { to: "/staff", label: "Dashboard", perm: "shipments:read" },
  { to: "/staff/shipments", label: "Shipments", perm: "shipments:read" },
  { to: "/staff/customers", label: "Customers", perm: "customers:read" },
  { to: "/staff/quotes", label: "Quotes", perm: "quotes:manage" },
  { to: "/staff/messages", label: "Messages", perm: "messages:manage" },
  { to: "/staff/notifications", label: "Notifications", perm: "notifications:read" },
  { to: "/staff/reports", label: "Reports", perm: "reports:read" },
  { to: "/staff/users", label: "Users", perm: "users:read" },
  { to: "/staff/statuses", label: "Statuses", perm: "statuses:manage" },
  { to: "/staff/locations", label: "Locations", perm: "locations:manage" },
  { to: "/staff/legal", label: "Legal pages", perm: "legal:write" },
  { to: "/staff/faq", label: "FAQ", perm: "faq:write" },
  { to: "/staff/audit-logs", label: "Audit logs", perm: "audit:read" },
  { to: "/staff/settings", label: "Settings", perm: "settings:read" },
];

export default function StaffLayout() {
  const { user, hasPerm, logout } = useAuth();
  const navigate = useNavigate();
  const settings = useSiteSettings();
  return (
    <div className="staff-shell">
      <aside className="staff-sidebar">
        <div style={{ padding: "0 20px 20px", fontWeight: 700, fontFamily: "var(--font-display)" }}>{settings["company.name"]}</div>
        <nav style={{ display: "flex", flexDirection: "column" }}>
          {NAV.filter((n) => hasPerm(n.perm)).map((n) => (
            <Link key={n.to} to={n.to} style={{ padding: "9px 20px", color: "var(--ink-900)", textDecoration: "none", fontSize: "0.92rem" }}>{n.label}</Link>
          ))}
        </nav>
        <div style={{ padding: "20px", marginTop: 20, borderTop: "1px solid var(--line-200)", fontSize: "0.85rem", color: "var(--slate-500)" }}>
          {user?.name} · {user?.role}
          <div style={{ marginTop: 8, display: "flex", gap: 10 }}>
            <button className="btn-secondary" style={{ border: "none", background: "none", padding: 0, cursor: "pointer", color: "var(--freight-700)" }}
                    onClick={async () => { await logout(); navigate("/login"); }}>Sign out</button>
          </div>
        </div>
      </aside>
      <main className="staff-main">
        <Outlet />
      </main>
    </div>
  );
}
