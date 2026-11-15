import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { Link, useParams } from "react-router-dom";
import { api } from "../../lib/api";
import { localized } from "../../lib/localized";
import ScrollReveal from "../../components/ScrollReveal";
import AnimatedCTA from "../../components/AnimatedCTA";
import NotFound from "./NotFound";
import { ServiceIcon } from "./Home";
import { genericBlurb, serviceSlug } from "./Services";

interface Service { code: string; name: Record<string, string>; }

export default function ServiceDetail() {
  const { slug } = useParams();
  const { i18n } = useTranslation();
  const [services, setServices] = useState<Service[] | null>(null);
  useEffect(() => { api.get<Service[]>("/api/services").then(setServices).catch(() => setServices([])); }, []);

  if (!services) return null;
  const service = services.find((s) => serviceSlug(s.code) === slug);
  if (!service) return <NotFound />;

  return (
    <div>
      <section style={{ padding: "48px 0", borderBottom: "1px solid var(--line-200)" }}>
        <div className="container" style={{ display: "flex", alignItems: "center", gap: 20 }}>
          <div style={{ background: "var(-- Track-100)", borderRadius: "var(--radius-md)", padding: 18 }}>
            <div style={{ transform: "scale(1.6)" }}><ServiceIcon code={service.code} /></div>
          </div>
          <div>
            <h1 style={{ fontSize: "1.8rem" }}>{localized(service.name, i18n.language)}</h1>
            <p style={{ color: "var(--slate-500)", margin: 0 }}>{genericBlurb(service.code)}</p>
          </div>
        </div>
      </section>

      <ScrollReveal className="container" style={{ padding: "40px 0", maxWidth: 680, color: "var(--slate-500)", lineHeight: 1.7 }}>
        <p>
          Specific capacity, coverage, transit times and pricing for {localized(service.name, i18n.language).toLowerCase()}{" "}
          depend on your shipment's origin, destination, and cargo details. Request a quote and our team will
          respond with what applies to your shipment.
        </p>
        <Link className="hover-underline" to="/services">← Back to all services</Link>
      </ScrollReveal>

      <AnimatedCTA
        title={`Ready to move cargo with ${localized(service.name, i18n.language)}?`}
        action={<Link className="btn btn-primary" to="/quote">Request a quote</Link>}
      />
    </div>
  );
}
