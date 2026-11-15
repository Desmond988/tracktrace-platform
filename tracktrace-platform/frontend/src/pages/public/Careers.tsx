import { useTranslation } from "react-i18next";
import { Link } from "react-router-dom";
import { useSiteSettings } from "../../hooks/useSiteSettings";
import ScrollReveal from "../../components/ScrollReveal";

/** There is no job-openings data source in this system - this page is intentionally a static
 * empty state, not a fetch to a nonexistent endpoint. When real openings exist, replace this
 * component's body with a fetched list; the page shell (hero + layout) can stay as-is. */
export default function Careers() {
  const { t } = useTranslation();
  const settings = useSiteSettings();

  return (
    <div>
      <section style={{ padding: "48px 0 24px", borderBottom: "1px solid var(--line-200)" }}>
        <div className="container">
          <h1 style={{ fontSize: "1.8rem" }}>{t("nav.careers")}</h1>
          <p style={{ color: "var(--slate-500)", maxWidth: 520 }}>Opportunities to work with {settings["company.name"]}.</p>
        </div>
      </section>

      <div className="container" style={{ padding: "40px 0 64px" }}>
        <ScrollReveal style={{ textAlign: "center", padding: "60px 20px", border: "1px dashed var(--line-200)", borderRadius: "var(--radius-md)", color: "var(--slate-500)" }}>
          <svg width="40" height="40" viewBox="0 0 24 24" fill="none" style={{ margin: "0 auto 14px", color: "var(--freight-700)" }}>
            <rect x="3" y="7" width="18" height="13" rx="2" stroke="currentColor" strokeWidth="1.6" />
            <path d="M8 7V5a2 2 0 012-2h4a2 2 0 012 2v2" stroke="currentColor" strokeWidth="1.6" />
          </svg>
          <p style={{ margin: 0, fontWeight: 600, color: "var(--ink-900)" }}>No open positions right now.</p>
          <p style={{ margin: "6px 0 0" }}>Check back later, or reach out through our <Link className="hover-underline" to="/contact">contact page</Link> if you'd like to introduce yourself.</p>
        </ScrollReveal>
      </div>
    </div>
  );
}
