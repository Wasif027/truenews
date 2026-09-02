"use client";

import { useEffect, useState } from "react";
import { type Country, listCountries } from "@/lib/api";

function readCookie(): string | null {
  const m = document.cookie.match(/(?:^|;\s*)tn_country=([^;]+)/);
  return m ? decodeURIComponent(m[1]) : null;
}

export function CountrySwitcher() {
  const [countries, setCountries] = useState<Country[]>([]);
  const [current, setCurrent] = useState<string>("");

  useEffect(() => {
    listCountries()
      .then((list) => {
        const sorted = [...list].sort((a, b) => a.name.localeCompare(b.name));
        setCountries(sorted);
        setCurrent(readCookie() ?? list[0]?.code ?? "");
      })
      .catch(() => setCountries([]));
  }, []);

  if (countries.length < 2) return null;

  function pick(code: string) {
    if (!code || code === current) return;
    document.cookie = `tn_country=${code}; path=/; max-age=${60 * 60 * 24 * 365}`;
    // Full load: the whole page keys off the country, so a clean reload is
    // simpler and more reliable than router-cache juggling for a rare action.
    window.location.assign("/");
  }

  return (
    <label className="flex items-center gap-2 text-xs" style={{ color: "var(--muted)" }}>
      <span className="kicker">Country</span>
      <span className="relative">
        <select
          value={current}
          onChange={(e) => pick(e.target.value)}
          className="cursor-pointer appearance-none rounded-md border bg-transparent py-1 pl-2.5 pr-7 text-xs font-medium transition-colors hairline hover:border-[var(--fg-soft)] focus:border-[var(--accent)] focus:outline-none"
          style={{ color: "var(--fg)" }}
        >
          {countries.map((c) => (
            <option key={c.code} value={c.code} style={{ background: "var(--card)", color: "var(--fg)" }}>
              {c.name}
            </option>
          ))}
        </select>
        <span
          className="pointer-events-none absolute right-2 top-1/2 -translate-y-1/2 text-[0.6rem]"
          style={{ color: "var(--muted)" }}
          aria-hidden
        >
          ▾
        </span>
      </span>
    </label>
  );
}
