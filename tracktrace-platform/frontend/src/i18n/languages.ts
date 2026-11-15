// Must match backend app.services.i18n.SUPPORTED_LANGUAGES exactly - the backend is the source of
// truth for *what's supported*; this file supplies the UI-chrome translation bundle for each one.
export interface LanguageMeta {
  code: string;
  englishName: string;
  nativeName: string;
  rtl: boolean;
}

export const SUPPORTED_LANGUAGES: LanguageMeta[] = [
  { code: "en", englishName: "English", nativeName: "English", rtl: false },
  { code: "fr", englishName: "French", nativeName: "Français", rtl: false },
  { code: "es", englishName: "Spanish", nativeName: "Español", rtl: false },
  { code: "de", englishName: "German", nativeName: "Deutsch", rtl: false },
  { code: "pt", englishName: "Portuguese", nativeName: "Português", rtl: false },
  { code: "it", englishName: "Italian", nativeName: "Italiano", rtl: false },
  { code: "nl", englishName: "Dutch", nativeName: "Nederlands", rtl: false },
  { code: "pl", englishName: "Polish", nativeName: "Polski", rtl: false },
  { code: "ru", englishName: "Russian", nativeName: "Русский", rtl: false },
  { code: "tr", englishName: "Turkish", nativeName: "Türkçe", rtl: false },
  { code: "ar", englishName: "Arabic", nativeName: "العربية", rtl: true },
  { code: "zh", englishName: "Chinese", nativeName: "中文", rtl: false },
  { code: "ja", englishName: "Japanese", nativeName: "日本語", rtl: false },
  { code: "ko", englishName: "Korean", nativeName: "한국어", rtl: false },
  { code: "hi", englishName: "Hindi", nativeName: "हिन्दी", rtl: false },
  { code: "sw", englishName: "Swahili", nativeName: "Kiswahili", rtl: false },
];

export const LANGUAGE_CODES = SUPPORTED_LANGUAGES.map((l) => l.code);

export function isRtl(code: string): boolean {
  return SUPPORTED_LANGUAGES.find((l) => l.code === code)?.rtl ?? false;
}

export function languageMeta(code: string): LanguageMeta | undefined {
  return SUPPORTED_LANGUAGES.find((l) => l.code === code);
}

let _cached: Promise<LanguageMeta[]> | null = null;

/** Fetches the authoritative language list from the backend (/api/languages), caching the result
 * for the session. Falls back to the local SUPPORTED_LANGUAGES constant above if the request fails
 * (offline, backend not yet reachable on first paint) so the language picker never comes up empty. */
export function fetchLanguages(): Promise<LanguageMeta[]> {
  if (!_cached) {
    const apiUrl = (import.meta as unknown as { env: Record<string, string | undefined> }).env.VITE_API_URL || "http://localhost:8000";
    _cached = fetch(`${apiUrl}/api/languages`)
      .then((r) => {
        if (!r.ok) throw new Error("languages fetch failed");
        return r.json();
      })
      .then((rows: { code: string; english_name: string; native_name: string; rtl: boolean }[]) =>
        rows.map((r) => ({ code: r.code, englishName: r.english_name, nativeName: r.native_name, rtl: r.rtl })))
      .catch(() => SUPPORTED_LANGUAGES);
  }
  return _cached;
}
