import { NavLink } from "react-router-dom";
import { useTranslation } from "react-i18next";

export default function CustomerNav() {
  const { t } = useTranslation();
  const linkStyle = ({ isActive }: { isActive: boolean }) => ({
    padding: "8px 4px", marginRight: 20, textDecoration: "none",
    color: isActive ? "var(--freight-700)" : "var(--ink-900)",
    borderBottom: isActive ? "2px solid var(--freight-700)" : "2px solid transparent", fontWeight: 600, fontSize: "0.92rem",
  });
  return (
    <nav style={{ borderBottom: "1px solid var(--line-200)", marginBottom: 24, display: "flex", flexWrap: "wrap" }}>
      <NavLink to="/account" end style={linkStyle}>{t("customer.myShipments")}</NavLink>
      <NavLink to="/account/notifications" style={linkStyle}>{t("customer.notifications")}</NavLink>
      <NavLink to="/account/profile" style={linkStyle}>{t("customer.myProfile")}</NavLink>
    </nav>
  );
}
