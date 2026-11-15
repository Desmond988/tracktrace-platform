import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";
import AdminShipments from "../pages/admin/Shipments";

vi.mock("../lib/api", () => ({ api: { get: vi.fn().mockResolvedValue({ items: [], total: 0 }) } }));
import { api } from "../lib/api";

describe("staff shipment quick-filters use real status codes", () => {
  it("sends the exact backend status code for each quick filter, not an invented category", async () => {
    const user = userEvent.setup();
    render(<MemoryRouter><AdminShipments /></MemoryRouter>);
    await waitFor(() => expect(api.get).toHaveBeenCalled());
    await user.click(screen.getByRole("button", { name: "Delayed" }));
    await waitFor(() => expect(api.get).toHaveBeenLastCalledWith(expect.stringContaining("status=DELAYED")));
    await user.click(screen.getByRole("button", { name: "Failed attempt" }));
    await waitFor(() => expect(api.get).toHaveBeenLastCalledWith(expect.stringContaining("status=FAILED_DELIVERY_ATTEMPT")));
    await user.click(screen.getByRole("button", { name: "Returned to sender" }));
    await waitFor(() => expect(api.get).toHaveBeenLastCalledWith(expect.stringContaining("status=RETURNED_TO_SENDER")));
    await user.click(screen.getByRole("button", { name: "All" }));
    await waitFor(() => expect(api.get).toHaveBeenLastCalledWith(expect.not.stringContaining("status=")));
  });

  it("sends origin/destination/date filters as real backend query params", async () => {
    const user = userEvent.setup();
    render(<MemoryRouter><AdminShipments /></MemoryRouter>);
    await user.type(screen.getByPlaceholderText("Origin"), "Toronto");
    await user.type(screen.getByPlaceholderText("Destination"), "Vancouver");
    await user.click(screen.getByRole("button", { name: "Apply filters" }));
    await waitFor(() => {
      const last = (api.get as ReturnType<typeof vi.fn>).mock.calls.at(-1)![0] as string;
      expect(last).toContain("origin=Toronto");
      expect(last).toContain("destination=Vancouver");
    });
  });
});
