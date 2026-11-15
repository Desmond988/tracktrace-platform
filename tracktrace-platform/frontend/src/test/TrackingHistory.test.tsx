import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { describe, expect, it, vi, beforeEach } from "vitest";
import Track from "../pages/public/Track";
import { setLanguage } from "../i18n";
import "../i18n";

vi.mock("../lib/api", async () => {
  const actual = await vi.importActual<typeof import("../lib/api")>("../lib/api");
  return { ...actual, api: { get: vi.fn() } };
});
import { api } from "../lib/api";

const STATUSES = [
  { code: "SHIPMENT_CREATED", label: { en: "Shipment Created" }, is_problem: false, is_terminal: false, sort_order: 10 },
  { code: "IN_TRANSIT", label: { en: "In Transit" }, is_problem: false, is_terminal: false, sort_order: 70 },
  { code: "OUT_FOR_DELIVERY", label: { en: "Out for Delivery" }, is_problem: false, is_terminal: false, sort_order: 110 },
];
const ago = (ms: number) => new Date(Date.now() - ms).toISOString();
const ev = (code: string, label: string, location: string, description: string | null, ts: string, problem = false) => ({
  status: code, status_ref: { code, label: { en: label }, is_problem: problem }, location, description, event_timestamp: ts,
});
// Deliberately out of order in the payload: the UI must present them oldest -> newest by event time.
const THREE_EVENTS = [
  ev("OUT_FOR_DELIVERY", "Out for Delivery", "City B", "With courier", ago(3_600_000)),
  ev("SHIPMENT_CREATED", "Shipment Created", "City A", null, ago(3 * 86_400_000)),
  ev("IN_TRANSIT", "In Transit", "Hub 1", "Left origin hub", ago(2 * 86_400_000)),
];

function mockTracking(status: Record<string, unknown>, events: unknown[], extra: Record<string, unknown> = {}) {
  (api.get as ReturnType<typeof vi.fn>).mockImplementation((path: string) => {
    if (path === "/api/statuses") return Promise.resolve(STATUSES);
    return Promise.resolve({
      tracking_number: "NWT-HIST0001", origin: "City A", destination: "City B", current_location: "City B",
      created_at: ago(3 * 86_400_000), estimated_delivery: null, actual_delivery: null, pieces: 1, updated_at: ago(3_600_000),
      status, events, ...extra,
    });
  });
}
const OUT_FOR_DELIVERY = { code: "OUT_FOR_DELIVERY", label: { en: "Out for Delivery" }, is_problem: false, is_terminal: false, sort_order: 110 };
function renderTrack() {
  return render(<MemoryRouter initialEntries={["/track/NWT-HIST0001"]}><Routes><Route path="/track/:trackingNumber" element={<Track />} /></Routes></MemoryRouter>);
}
beforeEach(() => setLanguage("en"));

