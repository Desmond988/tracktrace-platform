import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it, vi, afterEach } from "vitest";
import App from "../App";
import { AuthProvider } from "../context/AuthContext";
import Accordion from "../components/Accordion";
import ScrollReveal from "../components/ScrollReveal";
import "../i18n";

const SERVICES = [
  { id: "1", code: "AIR_FREIGHT", name: { en: "Air Freight" } },
  { id: "2", code: "CUSTOMS_CLEARANCE", name: { en: "Customs Clearance" } },
];
const LEGAL = [{ slug: "privacy-policy", title: { en: "Privacy Policy" } }];

vi.mock("../lib/api", async () => {
  const actual = await vi.importActual<typeof import("../lib/api")>("../lib/api");
  return {
    ...actual,
    api: {
      post: vi.fn(),
      get: vi.fn((path: string) => {
        if (path === "/api/auth/me") return Promise.reject(new Error("anonymous"));
        if (path === "/api/services") return Promise.resolve(SERVICES);
        if (path === "/api/legal") return Promise.resolve(LEGAL);
        if (path === "/api/locations") return Promise.resolve([]);
        if (path === "/api/faq") return Promise.resolve([{ id: "f1", question: { en: "Q one?" }, answer: { en: "A one." } }, { id: "f2", question: { en: "Q two?" }, answer: { en: "A two." } }]);
        if (path === "/api/public/settings") return Promise.reject(new Error("down"));
        return Promise.resolve([]);
      }),
    },
  };
});
import { api } from "../lib/api";

function renderAt(path: string) {
  return render(
    <MemoryRouter initialEntries={[path]}>
      <AuthProvider><App /></AuthProvider>
    </MemoryRouter>,
  );
}
afterEach(() => vi.clearAllMocks());

describe("mobile navigation", () => {
  it("opens from the menu button, exposes the real nav links, and closes on Escape", async () => {
    const user = userEvent.setup();
    renderAt("/");
    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: /menu/i }));
    const dialog = await screen.findByRole("dialog");
    expect(within(dialog).getByRole("link", { name: /track/i })).toHaveAttribute("href", "/track");
    expect(within(dialog).getByRole("link", { name: /request a quote/i })).toHaveAttribute("href", "/quote");
    await user.keyboard("{Escape}");
    await waitFor(() => expect(screen.queryByRole("dialog")).not.toBeInTheDocument());
  });

  it("closes after a link is chosen", async () => {
    const user = userEvent.setup();
    renderAt("/");
    await user.click(screen.getByRole("button", { name: /menu/i }));
    const dialog = await screen.findByRole("dialog");
    await user.click(within(dialog).getByRole("link", { name: /contact/i }));
    await waitFor(() => expect(screen.queryByRole("dialog")).not.toBeInTheDocument());
  });
});

describe("accordion accessibility", () => {
  it("uses real buttons with aria-expanded and toggles with the keyboard", async () => {
    const user = userEvent.setup();
    render(<Accordion items={[{ id: "a", question: "First?", answer: "One" }, { id: "b", question: "Second?", answer: "Two" }]} />);
    const first = screen.getByRole("button", { name: /first/i });
    const second = screen.getByRole("button", { name: /second/i });
    expect(first).toHaveAttribute("aria-expanded", "true");
    expect(second).toHaveAttribute("aria-expanded", "false");
    second.focus();
    await user.keyboard("{Enter}");
    expect(second).toHaveAttribute("aria-expanded", "true");
    expect(first).toHaveAttribute("aria-expanded", "false");
    expect(second).toHaveAttribute("aria-controls", expect.stringContaining("accordion-panel"));
  });
});

describe("motion never hides content", () => {
  it("ScrollReveal content is visible when IntersectionObserver is unavailable", async () => {
    // jsdom has no IntersectionObserver - this is exactly the "can't animate" situation.
    render(<ScrollReveal><p>Important information</p></ScrollReveal>);
    const el = screen.getByText("Important information").parentElement!;
    await waitFor(() => expect(el.style.opacity).toBe("1"));
  });
});

