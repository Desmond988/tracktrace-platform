import { useEffect, useState } from "react";
import { api, ApiError } from "../../lib/api";
import { SUPPORTED_LANGUAGES } from "../../i18n/languages";

interface FaqItem { id: string; question: Record<string, string>; answer: Record<string, string>; }

export default function FaqAdmin() {
  const [items, setItems] = useState<FaqItem[]>([]);
  const [questions, setQuestions] = useState<Record<string, string>>({ en: "" });
  const [answers, setAnswers] = useState<Record<string, string>>({ en: "" });
  const [msg, setMsg] = useState<string | null>(null);

  async function load() { setItems(await api.get<FaqItem[]>("/api/faq")); }
  useEffect(() => { load(); }, []);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setMsg(null);
    const question = Object.fromEntries(Object.entries(questions).filter(([, v]) => v.trim()));
    const answer = Object.fromEntries(Object.entries(answers).filter(([, v]) => v.trim()));
    try {
      await api.post("/api/admin/faq", { question, answer });
      setQuestions({ en: "" }); setAnswers({ en: "" });
      await load();
      setMsg("Added.");
    } catch (err) {
      setMsg(err instanceof ApiError ? err.message : "Could not add.");
    }
  }

  return (
    <div>
      <h1 style={{ fontSize: "1.5rem" }}>FAQ</h1>
      <p style={{ color: "var(--slate-500)", fontSize: "0.9rem" }}>
        This admin screen is in English only. Published entries appear on the public FAQ page immediately, in
        whichever languages you fill in below (English is required; other languages fall back to English until
        you add them). These are your own translations - nothing here is machine-generated for you.
      </p>
      {items.map((f) => (
        <div key={f.id} style={{ borderBottom: "1px solid var(--line-200)", padding: "10px 0" }}>
          <strong>{f.question.en}</strong>
          <p style={{ color: "var(--slate-500)", margin: "4px 0 0" }}>{f.answer.en}</p>
          <div className="mono" style={{ fontSize: "0.78rem", color: "var(--slate-500)" }}>Languages: {Object.keys(f.question).join(", ")}</div>
        </div>
      ))}
      <h2 style={{ fontSize: "1.1rem", marginTop: 24 }}>Add a question</h2>
      {msg && <div className={`banner ${msg === "Added." ? "banner-success" : "banner-error"}`}>{msg}</div>}
      <form onSubmit={onSubmit} style={{ maxWidth: 620 }}>
        {SUPPORTED_LANGUAGES.map((l) => (
          <fieldset key={l.code} style={{ border: "1px solid var(--line-200)", borderRadius: "var(--radius-sm)", padding: 12, marginBottom: 10 }}>
            <legend style={{ fontSize: "0.85rem", fontWeight: 600, color: "var(--slate-500)" }}>{l.englishName} ({l.nativeName}){l.code === "en" ? " *" : ""}</legend>
            <div className="field"><label>Question</label><input required={l.code === "en"} value={questions[l.code] || ""} onChange={(e) => setQuestions({ ...questions, [l.code]: e.target.value })} /></div>
            <div className="field" style={{ marginBottom: 0 }}><label>Answer</label><textarea rows={2} required={l.code === "en"} value={answers[l.code] || ""} onChange={(e) => setAnswers({ ...answers, [l.code]: e.target.value })} /></div>
          </fieldset>
        ))}
        <button className="btn btn-primary" type="submit">Add FAQ entry</button>
      </form>
    </div>
  );
}
