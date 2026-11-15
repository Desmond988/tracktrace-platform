import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";
import Track from "../pages/public/Track";
import "../i18n";
import { setLanguage } from "../i18n";

vi.mock("../lib/api", async () => {
  const actual = await vi.importActual<typeof import("../lib/api")>("../lib/api");
  return { ...actual, api: { get: vi.fn() } };
});
import { api } from "../lib/api";

const STATUSES = [{ code: "DELIVERED", label: { en: "Delivered" }, is_problem: false, is_terminal: true, sort_order: 120 }];
const LABEL = { en: "Delivered", fr: "Livré", es: "Entregado", ar: "تم التسليم" };
const TRACKING_RESPONSE = {
  tracking_number: "NWT-ABCDEFGH",
  status: { code: "DELIVERED", label: LABEL, is_problem: false, is_terminal: true, sort_order: 120 },
  origin: "Toronto, CA", destination: "Vancouver, CA", current_location: "Vancouver, CA",
  created_at: new Date(Date.now() - 86_400_000 * 3).toISOString(), estimated_delivery: null, actual_delivery: new Date().toISOString(),
  pieces: 1, updated_at: new Date().toISOString(),
  events: [{ status: "DELIVERED", status_ref: { code: "DELIVERED", label: LABEL, is_problem: false }, location: "Vancouver, CA", description: null, event_timestamp: new Date().toISOString() }],
};
function mockApi() {
  (api.get as ReturnType<typeof vi.fn>).mockImplementation((path: string) => (path === "/api/statuses" ? Promise.resolve(STATUSES) : Promise.resolve(TRACKING_RESPONSE)));
}
const ui = () => <MemoryRouter initialEntries={["/track?tn=NWT-ABCDEFGH"]}><Track /></MemoryRouter>;

describe("switching languages changes actual customer-facing content", () => {
  it("re-renders the SAME shipment's status label in the newly selected language, not just the dropdown", async () => {
    mockApi();
    setLanguage("en");
    const { rerender } = render(ui());
    await waitFor(() => expect(screen.getAllByText("Delivered").length).toBeGreaterThan(0));
    expect(screen.queryByText("Livré")).not.toBeInTheDocument();

    setLanguage("fr");
    rerender(ui());
    await waitFor(() => expect(screen.getAllByText("Livré").length).toBeGreaterThan(0));
    expect(screen.queryAllByText("Delivered").length).toBe(0);

    setLanguage("ar");
    rerender(ui());
    await waitFor(() => expect(screen.getAllByText("تم التسليم").length).toBeGreaterThan(0));
    expect(document.documentElement.dir).toBe("rtl");
    setLanguage("en");
  });

  it("falls back to English for a language the content has not been translated into", async () => {
    mockApi();
    setLanguage("sw");
    render(ui());
    await waitFor(() => expect(screen.getAllByText("Delivered").length).toBeGreaterThan(0));
    setLanguage("en");
  });
});
