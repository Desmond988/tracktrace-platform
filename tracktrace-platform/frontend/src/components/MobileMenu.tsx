import { useEffect, useRef } from "react";
import type { ReactNode } from "react";

interface Props {
  open: boolean;
  onClose: () => void;
  children: ReactNode;
}

/** Slide-in mobile navigation drawer. Closes on Escape or overlay click, moves focus into the
 * panel when opened and back to the trigger isn't handled here (the toggle button keeps its own
 * focus naturally since it isn't unmounted), and is inert (via aria-hidden absence when closed -
 * we simply don't render it) so closed-menu content is never in the tab order. */
export default function MobileMenu({ open, onClose, children }: Props) {
  const panelRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    document.addEventListener("keydown", onKey);
    panelRef.current?.querySelector<HTMLElement>("a, button")?.focus();
    document.body.style.overflow = "hidden";
    return () => {
      document.removeEventListener("keydown", onKey);
      document.body.style.overflow = "";
    };
  }, [open, onClose]);

  if (!open) return null;

  return (
    <>
      <div className="mobile-menu-overlay" onClick={onClose} />
      <div className="mobile-menu-panel" ref={panelRef} role="dialog" aria-modal="true" aria-label="Site menu">
        <div style={{ display: "flex", justifyContent: "flex-end", padding: "14px 16px 0" }}>
          <button
            onClick={onClose}
            aria-label="Close menu"
            style={{ background: "none", border: "none", cursor: "pointer", padding: 8, color: "var(--ink-900)" }}
          >
            <svg width="22" height="22" viewBox="0 0 20 20" fill="none" aria-hidden="true">
              <path d="M4 4l12 12M16 4L4 16" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
            </svg>
          </button>
        </div>
        <nav style={{ display: "flex", flexDirection: "column", padding: "8px 24px 24px", gap: 4 }}>{children}</nav>
      </div>
    </>
  );
}
