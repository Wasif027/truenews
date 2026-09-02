import Link from "next/link";
import type { StoryListItem } from "@/lib/types";
import { categoryLabel, timeAgo } from "@/lib/format";

function Meta({ story, showCountry }: { story: StoryListItem; showCountry?: boolean }) {
  return (
    <div className="flex flex-wrap items-center gap-x-2.5 gap-y-1 text-xs" style={{ color: "var(--muted)" }}>
      {showCountry && (
        <>
          <span className="kicker" style={{ color: "var(--accent)" }}>
            {story.country}
          </span>
          <span className="opacity-40" aria-hidden>
            ·
          </span>
        </>
      )}
      <span className="kicker">{categoryLabel(story.categories)}</span>
      <span className="opacity-40" aria-hidden>
        ·
      </span>
      <span className="tabular" suppressHydrationWarning>
        {timeAgo(story.updated_at)}
      </span>
      <span className="opacity-40" aria-hidden>
        ·
      </span>
      {story.is_single_source ? (
        <span className="italic">single source</span>
      ) : (
        <span className="tabular">{story.outlet_count} outlets</span>
      )}
    </div>
  );
}

export function LeadStory({ story }: { story: StoryListItem }) {
  return (
    <div className="border-t-2" style={{ borderColor: "var(--accent)" }}>
      <span
        className="kicker mt-3 block"
        style={{ color: "var(--accent)" }}
      >
        The lead story
      </span>
      <Link
        href={`/story/${story.id}`}
        className="group -mx-3 mt-1 block rounded-lg px-3 pb-7 pt-2 transition-colors duration-200 hover:bg-[var(--surface-2)]"
      >
        <Meta story={story} />
        <div className="mt-2.5 grid gap-x-14 lg:grid-cols-[1.15fr_0.85fr] lg:items-start">
          <h2 className="font-display text-[1.85rem] leading-[1.08] tracking-[-0.02em] transition-colors duration-200 group-hover:text-[var(--accent)] sm:text-[2.7rem] sm:leading-[1.03]">
            {story.title}
          </h2>
          {story.summary && (
            <p
              className="mt-3 line-clamp-5 text-[0.98rem] leading-relaxed lg:mt-2"
              style={{ color: "var(--fg-soft)" }}
            >
              {story.summary}
            </p>
          )}
        </div>
        <span
          className="mt-3 inline-flex items-center gap-1 text-xs font-medium opacity-0 transition-opacity duration-200 group-hover:opacity-100"
          style={{ color: "var(--accent)" }}
        >
          Compare coverage
          <span className="transition-transform duration-200 group-hover:translate-x-0.5">→</span>
        </span>
      </Link>
    </div>
  );
}

export function StoryCard({
  story,
  showCountry,
}: {
  story: StoryListItem;
  showCountry?: boolean;
}) {
  return (
    <Link
      href={`/story/${story.id}`}
      className="group -mx-3 block rounded-lg px-3 py-5 transition-colors duration-200 hover:bg-[var(--surface-2)]"
    >
      <Meta story={story} showCountry={showCountry} />
      <div className="mt-1.5 grid gap-x-12 gap-y-1.5 lg:grid-cols-[1.15fr_0.85fr] lg:items-baseline">
        <h3 className="font-display text-[1.3rem] leading-[1.28] transition-colors duration-200 group-hover:text-[var(--accent)] sm:text-[1.4rem]">
          {story.title}
        </h3>
        {story.summary && (
          <p className="line-clamp-3 text-sm leading-relaxed" style={{ color: "var(--fg-soft)" }}>
            {story.summary}
          </p>
        )}
      </div>
    </Link>
  );
}
