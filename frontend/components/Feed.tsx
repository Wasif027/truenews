"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { PAGE_SIZE, type StoryQuery, listStories } from "@/lib/api";
import type { StoryListItem } from "@/lib/types";
import { LeadStory, StoryCard } from "./StoryCard";

const POLL_MS = 90_000;

export function Feed({
  initial,
  query,
  showLead,
}: {
  initial: StoryListItem[];
  query: StoryQuery;
  showLead: boolean;
}) {
  const [items, setItems] = useState(initial);
  const [pending, setPending] = useState<StoryListItem[]>([]);
  const [done, setDone] = useState(initial.length < PAGE_SIZE);
  const [loading, setLoading] = useState(false);

  const sentinel = useRef<HTMLDivElement>(null);
  const seen = useRef(new Set(initial.map((s) => s.id)));
  const dismissed = useRef(new Set<number>());

  const loadMore = useCallback(async () => {
    if (loading || done) return;
    setLoading(true);
    try {
      const next = await listStories(query, items.length);
      next.forEach((s) => seen.current.add(s.id));
      setItems((cur) => [...cur, ...next]);
      if (next.length < PAGE_SIZE) setDone(true);
    } catch {
      setDone(true);
    } finally {
      setLoading(false);
    }
  }, [loading, done, query, items.length]);

  // infinite scroll
  useEffect(() => {
    const el = sentinel.current;
    if (!el || done) return;
    const io = new IntersectionObserver((e) => e[0].isIntersecting && loadMore(), {
      rootMargin: "800px",
    });
    io.observe(el);
    return () => io.disconnect();
  }, [loadMore, done]);

  // poll for stories that appeared since the page loaded
  useEffect(() => {
    const poll = async () => {
      if (document.hidden) return;
      try {
        const fresh = await listStories(query, 0);
        const fresh_new = fresh.filter(
          (s) => !seen.current.has(s.id) && !dismissed.current.has(s.id),
        );
        if (fresh_new.length) {
          setPending((p) => {
            const have = new Set(p.map((s) => s.id));
            return [...fresh_new.filter((s) => !have.has(s.id)), ...p];
          });
        }
      } catch {
        /* offline / API down: try again next tick */
      }
    };
    const id = setInterval(poll, POLL_MS);
    return () => clearInterval(id);
  }, [query]);

  const showPending = () => {
    setItems((cur) => {
      const have = new Set(cur.map((s) => s.id));
      const add = pending.filter((s) => !have.has(s.id));
      add.forEach((s) => seen.current.add(s.id));
      return [...add, ...cur];
    });
    setPending([]);
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  const dismissPending = () => {
    pending.forEach((s) => dismissed.current.add(s.id));
    setPending([]);
  };

  // The hero slot is the shop window — give it the hottest story that actually
  // has coverage to compare, not a lone-outlet report that happens to rank top.
  const leadIdx = showLead
    ? Math.max(0, items.findIndex((s) => !s.is_single_source))
    : -1;
  const lead = leadIdx >= 0 ? items[leadIdx] : undefined;
  const list = lead ? items.filter((_, i) => i !== leadIdx) : items;

  return (
    <div>
      {pending.length > 0 && (
        <div className="pointer-events-none sticky top-3 z-20 mb-3 flex justify-center">
          <div
            className="pill-in pointer-events-auto flex items-center gap-1 rounded-full border py-1 pl-4 pr-1.5 text-xs font-medium"
            style={{
              background: "var(--card)",
              borderColor: "var(--accent)",
              color: "var(--accent)",
              boxShadow: "var(--shadow)",
            }}
          >
            <button
              onClick={showPending}
              className="flex items-center gap-1.5 py-0.5 active:scale-[0.97]"
            >
              <span
                className="inline-block h-1.5 w-1.5 rounded-full"
                style={{ background: "var(--accent)" }}
              />
              {pending.length === 1 ? "1 new story" : `${pending.length} new stories`}
            </button>
            <button
              onClick={dismissPending}
              aria-label="Dismiss new stories"
              className="flex h-5 w-5 items-center justify-center rounded-full text-sm leading-none transition-colors hover:bg-[var(--accent-weak)]"
            >
              &times;
            </button>
          </div>
        </div>
      )}

      <div className="stagger">
        {showLead && lead && (
          <div style={{ "--i": 0 } as React.CSSProperties}>
            <LeadStory story={lead} />
          </div>
        )}
        <div className={showLead ? "border-t hairline" : ""}>
          {list.map((s, i) => (
            <div
              key={s.id}
              className="border-t hairline first:border-t-0"
              style={{ "--i": Math.min(i + 1, 12) } as React.CSSProperties}
            >
              <StoryCard story={s} />
            </div>
          ))}
        </div>
      </div>

      <div ref={sentinel} aria-hidden className="h-px" />

      <div
        className="border-t hairline py-8 text-center text-xs"
        style={{ color: "var(--muted)" }}
      >
        {loading && <span className="tabular">Loading more…</span>}
        {!loading && !done && (
          <button
            onClick={loadMore}
            className="font-medium transition-colors hover:text-[var(--fg)]"
          >
            Load more stories
          </button>
        )}
        {done && items.length > 0 && (
          <span>
            You&rsquo;ve reached the end · <span className="tabular">{items.length}</span> stories
          </span>
        )}
      </div>
    </div>
  );
}
