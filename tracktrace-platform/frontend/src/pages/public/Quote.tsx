import { useEffect, useState, type FormEvent } from "react";
import { useTranslation } from "react-i18next";
import { api, ApiError } from "../../lib/api";
import { localized } from "../../lib/localized";
import ScrollReveal from "../../components/ScrollReveal";

interface Service { code: string; id: string; name: Record<string, string>; }

const INITIAL = {
  name: "", company: "", email: "", phone: "", origin: "", destination: "",
  preferred_service_id: "", cargo_type: "", weight_kg: "", dimensions: "", pieces: "", additional_info: "", website: "",
};

export default function Quote() {
  const { t, i18n } = useTranslation();
  const [form, setForm] = useState(INITIAL);
  const [services, setServices] = useState<Service[]>([]);
  const [done, setDone] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => { api.get<Service[]>("/api/services").then(setServices).catch(() => setServices([])); }, []);

  function set<K extends keyof typeof form>(k: K, v: string) {
    setForm((f) => ({ ...f, [k]: v }));
  }

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      const payload = {
        ...form,
        preferred_service_id: form.preferred_service_id || undefined,
        weight_kg: form.weight_kg ? Number(form.weight_kg) : undefined,
        pieces: form.pieces ? Number(form.pieces) : undefined,
      };
      const r = await api.post<{ reference: string }>("/api/quotes", payload);
      setDone(r.reference);
    } catch (err) {
      setError(err instanceof ApiError ? t(`errors.${err.code}`, t("errors.UNKNOWN_ERROR")) : t("errors.UNKNOWN_ERROR"));
    } finally {
      setBusy(false);
    }
  }

  if (done) {
    return (
      <div className="container" style={{ padding: "72px 0", maxWidth: 480, textAlign: "center", animation: "crossfade-in 0.4s ease" }}>
        <div style={{ width: 52, height: 52, borderRadius: "50%", background: "var(--freight-100)", display: "flex", alignItems: "center", justifyContent: "center", margin: "0 auto 16px" }}>
          <svg width="26" height="26" viewBox="0 0 20 20" fill="none"><path d="M4 10l4 4 8-9" stroke="var(--freight-700)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" /></svg>
        </div>
        <div className="banner banner-success">{t("form.thankYouQuote")} <strong className="mono">{done}</strong>.</div>
      </div>
    );
  }

  return (
    <div>
      <section style={{ padding: "48px 0 24px", borderBottom: "1px solid var(--line-200)" }}>
        <div className="container" style={{ maxWidth: 640 }}>
          <h1 style={{ fontSize: "1.8rem" }}>{t("nav.quote")}</h1>
          <p style={{ color: "var(--slate-500)" }}>Tell us about your shipment and a member of our team will follow up.</p>
        </div>
      </section>

      <div className="container" style={{ padding: "40px 0 64px", maxWidth: 640 }}>
        {error && <div className="banner banner-error">{error}</div>}
        <form onSubmit={onSubmit}>
          <ScrollReveal as="section" style={{ marginBottom: 28 }}>
            <h2 style={{ fontSize: "1.05rem", color: "var(--freight-700)" }}>1. Contact details</h2>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
              <div className="field"><label>{t("form.name")}</label><input required value={form.name} onChange={(e) => set("name", e.target.value)} /></div>
              <div className="field"><label>Company</label><input value={form.company} onChange={(e) => set("company", e.target.value)} /></div>
              <div className="field"><label>{t("form.email")}</label><input type="email" required value={form.email} onChange={(e) => set("email", e.target.value)} /></div>
              <div className="field"><label>{t("form.phone")}</label><input value={form.phone} onChange={(e) => set("phone", e.target.value)} /></div>
            </div>
          </ScrollReveal>

          <ScrollReveal as="section" delayMs={60} style={{ marginBottom: 28 }}>
            <h2 style={{ fontSize: "1.05rem", color: "var(--freight-700)" }}>2. Shipment route</h2>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
              <div className="field"><label>{t("form.origin")}</label><input required value={form.origin} onChange={(e) => set("origin", e.target.value)} /></div>
              <div className="field"><label>{t("form.destination")}</label><input required value={form.destination} onChange={(e) => set("destination", e.target.value)} /></div>
              <div className="field" style={{ gridColumn: "1 / -1" }}>
                <label>Service</label>
                <select value={form.preferred_service_id} onChange={(e) => set("preferred_service_id", e.target.value)}>
                  <option value="">Not sure yet</option>
                  {services.map((s) => <option key={s.id} value={s.id}>{localized(s.name, i18n.language)}</option>)}
                </select>
              </div>
            </div>
          </ScrollReveal>

          <ScrollReveal as="section" delayMs={120} style={{ marginBottom: 28 }}>
            <h2 style={{ fontSize: "1.05rem", color: "var(--freight-700)" }}>3. Cargo details</h2>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 16 }}>
              <div className="field" style={{ gridColumn: "1 / -1" }}><label>Cargo type</label><input value={form.cargo_type} onChange={(e) => set("cargo_type", e.target.value)} /></div>
              <div className="field"><label>Weight (kg)</label><input type="number" min="0" value={form.weight_kg} onChange={(e) => set("weight_kg", e.target.value)} /></div>
              <div className="field"><label>Dimensions</label><input placeholder="L x W x H cm" value={form.dimensions} onChange={(e) => set("dimensions", e.target.value)} /></div>
              <div className="field"><label>Pieces</label><input type="number" min="1" value={form.pieces} onChange={(e) => set("pieces", e.target.value)} /></div>
            </div>
          </ScrollReveal>

          <ScrollReveal as="section" delayMs={180} style={{ marginBottom: 24 }}>
            <h2 style={{ fontSize: "1.05rem", color: "var(--freight-700)" }}>4. Anything else?</h2>
            <div className="field" style={{ marginBottom: 0 }}><textarea rows={4} placeholder={t("form.additionalInfo")} value={form.additional_info} onChange={(e) => set("additional_info", e.target.value)} /></div>
          </ScrollReveal>

          {/* honeypot, hidden from real users */}
          <input type="text" name="website" tabIndex={-1} autoComplete="off" style={{ position: "absolute", left: "-9999px" }} onChange={(e) => set("website", e.target.value)} />
          <button className="btn btn-primary" type="submit" disabled={busy} style={{ width: "100%" }}>{busy ? "Sending…" : t("form.sendRequest")}</button>
        </form>
      </div>
    </div>
  );
}
