import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it } from "vitest";
import Home from "../pages/public/Home";
import i18n, { setLanguage } from "../i18n";
import { vi } from "vitest";

vi.mock("../lib/api", () => ({ api: { get: vi.fn().mockResolvedValue([]) } }));

describe("language switching", () => {
  it("renders French copy after setLanguage('fr')", async () => {
    setLanguage("fr");
    render(
      <MemoryRouter>
        <Home />
      </MemoryRouter>,
    );
    expect(screen.getByText(/Suivez votre expédition/)).toBeInTheDocument();
    setLanguage("en");
    expect(i18n.language).toBe("en");
    await waitFor(() => expect(screen.getByText(/Track your shipment/)).toBeInTheDocument());
  });
});
