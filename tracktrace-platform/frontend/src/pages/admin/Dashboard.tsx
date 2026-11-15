import { useEffect, useState } from "react";
import { api } from "../../lib/api";

interface DashboardData {
  total_shipments: number; active_shipments: number; in_transit: number; out_for_delivery: number;
  delivered: number; delayed: number; exceptions: number; pending_quotes: number; unread_messages: number;
}

export default function AdminDashboard() {
  const [data, setData] = useState<DashboardData | null>(null);
  useEffect(() => { api.get<DashboardData>("/api/admin/dashboard").then(setData); }, []);
  if (!data) return null;
  const cards: [string, number][] = [
    ["Total shipments", data.total_shipments], ["Active", data.active_shipments], ["In transit", data.in_transit],
    ["Out for delivery", data.out_for_delivery], ["Delivered", data.delivered], ["Delayed", data.delayed],
    ["Exceptions", data.exceptions], ["Pending quotes", data.pending_quotes], ["Unread messages", data.unread_messages],
  ];
  return (
    <div>
      <h1 style={{ fontSize: "1.5rem" }}>Dashboard</h1>
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(160px, 1fr))", gap: 12, marginTop: 20 }}>
        {cards.map(([label, value]) => (
          <div key={label} style={{ border: "1px solid var(--line-200)", borderRadius: "var(--radius-md)", padding: 16, background: "var(--paper-0)" }}>
            <div className="mono" style={{ fontSize: "1.8rem", fontWeight: 700 }}>{value}</div>
            <div style={{ color: "var(--slate-500)", fontSize: "0.85rem" }}>{label}</div>
          </div>
        ))}
      </div>
    </div>
  );
}
