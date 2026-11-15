/** Mirrors the backend's app.services.i18n.localized fallback rule: current language, then English,
 * then any value present, then empty string. Never throws on missing/malformed data. */
export function localized(field: Record<string, string> | null | undefined, lang: string): string {
  if (!field) return "";
  if (field[lang]) return field[lang];
  if (field.en) return field.en;
  const first = Object.values(field).find(Boolean);
  return first || "";
}
