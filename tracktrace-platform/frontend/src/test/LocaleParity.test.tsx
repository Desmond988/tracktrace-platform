import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";
import Home from "../pages/public/Home";
import { setLanguage } from "../i18n";
import { LANGUAGE_CODES } from "../i18n/languages";

vi.mock("../lib/api", () => ({ api: { get: vi.fn().mockResolvedValue([]) } }));

const files = import.meta.glob("../i18n/locales/*.json", { eager: true }) as Record<string, { default: Record<string, Record<string, string>> }>;
const byCode = Object.fromEntries(Object.entries(files).map(([path, mod]) => [path.match(/([a-z]+)\.json$/)![1], mod.default]));
const flatten = (o: Record<string, Record<string, string>>) => Object.entries(o).flatMap(([s, keys]) => Object.keys(keys).map((k) => `${s}.${k}`)).sort();

describe("16-language locale files", () => {
  it("there is exactly one locale file per supported language", () => {
    expect(Object.keys(byCode).sort()).toEqual([...LANGUAGE_CODES].sort());
    expect(LANGUAGE_CODES).toHaveLength(16);
  });

  it.each(LANGUAGE_CODES)("%s has exactly the same keys as English, none empty", (code) => {
    expect(flatten(byCode[code])).toEqual(flatten(byCode.en));
    for (const [section, keys] of Object.entries(byCode[code])) {
      for (const [k, v] of Object.entries(keys)) expect(v, `${code}:${section}.${k}`).toBeTruthy();
    }
  });

  it("the home hero headline visibly changes with the selected language", () => {
    setLanguage("es");
    const { unmount } = render(<MemoryRouter><Home /></MemoryRouter>);
    expect(screen.getByRole("heading", { level: 1 })).toHaveTextContent("Rastree su envío");
    unmount();
    setLanguage("de");
    render(<MemoryRouter><Home /></MemoryRouter>);
    expect(screen.getByRole("heading", { level: 1 })).toHaveTextContent("Verfolgen Sie Ihre Sendung");
    setLanguage("en");
  });
});
