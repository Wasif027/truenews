"use client";

import { useEffect } from "react";

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error(error);
  }, [error]);

  return (
    <div className="reveal py-24 text-center">
      <span className="kicker" style={{ color: "var(--accent)" }}>
        Something went wrong
      </span>
      <h1 className="font-display mt-2 text-3xl">This page didn&rsquo;t load</h1>
      <p className="mx-auto mt-2 max-w-sm text-sm" style={{ color: "var(--muted)" }}>
        A temporary hiccup on our end. Try again in a moment.
      </p>
      <button
        onClick={reset}
        className="mt-6 inline-flex items-center gap-1.5 text-sm font-medium transition-colors hover:opacity-80"
        style={{ color: "var(--accent)" }}
      >
        Try again
      </button>
    </div>
  );
}
