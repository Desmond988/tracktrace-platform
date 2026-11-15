import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { Link } from "react-router-dom";
import { api } from "../../lib/api";
import { localized } from "../../lib/localized";
import { useSiteSettings } from "../../hooks/useSiteSettings";
import ScrollReveal from "../../components/ScrollReveal";
import AnimatedCTA from "../../components/AnimatedCTA";
import { ServiceIcon } from "./Home";

interface Service { code: string; name: Record<string, string>; }

function Placeholder({ children }: { children: React.ReactNode }) {
  return <span style={{ fontStyle: "italic", color: "var(--slate-500)" }}>{children}</span>;
}

/** A section that alternates its illustration to the left/right of its text on wide screens,
 * and stacks on narrow ones. */
function AlternatingSection({ reverse, icon, title, children, image }: { reverse?: boolean; icon: string; image?: string; title: string; children: React.ReactNode }) {
  return (
    <ScrollReveal as="section" style={{ padding: "44px 0", borderBottom: "1px solid var(--line-200)" }}>
      <div className="container" style={{ display: "grid", gridTemplateColumns: "0.7fr 1.3fr", gap: 40, alignItems: "center", direction: reverse ? "rtl" : "ltr" }}>
        <div style={{ direction: "ltr", display: "flex", alignItems: "center", justifyContent: "center", background: "var(--freight-100)", borderRadius: "var(--radius-md)", aspectRatio: "1 / 1", overflow: "hidden" }}>
          {image ? <img src={image} alt={title} style={{ width: "100%", height: "100%", objectFit: "cover", borderRadius: "16px", display: "block" }} /> : <div style={{ transform: "scale(2.2)" }}><ServiceIcon code={icon} /></div>}
        </div>
        <div style={{ direction: "ltr" }}>
          <h2 style={{ fontSize: "1.4rem" }}>{title}</h2>
          <div style={{ color: "var(--slate-500)", lineHeight: 1.7 }}>{children}</div>
        </div>
      </div>
    </ScrollReveal>
  );
}

export default function About() {
  const { i18n } = useTranslation();
  const settings = useSiteSettings();
  const name = settings["company.name"];
  const [services, setServices] = useState<Service[]>([]);
  useEffect(() => { api.get<Service[]>("/api/services").then(setServices).catch(() => setServices([])); }, []);

  return (
    <div>
      <section style={{ padding: "56px 0 40px", borderBottom: "1px solid var(--line-200)" }}>
        <div className="container" style={{ maxWidth: 720 }}>
          <h1 style={{ fontSize: "2.1rem" }}>About {name}</h1>
          <p style={{ color: "var(--slate-500)" }}>
            {name} is a freight and logistics company operating a shipment tracking and customer service
            platform. This page will grow to reflect {name}'s full story as that information is provided.
          </p>
        </div>
      </section>

      <AlternatingSection icon="FREIGHT_FORWARDING" title="Who we are" image="/images/about.jpg">
        <p>
          {name} is a freight and logistics company. This platform lets customers follow their shipments
          from booking to delivery.
        </p>
        <p>
          Company history, founding details, team size, and office locations will be provided by{" "}
          <Placeholder>{name} </Placeholder>.
        </p>
      </AlternatingSection>

      <AlternatingSection reverse icon="WAREHOUSING" title="What we do" image="/images/services.jpg">
        <p>The service categories below are available through this platform, and every shipment has its own tracking history.</p>
        <ul style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8, paddingLeft: 18 }}>
          {services.map((s) => <li key={s.code}>{localized(s.name, i18n.language)}</li>)}
        </ul>
      </AlternatingSection>

      <AlternatingSection icon="ROAD_FREIGHT" title="Our approach" image="/images/approach.jpg">
        <p>
          Every shipment gets a permanent, append-only tracking history - nothing is ever quietly overwritten,
          so both customers and staff can see exactly what happened and when.
        </p>
        <p>Specific service commitments, certifications and operating standards will be provided  and <Placeholder>confirmed by {name}</Placeholder>.</p>
      </AlternatingSection>

      <section className="container" style={{ padding: "44px 0" }}>
        <ScrollReveal><h2 style={{ fontSize: "1.4rem" }}>Why customers choose us</h2></ScrollReveal>
        <div className="stagger-grid" style={{ gridTemplateColumns: "repeat(auto-fill, minmax(220px, 1fr))", marginTop: 16 }}>
          {[
            ["A clear tracking history", "Every status and location change our team records is kept and shown to you, in your language."],
            ["Ask us directly", "Quote requests and messages go straight to our team through the forms on this site."],
            ["Document access", "Shipping and delivery documents can be shared with you in your account."],
          ].map(([title, body], i) => (
            <ScrollReveal key={title} delayMs={i * 80} className="hover-lift" style={{ padding: 18, border: "1px solid var(--line-200)", borderRadius: "var(--radius-md)", background: "var(--paper-0)" }}>
              <div style={{ fontWeight: 600, marginBottom: 6 }}>{title}</div>
              <div style={{ color: "var(--slate-500)", fontSize: "0.92rem" }}>{body}</div>
            </ScrollReveal>
          ))}
        </div>
      </section>

      <AnimatedCTA title="Have cargo to move?" body="Tell us where it needs to go and we'll get back to you." action={<Link className="btn btn-primary" to="/quote">Request a quote</Link>} />
    </div>
  );
}