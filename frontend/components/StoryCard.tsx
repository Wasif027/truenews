import Link from "next/link";
import type { StoryListItem } from "@/lib/types";
import { categoryLabel, timeAgo } from "@/lib/format";
import { CoverageStrip } from "./CoverageStrip";

function Dot() {
  return (
    <span className="opacity-40" aria-hidden>
      ·
    </span>
  );
}

function Meta({ story, showCountry }: { story: StoryListItem; showCountry?: boolean }) {
  return (
    <div
      className="flex flex-wrap items-center gap-x-2.5 gap-y-1 text-xs"
      style={{ color: "var(--muted)" }}
    >
      {showCountry && (
        <>
          <span className="kicker" style={{ color: "var(--accent-ink)" }}>
            {story.country}
          </span>
          <Dot />
        </>
      )}
      <span className="kicker">{categoryLabel(story.categories)}</span>
      <Dot />
      <span className="tabular" suppressHydrationWarning>
        {timeAgo(story.updated_at)}
      </span>
      <Dot />
      {story.is_single_source ? (
        <span className="inline-flex items-center gap-1.5">
          <span className="pip off" aria-hidden />
          <span className="italic">one source</span>
        </span>
      ) : (
        <span className="inline-flex items-center gap-1.5">
          <CoverageStrip count={story.outlet_count} />
          <span className="tabular">{story.outlet_count} sources</span>
        </span>
      )}
    </div>
  );
}

export function LeadStory({ story }: { story: StoryListItem }) {
  return (
    <div>
      <span className="kicker mb-2 block" style={{ color: "var(--accent-ink)" }}>
        The lead story
      </span>
      <Link
        href={`/story/${story.id}`}
        className="group panel block px-6 pb-7 pt-5 transition-[border-color,box-shadow] duration-200 hover:border-[var(--accent)] sm:px-8 sm:pt-6"
      >
        <Meta story={story} />
        <div className="mt-3 grid gap-x-14 lg:grid-cols-[1.15fr_0.85fr] lg:items-start">
          <h2 className="font-display text-[1.9rem] leading-[1.06] tracking-[-0.022em] transition-colors duration-200 group-hover:text-[var(--accent)] sm:text-[2.8rem] sm:leading-[1.02]">
            {story.title}
          </h2>
          {story.summary && (
            <p
              className="mt-3 line-clamp-6 text-[0.98rem] leading-relaxed lg:mt-1.5"
              style={{ color: "var(--fg-soft)" }}
            >
              {story.summary}
            </p>
          )}
        </div>
        <span
          className="mt-4 inline-flex items-center gap-1 text-xs font-medium transition-colors"
          style={{ color: "var(--accent-ink)" }}
        >
          Compare the coverage
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
