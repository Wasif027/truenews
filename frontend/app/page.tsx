import { cookies } from "next/headers";
import { Feed } from "@/components/Feed";
import { Filters } from "@/components/Filters";
import { listCategories, listStories } from "@/lib/api";
import type { CategoryCount, StoryListItem } from "@/lib/types";

export const dynamic = "force-dynamic";

type SP = Record<string, string | string[] | undefined>;
const one = (v: string | string[] | undefined) => (Array.isArray(v) ? v[0] : v);

export default async function FeedPage({ searchParams }: { searchParams: SP }) {
  const country = cookies().get("tn_country")?.value;
  const query = {
    country,
    category: one(searchParams.category),
    q: one(searchParams.q),
    sort: (one(searchParams.sort) as "hot" | "new") ?? "hot",
    min_outlets: one(searchParams.min_outlets) === "2" ? 2 : 1,
  };
  const filtered = Boolean(query.q || query.category);
  const showLead = !filtered && query.sort === "hot";

  let stories: StoryListItem[] = [];
  let categories: CategoryCount[] = [];
  let error: string | null = null;

  try {
    [stories, categories] = await Promise.all([
      listStories(query),
      listCategories(country, query.min_outlets),
    ]);
  } catch {
    error = "loading";
  }

  return (
    <div className="reveal">
      <Filters categories={categories} />

      {error && (
        <div className="max-w-xl rounded-md border p-4 text-sm" style={{ borderColor: "var(--border)" }}>
          <span className="kicker mb-1 block" style={{ color: "var(--accent)" }}>
            Stories didn&rsquo;t load
          </span>
          <p style={{ color: "var(--muted)" }}>
            We couldn&rsquo;t reach the news service just now. Give it a moment and{" "}
            <a href="/" className="underline underline-offset-2 hover:text-[var(--fg)]">
              refresh
            </a>
            .
          </p>
        </div>
      )}

      {!error && stories.length === 0 && (
        <div className="py-14 text-center">
          <span className="kicker">Nothing here</span>
          <p className="mx-auto mt-2 max-w-xs text-sm" style={{ color: "var(--muted)" }}>
            {filtered
              ? "No stories match that filter yet. Try another category or clear the search."
              : "No stories for this country yet. Check back after the next update."}
          </p>
        </div>
      )}

      {!error && stories.length > 0 && (
        <Feed
          key={`${country ?? ""}|${query.category ?? ""}|${query.q ?? ""}|${query.sort}|${query.min_outlets}`}
          initial={stories}
          query={query}
          showLead={showLead}
        />
      )}
    </div>
  );
}
