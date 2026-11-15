import type { ReactNode } from "react";
import ScrollReveal from "./ScrollReveal";

export default function AnimatedCTA({ title, body, action }: { title: string; body?: string; action: ReactNode }) {
  return (
    <section style={{ background: "var(-- Track-100)", padding: "44px 0" }}>
      <ScrollReveal className="container" style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: 20 }}>
        <div>
          <h2 style={{ fontSize: "1.35rem", marginBottom: 4 }}>{title}</h2>
          {body && <p style={{ color: "var(--slate-500)", margin: 0, maxWidth: 520 }}>{body}</p>}
        </div>
        {action}
      </ScrollReveal>
    </section>
  );
}
