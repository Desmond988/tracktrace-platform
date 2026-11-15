import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { setLanguage } from "../i18n";
import { SUPPORTED_LANGUAGES, fetchLanguages, type LanguageMeta } from "../i18n/languages";

export default function LanguageSwitch() {
  const { i18n } = useTranslation();
  // Starts from the local list so the picker renders immediately on first paint, then swaps to
  // the backend's live list once it resolves - this is the actual, meaningful use of
  // GET /api/languages (source of truth), not just a local hardcoded array.
  const [languages, setLanguages] = useState<LanguageMeta[]>(SUPPORTED_LANGUAGES);
  useEffect(() => {
    fetchLanguages().then(setLanguages);
  }, []);

  return (
    <span style={{ display: "inline-flex", flexDirection: "column", alignItems: "flex-start", gap: 2 }}>
      <select
        value={i18n.language}
        onChange={(e) => setLanguage(e.target.value)}
        aria-label="Language / Langue / Idioma"
        title="Translations are machine-generated and have not been reviewed by a native speaker."
        style={{ border: "1px solid var(--line-200)", borderRadius: "var(--radius-sm)", padding: "4px 8px", background: "var(--paper-0)", color: "var(--ink-900)", fontSize: "0.85rem" }}
      >
        {languages.map((l) => (
          <option key={l.code} value={l.code}>{l.nativeName}</option>
        ))}
      </select>
      {i18n.language !== "en" && (
        <span style={{ fontSize: "0.68rem", color: "var(--slate-500)", lineHeight: 1.2, maxWidth: 140 }}>
          Machine-translated, not reviewed by a native speaker
        </span>
      )}
    </span>
  );
}
