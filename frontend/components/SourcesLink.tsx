"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { listOutlets } from "@/lib/api";
import type { Outlet } from "@/lib/types";

function readCookie(): string | undefined {
  const m = document.cookie.match(/(?:^|;\s*)tn_country=([^;]+)/);
  return m ? decodeURIComponent(m[1]) : undefined;
}

const SHOWN = 5;

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
    <p
      className="mt-1 text-[0.7rem] leading-relaxed"
      style={{ color: "var(--muted)" }}
      title={outlets.map((o) => o.name).join(", ")}
    >
      {shown.map((o) => o.name).join("  ·  ")}
      {extra > 0 && (
        <>
          {"  ·  "}
          <Link href="/sources" className="underline-offset-2 hover:underline">
            {extra} more
          </Link>
        </>
      )}
    </p>
  );
}
