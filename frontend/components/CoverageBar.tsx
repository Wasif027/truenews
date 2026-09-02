export function CoverageBar({ reported, total }: { reported: number; total: number }) {
  const cells = Math.max(total, reported, 1);
  return (
    <div className="flex items-center gap-2.5 text-xs" style={{ color: "var(--muted)" }}>
      <span
        className="flex gap-[3px]"
        role="img"
        aria-label={`${reported} of ${total} tracked outlets reported this`}
      >
        {Array.from({ length: cells }).map((_, i) => (
          <span
            key={i}
            className="h-3.5 w-[5px] rounded-[1.5px] transition-colors"
            style={{
              background: i < reported ? "var(--accent)" : "var(--border)",
            }}
          />
        ))}
      </span>
      <span aria-hidden>
        <span className="tabular font-medium" style={{ color: "var(--fg-soft)" }}>
          {reported}
        </span>
        <span className="tabular"> / {total} outlets</span>
      </span>
    </div>
  );
}
