import Link from "next/link";

export default function NotFound() {
  return (
    <div className="reveal py-24 text-center">
      <span className="kicker">Error 404</span>
      <h1 className="font-display mt-2 text-3xl">This page isn&rsquo;t here</h1>
      <p className="mx-auto mt-2 max-w-sm text-sm" style={{ color: "var(--muted)" }}>
        The story may have rolled out of the window. TrueNews only keeps the last few days.
      </p>
      <Link
        href="/"
        className="mt-6 inline-flex items-center gap-1.5 text-sm font-medium transition-colors hover:opacity-80"
        style={{ color: "var(--accent)" }}
      >
        ← Back to all stories
      </Link>
    </div>
  );
}
