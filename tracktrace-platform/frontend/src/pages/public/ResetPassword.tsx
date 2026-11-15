import { useState, type FormEvent } from "react";
import { useTranslation } from "react-i18next";
import { useNavigate, useSearchParams } from "react-router-dom";
import { api, ApiError } from "../../lib/api";

export default function ResetPassword() {
  const { t } = useTranslation();
  const [params] = useSearchParams();
  const navigate = useNavigate();
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      await api.post("/api/auth/reset-password", { token: params.get("token"), new_password: password });
      navigate("/login");
    } catch (err) {
      setError(err instanceof ApiError ? t(`errors.${err.code}`, t("errors.UNKNOWN_ERROR")) : t("errors.UNKNOWN_ERROR"));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="container" style={{ maxWidth: 420, padding: "56px 0" }}>
      <h1 style={{ fontSize: "1.6rem" }}>{t("auth.newPassword")}</h1>
      {error && <div className="banner banner-error" role="alert">{error}</div>}
      <form onSubmit={onSubmit}>
        <div className="field">
          <label htmlFor="password">{t("auth.newPassword")}</label>
          <input id="password" type="password" required value={password} onChange={(e) => setPassword(e.target.value)} />
        </div>
        <button className="btn btn-primary" type="submit" disabled={busy} style={{ width: "100%" }}>{t("auth.resetButton")}</button>
      </form>
    </div>
  );
}
