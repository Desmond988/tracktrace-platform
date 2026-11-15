import { useEffect, useState } from "react";
import { api } from "../../lib/api";

interface Reports {
  shipments_by_month: { month: string; count: number }[];
  shipments_by_service: { service: string; count: number }[];
  top_destinations: { destination: string; count: number }[];
  delivered_count: number;
  avg_delivery_days: number | null;
  delivered_on_or_before_eta: { count: number; of: number };
  quotes_by_status: Record<string, number>;
}

export default function Reports() {
  const [data, setData] = useState<Reports | null>(null);
  useEffect(() => { api.get<Reports>("/api/admin/reports").then(setData); }, []);
  if (!data) return null;

  return (
    <div>
      <h1 style={{ fontSize: "1.5rem" }}>Reports</h1>
      <p style={{ color: "var(--slate-500)", fontSize: "0.9rem" }}>All figures are computed live from the database.</p>

      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(180px, 1fr))", gap: 12, margin: "16px 0" }}>
        <Card label="Delivered shipments" value={data.delivered_count} />
        <Card label="Avg. delivery time" value={data.avg_delivery_days != null ? `${data.avg_delivery_days} days` : "—"} />
        <Card label="Delivered on/before ETA" value={`${data.delivered_on_or_before_eta.count} / ${data.delivered_on_or_before_eta.of}`} />
      </div>

      <h2 style={{ fontSize: "1.1rem", marginTop: 24 }}>Shipments by month</h2>
      <div className="table-scroll">
        <table>
          <thead><tr><th>Month</th><th>Shipments</th></tr></thead>
          <tbody>{data.shipments_by_month.map((r) => <tr key={r.month}><td className="mono">{r.month}</td><td>{r.count}</td></tr>)}</tbody>
        </table>
      </div>

      <h2 style={{ fontSize: "1.1rem", marginTop: 24 }}>By service</h2>
      <div className="table-scroll">
        <table>
          <thead><tr><th>Service</th><th>Shipments</th></tr></thead>
          <tbody>{data.shipments_by_service.map((r) => <tr key={r.service}><td>{r.service}</td><td>{r.count}</td></tr>)}</tbody>
        </table>
      </div>

      <h2 style={{ fontSize: "1.1rem", marginTop: 24 }}>Top destinations</h2>
      <div className="table-scroll">
        <table>
          <thead><tr><th>Destination</th><th>Shipments</th></tr></thead>
          <tbody>{data.top_destinations.map((r) => <tr key={r.destination}><td>{r.destination}</td><td>{r.count}</td></tr>)}</tbody>
        </table>
      </div>

      <h2 style={{ fontSize: "1.1rem", marginTop: 24 }}>Quotes by status</h2>
      <div className="table-scroll">
        <table>
          <thead><tr><th>Status</th><th>Count</th></tr></thead>
          <tbody>{Object.entries(data.quotes_by_status).map(([s, c]) => <tr key={s}><td>{s}</td><td>{c}</td></tr>)}</tbody>
        </table>
      </div>
    </div>
  );
}

function Card({ label, value }: { label: string; value: string | number }) {
  return (
    <div style={{ border: "1px solid var(--line-200)", borderRadius: "var(--radius-md)", padding: 16, background: "var(--paper-0)" }}>
      <div className="mono" style={{ fontSize: "1.5rem", fontWeight: 700 }}>{value}</div>
      <div style={{ color: "var(--slate-500)", fontSize: "0.85rem" }}>{label}</div>
    </div>
  );
}
