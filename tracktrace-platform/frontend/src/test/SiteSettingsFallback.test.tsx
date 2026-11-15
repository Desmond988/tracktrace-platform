import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";
import PublicLayout from "../components/PublicLayout";
import { AuthProvider } from "../context/AuthContext";
import "../i18n";

// Both /api/auth/me and /api/public/settings fail here - this simulates the backend being
// completely unreachable, which is the actual failure mode requirement #4 asks about.
vi.mock("../lib/api", () => ({
  api: {
    get: vi.fn(() => Promise.reject(new Error("network error"))),
    post: vi.fn(),
  },
  ApiError: class extends Error {},
}));

describe("public site renders safely when the settings API is unreachable", () => {
  it("shows the fallback brand name, not a blank header, and does not crash", async () => {
    render(
      <MemoryRouter initialEntries={["/"]}>
        <AuthProvider>
          <PublicLayout />
        </AuthProvider>
      </MemoryRouter>,
    );
    // The fallback constant should be visible immediately on first paint (initial state, not
    // "eventually after retry") - this is the "no blank header" requirement.
    expect(screen.getAllByText("FreightXpress Delivery").length).toBeGreaterThan(0);
    // Give the failed fetches time to reject and confirm the app is still standing afterward.
    await waitFor(() => expect(screen.getAllByText("FreightXpress Delivery").length).toBeGreaterThan(0));
    expect(screen.getByText((text) => text.includes("New York City, New York, United States"))).toBeInTheDocument();
  });
});
