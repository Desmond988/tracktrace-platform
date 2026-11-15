import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";
import PublicLayout from "../components/PublicLayout";
import { AuthProvider } from "../context/AuthContext";
import "../i18n";

vi.mock("../lib/api", () => ({
  api: {
    get: vi.fn((path: string) => {
      if (path === "/api/auth/me") return Promise.resolve({ id: "1", name: "Ada", email: "ada@example.com", phone: null, role: "CUSTOMER", is_active: true, preferred_language: "en", permissions: [] });
      if (path === "/api/legal") return Promise.resolve([]);
      return Promise.resolve([]);
    }),
    post: vi.fn(),
  },
  ApiError: class extends Error {},
}));

describe("PublicLayout", () => {
  it("shows a sign-out control for a logged-in customer (not just staff)", async () => {
    render(
      <MemoryRouter initialEntries={["/"]}>
        <AuthProvider>
          <PublicLayout />
        </AuthProvider>
      </MemoryRouter>,
    );
    await waitFor(() => expect(screen.getByRole("button", { name: /sign out/i })).toBeInTheDocument());
  });
});
