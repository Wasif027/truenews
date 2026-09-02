import Link from "next/link";
import { notFound } from "next/navigation";
import { CoverageStrip } from "@/components/CoverageStrip";
import { HeadlineComparison } from "@/components/HeadlineComparison";
import { ReadAtSource } from "@/components/ReadAtSource";
import { ReadingProgress } from "@/components/ReadingProgress";
import { RecordVisit } from "@/components/RecordVisit";
import { StoryActions } from "@/components/StoryActions";
import { getStory } from "@/lib/api";
import { categoryLabel, timeAgo } from "@/lib/format";

// Story content is cached ~1 min (getStory: revalidate 60); per-user liked/saved
// are hydrated client-side in StoryActions.
export const revalidate = 60;

function SectionLabel({ children }: { children: React.ReactNode }) {
  return (
    <div className="mb-3 flex items-center gap-3">
      <span className="kicker whitespace-nowrap">{children}</span>
      <span className="h-px flex-1" style={{ background: "var(--border)" }} />
    </div>
  );
}

export default async function StoryPage({ params }: { params: { id: string } }) {
  const story = await getStory(params.id).catch(() => null);
  if (!story) notFound();

  const totalOutlets = story.coverage.reported.length + story.coverage.not_reporting.length;
  const flagged = story.sources.flatMap((s) => s.flagged_sentences);

  return (
    <article className="reveal mx-auto max-w-[46rem]">
      <ReadingProgress />
      <Link
        href="/"
        className="group inline-flex items-center gap-1.5 text-sm transition-colors hover:text-[var(--fg)]"
        style={{ color: "var(--muted)" }}
      >
        <span className="transition-transform duration-200 group-hover:-translate-x-0.5">←</span>
        All stories
      </Link>

      <header className="mt-6 space-y-3.5">
        <div className="flex items-center gap-2.5 text-xs" style={{ color: "var(--muted)" }}>
          <span className="kicker">{categoryLabel(story.categories)}</span>
          <span className="opacity-40">·</span>
          <span className="tabular">updated {timeAgo(story.updated_at)}</span>
        </div>

        <h1 className="font-display text-[1.85rem] font-medium leading-[1.1] tracking-[-0.022em] sm:text-[3rem] sm:leading-[1.02]">
          {story.title}
        </h1>

        <div className="flex flex-wrap items-center gap-x-3.5 gap-y-2 pt-0.5">
          <span className="inline-flex items-center gap-2 text-xs" style={{ color: "var(--fg-soft)" }}>
            <CoverageStrip count={story.coverage.reported.length} total={totalOutlets} />
            <span className="tabular font-medium">
              {story.coverage.reported.length} of {totalOutlets} sources
            </span>
          </span>
          {story.first_reported_by && (
            <span className="text-xs" style={{ color: "var(--muted)" }}>
              <span className="opacity-50">·</span> first reported by{" "}
              <span style={{ color: "var(--fg-soft)" }}>{story.first_reported_by.name}</span>,{" "}
              <span className="tabular">{timeAgo(story.first_reported_at)}</span>
            </span>
          )}
        </div>

        {story.is_single_source && (
          <p
            className="border-l-2 py-0.5 pl-3 text-xs italic leading-relaxed"
            style={{ borderColor: "var(--border)", color: "var(--muted)" }}
          >
            Reported by only 1 of {totalOutlets} tracked outlets. Not yet corroborated.
          </p>
        )}

        <div className="pt-1.5">
          <StoryActions
            storyId={story.id}
            sources={story.sources.map((s) => ({
              name: s.outlet.name,
              url: s.url,
              published_at: s.published_at,
            }))}
          />
        </div>
      </header>

      <RecordVisit storyId={story.id} />

      {story.summary && (
        <section className="mt-10">
          <p
            className={`font-display text-[1.24rem] leading-[1.62] ${
              /^[A-Za-z]/.test(story.summary) ? "dropcap" : ""
            }`}
            style={{ color: "var(--fg)" }}
          >
            {story.summary}
          </p>

          <p className="mt-4 text-[11px] leading-relaxed" style={{ color: "var(--muted)" }}>
            Machine-generated from the outlets&rsquo; coverage. Read the originals below.
          </p>
        </section>
      )}

      {(story.coverage_detail || story.coverage_diff) && story.sources.length >= 2 && (
        <section className="mt-10">
          <div
            className="panel overflow-hidden px-6 py-6 sm:px-8 sm:py-7"
            style={{ borderTop: "3px solid var(--accent)" }}
          >
            <span className="kicker" style={{ color: "var(--accent-ink)" }}>
              How the coverage differs
            </span>
            <p
              className={
                story.coverage_detail
                  ? "mt-3 text-[1.02rem] leading-[1.72]"
                  : "font-display mt-3 text-[1.15rem] italic leading-[1.55]"
              }
              style={{ color: "var(--fg)" }}
            >
              {story.coverage_detail || story.coverage_diff}
            </p>
          </div>
        </section>
      )}

      {story.sources.length >= 2 && (
        <section className="mt-9">
          <SectionLabel>How each outlet headlined it</SectionLabel>
          <p className="mb-1 text-[11px]" style={{ color: "var(--muted)" }}>
            In order of publication — first to report at the top.
          </p>
          <HeadlineComparison sources={story.sources} />
        </section>
      )}

      <section className="mt-9">
        <ReadAtSource sources={story.sources} />
      </section>

      {story.coverage.not_reporting.length > 0 && (
        <section className="mt-9">
          <SectionLabel>Not reporting this</SectionLabel>
          <p className="text-sm leading-relaxed" style={{ color: "var(--muted)" }}>
            {story.coverage.not_reporting.join(" · ")}
          </p>
        </section>
      )}

      {flagged.length > 0 && (
        <section className="mt-9">
          <SectionLabel>Loaded-language flags</SectionLabel>
          <ul className="space-y-2 text-sm leading-relaxed" style={{ color: "var(--fg-soft)" }}>
            {flagged.map((f, i) => (
              <li key={i}>
                <mark className="loaded">{f}</mark>
              </li>
            ))}
          </ul>
          <p className="mt-3 text-[11px]" style={{ color: "var(--muted)" }}>
            Flagged by a transparent lexicon scorer. See{" "}
            <Link
              href="/how-it-works"
              className="underline decoration-1 underline-offset-2 transition-colors hover:text-[var(--fg)]"
            >
              How it works
            </Link>
            .
          </p>
        </section>
      )}
    </article>
  );
}
