"use client";

import Link from "next/link";
import { useState } from "react";
import { CompareError, compareArticles } from "@/lib/api";
import type { CompareResult, OutletLean } from "@/lib/types";

const MAX_URLS = 4;

export default function ComparePage() {
  const [urls, setUrls] = useState<string[]>(["", ""]);
  const [status, setStatus] = useState<"idle" | "loading">("idle");
  const [error, setError] = useState<string | null>(null);
  const [failed, setFailed] = useState<{ url: string; reason: string }[] | null>(null);
  const [result, setResult] = useState<CompareResult | null>(null);

  const setUrl = (i: number, v: string) =>
    setUrls((u) => u.map((x, j) => (j === i ? v : x)));
  const addField = () => setUrls((u) => (u.length < MAX_URLS ? [...u, ""] : u));
  const removeField = (i: number) =>
    setUrls((u) => (u.length > 2 ? u.filter((_, j) => j !== i) : u));

  const filled = urls.map((u) => u.trim()).filter(Boolean);
  const canRun = filled.length >= 2 && status === "idle";

  async function run(e: React.FormEvent) {
    e.preventDefault();
    if (!canRun) return;
    setStatus("loading");
    setError(null);
    setFailed(null);
    setResult(null);
    try {
      setResult(await compareArticles(filled));
    } catch (err) {
      if (err instanceof CompareError) {
        setError(err.message);
        setFailed(err.failed ?? null);
      } else {
        setError("Something went wrong. Please try again.");
      }
    } finally {
      setStatus("idle");
    }
  }

  return (
    <div className="reveal mx-auto max-w-[46rem]">
      <span className="kicker">Side by side</span>
      <h1 className="font-display mt-2 text-[2.25rem] leading-tight">Compare coverage</h1>
      <p
        className="mt-3 max-w-[60ch] text-[1.02rem] leading-relaxed"
        style={{ color: "var(--fg-soft)" }}
      >
        Paste the links to two or more articles about the same event. TrueNews reads each one,
        lays the versions side by side, and reads how every outlet has angled the story &mdash;
        against neutral wire-service style, not just against each other. The articles are read
        once and discarded; nothing is stored.
      </p>

      <form onSubmit={run} className="mt-8 space-y-3">
        {urls.map((u, i) => (
          <div key={i} className="flex items-center gap-2">
            <span
              className="tabular w-4 shrink-0 text-xs font-semibold"
              style={{ color: "var(--muted)" }}
            >
              {i + 1}
            </span>
            <input
              type="url"
              inputMode="url"
              value={u}
              onChange={(e) => setUrl(i, e.target.value)}
              placeholder="https://…"
              className="card w-full rounded-md px-3 py-2 text-sm outline-none transition-colors focus:border-[var(--accent)]"
              style={{ color: "var(--fg)" }}
            />
            {urls.length > 2 && (
              <button
                type="button"
                onClick={() => removeField(i)}
                aria-label={`Remove link ${i + 1}`}
                className="shrink-0 px-1 text-lg leading-none transition-colors hover:text-[var(--fg)]"
                style={{ color: "var(--muted)" }}
              >
                &times;
              </button>
            )}
          </div>
        ))}

        <div className="flex items-center justify-between pt-1">
          {urls.length < MAX_URLS ? (
            <button
              type="button"
              onClick={addField}
              className="text-xs underline decoration-1 underline-offset-2 transition-colors hover:text-[var(--fg)]"
              style={{ color: "var(--muted)" }}
            >
              + another link
            </button>
          ) : (
            <span />
          )}

          <button
            type="submit"
            disabled={!canRun}
            className="rounded-md px-4 py-2 text-sm font-medium transition-opacity disabled:opacity-40"
            style={{ background: "var(--accent)", color: "var(--card)" }}
          >
            {status === "loading" ? "Comparing…" : "Compare"}
          </button>
        </div>
      </form>

      {status === "loading" && (
        <p
          className="mt-6 flex items-center gap-2 text-sm"
          style={{ color: "var(--muted)" }}
        >
          <span
            className="inline-block h-3 w-3 animate-spin rounded-full border-2 border-current border-t-transparent"
            aria-hidden
          />
          Reading the articles and comparing — this usually takes 10&ndash;25 seconds. The
          server may need a moment to wake first.
        </p>
      )}

      {error && (
        <div
          className="mt-6 rounded-md border p-4 text-sm"
          style={{ borderColor: "var(--accent)", color: "var(--fg-soft)" }}
        >
          {error}
          {failed && failed.length > 0 && (
            <ul className="mt-2 space-y-1 text-xs" style={{ color: "var(--muted)" }}>
              {failed.map((f) => (
                <li key={f.url}>
                  <span className="break-all">{f.url}</span> — {f.reason}
                </li>
              ))}
            </ul>
          )}
        </div>
      )}

      {result && <Result data={result} />}

      <p
        className="mt-12 max-w-[60ch] border-t hairline pt-4 text-[11px] leading-relaxed"
        style={{ color: "var(--muted)" }}
      >
        The lean read is generated automatically from each article&rsquo;s own words and shows
        the quotes it is based on. It describes how one story was told by one outlet on one day
        &mdash; not a permanent rating of the outlet. See{" "}
        <Link
          href="/how-it-works"
          className="underline decoration-1 underline-offset-2 transition-colors hover:text-[var(--fg)]"
        >
          How it works
        </Link>
        .
      </p>
    </div>
  );
}

