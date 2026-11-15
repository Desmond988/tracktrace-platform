import { useState, type FormEvent } from "react";
import { useTranslation } from "react-i18next";
import { api } from "../../lib/api";

export default function ForgotPassword() {
  const { t } = useTranslation();
  const [email, setEmail] = useState("");
  const [sent, setSent] = useState(false);
  const [busy, setBusy] = useState(false);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setBusy(true);
    try {
      await api.post("/api/auth/forgot-password", { email });
    } finally {
      setBusy(false);
      setSent(true); // always show the same generic confirmation
    }
  }

  return (
    <div className="container" style={{ maxWidth: 420, padding: "56px 0" }}>
      <h1 style={{ fontSize: "1.6rem" }}>{t("auth.forgot")}</h1>
      {sent ? (
        <div className="banner banner-success">{t("auth.resetSent")}</div>
      ) : (
        <form onSubmit={onSubmit}>
          <div className="field">
            <label htmlFor="email">{t("auth.email")}</label>
            <input id="email" type="email" required value={email} onChange={(e) => setEmail(e.target.value)} />
          </div>
          <button className="btn btn-primary" type="submit" disabled={busy} style={{ width: "100%" }}>{t("auth.forgot")}</button>
        </form>
      )}
    </div>
  );
}