describe("public pages render real, non-invented content", () => {
  it("Locations shows an honest empty state when the API returns no locations", async () => {
    renderAt("/locations");
    expect(await screen.findByText(/location network will appear here/i)).toBeInTheDocument();
    expect(api.get).toHaveBeenCalledWith("/api/locations");
  });

  it("Careers shows an empty state and invents no vacancies", async () => {
    renderAt("/careers");
    expect(await screen.findByText(/no open positions/i)).toBeInTheDocument();
  });

  it("Services lists exactly what /api/services returns, each linking to a detail page", async () => {
    renderAt("/services");
    const link = await screen.findByRole("link", { name: /air freight/i });
    expect(link).toHaveAttribute("href", "/services/air-freight");
    expect(screen.getByRole("link", { name: /customs clearance/i })).toHaveAttribute("href", "/services/customs-clearance");
  });

  it("an unknown service slug shows the not-found page, not a blank screen", async () => {
    renderAt("/services/does-not-exist");
    expect(await screen.findByText(/page not found/i)).toBeInTheDocument();
  });

  it("FAQ renders entries from the API through the accordion", async () => {
    renderAt("/faq");
    expect(await screen.findByRole("button", { name: /q one/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /q two/i })).toBeInTheDocument();
  });

  it("Track still queries the real tracking API and renders only what it returns", async () => {
    (api.get as ReturnType<typeof vi.fn>).mockImplementation((path: string) => {
      if (path.startsWith("/api/tracking/")) {
        return Promise.resolve({
          tracking_number: "NWT-REAL0001", status: { code: "IN_TRANSIT", label: { en: "In Transit" }, is_problem: false },
          origin: "Origin City", destination: "Destination City", current_location: "Somewhere Real",
          estimated_delivery: null, actual_delivery: null, pieces: 1, updated_at: new Date().toISOString(),
          events: [{ status: "IN_TRANSIT", status_ref: { code: "IN_TRANSIT", label: { en: "In Transit" }, is_problem: false }, location: "Somewhere Real", description: null, event_timestamp: new Date().toISOString() }],
        });
      }
      if (path === "/api/auth/me") return Promise.reject(new Error("anonymous"));
      return Promise.resolve([]);
    });
    renderAt("/track?tn=NWT-REAL0001");
    await waitFor(() => expect(api.get).toHaveBeenCalledWith("/api/tracking/NWT-REAL0001"));
    expect(await screen.findByText("Origin City")).toBeInTheDocument();
    expect(screen.getAllByText("Somewhere Real").length).toBeGreaterThan(0);
  });
});

describe("no dead public links", () => {
  const PUBLIC_PATHS = ["/", "/track", "/services", "/services/air-freight", "/about", "/quote", "/contact", "/faq", "/locations", "/careers", "/login", "/register", "/forgot-password", "/legal/privacy-policy"];

  it.each(PUBLIC_PATHS)("every internal link rendered on %s points at a real page (never the 404 page)", async (path) => {
    const { container, unmount } = renderAt(path);
    await waitFor(() => expect(container.querySelector("main")).not.toBeNull());
    const hrefs = Array.from(container.querySelectorAll("a[href]"))
      .map((a) => a.getAttribute("href")!)
      .filter((h) => h.startsWith("/"));
    expect(hrefs.length).toBeGreaterThan(0);
    for (const href of hrefs) {
      unmount();
      const { container: c2, unmount: u2 } = renderAt(href.split("?")[0] === "/legal/privacy-policy" ? href : href);
      await waitFor(() => expect(c2.querySelector("main")).not.toBeNull());
      expect(within(c2).queryByText(/^page not found$/i), `dead link: ${href} (found on ${path})`).toBeNull();
      u2();
      renderAt(path); // restore for the outer unmount
    }
  });
});
