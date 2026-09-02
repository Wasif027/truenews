"use client";

import Link from "next/link";
import { useEffect, useRef, useState } from "react";
import { getMyFlags, setLike, setSave } from "@/lib/api";
import { timeAgo } from "@/lib/format";
import { useAuth } from "./AuthProvider";

export type ShareSource = { name: string; url: string; published_at: string };

export function StoryActions({
  storyId,
  sources,
}: {
  storyId: number;
  sources: ShareSource[];
}) {
  const { user, loading } = useAuth();
  const [liked, setLiked] = useState(false);
  const [saved, setSaved] = useState(false);
  const [shareOpen, setShareOpen] = useState(false);

  // The story page is cached, so liked/saved are fetched here per user.
  useEffect(() => {
    if (!user) {
      setLiked(false);
      setSaved(false);
      return;
    }
    getMyFlags(storyId)
      .then((f) => {
        setLiked(f.liked);
        setSaved(f.saved);
      })
      .catch(() => {});
  }, [user, storyId]);
  const [copiedUrl, setCopiedUrl] = useState<string | null>(null);
  const shareRef = useRef<HTMLDivElement>(null);

  // One row per outlet — its first article — ordered first-to-report, matching
  // the comparison list. (Read-at-source lists every individual article.)
  const byOutlet = new Map<string, ShareSource>();
  for (const s of sources) {
    const seen = byOutlet.get(s.name);
    if (!seen || +new Date(s.published_at) < +new Date(seen.published_at)) {
      byOutlet.set(s.name, s);
    }
  }
  const ordered = [...byOutlet.values()].sort(
    (a, b) => +new Date(a.published_at) - +new Date(b.published_at),
  );

  useEffect(() => {
    if (!shareOpen) return;
    const close = (e: MouseEvent) => {
      if (shareRef.current && !shareRef.current.contains(e.target as Node)) setShareOpen(false);
    };
    document.addEventListener("mousedown", close);
    return () => document.removeEventListener("mousedown", close);
  }, [shareOpen]);

  async function toggle(kind: "like" | "save") {
    const cur = kind === "like" ? liked : saved;
    const setLocal = kind === "like" ? setLiked : setSaved;
    setLocal(!cur); // optimistic
    try {
      await (kind === "like" ? setLike : setSave)(storyId, !cur);
    } catch {
      setLocal(cur); // revert
    }
  }

  async function copy(url: string) {
    await navigator.clipboard.writeText(url).catch(() => {});
    setCopiedUrl(url);
    setTimeout(() => setCopiedUrl((c) => (c === url ? null : c)), 1500);
  }

  const cls =
    "inline-flex items-center gap-1.5 text-xs font-medium transition-colors hover:text-[var(--fg)] active:scale-[0.96]";

  return (
    <div className="flex items-center gap-5">
      {loading ? (
        <span className="h-4 w-24 rounded shimmer" style={{ background: "var(--border)" }} />
      ) : user ? (
        <>
          <button
            onClick={() => toggle("like")}
            className={cls}
            style={{ color: liked ? "var(--accent)" : "var(--muted)" }}
            aria-pressed={liked}
          >
            <span className="text-sm leading-none">{liked ? "♥" : "♡"}</span>
            {liked ? "Liked" : "Like"}
          </button>
          <button
            onClick={() => toggle("save")}
            className={cls}
            style={{ color: saved ? "var(--accent)" : "var(--muted)" }}
            aria-pressed={saved}
          >
            <span className="text-sm leading-none">{saved ? "★" : "☆"}</span>
            {saved ? "Saved" : "Save"}
          </button>
        </>
      ) : (
        <Link href="/login" className={cls} style={{ color: "var(--muted)" }}>
          Log in to like &amp; save
        </Link>
      )}

      <div className="relative" ref={shareRef}>
        <button
          onClick={() => setShareOpen((v) => !v)}
          className={cls}
          style={{ color: "var(--muted)" }}
          aria-haspopup="menu"
          aria-expanded={shareOpen}
        >
          Share <span aria-hidden>↗</span>
        </button>
        {shareOpen && (
          <div
            className="pill-in card absolute right-0 z-30 mt-2.5 w-72 overflow-hidden rounded-lg py-1.5"
            style={{ boxShadow: "var(--shadow)" }}
            role="menu"
          >
            <p className="kicker px-3.5 pb-1.5 pt-1">Select a source to copy its link</p>
            {ordered.map((s, i) => {
              const isCopied = copiedUrl === s.url;
              return (
                <button
                  key={s.url}
                  onClick={() => copy(s.url)}
                  role="menuitem"
                  className="flex w-full items-baseline justify-between gap-3 px-3.5 py-2 text-left text-sm transition-colors hover:bg-[var(--surface-2)]"
                >
                  <span className="min-w-0">
                    <span className="tabular mr-1.5 text-xs" style={{ color: "var(--muted)" }}>
                      {i + 1}
                    </span>
                    <span style={{ color: "var(--fg)" }}>{s.name}</span>
                  </span>
                  <span
                    className="shrink-0 text-xs"
                    style={{ color: isCopied ? "var(--accent)" : "var(--muted)" }}
                  >
                    {isCopied ? "Copied ✓" : timeAgo(s.published_at)}
                  </span>
                </button>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
