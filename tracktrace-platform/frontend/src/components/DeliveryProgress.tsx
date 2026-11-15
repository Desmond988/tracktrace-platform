interface Props {
  currentSortOrder: number;
  minSortOrder: number;
  maxSortOrder: number;
  label: string;
}

/** A simple honest progress bar: position is the shipment's real configured status order between
 * the lowest and highest active, non-terminal statuses. Never shown for problem/terminal states
 * (see Track.tsx) - a linear bar would misrepresent an exception or an already-finished shipment. */
export default function DeliveryProgress({ currentSortOrder, minSortOrder, maxSortOrder, label }: Props) {
  const span = Math.max(1, maxSortOrder - minSortOrder);
  const pct = Math.min(100, Math.max(4, Math.round(((currentSortOrder - minSortOrder) / span) * 100)));
  return (
    <div style={{ margin: "18px 0" }}>
      <div
        role="progressbar"
        aria-valuenow={pct}
        aria-valuemin={0}
        aria-valuemax={100}
        aria-label={label}
        style={{ height: 6, borderRadius: 999, background: "var(--line-200)", overflow: "hidden" }}
      >
        <div style={{ height: "100%", width: `${pct}%`, background: "var(--freight-700)", borderRadius: 999, transition: "width 0.6s ease" }} />
      </div>
    </div>
  );
}