function Result({ data }: { data: CompareResult }) {
  const unrelated = data.relation === "unrelated";
  const allEvenHanded =
    !unrelated &&
    data.sources.every((s) => !s.lean || s.lean.lean.toLowerCase() === "even-handed") &&
    data.unmatched_leans.every((l) => l.lean.toLowerCase() === "even-handed");

  return (
    <div className="reveal mt-10 space-y-9">
      {data.via === "offline" && (
        <p
          className="rounded-md border p-3 text-xs leading-relaxed"
          style={{ borderColor: "var(--border)", color: "var(--muted)" }}
        >
          The comparison model is busy right now, so this is a plain word-level read only. Try
          again shortly for the full side-by-side.
        </p>
      )}

      {data.relation_note && (
        <p
          className="rounded-md border-l-2 py-1 pl-4 text-sm leading-relaxed"
          style={{
            borderColor: unrelated ? "var(--muted)" : "var(--accent)",
            color: unrelated ? "var(--fg-soft)" : "var(--fg)",
          }}
        >
          <span className="kicker mr-2">
            {unrelated ? "Not the same story" : data.relation === "related" ? "Related" : "Same event"}
          </span>
          {data.relation_note}
        </p>
      )}

      <section>
        <div className="panel px-6 py-6 sm:px-8 sm:py-7" style={{ borderTop: "3px solid var(--accent)" }}>
          <span className="kicker" style={{ color: "var(--accent-ink)" }}>
            {unrelated ? "What each is about" : "The shared account"}
          </span>
          <p className="mt-3 text-[1.02rem] leading-[1.72]" style={{ color: "var(--fg)" }}>
            {data.shared_facts}
          </p>
        </div>
      </section>

      <section>
        <SectionLabel>
          {unrelated
            ? "Each piece"
            : allEvenHanded
              ? "How each outlet reports it"
              : "How each outlet angles it"}
        </SectionLabel>
        <ul className="space-y-4">
          {data.sources.map((s) => (
            <li key={s.url}>
              <LeanCard
                outlet={s.outlet}
                url={s.url}
                title={s.title}
                lean={s.lean}
              />
            </li>
          ))}
          {data.unmatched_leans.map((l) => (
            <li key={l.outlet}>
              <LeanCard outlet={l.outlet} lean={l} />
            </li>
          ))}
        </ul>
        {allEvenHanded && (
          <p className="mt-3 text-xs" style={{ color: "var(--muted)" }}>
            None of these articles reads as slanted — the comparison found straight reporting
            across the board.
          </p>
        )}
      </section>

      {!unrelated && data.consensus_slant && (
        <section>
          <div
            className="rounded-md border-l-2 py-1 pl-4"
            style={{ borderColor: "var(--accent)" }}
          >
            <span className="kicker" style={{ color: "var(--accent-ink)" }}>
              Shared slant
            </span>
            <p className="mt-1.5 text-[0.98rem] leading-relaxed" style={{ color: "var(--fg)" }}>
              {data.consensus_slant}
            </p>
          </div>
        </section>
      )}

      {data.differences.length > 0 && (
        <section>
          <SectionLabel>Where they diverge</SectionLabel>
          <Bullets items={data.differences} />
        </section>
      )}

      {data.agreements.length > 0 && (
        <section>
          <SectionLabel>Where they agree</SectionLabel>
          <Bullets items={data.agreements} muted />
        </section>
      )}

      {data.blind_spots.length > 0 && (
        <section>
          <SectionLabel>Likely blind spots</SectionLabel>
          <p className="mb-2 text-[11px]" style={{ color: "var(--muted)" }}>
            Angles or voices a reader would want that none of these articles supply.
          </p>
          <Bullets items={data.blind_spots} />
        </section>
      )}

      {data.takeaway && (
        <section>
          <div className="card rounded-md px-5 py-4">
            <span className="kicker">Takeaway</span>
            <p className="mt-2 text-[0.98rem] leading-relaxed" style={{ color: "var(--fg-soft)" }}>
              {data.takeaway}
            </p>
          </div>
        </section>
      )}
    </div>
  );
}

