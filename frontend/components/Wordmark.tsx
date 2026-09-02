/** The mark is a print misregistration — the same block run twice, not quite
 *  aligned. That's the product: one event, two (or ten) impressions of it. */
export function Wordmark() {
  return (
    <span className="flex items-center gap-[0.4em]">
      <svg viewBox="0 0 24 24" aria-hidden className="h-[0.82em] w-[0.82em] shrink-0">
        <rect x="3" y="3" width="13" height="13" rx="2.5" fill="currentColor" opacity="0.28" />
        <rect x="8" y="8" width="13" height="13" rx="2.5" fill="var(--accent)" />
      </svg>
      <span className="font-display font-medium leading-none tracking-[-0.035em]">
        True<span style={{ color: "var(--accent)" }}>News</span>
      </span>
    </span>
  );
}
