/** A set letterform, not an abstract shape — the same serif "T" a story's
 *  drop cap uses, boxed like a printer's block. Ink follows the page (dark
 *  chip on light mode, light chip on dark), the stroke stays the accent. */
export function Wordmark() {
  return (
    <span className="flex items-center gap-[0.34em]">
      <svg viewBox="0 0 32 32" aria-hidden className="h-[0.86em] w-[0.86em] shrink-0">
        <rect width="32" height="32" rx="6" fill="currentColor" />
        <rect x="7" y="8" width="18" height="3.4" rx="1" fill="var(--accent)" />
        <rect x="14.3" y="8" width="3.4" height="17" rx="1" fill="var(--accent)" />
      </svg>
      <span className="font-display font-medium leading-none tracking-[-0.035em]">
        True<span style={{ color: "var(--accent)" }}>News</span>
      </span>
    </span>
  );
}
