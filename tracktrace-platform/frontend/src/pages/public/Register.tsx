import { useState, type FormEvent } from "react";
import { useTranslation } from "react-i18next";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../../context/AuthContext";
import { api, ApiError } from "../../lib/api";
import type { Me } from "../../context/AuthContext";

export default function Register() {
  const { t } = useTranslation();
  const { refresh } = useAuth();
  const navigate = useNavigate();
  const [form, setForm] = useState({ name: "", email: "", phone: "", password: "" });
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      await api.post<Me>("/api/auth/register", form);
      await refresh();
      navigate("/account");
    } catch (err) {
      setError(err instanceof ApiError ? t(`errors.${err.code}`, t("errors.UNKNOWN_ERROR")) : t("errors.UNKNOWN_ERROR"));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="container" style={{ maxWidth: 420, padding: "56px 0" }}>
      <h1 style={{ fontSize: "1.6rem" }}>{t("nav.signup")}</h1>
      {error && <div className="banner banner-error" role="alert">{error}</div>}
      <form onSubmit={onSubmit}>
        <div className="field">
          <label htmlFor="name">{t("auth.name")}</label>
          <input id="name" required value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} />
        </div>
        <div className="field">
          <label htmlFor="email">{t("auth.email")}</label>
          <input id="email" type="email" required autoComplete="email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} />
        </div>
        <div className="field">
          <label htmlFor="phone">{t("auth.phone")}</label>
          <input id="phone" required value={form.phone} onChange={(e) => setForm({ ...form, phone: e.target.value })} />
        </div>
        <div className="field">
          <label htmlFor="password">{t("auth.password")}</label>
          <input id="password" type="password" required autoComplete="new-password" value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} />
        </div>
        <button className="btn btn-primary" type="submit" disabled={busy} style={{ width: "100%" }}>{t("auth.signupButton")}</button>
      </form>
      <div style={{ marginTop: 16, fontSize: "0.9rem" }}>
        <Link to="/login">{t("auth.haveAccount")}</Link>
      </div>
    </div>
  );
}
