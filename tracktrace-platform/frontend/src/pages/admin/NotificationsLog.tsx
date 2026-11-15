import { useEffect, useState } from "react";
import { api } from "../../lib/api";

interface NotifRow { id: string; shipment_id: string | null; channel: string; template: string; recipient: string | null; subject: string | null; status: string; error: string | null; created_at: string; sent_at: string | null; }

export default function NotificationsLog() {
  const [items, setItems] = useState<NotifRow[]>([]);
  useEffect(() => { api.get<{ items: NotifRow[] }>("/api/notifications?page_size=100").then((d) => setItems(d.items)); }, []);
  return (
    <div>
      <h1 style={{ fontSize: "1.5rem" }}>Notification delivery log</h1>
      <p style={{ color: "var(--slate-500)", fontSize: "0.9rem" }}>
        Shows what was actually sent, failed, or skipped because a channel isn't configured. Nothing here is ever marked "sent" unless a provider accepted it.
      </p>
      <div className="table-scroll">
        <table>
          <thead><tr><th>Time</th><th>Channel</th><th>Recipient</th><th>Subject / template</th><th>Status</th></tr></thead>
          <tbody>
            {items.map((n) => (
              <tr key={n.id}>
                <td className="mono">{new Date(n.created_at).toLocaleString()}</td>
                <td>{n.channel}</td>
                <td>{n.recipient || "—"}</td>
                <td>{n.subject || n.template}</td>
                <td>
                  <span className={`status-pill ${n.status === "FAILED" ? "problem" : ""}`}>{n.status}</span>
                  {n.error && <div style={{ fontSize: "0.78rem", color: "var(--slate-500)" }}>{n.error}</div>}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
