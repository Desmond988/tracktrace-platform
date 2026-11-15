import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { Link } from "react-router-dom";
import { api } from "../../lib/api";
import { localized } from "../../lib/localized";
import ScrollReveal from "../../components/ScrollReveal";
import AnimatedCTA from "../../components/AnimatedCTA";
import { ServiceIcon } from "./Home";

interface Service { code: string; name: Record<string, string>; }

export function serviceSlug(code: string) {
  return code.toLowerCase().replace(/_/g, "-");
}

export default function Services() {
  const { t, i18n } = useTranslation();
  const [items, setItems] = useState<Service[]>([]);
  useEffect(() => { api.get<Service[]>("/api/services").then(setItems); }, []);

  return (
    <div>
      <section style={{ padding: "48px 0 32px", borderBottom: "1px solid var(--line-200)" }}>
        <div className="container">
          <h1 style={{ fontSize: "2rem" }}>{t("home.servicesTitle")}</h1>
          <p style={{ color: "var(--slate-500)", maxWidth: 560 }}>
            The freight and logistics services available through our platform. Select one to learn more.
          </p>
        </div>
      </section>

      <div className="container" style={{ padding: "40px 0" }}>
        <div className="stagger-grid" style={{ gridTemplateColumns: "repeat(auto-fill, minmax(260px, 1fr))" }}>
          {items.map((s, i) => (
            <ScrollReveal key={s.code} delayMs={i * 70}>
              <Link
                to={`/services/${serviceSlug(s.code)}`}
                className="hover-lift"
                style={{ display: "block", height: "100%", padding: 24, border: "1px solid var(--line-200)", borderRadius: "var(--radius-md)", background: "var(--paper-0)", textDecoration: "none", color: "var(--ink-900)" }}
              >
                <ServiceIcon code={s.code} />
                <h2 style={{ fontSize: "1.1rem", marginTop: 14 }}>{localized(s.name, i18n.language)}</h2>
                <p style={{ color: "var(--slate-500)", fontSize: "0.9rem" }}>{genericBlurb(s.code)}</p>
                <span className="icon-hover hover-underline" style={{ fontSize: "0.85rem", color: "var(--freight-700)" }}>{t("common.learnMore")} →</span>
              </Link>
            </ScrollReveal>
          ))}
        </div>
      </div>

      <AnimatedCTA title="Not sure which service fits your cargo?" body="Send us the details and we'll point you in the right direction." action={<Link className="btn btn-primary" to="/quote">Request a quote</Link>} />
    </div>
  );
}

/** Generic, factual, industry-level descriptions of what each freight mode is - never a claim about
 * FreightXpress's own fleet, capacity, coverage, or performance, since none of that has been confirmed. */
export function genericBlurb(code: string): string {
  switch (code) {
    case "AIR_FREIGHT": return "Fast transport for time-sensitive or high-value cargo, moved by air.";
    case "OCEAN_FREIGHT": return "Cost-effective transport for larger cargo volumes, moved by sea.";
    case "ROAD_FREIGHT": return "Door-to-door transport by road, suited to regional and cross-border moves.";
    case "WAREHOUSING": return "Storage and handling for cargo between legs of its journey.";
    case "FREIGHT_FORWARDING": return "Coordination of multi-leg shipments across carriers and borders.";
    case "CUSTOMS_CLEARANCE": return "Handling the customs paperwork and clearance a shipment requires.";
    default: return "";
  }
}
