"use client";

import { useState } from "react";
import type { SourceArticle } from "@/lib/types";
import { timeAgo } from "@/lib/format";

export function ReadAtSource({ sources }: { sources: SourceArticle[] }) {
  const [open, setOpen] = useState(sources.length <= 3);
  const sorted = [...sources].sort(
    (a, b) => +new Date(a.published_at) - +new Date(b.published_at),
  );

  return (
    <div>
      <button
        onClick={() => setOpen((v) => !v)}
        className="group flex w-full items-center gap-3"
        aria-expanded={open}
      >
        <span className="kicker whitespace-nowrap">Read at source ({sources.length})</span>
        <span className="h-px flex-1" style={{ background: "var(--border)" }} />
        <span
          className="text-xs font-medium transition-colors group-hover:text-[var(--fg)]"
          style={{ color: "var(--accent)" }}
        >
          {open ? "Hide" : "Show all"}
        </span>
      </button>

      {open && (
        <ul className="mt-3 divide-y hairline border-t hairline">
          {sorted.map((s) => (
            <li key={s.id} className="group flex items-baseline justify-between gap-4 py-3">
              <div className="min-w-0">
                <div className="flex flex-wrap items-center gap-x-2 text-xs" style={{ color: "var(--muted)" }}>
                  <span className="font-medium" style={{ color: "var(--fg)" }}>
                    {s.outlet.name}
                  </span>
                  {s.byline && (
                    <>
                      <span className="opacity-40">·</span>
                      <span className="truncate">{s.byline}</span>
                    </>
                  )}
                  <span className="opacity-40">·</span>
                  <span className="tabular">{timeAgo(s.published_at)}</span>
                </div>
                <p className="mt-0.5 truncate text-sm" style={{ color: "var(--fg-soft)" }}>
                  {s.headline}
                </p>
              </div>
              <a
                href={s.url}
                target="_blank"
                rel="noopener noreferrer"
                className="shrink-0 text-xs font-medium transition-colors hover:text-[var(--fg)]"
                style={{ color: "var(--accent)" }}
              >
                Open <span className="inline-block transition-transform duration-200 group-hover:translate-x-0.5">↗</span>
              </a>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
