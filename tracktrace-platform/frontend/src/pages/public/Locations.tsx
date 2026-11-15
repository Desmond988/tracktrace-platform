import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { api } from "../../lib/api";
import ScrollReveal from "../../components/ScrollReveal";

interface LocationOut {
  id: string; name: string; type: string; address_line: string | null;
  city: string | null; region: string | null; country_code: string | null; phone: string | null; email: string | null;
}

// Shown when the API has no locations yet
const FALLBACK_LOCATIONS: LocationOut[] = [
  {
    id: "nyc-headquarters",
    name: "New York City — Headquarters",
    type: "OFFICE",
    address_line: "350 Fifth Avenue, Suite 4100",
    city: "New York",
    region: "NY",
    country_code: "US",
    phone: "+1 (212) 555-0140",
    email: "nyc@trackslogistics.com",
  },
];

export default function Locations() {
  const { t } = useTranslation();
  const [items, setItems] = useState<LocationOut[] | null>(null);
  useEffect(() => { api.get<LocationOut[]>("/api/locations").then(setItems).catch(() => setItems([])); }, []);

  // If API returns nothing, show New York City. If API has locations, show those.
  const displayItems = items && items.length > 0 ? items : items === null ? null : FALLBACK_LOCATIONS;

  return (
    <div>
      <section style={{ padding: "48px 0 24px", borderBottom: "1px solid var(--line-200)" }}>
        <div className="container">
          <h1 style={{ fontSize: "1.8rem" }}>{t("nav.locations")}</h1>
          <p style={{ color: "var(--slate-500)", maxWidth: 520 }}>Our office and facility network.</p>
        </div>
      </section>

      <div className="container" style={{ padding: "40px 0 64px" }}>
        {displayItems === null && <p style={{ color: "var(--slate-500)" }}>Loading…</p>}
        {displayItems && displayItems.length > 0 && (
          <div className="stagger-grid" style={{ gridTemplateColumns: "repeat(auto-fill, minmax(280px, 1fr))" }}>
            {displayItems.map((loc, i) => (
              <ScrollReveal key={loc.id} delayMs={i * 60} className="hover-lift" style={{ padding: 20, border: "1px solid var(--line-200)", borderRadius: "var(--radius-md)", background: "var(--paper-0)" }}>
                <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                  <svg width="22" height="22" viewBox="0 0 24 24" fill="none" style={{ color: "var(--freight-700)" }}>
                    <path d="M12 21s7-6.5 7-12a7 7 0 10-14 0c0 5.5 7 12 7 12z" stroke="currentColor" strokeWidth="1.6" />
                    <circle cx="12" cy="9" r="2.4" stroke="currentColor" strokeWidth="1.6" />
                  </svg>
                  <div style={{ fontWeight: 600 }}>{loc.name}</div>
                </div>
                <div style={{ color: "var(--slate-500)", fontSize: "0.9rem", marginTop: 8 }}>
                  {[loc.address_line, loc.city, loc.region, loc.country_code].filter(Boolean).join(", ") || "—"}
                </div>
                <div style={{ color: "var(--slate-500)", fontSize: "0.9rem", marginTop: 4 }}>Mon – Fri: 9:00 AM – 6:00 PM</div>
                {loc.phone && <div style={{ fontSize: "0.9rem", marginTop: 8 }}>{loc.phone}</div>}
                {loc.email && <div style={{ fontSize: "0.9rem" }}>{loc.email}</div>}
              </ScrollReveal>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}