describe("expandable tracking history", () => {
  it("shows only a concise latest-update summary by default, with the full history collapsed", async () => {
    mockTracking(OUT_FOR_DELIVERY, THREE_EVENTS);
    renderTrack();
    const summary = await screen.findByRole("region", { name: "Latest update" });
    expect(summary).toHaveTextContent("Out for Delivery");
    expect(summary).toHaveTextContent("With courier");
    expect(screen.queryByText("Left origin hub")).not.toBeInTheDocument(); // older events are not rendered yet
    const toggle = screen.getByRole("button", { name: /view full tracking history/i });
    expect(toggle).toHaveAttribute("aria-expanded", "false");
    expect(toggle).toHaveAttribute("aria-controls", "full-tracking-history");
    expect(document.getElementById("full-tracking-history")).toHaveAttribute("hidden");
    expect(screen.queryByRole("list", { name: "Tracking history" })).not.toBeInTheDocument();
  });

  it("expands to the complete chronological timeline (oldest first) and collapses again", async () => {
    const user = userEvent.setup();
    mockTracking(OUT_FOR_DELIVERY, THREE_EVENTS);
    renderTrack();
    await user.click(await screen.findByRole("button", { name: /view full tracking history/i }));

    const list = await screen.findByRole("list", { name: "Tracking history" });
    const items = within(list).getAllByRole("listitem");
    expect(items).toHaveLength(3);
    expect(items[0]).toHaveTextContent("Shipment Created");
    expect(items[1]).toHaveTextContent("In Transit");
    expect(items[1]).toHaveTextContent("Left origin hub");
    expect(items[2]).toHaveTextContent("Out for Delivery");
    expect(items[2]).toHaveAttribute("aria-current", "step"); // the latest event is marked as the current step
    const toggle = screen.getByRole("button", { name: /hide full tracking history/i });
    expect(toggle).toHaveAttribute("aria-expanded", "true");
    expect(document.getElementById("full-tracking-history")).not.toHaveAttribute("hidden");

    await user.click(toggle);
    expect(screen.queryByRole("list", { name: "Tracking history" })).not.toBeInTheDocument();
    expect(screen.queryByText("Left origin hub")).not.toBeInTheDocument();
    expect(screen.getByRole("button", { name: /view full tracking history/i })).toHaveAttribute("aria-expanded", "false");
  });

  it("is operable with the keyboard alone (Enter expands, Space collapses)", async () => {
    const user = userEvent.setup();
    mockTracking(OUT_FOR_DELIVERY, THREE_EVENTS);
    renderTrack();
    const toggle = await screen.findByRole("button", { name: /view full tracking history/i });
    toggle.focus();
    expect(toggle).toHaveFocus();
    await user.keyboard("{Enter}");
    expect(await screen.findByRole("list", { name: "Tracking history" })).toBeInTheDocument();
    expect(toggle).toHaveFocus(); // focus is not lost when the panel opens
    await user.keyboard(" ");
    await waitFor(() => expect(screen.queryByRole("list", { name: "Tracking history" })).not.toBeInTheDocument());
    expect(toggle).toHaveFocus();
  });

  it("offers no history toggle when there is only one event (nothing more to reveal)", async () => {
    mockTracking(OUT_FOR_DELIVERY, [THREE_EVENTS[1]]);
    renderTrack();
    await screen.findByRole("region", { name: "Latest update" });
    expect(screen.queryByRole("button", { name: /full tracking history/i })).not.toBeInTheDocument();
  });

  it("renders the toggle label in the selected language", async () => {
    setLanguage("fr");
    mockTracking(OUT_FOR_DELIVERY, THREE_EVENTS);
    renderTrack();
    expect(await screen.findByRole("button", { name: /voir l'historique complet du suivi/i })).toBeInTheDocument();
    setLanguage("en");
  });
});

describe("Returned to Sender on the public tracking page", () => {
  const RETURNED = { code: "RETURNED_TO_SENDER", label: { en: "Returned to Sender", ar: "أُعيدت إلى المرسل" }, is_problem: true, is_terminal: true, sort_order: 145 };
  const returnedEvents = [
    ev("SHIPMENT_CREATED", "Shipment Created", "City A", null, ago(5 * 86_400_000)),
    ev("IN_TRANSIT", "In Transit", "Hub 1", null, ago(3 * 86_400_000)),
    { ...ev("RETURNED_TO_SENDER", "Returned to Sender", "City A", "Recipient refused delivery; returning to sender.", ago(3_600_000), true),
      status_ref: { code: "RETURNED_TO_SENDER", label: RETURNED.label, is_problem: true } },
  ];

  it("shows the correct status, an explanatory banner, no progress bar, and never claims delivery", async () => {
    const user = userEvent.setup();
    mockTracking(RETURNED, returnedEvents, { current_location: "City A", actual_delivery: null });
    renderTrack();
    expect((await screen.findAllByText("Returned to Sender")).length).toBeGreaterThan(0);
    expect(screen.getByRole("alert")).toHaveTextContent("Recipient refused delivery");
    expect(screen.queryByRole("progressbar")).not.toBeInTheDocument();
    expect(screen.queryByText("Delivered on time")).not.toBeInTheDocument();
    expect(screen.queryByText(/^Delivered/)).not.toBeInTheDocument();
    expect(screen.getByText("Estimated delivery date unavailable")).toBeInTheDocument();
    // The full history, including the return, is available on demand.
    await user.click(screen.getByRole("button", { name: /view full tracking history/i }));
    const items = within(await screen.findByRole("list", { name: "Tracking history" })).getAllByRole("listitem");
    expect(items).toHaveLength(3);
    expect(items[2]).toHaveTextContent("Returned to Sender");
  });

  it("displays the Arabic status label and RTL direction", async () => {
    setLanguage("ar");
    mockTracking(RETURNED, returnedEvents, { current_location: "City A" });
    renderTrack();
    expect((await screen.findAllByText("أُعيدت إلى المرسل")).length).toBeGreaterThan(0);
    expect(document.documentElement.dir).toBe("rtl");
    setLanguage("en");
  });
});
