"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { Suspense, useEffect, useState } from "react";
import { useAuth } from "@/components/AuthProvider";
import { StoryCard } from "@/components/StoryCard";
import { myHistory, myLikes, mySaves } from "@/lib/api";
import type { StoryListItem } from "@/lib/types";

type Tab = "saved" | "liked" | "history";
const HISTORY_KEPT = 20;

const TABS: { key: Tab; label: string; load: () => Promise<StoryListItem[]>; empty: string }[] = [
  { key: "saved", label: "Saved", load: mySaves, empty: "Nothing saved yet. Open a story and press Save." },
  { key: "liked", label: "Liked", load: myLikes, empty: "Nothing liked yet. Open a story and press Like." },
  { key: "history", label: "Recent history", load: myHistory, empty: "No reading history yet." },
];

export default function MePage() {
  return (
    <Suspense fallback={null}>
      <MeContent />
    </Suspense>
  );
}

function MeContent() {
  const { user, loading } = useAuth();
  const spTab = useSearchParams().get("tab");
  const [tab, setTab] = useState<Tab>("saved");
  const [items, setItems] = useState<StoryListItem[]>([]);
  const [fetching, setFetching] = useState(true);

  useEffect(() => {
    if (spTab && TABS.some((t) => t.key === spTab)) setTab(spTab as Tab);
  }, [spTab]);

  useEffect(() => {
    if (!user) return;
    setFetching(true);
    TABS.find((t) => t.key === tab)!
      .load()
      .then(setItems)
      .catch(() => setItems([]))
      .finally(() => setFetching(false));
  }, [tab, user]);

  if (loading) return null;

  if (!user) {
    return (
      <div className="reveal py-16 text-center">
        <span className="kicker">Members only</span>
        <p className="mx-auto mt-2 max-w-xs text-sm" style={{ color: "var(--muted)" }}>
          <Link href="/login" className="font-medium" style={{ color: "var(--accent)" }}>
            Log in
          </Link>{" "}
          to see your saved stories and reading history.
        </p>
      </div>
    );
  }

  const active = TABS.find((t) => t.key === tab)!;

  return (
    <div className="reveal mx-auto max-w-[46rem]">
      <span className="kicker">Your account</span>
      <h1 className="font-display mt-1.5 text-[1.75rem]">{user.username}</h1>

      <div className="mb-6 mt-5 flex gap-6 border-b text-sm hairline">
        {TABS.map((t) => (
          <button
            key={t.key}
            onClick={() => setTab(t.key)}
            className="relative pb-2.5 transition-colors"
            style={{ color: tab === t.key ? "var(--fg)" : "var(--muted)" }}
            aria-current={tab === t.key ? "true" : undefined}
          >
            <span className={tab === t.key ? "font-medium" : ""}>{t.label}</span>
            <span
              className="absolute -bottom-px left-0 h-0.5 rounded-full transition-all duration-200"
              style={{ width: tab === t.key ? "100%" : "0%", background: "var(--accent)" }}
            />
          </button>
        ))}
      </div>

      {tab === "history" && (
        <p className="-mt-2 mb-5 text-xs" style={{ color: "var(--muted)" }}>
          TrueNews keeps only your {HISTORY_KEPT} most recently opened stories.
        </p>
      )}

      {fetching ? (
        <div className="divide-y hairline">
          {Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="space-y-2.5 py-5">
              <div className="h-3 w-40 rounded shimmer" style={{ background: "var(--border)" }} />
              <div className="h-5 w-4/5 rounded shimmer" style={{ background: "var(--border)" }} />
            </div>
          ))}
        </div>
      ) : items.length === 0 ? (
        <p className="py-10 text-center text-sm" style={{ color: "var(--muted)" }}>
          {active.empty}
        </p>
      ) : (
        <>
          <div className="divide-y hairline">
            {items.map((s) => (
              <StoryCard key={s.id} story={s} showCountry />
            ))}
          </div>
        </>
      )}
    </div>
  );
}
