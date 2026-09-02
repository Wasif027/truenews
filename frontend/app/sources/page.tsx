import { cookies } from "next/headers";
import { type Country, listCountries, listOutlets } from "@/lib/api";
import type { Outlet } from "@/lib/types";

export const dynamic = "force-dynamic";
export const metadata = { title: "Sources" };

export default async function SourcesPage() {
  const code = cookies().get("tn_country")?.value;
  const [outlets, countries] = await Promise.all([
    listOutlets(code).catch(() => [] as Outlet[]),
    listCountries().catch(() => [] as Country[]),
  ]);
  const name = countries.find((c) => c.code === code)?.name ?? "Bangladesh";

  return (
    <div className="reveal mx-auto max-w-[44rem]">
      <span className="kicker">Where the news comes from</span>
      <h1 className="font-display mt-2 text-[2.25rem] leading-tight">Sources</h1>
      <p className="mt-3 max-w-[58ch] text-[1.02rem] leading-relaxed" style={{ color: "var(--fg-soft)" }}>
        TrueNews reads the public RSS feeds of these outlets for{" "}
        <span style={{ color: "var(--fg)" }}>{name}</span> — {outlets.length} in all. Change the
        country in the header to see its list. Every headline links back to the outlet&rsquo;s own
        article; nothing else is stored.
      </p>

      {outlets.length === 0 ? (
        <p className="mt-8 text-sm" style={{ color: "var(--muted)" }}>
          Couldn&rsquo;t load the source list right now.
        </p>
      ) : (
        <ul className="mt-8 divide-y border-y hairline">
          {outlets.map((o) => (
            <li key={o.slug} className="py-3">
              <a
                href={o.homepage}
                target="_blank"
                rel="noopener noreferrer"
                className="group flex items-baseline justify-between gap-4"
              >
                <span className="font-display text-[1.08rem] transition-colors group-hover:text-[var(--accent)]">
                  {o.name}
                </span>
                <span className="tabular shrink-0 text-xs" style={{ color: "var(--muted)" }}>
                  {o.homepage.replace(/^https?:\/\/(www\.)?/, "").replace(/\/$/, "")}
                </span>
              </a>
            </li>
          ))}
        </ul>
      )}

      <p className="mt-8 max-w-[58ch] text-xs leading-relaxed" style={{ color: "var(--muted)" }}>
        A country is added once at least three of its outlets have a working, current
        English-language feed. A feed that stops responding is skipped automatically and rejoins
        when it recovers.
      </p>
    </div>
  );
}
