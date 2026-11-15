import { useState, type FormEvent } from "react";
import { useTranslation } from "react-i18next";
import { api, ApiError } from "../../lib/api";
import { useSiteSettings } from "../../hooks/useSiteSettings";
import ScrollReveal from "../../components/ScrollReveal";

export default function Contact() {
  const { t } = useTranslation();
  const settings = useSiteSettings();
  const [form, setForm] = useState({ name: "", email: "", phone: "", subject: "", message: "", website: "" });
  const [done, setDone] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      await api.post("/api/contact", form);
      setDone(true);
    } catch (err) {
      setError(err instanceof ApiError ? t(`errors.${err.code}`, t("errors.UNKNOWN_ERROR")) : t("errors.UNKNOWN_ERROR"));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div>
      <section style={{ padding: "48px 0 24px", borderBottom: "1px solid var(--line-200)" }}>
        <div className="container">
          <h1 style={{ fontSize: "1.8rem" }}>{t("nav.contact")}</h1>
          <p style={{ color: "var(--slate-500)", maxWidth: 520 }}>Questions about a shipment, a quote, or anything else - we'd like to hear from you.</p>
        </div>
      </section>

      <div className="container" style={{ padding: "40px 0 64px", display: "grid", gridTemplateColumns: "1fr 1fr", gap: 48 }}>
        <ScrollReveal>
          {done ? (
            <div className="banner banner-success">{t("form.thankYouMessage")}</div>
          ) : (
            <form onSubmit={onSubmit}>
              {error && <div className="banner banner-error">{error}</div>}
              <div className="field"><label>{t("form.name")}</label><input required value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} /></div>
              <div className="field"><label>{t("form.email")}</label><input type="email" required value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} /></div>
              <div className="field"><label>{t("form.phone")}</label><input value={form.phone} onChange={(e) => setForm({ ...form, phone: e.target.value })} /></div>
              <div className="field"><label>{t("form.subject")}</label><input required value={form.subject} onChange={(e) => setForm({ ...form, subject: e.target.value })} /></div>
              <div className="field"><label>{t("form.message")}</label><textarea rows={5} required value={form.message} onChange={(e) => setForm({ ...form, message: e.target.value })} /></div>
              <input type="text" name="website" tabIndex={-1} autoComplete="off" style={{ position: "absolute", left: "-9999px" }} onChange={(e) => setForm({ ...form, website: e.target.value })} />
              <button className="btn btn-primary" type="submit" disabled={busy} style={{ width: "100%" }}>{busy ? "Sending…" : t("form.send")}</button>
            </form>
          )}
        </ScrollReveal>

        <ScrollReveal delayMs={100}>
          <div style={{ background: "var(--freight-100)", borderRadius: "var(--radius-md)", padding: 28 }}>
            <h2 style={{ fontSize: "1.1rem" }}>{settings["company.name"]}</h2>
            <dl style={{ display: "grid", gap: 14, fontSize: "0.95rem", marginTop: 16 }}>
              <div><dt style={{ color: "var(--slate-500)", fontSize: "0.8rem" }}>Address</dt><dd style={{ margin: 0 }}>{settings["company.address"]}</dd></div>
              <div><dt style={{ color: "var(--slate-500)", fontSize: "0.8rem" }}>Phone</dt><dd style={{ margin: 0 }}>{settings["company.phone"]}</dd></div>
              <div><dt style={{ color: "var(--slate-500)", fontSize: "0.8rem" }}>Email</dt><dd style={{ margin: 0 }}>{settings["company.email"]}</dd></div>
              <div><dt style={{ color: "var(--slate-500)", fontSize: "0.8rem" }}>Business hours</dt><dd style={{ margin: 0 }}>{String(settings["company.business_hours"] ?? " Available 24/7")}</dd></div>
            </dl>
          </div>
        </ScrollReveal>
      </div>
    </div>
  );
}
