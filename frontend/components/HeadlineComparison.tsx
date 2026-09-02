import type { SourceArticle } from "@/lib/types";
import { timeAgo } from "@/lib/format";

/** Same event, each outlet's own headline, ordered first-to-report → last.
 *  Framing comparison with no model. */
export function HeadlineComparison({ sources }: { sources: SourceArticle[] }) {
  if (sources.length < 2) return null;

  // One row per outlet — the headline it led with when it first ran the story.
  // Big clusters carry dozens of follow-ups from the same masthead; showing all
  // of them buries the framing comparison this section exists for.
  const byOutlet = new Map<string, SourceArticle>();
  for (const s of sources) {
    const key = s.outlet.name;
    const seen = byOutlet.get(key);
    if (!seen || +new Date(s.published_at) < +new Date(seen.published_at)) {
      byOutlet.set(key, s);
    }
  }
  const ordered = [...byOutlet.values()].sort(
    (a, b) => +new Date(a.published_at) - +new Date(b.published_at),
  );
  if (ordered.length < 2) return null;
  return (
    <ul className="divide-y hairline border-t hairline">
      {ordered.map((s, i) => (
        <li key={s.id} className="flex gap-3.5 py-3.5">
          <span
            className="tabular mt-1 shrink-0 text-xs font-semibold"
            style={{ color: "var(--muted)" }}
          >
            {i + 1}
          </span>
          <div className="min-w-0">
            <div
              className="flex flex-wrap items-center gap-x-2 gap-y-1 text-xs"
              style={{ color: "var(--muted)" }}
            >
              <span className="font-medium" style={{ color: "var(--fg)" }}>
                {s.outlet.name}
              </span>
              {i === 0 && (
                <span
                  className="rounded-[3px] px-1.5 py-px text-[0.6rem] font-semibold uppercase tracking-[0.08em]"
                  style={{ background: "var(--accent)", color: "var(--card)" }}
                >
                  first to report
                </span>
              )}
              <span className="opacity-40">·</span>
              <span className="tabular">{timeAgo(s.published_at)}</span>
            </div>
            <p className="font-display mt-1 text-[1.08rem] leading-[1.35]">
              <span style={{ color: "var(--accent)" }}>&ldquo;</span>
              {s.headline}
              <span style={{ color: "var(--accent)" }}>&rdquo;</span>
            </p>
          </div>
        </li>
      ))}
    </ul>
  );
}
