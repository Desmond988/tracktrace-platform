import type { CSSProperties, ReactNode } from "react";
import { useInView } from "../hooks/useInView";

interface Props {
  children: ReactNode;
  delayMs?: number;
  as?: "div" | "section" | "li";
  className?: string;
  style?: CSSProperties;
}

/** Fades and gently rises content into place the first time it scrolls into view. Pure CSS
 * transition (no animation library); becomes a no-op transition under prefers-reduced-motion. */
export default function ScrollReveal({ children, delayMs = 0, as = "div", className, style }: Props) {
  const [ref, inView] = useInView<HTMLDivElement>();
  const Tag = as as "div";
  return (
    <Tag
      ref={ref}
      className={className}
      style={{
        ...style,
        opacity: inView ? 1 : 0,
        transform: inView ? "translateY(0)" : "translateY(18px)",
        transition: `opacity 0.6s ease ${delayMs}ms, transform 0.6s ease ${delayMs}ms`,
      }}
    >
      {children}
    </Tag>
  );
}
