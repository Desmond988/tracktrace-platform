import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api, ApiError } from "../../lib/api";

interface CustomerOpt { id: string; name: string; email: string | null; }

export default function ShipmentCreate() {
  const navigate = useNavigate();
  const [customers, setCustomers] = useState<CustomerOpt[]>([]);
  const [form, setForm] = useState({ customer_id: "", origin: "", destination: "", pieces: 1, reference_number: "" });
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => { api.get<{ items: CustomerOpt[] }>("/api/customers?page_size=100").then((d) => setCustomers(d.items)); }, []);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      const s = await api.post<{ id: string }>("/api/shipments", form);
      navigate(`/staff/shipments/${s.id}`);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Something went wrong.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div style={{ maxWidth: 480 }}>
      <h1 style={{ fontSize: "1.5rem" }}>New shipment</h1>
      {error && <div className="banner banner-error">{error}</div>}
      <form onSubmit={onSubmit}>
        <div className="field">
          <label>Customer</label>
          <select required value={form.customer_id} onChange={(e) => setForm({ ...form, customer_id: e.target.value })}>
            <option value="">Select a customer...</option>
            {customers.map((c) => <option key={c.id} value={c.id}>{c.name}{c.email ? ` (${c.email})` : ""}</option>)}
          </select>
        </div>
        <div className="field"><label>Reference number</label><input value={form.reference_number} onChange={(e) => setForm({ ...form, reference_number: e.target.value })} /></div>
        <div className="field"><label>Origin</label><input required value={form.origin} onChange={(e) => setForm({ ...form, origin: e.target.value })} /></div>
        <div className="field"><label>Destination</label><input required value={form.destination} onChange={(e) => setForm({ ...form, destination: e.target.value })} /></div>
        <div className="field"><label>Pieces</label><input type="number" min={1} value={form.pieces} onChange={(e) => setForm({ ...form, pieces: Number(e.target.value) })} /></div>
        <button className="btn btn-primary" type="submit" disabled={busy} style={{ width: "100%" }}>Create shipment</button>
      </form>
    </div>
  );
}
