import { useEffect, useRef, useState } from "react";
import { prefersReducedMotion } from "../lib/motion";

interface Props {
  phrases: string[];
  intervalMs?: number;
}

/** Slowly crossfades between a handful of short phrases. Pauses on hover/focus (so it never
 * interrupts someone reading), and shows only the first phrase, statically, under
 * prefers-reduced-motion. */
export default function RotatingTagline({ phrases, intervalMs = 4200 }: Props) {
  const [index, setIndex] = useState(0);
  const paused = useRef(false);

  useEffect(() => {
    if (phrases.length <= 1) return;
    if (prefersReducedMotion()) return;
    const id = setInterval(() => {
      if (!paused.current) setIndex((i) => (i + 1) % phrases.length);
    }, intervalMs);
    return () => clearInterval(id);
  }, [phrases.length, intervalMs]);

  return (
    <span
      onMouseEnter={() => (paused.current = true)}
      onMouseLeave={() => (paused.current = false)}
      onFocus={() => (paused.current = true)}
      onBlur={() => (paused.current = false)}
      style={{ display: "inline-block", position: "relative", minHeight: "1.3em" }}
    >
      <span key={index} style={{ display: "inline-block", animation: "rotate-line-in 0.5s ease" }}>
        {phrases[index]}
      </span>
    </span>
  );
}
