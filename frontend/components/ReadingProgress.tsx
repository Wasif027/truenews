"use client";

import { useEffect, useRef } from "react";

/** Hairline scroll-progress indicator pinned to the top of the viewport.
 *  Transform-only (GPU); no work beyond a rAF-throttled scroll listener. */
export function ReadingProgress() {
  const bar = useRef<HTMLDivElement>(null);

  useEffect(() => {
    let frame = 0;
    const update = () => {
      frame = 0;
      const doc = document.documentElement;
      const max = doc.scrollHeight - doc.clientHeight;
      const pct = max > 0 ? Math.min(1, doc.scrollTop / max) : 0;
      if (bar.current) bar.current.style.transform = `scaleX(${pct})`;
    };
    const onScroll = () => {
      if (!frame) frame = requestAnimationFrame(update);
    };
    update();
    window.addEventListener("scroll", onScroll, { passive: true });
    window.addEventListener("resize", onScroll, { passive: true });
    return () => {
      window.removeEventListener("scroll", onScroll);
      window.removeEventListener("resize", onScroll);
      if (frame) cancelAnimationFrame(frame);
    };
  }, []);

  return (
    <div
      aria-hidden
      className="pointer-events-none fixed inset-x-0 top-0 z-40 h-[2px]"
      style={{ background: "transparent" }}
    >
      <div
        ref={bar}
        className="h-full origin-left"
        style={{ background: "var(--accent)", transform: "scaleX(0)" }}
      />
    </div>
  );
}
