import { useEffect, useRef, useState } from "react";
import { canObserveViewport, prefersReducedMotion } from "../lib/motion";

/** True once the element has scrolled into view (stays true afterward - entrances shouldn't replay
 * on scroll-up, that reads as jittery rather than purposeful). Respects prefers-reduced-motion by
 * reporting "already in view" immediately, so reduced-motion users see final-state content with no
 * transition at all rather than a motion-free "pop". */
export function useInView<T extends HTMLElement>(threshold = 0.15): [React.RefObject<T | null>, boolean] {
  const ref = useRef<T | null>(null);
  const [inView, setInView] = useState(false);

  useEffect(() => {
    // Never leave content hidden: if the user wants reduced motion, or the browser can't observe
    // the viewport, show the final state right away.
    if (prefersReducedMotion() || !canObserveViewport()) {
      setInView(true);
      return;
    }
    const el = ref.current;
    if (!el) return;
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setInView(true);
          observer.disconnect();
        }
      },
      { threshold },
    );
    observer.observe(el);
    return () => observer.disconnect();
  }, [threshold]);

  return [ref, inView];
}
