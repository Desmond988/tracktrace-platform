import { useEffect, useState, type FormEvent } from "react";
import { useTranslation } from "react-i18next";
import { Link, useNavigate } from "react-router-dom";
import { api } from "../../lib/api";
import { localized } from "../../lib/localized";
import HeroVisual from "../../components/HeroVisual";
import RotatingTagline from "../../components/RotatingTagline";
import ScrollReveal from "../../components/ScrollReveal";
import AnimatedCTA from "../../components/AnimatedCTA";

interface Service { code: string; name: Record<string, string>; }

export default function Home() {
  const { t } = useTranslation();
  const [value, setValue] = useState("");
  const navigate = useNavigate();

  function onSubmit(e: FormEvent) {
    e.preventDefault();
    const v = value.trim();
    if (v) navigate(`/track/${encodeURIComponent(v)}`);
  }

  const taglines = [t("home.heroTitle"), t("home.tagline2"), t("home.tagline3")];

  return (
    <>
      <section style={{ padding: "56px 0 64px", borderBottom: "1px solid var(--line-200)" }}>
        <div className="container" style={{ display: "grid", gridTemplateColumns: "1.1fr 0.9fr", gap: 48, alignItems: "center" }}>
          <div style={{ maxWidth: 560 }}>
            <h1 style={{ fontSize: "2.4rem" }}><RotatingTagline phrases={taglines} /></h1>
            <p style={{ color: "var(--slate-500)", maxWidth: "var(--max-line)" }}>{t("home.heroSubtitle")}</p>
            <form onSubmit={onSubmit} style={{ display: "flex", gap: 10, marginTop: 24, flexWrap: "wrap" }}>
              <input
                className="mono"
                value={value}
                onChange={(e) => setValue(e.target.value)}
                placeholder={t("home.trackPlaceholder")}
                aria-label={t("home.trackPlaceholder")}
                style={{ flex: 1, minWidth: 200, padding: "14px 16px", fontSize: "1.05rem", border: "1px solid var(--line-200)", borderRadius: "var(--radius-sm)", background: "var(--paper-0)", color: "var(--ink-900)" }}
              />
              <button className="btn btn-primary" type="submit" style={{ padding: "14px 26px" }}>{t("home.trackButton")}</button>
            </form>
            <div style={{ display: "flex", gap: 20, marginTop: 20, fontSize: "0.92rem" }}>
              <Link className="hover-underline" to="/quote">{t("nav.quote")} →</Link>
              <Link className="hover-underline" to="/contact">{t("nav.contact")} →</Link>
            </div>
          </div>
          <ScrollReveal>
            <HeroVisual />
          </ScrollReveal>
        </div>
      </section>

      <section className="container" style={{ padding: "56px 0" }}>
        <ScrollReveal><h2 style={{ fontSize: "1.5rem" }}>{t("home.servicesTitle")}</h2></ScrollReveal>
        <ServicesShowcase />
      </section>

      <AnimatedCTA
        title={t("home.quoteCta")}
        body={t("home.quoteCtaBody")}
        action={<Link className="btn btn-primary" to="/quote">{t("nav.quote")}</Link>}
      />
    </>
  );
}

function ServicesShowcase() {
  const { t, i18n } = useTranslation();
  const [services, setServices] = useState<Service[] | null>(null);
  useEffect(() => {
    api.get<Service[]>("/api/services").then(setServices).catch(() => setServices([]));
  }, []);
  if (!services) return null;
  return (
    <div className="stagger-grid" style={{ gridTemplateColumns: "repeat(auto-fill, minmax(230px, 1fr))" }}>
      {services.map((s, i) => (
        <ScrollReveal key={s.code} delayMs={i * 70}>
          <Link
            to={`/services/${s.code.toLowerCase().replace(/_/g, "-")}`}
            className="hover-lift"
            style={{ display: "block", padding: 20, border: "1px solid var(--line-200)", borderRadius: "var(--radius-md)", background: "var(--paper-0)", textDecoration: "none", color: "var(--ink-900)", height: "100%" }}
          >
            <ServiceIcon code={s.code} />
            <div style={{ fontWeight: 600, marginTop: 12 }}>{localized(s.name, i18n.language)}</div>
            <span className="icon-hover hover-underline" style={{ fontSize: "0.85rem", color: "var(--freight-700)", marginTop: 6 }}>{t("common.learnMore")} →</span>
          </Link>
        </ScrollReveal>
      ))}
    </div>
  );
}

export function ServiceIcon({ code }: { code: string }) {
  const common = { width: 34, height: 34, viewBox: "0 0 24 24", fill: "none", stroke: "var(--freight-700)", strokeWidth: 1.6 } as const;
  if (code === "AIR_FREIGHT") return <svg {...common}><path d="M2 16l7-2 4-8 2 1-3 7 6-1 3-3 1 1-3 4-7 1-6 3z" /></svg>;
  if (code === "OCEAN_FREIGHT") return <svg {...common}><path d="M3 17c2 1 4 1 6 0s4-1 6 0 4 1 6 0M5 13h14l-2-6H7z" /></svg>;
  if (code === "ROAD_FREIGHT") return <svg {...common}><rect x="2" y="8" width="13" height="8" rx="1" /><path d="M15 11h4l3 3v2h-7z" /><circle cx="6" cy="18" r="1.6" /><circle cx="18" cy="18" r="1.6" /></svg>;
  if (code === "WAREHOUSING") return <svg {...common}><path d="M3 10l9-6 9 6v10H3z" /><path d="M9 20v-6h6v6" /></svg>;
  if (code === "FREIGHT_FORWARDING") return <svg {...common}><path d="M4 6h9v9H4zM13 10h4l3 3v2h-7z" /><circle cx="7.5" cy="18" r="1.6" /><circle cx="17" cy="18" r="1.6" /></svg>;
  return <svg {...common}><path d="M4 4h16v6H4zM4 14h10v6H4z" /></svg>;
}
