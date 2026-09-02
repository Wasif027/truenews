/** The pickup meter: a pip for every outlet that ran the story, faint ghosts for
 *  the ones that didn't. The single visual that says "how corroborated is this."
 *  `total` is optional — with it you get the full strip (covered + blindspot);
 *  without it, just the covered pips as a weight indicator. */
export function CoverageStrip({
  count,
  total,
  className = "",
}: {
  count: number;
  total?: number;
  className?: string;
}) {
  const cap = 12;
  const covered = Math.min(count, cap);
  const ghosts = total ? Math.min(Math.max(total - count, 0), cap - covered) : 0;

  return (
    <span
      className={`inline-flex items-center gap-[3px] align-middle ${className}`}
      aria-hidden
    >
      {Array.from({ length: covered }, (_, i) => (
        <span key={`c${i}`} className="pip" />
      ))}
      {Array.from({ length: ghosts }, (_, i) => (
        <span key={`g${i}`} className="pip off" />
      ))}
    </span>
  );
}
