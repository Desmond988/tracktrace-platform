import { useState, type FormEvent } from "react";
import { useTranslation } from "react-i18next";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../../context/AuthContext";
import { ApiError } from "../../lib/api";

export default function Login() {
  const { t } = useTranslation();
  const { login } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      const me = await login(email, password);
      navigate(me.role === "CUSTOMER" ? "/account" : "/staff");
    } catch (err) {
      setError(err instanceof ApiError ? t(`errors.${err.code}`, t("errors.UNKNOWN_ERROR")) : t("errors.UNKNOWN_ERROR"));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="container" style={{ maxWidth: 420, padding: "56px 0" }}>
      <h1 style={{ fontSize: "1.6rem" }}>{t("auth.signin")}</h1>
      {error && <div className="banner banner-error" role="alert">{error}</div>}
      <form onSubmit={onSubmit}>
        <div className="field">
          <label htmlFor="email">{t("auth.email")}</label>
          <input id="email" type="email" required autoComplete="email" value={email} onChange={(e) => setEmail(e.target.value)} />
        </div>
        <div className="field">
          <label htmlFor="password">{t("auth.password")}</label>
          <input id="password" type="password" required autoComplete="current-password" value={password} onChange={(e) => setPassword(e.target.value)} />
        </div>
        <button className="btn btn-primary" type="submit" disabled={busy} style={{ width: "100%" }}>{t("auth.signinButton")}</button>
      </form>
      <div style={{ marginTop: 16, display: "flex", justifyContent: "space-between", fontSize: "0.9rem" }}>
        <Link to="/forgot-password">{t("auth.forgot")}</Link>
        <Link to="/register">{t("auth.noAccount")}</Link>
      </div>
    </div>
  );
}
