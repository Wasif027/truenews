import { cookies } from "next/headers";
import { getStatus, listCountries } from "@/lib/api";
import { timeAgo } from "@/lib/format";

export const dynamic = "force-dynamic";
export const metadata = { title: "Pipeline status" };

export default async function StatusPage() {
  const code = cookies().get("tn_country")?.value;
  const [status, countries] = await Promise.all([
    getStatus(code).catch(() => null),
    listCountries().catch(() => []),
  ]);

  if (!status) {
    return (
      <div className="reveal py-16 text-center">
        <span className="kicker">Offline</span>
        <p className="mx-auto mt-2 max-w-xs text-sm" style={{ color: "var(--muted)" }}>
          The API isn&rsquo;t responding right now.
        </p>
      </div>
    );
  }

  const name = countries.find((c) => c.code === status.country)?.name ?? status.country.toUpperCase();
  const fresh = status.last_story_update
    ? timeAgo(status.last_story_update)
    : "never";
  // Ingestion is hourly; only flag it if we're well past a missed run.
  const stale =
    status.last_story_update &&
    Date.now() - new Date(status.last_story_update).getTime() > 150 * 60 * 1000;

  const rows: [string, string][] = [
    ["Country", name],
    ["Tracked outlets", String(status.outlets)],
    ["Articles held", status.articles.toLocaleString("en-US")],
    ["Stories", status.stories.toLocaleString("en-US")],
    ["Clustering window", `${status.window_hours} hours`],
    ["Similarity threshold", status.sim_threshold.toFixed(2)],
    ["Summaries", status.llm_enabled ? "model-backed" : "offline extractive"],
  ];

  return (
    <div className="reveal mx-auto max-w-[40rem]">
      <span className="kicker">System</span>
      <h1 className="font-display mt-1.5 text-[2rem]">Pipeline status</h1>

      <div
        className="mt-6 flex items-center gap-2.5 rounded-md border p-3 text-sm"
        style={{ borderColor: "var(--border)" }}
      >
        <span
          className="inline-block h-2 w-2 rounded-full"
          style={{ background: stale ? "var(--muted)" : "var(--accent)" }}
        />
        <span style={{ color: "var(--fg-soft)" }}>
          Last update <span className="tabular font-medium">{fresh}</span>
          {stale && " — an update may have been missed"}
        </span>
      </div>

      <dl className="mt-6 divide-y border-y hairline">
        {rows.map(([k, v]) => (
          <div key={k} className="flex items-center justify-between py-3 text-sm">
            <dt style={{ color: "var(--muted)" }}>{k}</dt>
            <dd className="tabular font-medium" style={{ color: "var(--fg-soft)" }}>
              {v}
            </dd>
          </div>
        ))}
      </dl>

      <p className="mt-4 max-w-[60ch] text-xs leading-relaxed" style={{ color: "var(--muted)" }}>
        Ingestion runs about once an hour on a scheduled job: fetch new articles, cluster
        them by story, then summarise and compare the coverage.
      </p>
    </div>
  );
}
