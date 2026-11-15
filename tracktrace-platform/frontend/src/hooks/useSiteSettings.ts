import { useEffect, useState } from "react";
import { api } from "../lib/api";

export interface PublicSiteSettings {
  "company.name": string;
  "company.address": string;
  "company.phone": string;
  "company.email": string;
  [key: string]: unknown;
}

//  TracksLogistics is used as the safe default while the settings request is in flight or if
// it fails - the company name is known and confirmed; other facts stay as placeholders until a staff
// member fills them in via the admin Settings page (GET/PUT /api/admin/settings).
const DEFAULTS: PublicSiteSettings = {
  "company.name": " TracksLogistics",
  "company.address": "New York City, New York, United States",
  "company.phone": " +1 (936) 276‑8193‬",
  "company.email": " trackslogistic0@gmail.com",
};

let cached: Promise<PublicSiteSettings> | null = null;

function fetchSettings(): Promise<PublicSiteSettings> {
  if (!cached) {
    cached = api.get<PublicSiteSettings>("/api/public/settings").catch(() => DEFAULTS);
  }
  return cached;
}

/** Centrally-editable company/site info (name, address, phone, email, ...), sourced live from the
 * backend so a staff change in Settings shows up on the public site without a frontend deploy. */
export function useSiteSettings(): PublicSiteSettings {
  const [settings, setSettings] = useState<PublicSiteSettings>(DEFAULTS);
  useEffect(() => {
    fetchSettings().then((s) => {
      setSettings(s);
      if (s["company.name"]) {
        document.title = document.title.includes("|") ? `${s["company.name"]} | Track & Trace` : document.title;
      }
    });
  }, []);
  return settings;
}
