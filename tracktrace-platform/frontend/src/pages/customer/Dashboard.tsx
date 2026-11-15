import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { Link } from "react-router-dom";
import { api } from "../../lib/api";
import { localized } from "../../lib/localized";
import CustomerNav from "../../components/CustomerNav";

interface ShipmentListItem {
  id: string; tracking_number: string; origin: string; destination: string;
  status_ref: { code: string; label: Record<string, string>; is_problem: boolean };
  estimated_delivery: string | null; updated_at: string;
}

export default function CustomerDashboard() {
  const { t, i18n } = useTranslation();
  const [items, setItems] = useState<ShipmentListItem[] | null>(null);

  useEffect(() => {
    api.get<{ items: ShipmentListItem[] }>("/api/me/shipments").then((d) => setItems(d.items)).catch(() => setItems([]));
  }, []);

  return (
    <div className="container" style={{ padding: "40px 0" }}>
      <CustomerNav />
      <h1 style={{ fontSize: "1.6rem" }}>{t("customer.myShipments")}</h1>
      {items && items.length === 0 && <p style={{ color: "var(--slate-500)" }}>{t("customer.noShipments")}</p>}
      {items && items.length > 0 && (
        <div className="table-scroll">
          <table>
            <thead>
              <tr><th>Tracking #</th><th>Origin</th><th>Destination</th><th>Status</th><th>ETA</th></tr>
            </thead>
            <tbody>
              {items.map((s) => (
                <tr key={s.id}>
                  <td><Link to={`/account/shipments/${s.id}`} className="mono">{s.tracking_number}</Link></td>
                  <td>{s.origin}</td>
                  <td>{s.destination}</td>
                  <td><span className={`status-pill ${s.status_ref.is_problem ? "problem" : ""}`}>{localized(s.status_ref.label, i18n.language)}</span></td>
                  <td className="mono">{s.estimated_delivery ? new Date(s.estimated_delivery).toLocaleDateString() : "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
