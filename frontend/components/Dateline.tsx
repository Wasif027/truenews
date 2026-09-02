"use client";

import { useEffect, useState } from "react";

/** The masthead date, in the reader's own timezone. Rendered client-side —
 *  server-rendered it would be UTC, and cached, so it drifts a day off. */
export function Dateline() {
  const [date, setDate] = useState("");

  useEffect(() => {
    setDate(
      new Date().toLocaleDateString(undefined, {
        weekday: "long",
        day: "numeric",
        month: "long",
        year: "numeric",
      }),
    );
  }, []);

  return (
    <time className="kicker hidden whitespace-nowrap sm:inline" suppressHydrationWarning>
      {date}
    </time>
  );
}
