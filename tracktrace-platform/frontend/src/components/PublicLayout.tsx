import { useEffect, useState } from "react";
import { Link, NavLink, Outlet, useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import LanguageSwitch from "./LanguageSwitch";
import MobileMenu from "./MobileMenu";
import { useAuth } from "../context/AuthContext";
import { api } from "../lib/api";
import { localized } from "../lib/localized";
import { useSiteSettings } from "../hooks/useSiteSettings";

function Brand() {
  const settings = useSiteSettings();
  const logoUrl = settings["company.logo_url"] as string | undefined;
  const name = settings["company.name"];
  return (
    <Link to="/" style={{ display: "flex", alignItems: "center", gap: 10, textDecoration: "none", color: "var(--ink-900)" }}>
      {logoUrl ? (
        <img src={logoUrl} alt={String(name)} style={{ height: 30, width: "auto" }} />
      ) : (
        <span style={{ fontFamily: "var(--font-display)", fontWeight: 700, fontSize: "1.3rem" }}>{name}</span>
      )}
    </Link>
  );
}

function NavLinks({ onNavigate }: { onNavigate?: () => void }) {
  const { t } = useTranslation();
  const { user, isStaff, logout } = useAuth();
  const navigate = useNavigate();

  async function onSignOut() {
    await logout();
    onNavigate?.();
    navigate("/");
  }

  const linkStyle = ({ isActive }: { isActive: boolean }) =>
    ({ textDecoration: "none", color: isActive ? "var(--freight-700)" : "var(--ink-900)" }) as const;

  return (
    <>
      <NavLink to="/track" className="hover-underline" style={linkStyle} onClick={onNavigate}>{t("nav.track")}</NavLink>
      <NavLink to="/services" className="hover-underline" style={linkStyle} onClick={onNavigate}>{t("nav.services")}</NavLink>
      <NavLink to="/about" className="hover-underline" style={linkStyle} onClick={onNavigate}>{t("nav.about")}</NavLink>
      <NavLink to="/quote" className="hover-underline" style={linkStyle} onClick={onNavigate}>{t("nav.quote")}</NavLink>
      <NavLink to="/contact" className="hover-underline" style={linkStyle} onClick={onNavigate}>{t("nav.contact")}</NavLink>
      {user ? (
        <>
          <NavLink to={isStaff ? "/staff" : "/account"} className="hover-underline" style={linkStyle} onClick={onNavigate}>
            {isStaff ? t("nav.admin") : t("nav.dashboard")}
          </NavLink>
          <button className="btn-secondary" style={{ border: "none", background: "none", padding: 0, cursor: "pointer", color: "var(--freight-700)", fontWeight: 600, textAlign: "left" }} onClick={onSignOut}>
            {t("nav.signout")}
          </button>
        </>
      ) : (
        <>
          <NavLink to="/login" className="hover-underline" style={linkStyle} onClick={onNavigate}>{t("nav.signin")}</NavLink>
          <NavLink to="/register" className="hover-underline" style={linkStyle} onClick={onNavigate}>{t("nav.signup")}</NavLink>
        </>
      )}
    </>
  );
}

export default function PublicLayout() {
  const { t } = useTranslation();
  const [menuOpen, setMenuOpen] = useState(false);

  return (
    <div>
      <header style={{ borderBottom: "1px solid var(--line-200)", background: "var(--paper-0)", position: "sticky", top: 0, zIndex: 30 }}>
        <div className="container site-header-inner">
          <Brand />
          <nav className="site-nav desktop-nav-links">
            <NavLinks />
            <LanguageSwitch />
          </nav>
          <button
            className="mobile-menu-toggle"
            onClick={() => setMenuOpen(true)}
            aria-label={t("nav.menu")}
            aria-haspopup="dialog"
            style={{ background: "none", border: "1px solid var(--line-200)", borderRadius: "var(--radius-sm)", padding: 8, cursor: "pointer", color: "var(--ink-900)" }}
          >
            <svg width="20" height="20" viewBox="0 0 20 20" fill="none" aria-hidden="true">
              <path d="M2 5h16M2 10h16M2 15h16" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" />
            </svg>
          </button>
        </div>
      </header>

      <MobileMenu open={menuOpen} onClose={() => setMenuOpen(false)}>
        <NavLinks onNavigate={() => setMenuOpen(false)} />
        <div style={{ marginTop: 12 }}><LanguageSwitch /></div>
      </MobileMenu>

      <main>
        <Outlet />
      </main>
      <Footer />
    </div>
  );
}

interface LegalSummary { slug: string; title: Record<string, string>; }

function Footer() {
  const { t, i18n } = useTranslation();
  const [pages, setPages] = useState<LegalSummary[]>([]);
  const settings = useSiteSettings();
  useEffect(() => { api.get<LegalSummary[]>("/api/legal").then(setPages).catch(() => setPages([])); }, []);

  const colStyle = { display: "flex", flexDirection: "column" as const, gap: 8 };
  const linkStyle = { color: "var(--slate-500)", textDecoration: "none" };

  return (
    <footer style={{ borderTop: "1px solid var(--line-200)", marginTop: 60, padding: "44px 0 28px", color: "var(--slate-500)", fontSize: "0.9rem" }}>
      <div className="container footer-grid" style={{ display: "grid", gridTemplateColumns: "1.4fr 1fr 1fr 1fr", gap: 32 }}>
        <div>
          <div style={{ fontFamily: "var(--font-display)", fontWeight: 700, fontSize: "1.15rem", color: "var(--ink-900)", marginBottom: 8 }}>
            {settings["company.name"]}
          </div>
          <div>{settings["company.address"]}</div>
          <div>{settings["company.phone"]}</div>
          <div>{settings["company.email"]}</div>
        </div>
        <div style={colStyle}>
          <div style={{ fontWeight: 600, color: "var(--ink-900)" }}>{t("footer.company")}</div>
          <Link to="/about" style={linkStyle}>{t("nav.about")}</Link>
          <Link to="/services" style={linkStyle}>{t("nav.services")}</Link>
          <Link to="/track" style={linkStyle}>{t("nav.track")}</Link>
          <Link to="/contact" style={linkStyle}>{t("nav.contact")}</Link>
          <Link to="/quote" style={linkStyle}>{t("nav.quote")}</Link>
        </div>
        <div style={colStyle}>
          <div style={{ fontWeight: 600, color: "var(--ink-900)" }}>{t("footer.resources")}</div>
          <Link to="/faq" style={linkStyle}>FAQ</Link>
          <Link to="/careers" style={linkStyle}>{t("nav.careers")}</Link>
          <Link to="/locations" style={linkStyle}>{t("nav.locations")}</Link>
        </div>
        <div style={colStyle}>
          <div style={{ fontWeight: 600, color: "var(--ink-900)" }}>{t("footer.legalPages")}</div>
          {pages.map((p) => (
            <Link key={p.slug} to={`/legal/${p.slug}`} style={linkStyle}>{localized(p.title, i18n.language)}</Link>
          ))}
        </div>
      </div>
      <div className="container" style={{ marginTop: 28, paddingTop: 18, borderTop: "1px solid var(--line-200)", fontSize: "0.8rem" }}>
        © {new Date().getFullYear()} {settings["company.name"]}
      </div>
    </footer>
  );
}
