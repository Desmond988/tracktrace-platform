import { useEffect, useState } from "react";
import { api, ApiError } from "../../lib/api";

interface Customer { id: string; name: string; company: string | null; email: string | null; phone: string | null; user_id: string | null; }

export default function Customers() {
  const [items, setItems] = useState<Customer[]>([]);
  const [form, setForm] = useState({ name: "", email: "", phone: "", company: "" });
  const [editing, setEditing] = useState<Customer | null>(null);
  const [editForm, setEditForm] = useState({ name: "", company: "", email: "", phone: "" });
  const [linkEmail, setLinkEmail] = useState<Record<string, string>>({});
  const [msg, setMsg] = useState<string | null>(null);

  async function load() {
    const d = await api.get<{ items: Customer[] }>("/api/customers?page_size=100");
    setItems(d.items);
  }
  useEffect(() => { load(); }, []);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    await api.post("/api/customers", form);
    setForm({ name: "", email: "", phone: "", company: "" });
    load();
  }

  function startEdit(c: Customer) {
    setEditing(c);
    setEditForm({ name: c.name, company: c.company || "", email: c.email || "", phone: c.phone || "" });
  }

  async function saveEdit(e: React.FormEvent) {
    e.preventDefault();
    if (!editing) return;
    setMsg(null);
    try {
      await api.patch(`/api/customers/${editing.id}`, editForm);
      setEditing(null);
      await load();
    } catch (err) {
      setMsg(err instanceof ApiError ? err.message : "Could not save.");
    }
  }

  async function linkUser(c: Customer) {
    const email = linkEmail[c.id];
    if (!email) return;
    setMsg(null);
    try {
      await api.post(`/api/customers/${c.id}/link-user`, { email });
      setLinkEmail({ ...linkEmail, [c.id]: "" });
      await load();
    } catch (err) {
      setMsg(err instanceof ApiError ? err.message : "Could not link. Check the email matches an existing customer login.");
    }
  }

  return (
    <div>
      <h1 style={{ fontSize: "1.5rem" }}>Customers</h1>
      {msg && <div className="banner banner-error">{msg}</div>}
      <form onSubmit={onSubmit} style={{ display: "flex", gap: 8, flexWrap: "wrap", margin: "16px 0" }}>
        <input placeholder="Name" required value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} style={{ padding: 8, border: "1px solid var(--line-200)", borderRadius: "var(--radius-sm)" }} />
        <input placeholder="Company" value={form.company} onChange={(e) => setForm({ ...form, company: e.target.value })} style={{ padding: 8, border: "1px solid var(--line-200)", borderRadius: "var(--radius-sm)" }} />
        <input placeholder="Email" type="email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} style={{ padding: 8, border: "1px solid var(--line-200)", borderRadius: "var(--radius-sm)" }} />
        <input placeholder="Phone" value={form.phone} onChange={(e) => setForm({ ...form, phone: e.target.value })} style={{ padding: 8, border: "1px solid var(--line-200)", borderRadius: "var(--radius-sm)" }} />
        <button className="btn btn-primary" type="submit">Add customer</button>
      </form>

      {editing && (
        <form onSubmit={saveEdit} style={{ border: "1px solid var(--line-200)", borderRadius: "var(--radius-md)", padding: 16, marginBottom: 16, maxWidth: 480 }}>
          <h2 style={{ fontSize: "1rem", marginTop: 0 }}>Edit {editing.name}</h2>
          <div className="field"><label>Name</label><input value={editForm.name} onChange={(e) => setEditForm({ ...editForm, name: e.target.value })} /></div>
          <div className="field"><label>Company</label><input value={editForm.company} onChange={(e) => setEditForm({ ...editForm, company: e.target.value })} /></div>
          <div className="field"><label>Email</label><input value={editForm.email} onChange={(e) => setEditForm({ ...editForm, email: e.target.value })} /></div>
          <div className="field"><label>Phone</label><input value={editForm.phone} onChange={(e) => setEditForm({ ...editForm, phone: e.target.value })} /></div>
          <div style={{ display: "flex", gap: 10 }}>
            <button className="btn btn-primary" type="submit">Save</button>
            <button className="btn btn-secondary" type="button" onClick={() => setEditing(null)}>Cancel</button>
          </div>
        </form>
      )}

      <div className="table-scroll">
        <table>
          <thead><tr><th>Name</th><th>Company</th><th>Email</th><th>Phone</th><th>Login</th><th></th></tr></thead>
          <tbody>
            {items.map((c) => (
              <tr key={c.id}>
                <td>{c.name}</td><td>{c.company || "—"}</td><td>{c.email || "—"}</td><td>{c.phone || "—"}</td>
                <td>
                  {c.user_id ? "Linked" : (
                    <span style={{ display: "flex", gap: 6 }}>
                      <input placeholder="customer's email" value={linkEmail[c.id] || ""} onChange={(e) => setLinkEmail({ ...linkEmail, [c.id]: e.target.value })} style={{ padding: 4, width: 140, border: "1px solid var(--line-200)", borderRadius: "var(--radius-sm)" }} />
                      <button className="btn-secondary" style={{ border: "none", background: "none", color: "var(--freight-700)", cursor: "pointer" }} onClick={() => linkUser(c)}>Link</button>
                    </span>
                  )}
                </td>
                <td><button className="btn-secondary" style={{ border: "none", background: "none", color: "var(--freight-700)", cursor: "pointer" }} onClick={() => startEdit(c)}>Edit</button></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
