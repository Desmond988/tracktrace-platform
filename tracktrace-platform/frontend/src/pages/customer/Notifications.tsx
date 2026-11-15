import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { api } from "../../lib/api";
import CustomerNav from "../../components/CustomerNav";

interface Notif { id: string; shipment_id: string | null; subject: string | null; body: string; is_read: boolean; created_at: string; }

export default function CustomerNotifications() {
  const { t } = useTranslation();
  const [items, setItems] = useState<Notif[] | null>(null);

  async function load() {
    const data = await api.get<Notif[]>("/api/me/notifications");
    setItems(data);
  }
  useEffect(() => { load(); }, []);

  async function markRead(id: string) {
    await api.post(`/api/me/notifications/${id}/read`);
    setItems((prev) => prev && prev.map((n) => (n.id === id ? { ...n, is_read: true } : n)));
  }

  return (
    <div className="container" style={{ padding: "40px 0", maxWidth: 640 }}>
      <CustomerNav />
      <h1 style={{ fontSize: "1.6rem" }}>{t("customer.notifications")}</h1>
      {items && items.length === 0 && <p style={{ color: "var(--slate-500)" }}>{t("customer.noNotifications")}</p>}
      {items?.map((n) => (
        <div key={n.id} style={{ border: "1px solid var(--line-200)", borderRadius: "var(--radius-md)", padding: 14, marginBottom: 10, background: n.is_read ? "var(--paper-0)" : "var(-- Track-100)" }}>
          <div style={{ display: "flex", justifyContent: "space-between", gap: 12 }}>
            <strong>{n.subject || t("customer.notifications")}</strong>
            {!n.is_read && (
              <button className="btn-secondary" style={{ border: "none", background: "none", padding: 0, cursor: "pointer", color: "var(-- Track-700)", fontSize: "0.85rem" }} onClick={() => markRead(n.id)}>
                {t("customer.markRead")}
              </button>
            )}
          </div>
          <p style={{ margin: "6px 0 4px" }}>{n.body}</p>
          <div className="mono" style={{ fontSize: "0.78rem", color: "var(--slate-500)" }}>{new Date(n.created_at).toLocaleString()}</div>
        </div>
      ))}
    </div>
  );
}
