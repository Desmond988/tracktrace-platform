import { useEffect, useState } from "react";
import { api, ApiError } from "../../lib/api";
import { SUPPORTED_LANGUAGES } from "../../i18n/languages";

interface StatusOut { code: string; label: Record<string, string>; sort_order: number; is_terminal: boolean; is_problem: boolean; is_active: boolean; notify_customer: boolean; }

export default function Statuses() {
  const [items, setItems] = useState<StatusOut[]>([]);
  const [code, setCode] = useState("");
  const [labels, setLabels] = useState<Record<string, string>>({ en: "" });
  const [isTerminal, setIsTerminal] = useState(false);
  const [isProblem, setIsProblem] = useState(false);
  const [msg, setMsg] = useState<string | null>(null);

  async function load() { setItems(await api.get<StatusOut[]>("/api/statuses?include_inactive=true")); }
  useEffect(() => { load(); }, []);

  function setLabel(lang: string, value: string) {
    setLabels((prev) => ({ ...prev, [lang]: value }));
  }

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setMsg(null);
    const label = Object.fromEntries(Object.entries(labels).filter(([, v]) => v.trim()));
    try {
      await api.post("/api/admin/statuses", { code: code.toUpperCase().replace(/\s+/g, "_"), label, is_terminal: isTerminal, is_problem: isProblem, is_active: true, notify_customer: true, sort_order: 100 });
      setCode(""); setLabels({ en: "" }); setIsTerminal(false); setIsProblem(false);
      await load();
      setMsg("Added.");
    } catch (err) {
      setMsg(err instanceof ApiError ? err.message : "Could not add.");
    }
  }

  async function toggleActive(s: StatusOut) {
    await api.patch(`/api/admin/statuses/${s.code}`, { is_active: !s.is_active });
    load();
  }

  return (
    <div>
      <h1 style={{ fontSize: "1.5rem" }}>Shipment statuses</h1>
      <p style={{ color: "var(--slate-500)", fontSize: "0.9rem" }}>
        This admin screen is in English only. The <strong>label</strong> for each status is customer-facing and can
        be entered in any of the {SUPPORTED_LANGUAGES.length} supported languages - a language you leave blank falls
        back to English on the public site. These are your own translations; nothing here has been machine-generated
        or reviewed for you.
      </p>
      <div className="table-scroll">
        <table>
          <thead><tr><th>Code</th><th>Label (EN)</th><th>Languages entered</th><th>Terminal</th><th>Problem</th><th>Active</th><th></th></tr></thead>
          <tbody>
            {items.map((s) => (
              <tr key={s.code}>
                <td className="mono">{s.code}</td><td>{s.label.en}</td>
                <td className="mono" style={{ fontSize: "0.8rem" }}>{Object.keys(s.label).join(", ")}</td>
                <td>{s.is_terminal ? "Yes" : "No"}</td><td>{s.is_problem ? "Yes" : "No"}</td>
                <td>{s.is_active ? "Active" : "Inactive"}</td>
                <td><button className="btn-secondary" style={{ border: "none", background: "none", color: "var(-- Track-700)", cursor: "pointer" }} onClick={() => toggleActive(s)}>{s.is_active ? "Deactivate" : "Activate"}</button></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <h2 style={{ fontSize: "1.1rem", marginTop: 24 }}>Add status</h2>
      {msg && <div className={`banner ${msg === "Added." ? "banner-success" : "banner-error"}`}>{msg}</div>}
      <form onSubmit={onSubmit} style={{ maxWidth: 620 }}>
        <div className="field"><label>Code</label><input placeholder="e.g. AWAITING_PICKUP" required value={code} onChange={(e) => setCode(e.target.value)} /></div>
        <div style={{ display: "flex", gap: 16, marginBottom: 12 }}>
          <label style={{ display: "flex", gap: 6, fontSize: "0.88rem" }}><input type="checkbox" checked={isProblem} onChange={(e) => setIsProblem(e.target.checked)} /> Problem status</label>
          <label style={{ display: "flex", gap: 6, fontSize: "0.88rem" }}><input type="checkbox" checked={isTerminal} onChange={(e) => setIsTerminal(e.target.checked)} /> Terminal (no further changes expected)</label>
        </div>
        <fieldset style={{ border: "1px solid var(--line-200)", borderRadius: "var(--radius-sm)", padding: 12 }}>
          <legend style={{ fontSize: "0.85rem", fontWeight: 600, color: "var(--slate-500)" }}>Label by language (English required)</legend>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10 }}>
            {SUPPORTED_LANGUAGES.map((l) => (
              <div className="field" key={l.code} style={{ marginBottom: 0 }}>
                <label>{l.englishName} ({l.nativeName}){l.code === "en" ? " *" : ""}</label>
                <input required={l.code === "en"} value={labels[l.code] || ""} onChange={(e) => setLabel(l.code, e.target.value)} />
              </div>
            ))}
          </div>
        </fieldset>
        <button className="btn btn-primary" type="submit" style={{ marginTop: 14 }}>Add status</button>
      </form>
    </div>
  );
}
