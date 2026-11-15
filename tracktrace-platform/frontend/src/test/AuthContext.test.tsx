import { render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { AuthProvider, useAuth } from "../context/AuthContext";

vi.mock("../lib/api", () => ({
  api: { get: vi.fn().mockRejectedValue(new Error("no session")), post: vi.fn() },
  ApiError: class extends Error {},
}));

function Probe() {
  const { user, loading } = useAuth();
  if (loading) return <div>loading</div>;
  return <div>{user ? "logged-in" : "anonymous"}</div>;
}

describe("AuthProvider", () => {
  it("resolves to anonymous when there is no session", async () => {
    render(
      <AuthProvider>
        <Probe />
      </AuthProvider>,
    );
    await waitFor(() => expect(screen.getByText("anonymous")).toBeInTheDocument());
  });
});
