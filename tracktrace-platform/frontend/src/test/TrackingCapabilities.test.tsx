import { render, screen, waitFor } from "@testing-library/react";
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
  { code: "DELIVERED", label: { en: "Delivered" }, is_problem: false, is_terminal: true, sort_order: 120 },
  { code: "DELAYED", label: { en: "Delayed" }, is_problem: true, is_terminal: false, sort_order: 130 },
];

function mockTracking(overrides: Record<string, unknown>) {
  (api.get as ReturnType<typeof vi.fn>).mockImplementation((path: string) => {
    if (path === "/api/statuses") return Promise.resolve(STATUSES);
    return Promise.resolve({
      tracking_number: "NWT-CAP00001", origin: "Origin City", destination: "Dest City", current_location: "Somewhere",
      created_at: new Date(Date.now() - 86_400_000 * 2).toISOString(), pieces: 1, updated_at: new Date().toISOString(), events: [],
      status: { code: "IN_TRANSIT", label: { en: "In Transit" }, is_problem: false, is_terminal: false, sort_order: 70 },
      estimated_delivery: null, actual_delivery: null, ...overrides,
    });
  });
}

function renderTrack() {
  return render(
    <MemoryRouter initialEntries={["/track/NWT-CAP00001"]}>
      <Routes><Route path="/track/:trackingNumber" element={<Track />} /></Routes>
    </MemoryRouter>,
  );
}
beforeEach(() => setLanguage("en"));

describe("exception banner (real-data only)", () => {
  it("shows an exception banner with what/when/next when the status is flagged as a problem", async () => {
    mockTracking({
      status: { code: "DELAYED", label: { en: "Delayed" }, is_problem: true, is_terminal: false, sort_order: 130 },
      events: [{ status: "DELAYED", status_ref: { code: "DELAYED", label: { en: "Delayed" }, is_problem: true }, location: "Somewhere", description: "Weather delay at hub.", event_timestamp: new Date().toISOString() }],
    });
    renderTrack();
    const alert = await screen.findByRole("alert");
    expect(alert).toHaveTextContent("Weather delay at hub.");
    expect(alert).toHaveTextContent("What happened");
    expect(alert).toHaveTextContent("What happens next");
  });

  it("shows no exception banner for a normal in-transit shipment", async () => {
    mockTracking({});
    renderTrack();
    await waitFor(() => expect(screen.getByText("NWT-CAP00001")).toBeInTheDocument());
    expect(screen.queryByRole("alert")).not.toBeInTheDocument();
  });
});

describe("honest ETA and delivery-timing states (computed from real dates only)", () => {
  it("shows an explicit unavailable message when there is no ETA", async () => {
    mockTracking({ estimated_delivery: null, actual_delivery: null });
    renderTrack();
    expect(await screen.findByText("Estimated delivery date unavailable")).toBeInTheDocument();
  });
  it("shows 'overdue' only when today is genuinely past a real stored ETA", async () => {
    mockTracking({ estimated_delivery: new Date(Date.now() - 86_400_000).toISOString(), actual_delivery: null });
    renderTrack();
    expect(await screen.findByText("Past the estimated delivery date")).toBeInTheDocument();
  });
  it("shows 'on track' when a real ETA is still in the future", async () => {
    mockTracking({ estimated_delivery: new Date(Date.now() + 86_400_000 * 2).toISOString(), actual_delivery: null });
    renderTrack();
    expect(await screen.findByText("On track for estimated delivery")).toBeInTheDocument();
  });
  it("computes transit time only from real created_at/actual_delivery timestamps", async () => {
    const delivered = new Date();
    mockTracking({ created_at: new Date(Date.now() - 86_400_000 * 4).toISOString(), actual_delivery: delivered.toISOString(), estimated_delivery: delivered.toISOString() });
    renderTrack();
    expect(await screen.findByText("4 days")).toBeInTheDocument();
    expect(await screen.findByText("Delivered on time")).toBeInTheDocument();
  });
});

describe("direct tracking URL", () => {
  it("looks up the shipment automatically from /track/:trackingNumber, no form submission needed", async () => {
    mockTracking({});
    renderTrack();
    await waitFor(() => expect(api.get).toHaveBeenCalledWith("/api/tracking/NWT-CAP00001"));
    expect(await screen.findByText("NWT-CAP00001")).toBeInTheDocument();
  });
});

describe("progress indicator never shown for problem or terminal states", () => {
  it("renders a progressbar for a normal in-transit shipment", async () => {
    mockTracking({});
    renderTrack();
    expect(await screen.findByRole("progressbar")).toBeInTheDocument();
  });
  it("does NOT render a progressbar for a delayed (problem) shipment", async () => {
    mockTracking({ status: { code: "DELAYED", label: { en: "Delayed" }, is_problem: true, is_terminal: false, sort_order: 130 } });
    renderTrack();
    await waitFor(() => expect(screen.getByText("NWT-CAP00001")).toBeInTheDocument());
    expect(screen.queryByRole("progressbar")).not.toBeInTheDocument();
  });
  it("does NOT render a progressbar once delivered (terminal)", async () => {
    mockTracking({ status: { code: "DELIVERED", label: { en: "Delivered" }, is_problem: false, is_terminal: true, sort_order: 120 }, actual_delivery: new Date().toISOString() });
    renderTrack();
    await waitFor(() => expect(screen.getByText("NWT-CAP00001")).toBeInTheDocument());
    expect(screen.queryByRole("progressbar")).not.toBeInTheDocument();
  });
});

describe("share and track-another controls", () => {
  it("offers a share-tracking button and a track-another-shipment reset", async () => {
    mockTracking({});
    renderTrack();
    expect(await screen.findByRole("button", { name: /share tracking/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /track another shipment/i })).toBeInTheDocument();
  });
});

describe("Arabic RTL on the tracking page", () => {
  it("renders the exception banner and sets RTL direction together", async () => {
    setLanguage("ar");
    mockTracking({
      status: { code: "DELAYED", label: { en: "Delayed", ar: "متأخر" }, is_problem: true, is_terminal: false, sort_order: 130 },
      events: [{ status: "DELAYED", status_ref: { code: "DELAYED", label: { en: "Delayed", ar: "متأخر" }, is_problem: true }, location: null, description: null, event_timestamp: new Date().toISOString() }],
    });
    renderTrack();
    expect(await screen.findByRole("alert")).toBeInTheDocument();
    expect(document.documentElement.dir).toBe("rtl");
    setLanguage("en");
  });
});
