import { useEffect, useState } from "react";
import { api } from "../../lib/api";

interface Log { id: number; user_email: string | null; action: string; entity_type: string | null; entity_id: string | null; created_at: string; }

export default function AuditLogs() {
  const [items, setItems] = useState<Log[]>([]);
  useEffect(() => { api.get<{ items: Log[] }>("/api/admin/audit-logs?page_size=100").then((d) => setItems(d.items)); }, []);
  return (
    <div>
      <h1 style={{ fontSize: "1.5rem" }}>Audit logs</h1>
      <table>
        <thead><tr><th>Time</th><th>User</th><th>Action</th><th>Entity</th></tr></thead>
        <tbody>
          {items.map((l) => (
            <tr key={l.id}>
              <td className="mono">{new Date(l.created_at).toLocaleString()}</td>
              <td>{l.user_email || "—"}</td>
              <td>{l.action}</td>
              <td>{l.entity_type ? `${l.entity_type}:${l.entity_id}` : "—"}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
