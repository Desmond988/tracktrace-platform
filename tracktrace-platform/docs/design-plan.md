# Design plan — Track & Trace platform

## Subject
A freight/logistics company's public site + customer portal + staff console. Audience: shippers checking
on cargo (anxious, wants certainty fast), prospects sizing up a logistics partner (wants competence and
scale), and internal staff (wants density and speed, not marketing polish).

## Color
- `--ink-900:  #14212B` - near-black navy, body text, headers
- `--paper-50: #F6F4EF` - warm off-white background (not the AI-cliché cream #F4F1EA - cooler, greyer)
- `--freight-700: #1F5C52` - deep teal-green, primary brand/action color (evokes shipping containers/ports, not SaaS blue)
- `--signal-500: #C65D2E` - burnt orange, used ONLY for status attention (delayed/exception), never decoration
- `--line-200: #D8D3C6` - hairline rule/border color
- `--slate-500: #5B6B70` - secondary text, captions

## Type
- Display/headline: "Fraunces" (serif, has real weight range, feels like a shipping manifest/ledger rather than a tech startup) at 600-700 weight
- Body/UI: "Inter" for legibility at small sizes in dense tables and forms
- Data/tracking numbers: "IBM Plex Mono" for tracking numbers and timestamps only, so they're scannable and unambiguous (never as a decorative label font)

## Layout
- Public site: broadsheet-inspired but restrained - a single strong hairline under the header, generous
  left-aligned text blocks, no card-grid homepage. Hero is the tracking input itself, oversized, because
  that's the single most common reason anyone lands on this site.
  ASCII:
  ```
  [ logo    nav nav nav nav         EN|FR ]
  ------------------------------------------
   Track your shipment
   [ NWT-XXXXXXXX................] [Track]

   quiet supporting line about services below
  ```
- Tracking result: timeline is a vertical rule with status nodes, most recent at top, dates in mono type.
- Admin console: dense data-table-first layout, sidebar nav, no marketing chrome. Left-aligned tables,
  sortable headers, filters as a thin toolbar above the table - utilitarian, not branded.
- Alignment: left-aligned throughout (freight documents/manifests are left-aligned, scannable - not centered marketing).

## Principles
1. The tracking input is the hero everywhere it can be - homepage, header, and its own page.
2. Status color (teal/orange) is reserved for shipment state, never used decoratively elsewhere - so when
   something is orange, it always means "pay attention."
3. No card-grid SaaS kit, no gradients, no glassmorphism. Flat fills, hairline borders, one accent.
4. Numbers (tracking numbers, dates, weights) always render in mono so they read as data, not prose.
5. Admin UI prioritizes information density over whitespace; public site prioritizes whitespace and calm.

## Self-review against generic defaults
- Rejected warm-cream-serif-terracotta combo (too close to the flagged Claude-tell palette) → shifted to
  cooler paper tone + teal/burnt-orange instead of terracotta.
- Rejected numbered-step markers on the homepage (no real sequence there) - kept them ONLY on the tracking
  timeline, where a sequence genuinely exists.
- Rejected ALL-CAPS tracked-out eyebrow labels above every section header - used sentence case throughout.
