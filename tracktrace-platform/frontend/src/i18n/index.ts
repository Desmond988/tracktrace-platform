import i18n from "i18next";
import { initReactI18next } from "react-i18next";
import en from "./locales/en.json";
import fr from "./locales/fr.json";
import es from "./locales/es.json";
import de from "./locales/de.json";
import pt from "./locales/pt.json";
import it from "./locales/it.json";
import nl from "./locales/nl.json";
import pl from "./locales/pl.json";
import ru from "./locales/ru.json";
import tr from "./locales/tr.json";
import ar from "./locales/ar.json";
import zh from "./locales/zh.json";
import ja from "./locales/ja.json";
import ko from "./locales/ko.json";
import hi from "./locales/hi.json";
import sw from "./locales/sw.json";
import { LANGUAGE_CODES, isRtl } from "./languages";

const RESOURCES = { en, fr, es, de, pt, it, nl, pl, ru, tr, ar, zh, ja, ko, hi, sw };

const stored = localStorage.getItem("tnt_lang");
const initial = stored && LANGUAGE_CODES.includes(stored) ? stored : "en";

i18n.use(initReactI18next).init({
  resources: Object.fromEntries(Object.entries(RESOURCES).map(([code, translation]) => [code, { translation }])),
  lng: initial,
  fallbackLng: "en",
  interpolation: { escapeValue: false },
});

applyDocumentDirection(initial);

export function setLanguage(code: string) {
  if (!LANGUAGE_CODES.includes(code)) return;
  localStorage.setItem("tnt_lang", code);
  i18n.changeLanguage(code);
  applyDocumentDirection(code);
}

function applyDocumentDirection(code: string) {
  document.documentElement.lang = code;
  document.documentElement.dir = isRtl(code) ? "rtl" : "ltr";
}

export default i18n;
