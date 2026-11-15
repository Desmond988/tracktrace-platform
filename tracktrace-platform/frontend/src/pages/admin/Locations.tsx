import { useEffect, useState } from "react";
import { api, ApiError } from "../../lib/api";

interface Location { id: string; name: string; code: string | null; type: string; city: string | null; country_code: string | null; is_public: boolean; }

export default function Locations() {
  const [items, setItems] = useState<Location[]>([]);
  const [form, setForm] = useState({ name: "", code: "", type: "OFFICE", city: "", country_code: "", is_public: false });
  const [msg, setMsg] = useState<string | null>(null);

  async function load() { setItems(await api.get<Location[]>("/api/admin/locations")); }
  useEffect(() => { load(); }, []);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setMsg(null);
    try {
      await api.post("/api/admin/locations", { ...form, code: form.code || null, country_code: form.country_code ? form.country_code.toUpperCase() : null });
      setForm({ name: "", code: "", type: "OFFICE", city: "", country_code: "", is_public: false });
      await load();
      setMsg("Added.");
    } catch (err) {
      setMsg(err instanceof ApiError ? err.message : "Could not add.");
    }
  }

  return (
    <div>
      <h1 style={{ fontSize: "1.5rem" }}>Locations</h1>
      <p style={{ color: "var(--slate-500)", fontSize: "0.9rem" }}>Offices, warehouses and hubs staff can select when adding a tracking event.</p>
      <div className="table-scroll">
        <table>
          <thead><tr><th>Name</th><th>Type</th><th>City</th><th>Country</th><th>Public</th></tr></thead>
          <tbody>{items.map((l) => <tr key={l.id}><td>{l.name}</td><td>{l.type}</td><td>{l.city || "—"}</td><td>{l.country_code || "—"}</td><td>{l.is_public ? "Yes" : "No"}</td></tr>)}</tbody>
        </table>
      </div>
      <h2 style={{ fontSize: "1.1rem", marginTop: 24 }}>Add location</h2>
      {msg && <div className={`banner ${msg === "Added." ? "banner-success" : "banner-error"}`}>{msg}</div>}
      <form onSubmit={onSubmit} style={{ display: "flex", gap: 8, flexWrap: "wrap", maxWidth: 620 }}>
        <input placeholder="Name" required value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} style={{ padding: 8, border: "1px solid var(--line-200)", borderRadius: "var(--radius-sm)" }} />
        <input placeholder="Code" value={form.code} onChange={(e) => setForm({ ...form, code: e.target.value })} style={{ padding: 8, border: "1px solid var(--line-200)", borderRadius: "var(--radius-sm)", width: 90 }} />
        <select value={form.type} onChange={(e) => setForm({ ...form, type: e.target.value })} style={{ padding: 8, border: "1px solid var(--line-200)", borderRadius: "var(--radius-sm)" }}>
          <option value="OFFICE">Office</option><option value="WAREHOUSE">Warehouse</option><option value="HUB">Hub</option>
          <option value="PORT">Port</option><option value="AIRPORT">Airport</option><option value="OTHER">Other</option>
        </select>
        <input placeholder="City" value={form.city} onChange={(e) => setForm({ ...form, city: e.target.value })} style={{ padding: 8, border: "1px solid var(--line-200)", borderRadius: "var(--radius-sm)" }} />
        <input placeholder="CC" maxLength={2} value={form.country_code} onChange={(e) => setForm({ ...form, country_code: e.target.value })} style={{ padding: 8, border: "1px solid var(--line-200)", borderRadius: "var(--radius-sm)", width: 60 }} />
        <label style={{ display: "flex", gap: 6, alignItems: "center", fontSize: "0.88rem" }}>
          <input type="checkbox" checked={form.is_public} onChange={(e) => setForm({ ...form, is_public: e.target.checked })} /> Public
        </label>
        <button className="btn btn-primary" type="submit">Add</button>
      </form>
    </div>
  );
}
