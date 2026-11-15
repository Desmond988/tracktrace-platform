import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";
import Track from "../pages/public/Track";
import { ApiError } from "../lib/api";
import "../i18n";

vi.mock("../lib/api", async () => {
  const actual = await vi.importActual<typeof import("../lib/api")>("../lib/api");
  return { ...actual, api: { get: vi.fn() } };
});
import { api } from "../lib/api";

const STATUSES = [
  { code: "SHIPMENT_CREATED", label: { en: "Shipment Created" }, is_problem: false, is_terminal: false, sort_order: 10 },
  { code: "IN_TRANSIT", label: { en: "In Transit" }, is_problem: false, is_terminal: false, sort_order: 70 },
  { code: "DELIVERED", label: { en: "Delivered" }, is_problem: false, is_terminal: true, sort_order: 120 },
];

describe("Track page", () => {
  it("shows the not-found message for an unknown tracking number", async () => {
    (api.get as ReturnType<typeof vi.fn>).mockImplementation((path: string) =>
      path === "/api/statuses" ? Promise.resolve(STATUSES) : Promise.reject(new ApiError(404, { code: "TRACKING_NOT_FOUND", message: "Tracking number not found." })),
    );
    render(<MemoryRouter initialEntries={["/track?tn=NWT-ZZZZZZZZ"]}><Track /></MemoryRouter>);
    await waitFor(() => expect(screen.getByRole("alert")).toBeInTheDocument());
  });

  it("renders shipment details on success", async () => {
    (api.get as ReturnType<typeof vi.fn>).mockImplementation((path: string) => {
      if (path === "/api/statuses") return Promise.resolve(STATUSES);
      return Promise.resolve({
        tracking_number: "NWT-ABCDEFGH",
        status: { code: "IN_TRANSIT", label: { en: "In Transit", fr: "En transit" }, is_problem: false, is_terminal: false, sort_order: 70 },
        origin: "Toronto, CA", destination: "Vancouver, CA", current_location: "Winnipeg, CA",
        created_at: new Date().toISOString(), estimated_delivery: null, actual_delivery: null, pieces: 1, updated_at: new Date().toISOString(),
        events: [{ status: "SHIPMENT_CREATED", status_ref: { code: "SHIPMENT_CREATED", label: { en: "Shipment Created", fr: "x" }, is_problem: false }, location: "Toronto, CA", description: null, event_timestamp: new Date().toISOString() }],
      });
    });
    render(<MemoryRouter initialEntries={["/track?tn=NWT-ABCDEFGH"]}><Track /></MemoryRouter>);
    await waitFor(() => expect(screen.getByText("NWT-ABCDEFGH")).toBeInTheDocument());
    expect(screen.getAllByText("Toronto, CA").length).toBeGreaterThan(0);
    expect(screen.getByText("In Transit")).toBeInTheDocument();
  });
});
