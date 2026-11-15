import { useState, useEffect } from "react";

const SCENES = [
  { key: "air", label: "Air freight", src: "/images/air.png" },
  { key: "ocean", label: "Ocean freight", src: "/images/ocean.jpg" },
  { key: "road", label: "Road freight", src: "/images/road.jpg" },
] as const;

export default function HeroVisual() {
  const [active, setActive] = useState(0);
  const scene = SCENES[active];

  // Auto-change every 4 seconds
  useEffect(() => {
    const timer = setInterval(() => {
      setActive((prev) => (prev + 1) % SCENES.length);
    }, 4000);
    return () => clearInterval(timer);
  }, []);

  return (
    <div style={{ width: "100%" }}>
      <div style={{ width: "100%", height: 280, borderRadius: 16, overflow: "hidden", background: "#e5e7eb" }}>
        <img
          src={scene.src}
          alt={scene.label}
          style={{ width: "100%", height: "100%", objectFit: "cover", display: "block" }}
        />
      </div>
      <div style={{ display: "flex", gap: 8, justifyContent: "center", marginTop: 12 }}>
        {SCENES.map((s, i) => (
          <button
            key={s.key}
            onClick={() => setActive(i)}
            style={{
              padding: "6px 12px",
              borderRadius: 999,
              border: "none",
              cursor: "pointer",
              background: i === active ? "#059669" : "#e5e7eb",
              color: i === active ? "#fff" : "#111827",
              fontWeight: 600,
              fontSize: 13,
            }}
          >
            {s.label}
          </button>
        ))}
      </div>
    </div>
  );
}