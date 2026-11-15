import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { Link, useParams } from "react-router-dom";
import { api } from "../../lib/api";
import { localized } from "../../lib/localized";
import CustomerNav from "../../components/CustomerNav";

interface StatusOut { code: string; label: Record<string, string>; is_problem: boolean; }
interface PublicEvent { status: string; status_ref: StatusOut; location: string | null; description: string | null; event_timestamp: string; }
interface Detail {
  id: string; tracking_number: string; origin: string; destination: string; current_location: string | null;
  status_ref: StatusOut; estimated_delivery: string | null; actual_delivery: string | null; pieces: number; events: PublicEvent[];
}
interface DocumentOut { id: string; filename: string; doc_type: string; created_at: string; }

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

export default function CustomerShipmentDetail() {
  const { id } = useParams();
  const { t, i18n } = useTranslation();
  const [data, setData] = useState<Detail | null>(null);
  const [docs, setDocs] = useState<DocumentOut[] | null>(null);
  const [error, setError] = useState(false);

  useEffect(() => {
    api.get<Detail>(`/api/me/shipments/${id}`).then(setData).catch(() => setError(true));
    api.get<DocumentOut[]>(`/api/me/shipments/${id}/documents`).then(setDocs).catch(() => setDocs([]));
  }, [id]);

  const label = (s: StatusOut) => localized(s.label, i18n.language);

  return (
    <div className="container" style={{ padding: "40px 0", maxWidth: 760 }}>
      <CustomerNav />
      <Link to="/account" style={{ fontSize: "0.9rem" }}>&larr; {t("customer.backToShipments")}</Link>
      {error && <div className="banner banner-error" style={{ marginTop: 16 }}>{t("track.notFoundTitle")}</div>}
      {data && (
        <>
          <h1 className="mono" style={{ fontSize: "1.4rem", marginTop: 12 }}>{data.tracking_number}</h1>
          <span className={`status-pill ${data.status_ref.is_problem ? "problem" : ""}`}>{label(data.status_ref)}</span>
          <dl style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12, margin: "20px 0", fontSize: "0.95rem" }}>
            <div><dt style={{ color: "var(--slate-500)" }}>{t("track.origin")}</dt><dd style={{ margin: 0 }}>{data.origin}</dd></div>
            <div><dt style={{ color: "var(--slate-500)" }}>{t("track.destination")}</dt><dd style={{ margin: 0 }}>{data.destination}</dd></div>
            <div><dt style={{ color: "var(--slate-500)" }}>{t("track.currentLocation")}</dt><dd style={{ margin: 0 }}>{data.current_location || "—"}</dd></div>
            <div>
              <dt style={{ color: "var(--slate-500)" }}>{data.actual_delivery ? t("track.actualDelivery") : t("track.estimatedDelivery")}</dt>
              <dd className="mono" style={{ margin: 0 }}>{fmt(data.actual_delivery || data.estimated_delivery)}</dd>
            </div>
          </dl>

          <h2 style={{ fontSize: "1.05rem" }}>{t("track.history")}</h2>
          <ol style={{ listStyle: "none", padding: 0, borderLeft: "2px solid var(--line-200)" }}>
            {[...data.events].reverse().map((e, i) => (
              <li key={i} style={{ paddingLeft: 18, paddingBottom: 18, position: "relative" }}>
                <span style={{ position: "absolute", left: -6, top: 4, width: 10, height: 10, borderRadius: "50%", background: e.status_ref.is_problem ? "var(--signal-500)" : "var(--freight-700)" }} />
                <div style={{ fontWeight: 600 }}>{label(e.status_ref)}</div>
                {e.location && <div style={{ fontSize: "0.9rem", color: "var(--slate-500)" }}>{e.location}</div>}
                {e.description && <div style={{ fontSize: "0.9rem" }}>{e.description}</div>}
                <div className="mono" style={{ fontSize: "0.8rem", color: "var(--slate-500)" }}>{fmt(e.event_timestamp)}</div>
              </li>
            ))}
          </ol>

          <h2 style={{ fontSize: "1.05rem", marginTop: 24 }}>{t("customer.documentsFor")}</h2>
          {docs && docs.length === 0 && <p style={{ color: "var(--slate-500)" }}>{t("customer.noDocuments")}</p>}
          {docs && docs.length > 0 && (
            <ul style={{ listStyle: "none", padding: 0 }}>
              {docs.map((d) => (
                <li key={d.id} style={{ padding: "8px 0", borderBottom: "1px solid var(--line-200)", display: "flex", justifyContent: "space-between" }}>
                  <span>{d.filename}</span>
                  <a href={`${API_URL}/api/documents/${d.id}/download`} target="_blank" rel="noreferrer">{t("customer.download")}</a>
                </li>
              ))}
            </ul>
          )}
        </>
      )}
    </div>
  );
}

function fmt(iso: string | null): string {
  if (!iso) return "—";
  return new Date(iso).toLocaleString(undefined, { dateStyle: "medium", timeStyle: "short" });
}
