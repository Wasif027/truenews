"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { listOutlets } from "@/lib/api";
import type { Outlet } from "@/lib/types";

function readCookie(): string | undefined {
  const m = document.cookie.match(/(?:^|;\s*)tn_country=([^;]+)/);
  return m ? decodeURIComponent(m[1]) : undefined;
}

const SHOWN = 7;

export function SourcesLink() {
  const [outlets, setOutlets] = useState<Outlet[]>([]);

  useEffect(() => {
    listOutlets(readCookie())
      .then(setOutlets)
      .catch(() => setOutlets([]));
  }, []);

  if (!outlets.length) return null;

  const shown = outlets.slice(0, SHOWN);
  const extra = outlets.length - shown.length;

  return (
    <p className="pt-1.5 text-xs leading-relaxed" style={{ color: "var(--muted)" }}>
      <span className="kicker mr-1.5">Reading</span>
      {shown.map((o, i) => (
        <span key={o.slug}>
          <a
            href={o.homepage}
            target="_blank"
            rel="noopener noreferrer"
            className="transition-colors hover:text-[var(--fg)]"
          >
            {o.name}
          </a>
          {i < shown.length - 1 && <span className="opacity-40"> · </span>}
        </span>
      ))}
      {extra > 0 && (
        <>
          <span className="opacity-40"> · </span>
          <Link href="/sources" className="transition-colors hover:text-[var(--fg)]">
            +{extra} more
          </Link>
        </>
      )}
    </p>
  );
}
