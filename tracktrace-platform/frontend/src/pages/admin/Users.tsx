import { useEffect, useState } from "react";
import { api } from "../../lib/api";

interface UserRow { id: string; name: string; email: string; role: string; is_active: boolean; }

export default function Users() {
  const [items, setItems] = useState<UserRow[]>([]);
  const [form, setForm] = useState({ name: "", email: "", password: "", role: "STAFF" });
  const [error, setError] = useState<string | null>(null);

  async function load() {
    const d = await api.get<{ items: UserRow[] }>("/api/users?page_size=100");
    setItems(d.items);
  }
  useEffect(() => { load(); }, []);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    try {
      await api.post("/api/users", form);
      setForm({ name: "", email: "", password: "", role: "STAFF" });
      load();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed");
    }
  }

  async function toggleActive(u: UserRow) {
    setError(null);
    try {
      await api.patch(`/api/users/${u.id}`, { is_active: !u.is_active });
      load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed");
    }
  }

  async function deleteUser(u: UserRow) {
    if (!window.confirm(`Delete ${u.name}? This cannot be undone.`)) return;
    setError(null);
    try {
      await api.del(`/api/users/${u.id}`);
      load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed");
    }
  }

  return (
    <div>
      <h1 style={{ fontSize: "1.5rem" }}>Users</h1>
      {error && <div className="banner banner-error">{error}</div>}
      <form onSubmit={onSubmit} style={{ display: "flex", gap: 8, flexWrap: "wrap", margin: "16px 0" }}>
        <input placeholder="Name" required value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} style={{ padding: 8, border: "1px solid var(--line-200)", borderRadius: "var(--radius-sm)" }} />
        <input placeholder="Email" type="email" required value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} style={{ padding: 8, border: "1px solid var(--line-200)", borderRadius: "var(--radius-sm)" }} />
        <input placeholder="Temporary password" required value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} style={{ padding: 8, border: "1px solid var(--line-200)", borderRadius: "var(--radius-sm)" }} />
        <select value={form.role} onChange={(e) => setForm({ ...form, role: e.target.value })} style={{ padding: 8, border: "1px solid var(--line-200)", borderRadius: "var(--radius-sm)" }}>
          <option value="STAFF">Staff</option>
          <option value="OPERATIONS">Operations</option>
          <option value="ADMIN">Admin</option>
          <option value="SUPER_ADMIN">Super admin</option>
        </select>
        <button className="btn btn-primary" type="submit">Add user</button>
      </form>
      <table>
        <thead><tr><th>Name</th><th>Email</th><th>Role</th><th>Status</th><th></th></tr></thead>
        <tbody>
          {items.map((u) => (
            <tr key={u.id}>
              <td>{u.name}</td><td>{u.email}</td><td>{u.role}</td>
              <td>{u.is_active ? "Active" : "Inactive"}</td>
              <td style={{ display: "flex", gap: 10 }}>
                <button className="btn-secondary" style={{ border: "none", background: "none", color: "var(--freight-700)", cursor: "pointer" }} onClick={() => toggleActive(u)}>{u.is_active ? "Deactivate" : "Activate"}</button>
                <button className="btn-secondary" style={{ border: "none", background: "none", color: "var(--danger-600)", cursor: "pointer" }} onClick={() => deleteUser(u)}>Delete</button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
