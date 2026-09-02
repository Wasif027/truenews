"use client";

import { useRouter, useSearchParams } from "next/navigation";
import { useState } from "react";
import type { CategoryCount } from "@/lib/types";
import { titleCase } from "@/lib/format";

export function Filters({ categories }: { categories: CategoryCount[] }) {
  const router = useRouter();
  const params = useSearchParams();
  const [q, setQ] = useState(params.get("q") ?? "");

  const active = new Set(
    (params.get("category") ?? "").split(",").filter(Boolean),
  );
  const sort = params.get("sort") ?? "hot";
  const hideSingle = params.get("min_outlets") === "2";

  function apply(next: Record<string, string | null>) {
    const sp = new URLSearchParams(params.toString());
    for (const [k, v] of Object.entries(next)) {
      if (v === null || v === "") sp.delete(k);
      else sp.set(k, v);
    }
    router.push(sp.toString() ? `/?${sp.toString()}` : "/");
  }

  function toggleCat(cat: string) {
    const next = new Set(active);
    if (next.has(cat)) next.delete(cat);
    else next.add(cat);
    apply({ category: [...next].join(",") || null });
  }

  return (
    <div className="mb-8 space-y-3.5">
      <form
        onSubmit={(e) => {
          e.preventDefault();
          apply({ q: q.trim() || null });
        }}
        className="flex items-center gap-2 border-b pb-3 transition-colors hairline focus-within:border-[var(--fg)]"
      >
        <svg
          width="15"
          height="15"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          className="shrink-0 opacity-45"
          aria-hidden
        >
          <circle cx="11" cy="11" r="7" />
          <path d="m20 20-3.5-3.5" />
        </svg>
        <input
          value={q}
          onChange={(e) => setQ(e.target.value)}
          placeholder="Search stories"
          aria-label="Search stories"
          className="w-full bg-transparent text-sm outline-none placeholder:text-[var(--muted)]"
        />
        {q && (
          <button
            type="button"
            onClick={() => {
              setQ("");
              apply({ q: null });
            }}
            className="text-xs transition-colors hover:text-[var(--fg)]"
            style={{ color: "var(--muted)" }}
          >
            Clear
          </button>
        )}
      </form>

      <nav className="-mb-1 flex flex-wrap gap-x-4 gap-y-1.5 text-sm" aria-label="Categories">
        <Tab label="Top" active={active.size === 0} onClick={() => apply({ category: null })} />
        {categories.map((c) => (
          <Tab
            key={c.category}
            label={titleCase(c.category)}
            count={c.count}
            active={active.has(c.category)}
            onClick={() => toggleCat(c.category)}
          />
        ))}
      </nav>

      <div className="flex items-center gap-5 text-xs" style={{ color: "var(--muted)" }}>
        <button
          onClick={() => apply({ sort: sort === "hot" ? "new" : "hot" })}
          className="transition-colors hover:text-[var(--fg)]"
        >
          {sort === "hot" ? "Sorted by pickup" : "Sorted by time"}
        </button>
        <label className="flex cursor-pointer items-center gap-1.5 transition-colors hover:text-[var(--fg)]">
          <input
            type="checkbox"
            checked={hideSingle}
            onChange={(e) => apply({ min_outlets: e.target.checked ? "2" : null })}
            className="h-3 w-3 accent-[var(--accent)]"
          />
          Hide single-source
        </label>
        {active.size > 1 && (
          <span className="tabular" style={{ color: "var(--fg-soft)" }}>
            {active.size} categories
          </span>
        )}
      </div>
    </div>
  );
}

function Tab({
  label,
  count,
  active,
  onClick,
}: {
  label: string;
  count?: number;
  active: boolean;
  onClick: () => void;
}) {
  return (
    <button
      onClick={onClick}
      className="relative pb-1 transition-colors duration-150"
      style={{ color: active ? "var(--fg)" : "var(--muted)" }}
      aria-pressed={active}
    >
      <span className={active ? "font-medium" : ""}>{label}</span>
      {count != null && (
        <span className="tabular ml-1 text-[0.68rem] opacity-55">{count}</span>
      )}
      <span
        className="absolute -bottom-px left-0 h-0.5 rounded-full transition-all duration-200"
        style={{ width: active ? "100%" : "0%", background: "var(--accent)" }}
      />
    </button>
  );
}
