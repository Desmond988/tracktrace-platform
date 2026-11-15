import { useEffect, useState } from "react";
import { api, ApiError } from "../../lib/api";
import { SUPPORTED_LANGUAGES } from "../../i18n/languages";

interface LegalSummary { slug: string; title: Record<string, string>; }
interface LegalPage { slug: string; title: Record<string, string>; body: Record<string, string>; legally_reviewed: boolean; review_note?: Record<string, string> | null; }

export default function LegalAdmin() {
  const [list, setList] = useState<LegalSummary[]>([]);
  const [slug, setSlug] = useState<string | null>(null);
  const [page, setPage] = useState<LegalPage | null>(null);
  const [editLang, setEditLang] = useState("en");
  const [msg, setMsg] = useState<string | null>(null);

  useEffect(() => { api.get<LegalSummary[]>("/api/legal").then(setList); }, []);

  async function open(s: string) {
    setSlug(s);
    setMsg(null);
    setEditLang("en");
    setPage(await api.get<LegalPage>(`/api/legal/${s}`));
  }

  function setField(kind: "title" | "body", value: string) {
    if (!page) return;
    setPage({ ...page, [kind]: { ...page[kind], [editLang]: value } });
  }

  async function save(e: React.FormEvent) {
    e.preventDefault();
    if (!slug || !page) return;
    setMsg(null);
    const title = Object.fromEntries(Object.entries(page.title).filter(([, v]) => v.trim()));
    const body = Object.fromEntries(Object.entries(page.body).filter(([, v]) => v.trim()));
    try {
      const saved = await api.put<LegalPage>(`/api/admin/legal/${slug}`, { title, body, legally_reviewed: page.legally_reviewed });
      setPage(saved);
      setMsg("Saved.");
    } catch (err) {
      setMsg(err instanceof ApiError ? err.message : "Could not save. English needs a title and at least 10 characters of body text.");
    }
  }

  const languagesWithContent = page ? Object.keys(page.title) : [];

  return (
    <div style={{ display: "flex", gap: 24, flexWrap: "wrap" }}>
      <div style={{ minWidth: 200 }}>
        <h1 style={{ fontSize: "1.5rem" }}>Legal pages</h1>
        <p style={{ color: "var(--slate-500)", fontSize: "0.85rem" }}>Admin screen is English-only. Page content can be entered in any supported language.</p>
        <ul style={{ listStyle: "none", padding: 0 }}>
          {list.map((l) => (
            <li key={l.slug}>
              <button className="btn-secondary" style={{ border: "none", background: "none", padding: "6px 0", cursor: "pointer", color: slug === l.slug ? "var(--freight-700)" : "var(--ink-900)", fontWeight: slug === l.slug ? 700 : 400 }} onClick={() => open(l.slug)}>
                {l.title.en}
              </button>
            </li>
          ))}
        </ul>
      </div>
      {page && (
        <form onSubmit={save} style={{ flex: 1, minWidth: 320, maxWidth: 620 }}>
          {!page.legally_reviewed && page.review_note && <div className="banner banner-error" style={{ fontSize: "0.85rem" }}>{page.review_note.en}</div>}
          {msg && <div className={`banner ${msg === "Saved." ? "banner-success" : "banner-error"}`}>{msg}</div>}

          <div className="field">
            <label>Editing language {editLang !== "en" && !languagesWithContent.includes(editLang) && "(not yet translated - starts blank)"}</label>
            <select value={editLang} onChange={(e) => setEditLang(e.target.value)}>
              {SUPPORTED_LANGUAGES.map((l) => (
                <option key={l.code} value={l.code}>{l.englishName} ({l.nativeName}){languagesWithContent.includes(l.code) ? " ✓" : ""}</option>
              ))}
            </select>
          </div>
          <div className="field"><label>Title {editLang === "en" ? "*" : ""}</label><input value={page.title[editLang] || ""} onChange={(e) => setField("title", e.target.value)} /></div>
          <div className="field"><label>Body {editLang === "en" ? "*" : ""} — use "## Heading" lines for section headings</label><textarea rows={12} value={page.body[editLang] || ""} onChange={(e) => setField("body", e.target.value)} /></div>
          <p style={{ color: "var(--slate-500)", fontSize: "0.8rem" }}>Languages with content: {languagesWithContent.join(", ") || "none yet"}</p>
          <label style={{ display: "flex", gap: 8, alignItems: "center", marginBottom: 16 }}>
            <input type="checkbox" checked={page.legally_reviewed} onChange={(e) => setPage({ ...page, legally_reviewed: e.target.checked })} />
            This text has been reviewed and approved by our legal representative
          </label>
          <button className="btn btn-primary" type="submit">Save</button>
        </form>
      )}
    </div>
  );
}
