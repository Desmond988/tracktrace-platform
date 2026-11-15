import { useState, type FormEvent } from "react";
import { useTranslation } from "react-i18next";
import CustomerNav from "../../components/CustomerNav";
import { useAuth } from "../../context/AuthContext";
import { api, ApiError } from "../../lib/api";
import type { Me } from "../../context/AuthContext";

export default function CustomerProfile() {
  const { t } = useTranslation();
  const { user, refresh } = useAuth();
  const [form, setForm] = useState({
    name: user?.name || "", phone: user?.phone || "",
    notify_email: user?.notify_email ?? true, notify_sms: user?.notify_sms ?? false, notify_whatsapp: user?.notify_whatsapp ?? false,
  });
  const [pw, setPw] = useState({ current_password: "", new_password: "" });
  const [msg, setMsg] = useState<{ kind: "success" | "error"; text: string } | null>(null);
  const [pwMsg, setPwMsg] = useState<{ kind: "success" | "error"; text: string } | null>(null);
  const [busy, setBusy] = useState(false);
  const [pwBusy, setPwBusy] = useState(false);

  async function saveProfile(e: FormEvent) {
    e.preventDefault();
    setBusy(true);
    setMsg(null);
    try {
      await api.patch<Me>("/api/auth/me", form);
      await refresh();
      setMsg({ kind: "success", text: t("customer.profileUpdated") });
    } catch (err) {
      setMsg({ kind: "error", text: err instanceof ApiError ? err.message : t("errors.UNKNOWN_ERROR") });
    } finally {
      setBusy(false);
    }
  }

  async function changePassword(e: FormEvent) {
    e.preventDefault();
    setPwBusy(true);
    setPwMsg(null);
    try {
      await api.post("/api/auth/change-password", pw);
      setPw({ current_password: "", new_password: "" });
      setPwMsg({ kind: "success", text: t("customer.passwordChanged") });
    } catch (err) {
      setPwMsg({ kind: "error", text: err instanceof ApiError ? err.message : t("errors.UNKNOWN_ERROR") });
    } finally {
      setPwBusy(false);
    }
  }

  return (
    <div className="container" style={{ padding: "40px 0", maxWidth: 480 }}>
      <CustomerNav />
      <h1 style={{ fontSize: "1.6rem" }}>{t("customer.accountSettings")}</h1>

      <h2 style={{ fontSize: "1.1rem" }}>{t("customer.myProfile")}</h2>
      {msg && <div className={`banner banner-${msg.kind}`}>{msg.text}</div>}
      <form onSubmit={saveProfile}>
        <div className="field"><label>{t("auth.name")}</label><input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} /></div>
        <div className="field"><label>{t("auth.phone")}</label><input value={form.phone} onChange={(e) => setForm({ ...form, phone: e.target.value })} /></div>
        <fieldset style={{ border: "1px solid var(--line-200)", borderRadius: "var(--radius-sm)", padding: 12, marginBottom: 16 }}>
          <legend style={{ fontSize: "0.85rem", fontWeight: 600, color: "var(--slate-500)" }}>{t("customer.notificationPrefs")}</legend>
          <label style={{ display: "flex", gap: 8, alignItems: "center", marginBottom: 6 }}>
            <input type="checkbox" checked={form.notify_email} onChange={(e) => setForm({ ...form, notify_email: e.target.checked })} /> {t("customer.notifyEmail")}
          </label>
          <label style={{ display: "flex", gap: 8, alignItems: "center", marginBottom: 6 }}>
            <input type="checkbox" checked={form.notify_sms} onChange={(e) => setForm({ ...form, notify_sms: e.target.checked })} /> {t("customer.notifySms")}
          </label>
          <label style={{ display: "flex", gap: 8, alignItems: "center" }}>
            <input type="checkbox" checked={form.notify_whatsapp} onChange={(e) => setForm({ ...form, notify_whatsapp: e.target.checked })} /> {t("customer.notifyWhatsapp")}
          </label>
        </fieldset>
        <button className="btn btn-primary" type="submit" disabled={busy}>{t("customer.saveChanges")}</button>
      </form>

      <h2 style={{ fontSize: "1.1rem", marginTop: 32 }}>{t("customer.changePassword")}</h2>
      {pwMsg && <div className={`banner banner-${pwMsg.kind}`}>{pwMsg.text}</div>}
      <form onSubmit={changePassword}>
        <div className="field"><label>{t("auth.currentPassword")}</label><input type="password" required autoComplete="current-password" value={pw.current_password} onChange={(e) => setPw({ ...pw, current_password: e.target.value })} /></div>
        <div className="field"><label>{t("auth.newPassword")}</label><input type="password" required autoComplete="new-password" value={pw.new_password} onChange={(e) => setPw({ ...pw, new_password: e.target.value })} /></div>
        <button className="btn btn-primary" type="submit" disabled={pwBusy}>{t("customer.changePassword")}</button>
      </form>
    </div>
  );
}
