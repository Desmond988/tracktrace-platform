import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../../lib/api";

interface Row {
  id: string; tracking_number: string; customer: { name: string }; origin: string; destination: string;
  status_ref: { label: Record<string, string>; is_problem: boolean }; estimated_delivery: string | null; updated_at: string;
}

// Real, existing status codes only - no invented "Pending" bucket that doesn't correspond to an
// actual configured status (see GET /api/statuses for the authoritative list).
const QUICK_FILTERS: { label: string; status: string | null }[] = [
  { label: "All", status: null },
  { label: "In transit", status: "IN_TRANSIT" },
  { label: "Out for delivery", status: "OUT_FOR_DELIVERY" },
  { label: "Delivered", status: "DELIVERED" },
  { label: "Delayed", status: "DELAYED" },
  { label: "Exceptions", status: "EXCEPTION" },
  { label: "Failed attempt", status: "FAILED_DELIVERY_ATTEMPT" },
  { label: "Returned to sender", status: "RETURNED_TO_SENDER" },
  { label: "Cancelled", status: "CANCELLED" },
];

export default function AdminShipments() {
  const [items, setItems] = useState<Row[]>([]);
  const [total, setTotal] = useState(0);
  const [q, setQ] = useState("");
  const [status, setStatus] = useState<string | null>(null);
  const [origin, setOrigin] = useState("");
  const [destination, setDestination] = useState("");
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");

  async function load() {
    const params = new URLSearchParams();
    if (q) params.set("q", q);
    if (status) params.set("status", status);
    if (origin) params.set("origin", origin);
    if (destination) params.set("destination", destination);
    if (dateFrom) params.set("date_from", new Date(dateFrom).toISOString());
    if (dateTo) params.set("date_to", new Date(dateTo + "T23:59:59").toISOString());
    const data = await api.get<{ items: Row[]; total: number }>(`/api/shipments?${params}`);
    setItems(data.items);
    setTotal(data.total);
  }

  // eslint-disable-next-line react-hooks/exhaustive-deps
  useEffect(() => { load(); }, [status]);

  const field = { padding: "8px 10px", border: "1px solid var(--line-200)", borderRadius: "var(--radius-sm)" } as const;
  const dateLabel = { fontSize: "0.8rem", color: "var(--slate-500)", display: "flex", flexDirection: "column", gap: 2 } as const;

  return (
    <div>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <h1 style={{ fontSize: "1.5rem" }}>Shipments ({total})</h1>
        <Link className="btn btn-primary" to="/staff/shipments/create">New shipment</Link>
      </div>

      <div style={{ display: "flex", gap: 8, flexWrap: "wrap", margin: "16px 0 8px" }}>
        {QUICK_FILTERS.map((f) => (
          <button
            key={f.label}
            type="button"
            onClick={() => setStatus(f.status)}
            className={status === f.status ? "btn btn-primary" : "btn btn-secondary"}
            style={{ padding: "6px 14px", fontSize: "0.85rem" }}
          >
            {f.label}
          </button>
        ))}
      </div>

      <form onSubmit={(e) => { e.preventDefault(); load(); }} style={{ display: "flex", gap: 8, flexWrap: "wrap", marginBottom: 16, alignItems: "flex-end" }}>
        <input placeholder="Tracking #, reference, customer..." value={q} onChange={(e) => setQ(e.target.value)} style={{ ...field, minWidth: 220 }} />
        <input placeholder="Origin" value={origin} onChange={(e) => setOrigin(e.target.value)} style={{ ...field, width: 140 }} />
        <input placeholder="Destination" value={destination} onChange={(e) => setDestination(e.target.value)} style={{ ...field, width: 140 }} />
        <label style={dateLabel}>From<input type="date" value={dateFrom} onChange={(e) => setDateFrom(e.target.value)} style={field} /></label>
        <label style={dateLabel}>To<input type="date" value={dateTo} onChange={(e) => setDateTo(e.target.value)} style={field} /></label>
        <button className="btn btn-secondary" type="submit">Apply filters</button>
      </form>

      <div className="table-scroll">
        <table>
          <thead><tr><th>Tracking #</th><th>Customer</th><th>Origin</th><th>Destination</th><th>Status</th><th>ETA</th></tr></thead>
          <tbody>
            {items.map((s) => (
              <tr key={s.id}>
                <td><Link className="mono" to={`/staff/shipments/${s.id}`}>{s.tracking_number}</Link></td>
                <td>{s.customer.name}</td>
                <td>{s.origin}</td>
                <td>{s.destination}</td>
                <td><span className={`status-pill ${s.status_ref.is_problem ? "problem" : ""}`}>{s.status_ref.label.en}</span></td>
                <td className="mono">{s.estimated_delivery ? new Date(s.estimated_delivery).toLocaleDateString() : "—"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
