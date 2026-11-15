import { useTranslation } from "react-i18next";

interface Props {
  statusLabel: string;
  location: string | null;
  description: string | null;
  timestamp: string;
}

/** Shown only when the shipment's current status is flagged is_problem by the backend - never
 * inferred from the frontend, always the real latest event. Tells the customer what happened,
 * when, and the one honest "what happens next" we can offer without inventing a specific remedy. */
export default function ExceptionBanner({ statusLabel, location, description, timestamp }: Props) {
  const { t } = useTranslation();
  return (
    <div
      role="alert"
      style={{ background: "var(--signal-100)", border: "1px solid var(--signal-500)", borderRadius: "var(--radius-md)", padding: 16, marginBottom: 20 }}
    >
      <div style={{ display: "flex", alignItems: "flex-start", gap: 10 }}>
        <svg width="20" height="20" viewBox="0 0 20 20" fill="none" style={{ flexShrink: 0, marginTop: 2, color: "var(--signal-500)" }} aria-hidden="true">
          <path d="M10 2L18 17H2L10 2z" stroke="currentColor" strokeWidth="1.6" strokeLinejoin="round" />
          <path d="M10 8v4M10 14.2v.1" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" />
        </svg>
        <div>
          <div style={{ fontWeight: 700, color: "var(--signal-500)" }}>{statusLabel}</div>
          <dl style={{ margin: "8px 0 0", fontSize: "0.9rem" }}>
            <dt style={{ fontWeight: 600, display: "inline" }}>{t("track.exceptionWhatHappened")}: </dt>
            <dd style={{ display: "inline", margin: 0 }}>{description || statusLabel}{location ? ` — ${location}` : ""}</dd>
          </dl>
          <div className="mono" style={{ fontSize: "0.78rem", color: "var(--slate-500)", marginTop: 4 }}>{new Date(timestamp).toLocaleString()}</div>
          <div style={{ marginTop: 8, fontSize: "0.9rem" }}>
            <strong>{t("track.exceptionWhatNext")}:</strong> {t("track.exceptionNextCopy")}
          </div>
        </div>
      </div>
    </div>
  );
}
