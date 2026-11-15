/** True if the user asked the OS/browser for reduced motion. Safe when matchMedia is unavailable
 * (very old browsers, some embedded webviews, test DOMs): in that case we report "reduced", which
 * is the conservative choice - content is shown immediately and nothing animates. */
export function prefersReducedMotion(): boolean {
  if (typeof window === "undefined" || typeof window.matchMedia !== "function") return true;
  return window.matchMedia("(prefers-reduced-motion: reduce)").matches;
}

export const canObserveViewport = (): boolean =>
  typeof window !== "undefined" && typeof window.IntersectionObserver === "function";
