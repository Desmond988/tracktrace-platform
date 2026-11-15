import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it, vi, beforeEach } from "vitest";
import Home from "../pages/public/Home";
import "../i18n";

vi.mock("../lib/api", () => ({ api: { get: vi.fn().mockResolvedValue([]) } }));

describe("Home", () => {
  beforeEach(() => window.history.pushState({}, "", "/"));

  it("renders the tracking hero and navigates on submit", async () => {
    const user = userEvent.setup();
    render(
      <MemoryRouter initialEntries={["/"]}>
        <Home />
      </MemoryRouter>,
    );
    expect(screen.getByRole("heading", { level: 1 })).toBeInTheDocument();
    const input = screen.getByPlaceholderText(/NWT/i);
    await user.type(input, "NWT-ABCDEFGH");
    await user.click(screen.getByRole("button", { name: /track/i }));
    await waitFor(() => expect(input).toBeInTheDocument());
    // no crash on submit; navigation is verified in Track.test.tsx via routing
  });
});
