import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { useNavigate, useParams, useSearchParams } from "react-router-dom";
import { api, ApiError } from "../../lib/api";
import { localized } from "../../lib/localized";
import ExceptionBanner from "../../components/ExceptionBanner";
import DeliveryProgress from "../../components/DeliveryProgress";
import ShareTrackingButton from "../../components/ShareTrackingButton";

interface StatusOut { code: string; label: Record<string, string>; is_problem: boolean; is_terminal: boolean; sort_order: number; }
interface EventOut { status: string; status_ref: StatusOut; location: string | null; description: string | null; event_timestamp: string; }
interface PublicTracking {
  tracking_number: string; status: StatusOut; origin: string; destination: string; current_location: string | null;
  created_at: string; estimated_delivery: string | null; actual_delivery: string | null; pieces: number; updated_at: string; events: EventOut[];
}

export default function Track() {
  const { t, i18n } = useTranslation();
  const { trackingNumber: pathTn } = useParams();
  const [params] = useSearchParams();
  const navigate = useNavigate();
  const initialTn = pathTn || params.get("tn") || "";
  const [value, setValue] = useState(initialTn);
  const [result, setResult] = useState<PublicTracking | null>(null);
  const [statuses, setStatuses] = useState<StatusOut[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [historyOpen, setHistoryOpen] = useState(false);

  useEffect(() => { api.get<StatusOut[]>("/api/statuses").then(setStatuses).catch(() => setStatuses([])); }, []);

  async function lookup(tn: string) {
    if (!tn.trim()) return;
    setLoading(true);
    setError(null);
    setResult(null);
    setHistoryOpen(false);
    try {
      const data = await api.get<PublicTracking>(`/api/tracking/${encodeURIComponent(tn.trim())}`);
      setResult(data);
    } catch (e) {
      if (e instanceof ApiError) {
        setError(e.code === "TRACKING_NOT_FOUND" ? t("track.notFoundTitle") : t(`errors.${e.code}`, t("errors.UNKNOWN_ERROR")));
      } else {
        setError(t("errors.UNKNOWN_ERROR"));
      }
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    if (initialTn) lookup(initialTn);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [pathTn]);

  const label = (s: StatusOut) => localized(s.label, i18n.language);

  function trackAnother() {
    setResult(null);
    setError(null);
    setValue("");
    setHistoryOpen(false);
    navigate("/track");
  }

  function deliveryTimingNote(r: PublicTracking): string | null {
    if (r.actual_delivery && r.estimated_delivery) {
      return new Date(r.actual_delivery) <= new Date(r.estimated_delivery) ? t("track.deliveredOnTime") : t("track.deliveredLate");
    }
    if (!r.actual_delivery && r.estimated_delivery) {
      return new Date() > new Date(r.estimated_delivery) ? t("track.overdue") : t("track.onTrack");
    }
    return null; // no ETA to compare against - say nothing rather than invent one
  }

  function transitDays(r: PublicTracking): number | null {
    if (!r.actual_delivery) return null;
    const ms = new Date(r.actual_delivery).getTime() - new Date(r.created_at).getTime();
    return ms > 0 ? Math.round(ms / 86_400_000) : null;
  }

  const activeStatuses = statuses.filter((s) => !s.is_terminal && !s.is_problem).sort((a, b) => a.sort_order - b.sort_order);
  const minSort = activeStatuses[0]?.sort_order ?? 0;
  const maxSort = activeStatuses[activeStatuses.length - 1]?.sort_order ?? 1;
  const showProgress = result && !result.status.is_problem && !result.status.is_terminal && activeStatuses.length > 1;

  // Oldest -> newest: the real, append-only event order. The latest event is the last entry.
  const chronological = result
    ? [...result.events].sort((a, b) => new Date(a.event_timestamp).getTime() - new Date(b.event_timestamp).getTime())
    : [];
  const latest = chronological[chronological.length - 1];

  return (
    <div>
      <section style={{ background: "var(-- Track-800)", color: "var(--paper-0)", padding: "48px 0" }}>
        <div className="container" style={{ maxWidth: 760 }}>
          <h1 style={{ fontSize: "1.9rem", color: "var(--paper-0)" }}>{t("nav.track")}</h1>
          <p style={{ opacity: 0.85, maxWidth: 480 }}>{t("home.heroSubtitle")}</p>
          <form onSubmit={(e) => { e.preventDefault(); navigate(`/track/${encodeURIComponent(value.trim())}`); }} style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
            <input className="mono" value={value} onChange={(e) => setValue(e.target.value)} placeholder={t("home.trackPlaceholder")}
                   aria-label={t("home.trackPlaceholder")}
                   style={{ flex: 1, minWidth: 200, padding: "13px 14px", border: "1px solid transparent", borderRadius: "var(--radius-sm)", background: "var(--paper-0)", color: "var(--ink-900)" }} />
            <button className="btn btn-primary" type="submit">{t("home.trackButton")}</button>
          </form>
        </div>
      </section>

      <div className="container" style={{ padding: "36px 0 48px", maxWidth: 760 }}>
        {loading && <p style={{ color: "var(--slate-500)" }} aria-live="polite">{t("track.loading")}</p>}
        {error && <div className="banner banner-error" role="alert">{error}</div>}

        {result && (
          <div style={{ animation: "crossfade-in 0.4s ease" }}>
            {result.status.is_problem && (
              <ExceptionBanner
                statusLabel={label(result.status)}
                location={result.current_location}
                description={[...chronological].reverse().find((e) => e.status === result.status.code)?.description ?? null}
                timestamp={result.updated_at}
              />
            )}

            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", flexWrap: "wrap", gap: 8 }}>
              <span className="mono" style={{ fontSize: "1.1rem", fontWeight: 700 }}>{result.tracking_number}</span>
              <span className={`status-pill ${result.status.is_problem ? "problem" : ""}`}>{label(result.status)}</span>
            </div>

            {showProgress && (
              <DeliveryProgress currentSortOrder={result.status.sort_order} minSortOrder={minSort} maxSortOrder={maxSort} label={label(result.status)} />
            )}

            <dl style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12, margin: "20px 0", fontSize: "0.95rem" }}>
              <div><dt style={{ color: "var(--slate-500)" }}>{t("track.origin")}</dt><dd style={{ margin: 0 }}>{result.origin}</dd></div>
              <div><dt style={{ color: "var(--slate-500)" }}>{t("track.destination")}</dt><dd style={{ margin: 0 }}>{result.destination}</dd></div>
              <div><dt style={{ color: "var(--slate-500)" }}>{t("track.currentLocation")}</dt><dd style={{ margin: 0 }}>{result.current_location || "—"}</dd></div>
              <div>
                <dt style={{ color: "var(--slate-500)" }}>{result.actual_delivery ? t("track.actualDelivery") : t("track.estimatedDelivery")}</dt>
                <dd className="mono" style={{ margin: 0 }}>{fmt(result.actual_delivery || result.estimated_delivery) || t("track.etaUnavailable")}</dd>
              </div>
              <div><dt style={{ color: "var(--slate-500)" }}>{t("track.pickupDate")}</dt><dd className="mono" style={{ margin: 0 }}>{fmt(result.created_at)}</dd></div>
              {transitDays(result) !== null && (
                <div><dt style={{ color: "var(--slate-500)" }}>{t("track.transitTime")}</dt><dd className="mono" style={{ margin: 0 }}>{transitDays(result)} {t("track.days")}</dd></div>
              )}
            </dl>
            {deliveryTimingNote(result) && !result.status.is_problem && (
              <p style={{ fontSize: "0.88rem", color: "var(--slate-500)", marginTop: -8 }}>{deliveryTimingNote(result)}</p>
            )}

            {latest && (
              <section aria-labelledby="latest-update-title" style={{ border: "1px solid var(--line-200)", borderRadius: "var(--radius-md)", padding: 16, background: "var(--paper-0)" }}>
                <h2 id="latest-update-title" style={{ fontSize: "0.85rem", color: "var(--slate-500)", fontFamily: "var(--font-body)", fontWeight: 600, margin: "0 0 6px" }}>{t("track.latestUpdate")}</h2>
                <div style={{ fontWeight: 600 }}>{label(latest.status_ref)}</div>
                {latest.location && <div style={{ color: "var(--slate-500)", fontSize: "0.9rem" }}>{latest.location}</div>}
                {latest.description && <div style={{ fontSize: "0.9rem" }}>{latest.description}</div>}
                <div className="mono" style={{ fontSize: "0.8rem", color: "var(--slate-500)" }}>{fmt(latest.event_timestamp)}</div>
              </section>
            )}

            {chronological.length > 1 && (
              <>
                <button
                  type="button"
                  className="btn btn-secondary"
                  aria-expanded={historyOpen}
                  aria-controls="full-tracking-history"
                  onClick={() => setHistoryOpen((o) => !o)}
                  style={{ marginTop: 14, minHeight: 44, width: "100%", justifyContent: "space-between" }}
                >
                  <span>{historyOpen ? t("track.hideFullHistory") : t("track.viewFullHistory")} ({chronological.length})</span>
                  <svg width="16" height="16" viewBox="0 0 20 20" fill="none" aria-hidden="true" style={{ transition: "transform 0.25s ease", transform: historyOpen ? "rotate(180deg)" : "none" }}>
                    <path d="M5 8l5 5 5-5" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                  </svg>
                </button>
                <div id="full-tracking-history" hidden={!historyOpen}>
                  {historyOpen && (
                    <ol aria-label={t("track.history")} style={{ listStyle: "none", padding: 0, margin: "18px 0 0", borderLeft: "2px solid var(--line-200)" }}>
                      {chronological.map((e, i) => (
                        <li
                          key={i}
                          aria-current={i === chronological.length - 1 ? "step" : undefined}
                          style={{ paddingLeft: 18, paddingBottom: 20, position: "relative", animation: `rotate-line-in 0.45s ease ${i * 70}ms both` }}
                        >
                          <span style={{ position: "absolute", left: -6, top: 4, width: 10, height: 10, borderRadius: "50%", background: e.status_ref.is_problem ? "var(--signal-500)" : "var(-- Track-700)" }} />
                          <div style={{ fontWeight: 600 }}>{label(e.status_ref)}</div>
                          {e.location && <div style={{ color: "var(--slate-500)", fontSize: "0.9rem" }}>{e.location}</div>}
                          {e.description && <div style={{ fontSize: "0.9rem" }}>{e.description}</div>}
                          <div className="mono" style={{ fontSize: "0.8rem", color: "var(--slate-500)" }}>{fmt(e.event_timestamp)}</div>
                        </li>
                      ))}
                    </ol>
                  )}
                </div>
              </>
            )}

            <div style={{ display: "flex", gap: 10, marginTop: 24, flexWrap: "wrap" }}>
              <ShareTrackingButton trackingNumber={result.tracking_number} />
              <button className="btn btn-secondary" type="button" onClick={trackAnother}>{t("track.trackAnother")}</button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

function fmt(iso: string | null): string {
  if (!iso) return "";
  return new Date(iso).toLocaleString(undefined, { dateStyle: "medium", timeStyle: "short" });
}
