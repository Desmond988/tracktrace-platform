import { useEffect, useState } from "react";
import { api } from "../../lib/api";

interface Msg { id: string; name: string; email: string; subject: string; message: string; status: string; created_at: string; }

export default function Messages() {
  const [items, setItems] = useState<Msg[]>([]);
  useEffect(() => { api.get<{ items: Msg[] }>("/api/messages?page_size=100").then((d) => setItems(d.items)); }, []);

  async function setStatus(id: string, status: string) {
    await api.patch(`/api/messages/${id}`, { status });
    setItems((prev) => prev.map((m) => (m.id === id ? { ...m, status } : m)));
  }

  return (
    <div>
      <h1 style={{ fontSize: "1.5rem" }}>Contact messages</h1>
      {items.map((m) => (
        <div key={m.id} style={{ border: "1px solid var(--line-200)", borderRadius: "var(--radius-md)", padding: 14, marginBottom: 10, background: "var(--paper-0)" }}>
          <div style={{ display: "flex", justifyContent: "space-between" }}>
            <strong>{m.subject}</strong>
            <select value={m.status} onChange={(e) => setStatus(m.id, e.target.value)}>
              <option value="NEW">New</option><option value="READ">Read</option><option value="REPLIED">Replied</option><option value="ARCHIVED">Archived</option>
            </select>
          </div>
          <div style={{ color: "var(--slate-500)", fontSize: "0.85rem" }}>{m.name} · {m.email}</div>
          <p style={{ margin: "8px 0 0" }}>{m.message}</p>
        </div>
      ))}
    </div>
  );
}