const CONF_DOT: Record<string, string> = {
  high: "var(--accent)",
  medium: "var(--fg-soft)",
  low: "var(--muted)",
};

function LeanCard({
  outlet,
  url,
  title,
  lean,
}: {
  outlet: string;
  url?: string;
  title?: string;
  lean: OutletLean | null;
}) {
  return (
    <div className="card rounded-md px-5 py-4">
      <div className="flex flex-wrap items-baseline justify-between gap-x-3 gap-y-1">
        <span className="font-display text-[1.08rem]" style={{ color: "var(--fg)" }}>
          {url ? (
            <a
              href={url}
              target="_blank"
              rel="noopener noreferrer"
              className="transition-colors hover:text-[var(--accent)]"
            >
              {outlet}
            </a>
          ) : (
            outlet
          )}
        </span>
        {lean &&
          (lean.lean.toLowerCase() === "even-handed" ? (
            <span className="text-xs" style={{ color: "var(--muted)" }}>
              Even-handed
            </span>
          ) : (
            <span
              className="inline-flex items-center gap-1.5 text-xs font-medium"
              style={{ color: "var(--fg-soft)" }}
            >
              <span
                className="inline-block h-1.5 w-1.5 rounded-full"
                style={{ background: CONF_DOT[lean.confidence] ?? "var(--muted)" }}
                title={`${lean.confidence} confidence`}
              />
              {lean.lean}
            </span>
          ))}
      </div>

      {title && (
        <p className="mt-1 text-xs italic" style={{ color: "var(--muted)" }}>
          &ldquo;{title}&rdquo;
        </p>
      )}

      {lean && lean.evidence.length > 0 && (
        <ul className="mt-3 space-y-1.5 text-[0.85rem] leading-relaxed" style={{ color: "var(--fg-soft)" }}>
          {lean.evidence.map((q, i) => (
            <li key={i} className="border-l-2 pl-3" style={{ borderColor: "var(--border)" }}>
              &ldquo;{q}&rdquo;
            </li>
          ))}
        </ul>
      )}

      {lean && lean.loaded_language.length > 0 && (
        <p className="mt-3 flex flex-wrap gap-x-1 gap-y-1 text-xs" style={{ color: "var(--muted)" }}>
          <span className="mr-1">Loaded wording:</span>
          {lean.loaded_language.map((f, i) => (
            <mark key={i} className="loaded">
              {f}
            </mark>
          ))}
        </p>
      )}
    </div>
  );
}

function SectionLabel({ children }: { children: React.ReactNode }) {
  return (
    <div className="mb-3 flex items-center gap-3">
      <span className="kicker whitespace-nowrap">{children}</span>
      <span className="h-px flex-1" style={{ background: "var(--border)" }} />
    </div>
  );
}

function Bullets({ items, muted }: { items: string[]; muted?: boolean }) {
  return (
    <ul
      className="space-y-2 text-[0.95rem] leading-relaxed"
      style={{ color: muted ? "var(--fg-soft)" : "var(--fg)" }}
    >
      {items.map((t, i) => (
        <li key={i} className="flex gap-2.5">
          <span aria-hidden style={{ color: "var(--accent)" }}>
            &bull;
          </span>
          <span>{t}</span>
        </li>
      ))}
    </ul>
  );
}
