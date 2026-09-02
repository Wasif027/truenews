"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { listOutlets } from "@/lib/api";

function readCookie(): string | undefined {
  const m = document.cookie.match(/(?:^|;\s*)tn_country=([^;]+)/);
  return m ? decodeURIComponent(m[1]) : undefined;
}

export function SourcesLink() {
  const [n, setN] = useState<number | null>(null);

  useEffect(() => {
    listOutlets(readCookie())
      .then((list) => setN(list.length))
      .catch(() => setN(null));
  }, []);

  if (!n) return null;

  return (
    <Link
      href="/sources"
      className="kicker whitespace-nowrap transition-colors hover:text-[var(--fg)]"
      style={{ color: "var(--muted)" }}
    >
      {n} sources
    </Link>
  );
}
