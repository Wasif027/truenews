"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { useAuth } from "@/components/AuthProvider";

export default function LoginPage() {
  const { user, signup, login } = useAuth();
  const router = useRouter();
  const [mode, setMode] = useState<"login" | "signup">("login");
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setBusy(true);
    try {
      await (mode === "signup" ? signup(username, password) : login(username, password));
      router.push("/");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong. Please try again.");
    } finally {
      setBusy(false);
    }
  }

  if (user) {
    return (
      <div className="reveal py-10 text-center">
        <span className="kicker">Signed in</span>
        <p className="font-display mt-2 text-2xl">Hello, {user.username}</p>
        <a
          href="/me"
          className="mt-4 inline-block text-sm font-medium"
          style={{ color: "var(--accent)" }}
        >
          Your saved &amp; history →
        </a>
      </div>
    );
  }

  const field =
    "w-full rounded-md border bg-transparent px-3 py-2 text-sm transition-colors hairline focus:border-[var(--accent)] focus:outline-none";

  return (
    <div className="reveal mx-auto max-w-sm py-6">
      <span className="kicker">{mode === "signup" ? "New account" : "Welcome back"}</span>
      <h1 className="font-display mt-2 text-[1.75rem] leading-tight">
        {mode === "signup" ? "Create an account" : "Log in"}
      </h1>
      <p className="mb-7 mt-1.5 text-sm" style={{ color: "var(--muted)" }}>
        {mode === "signup"
          ? "So you can like stories, save them, and keep a reading history."
          : "Pick up where you left off."}
      </p>

      <form onSubmit={submit} className="space-y-4">
        <label className="block">
          <span className="mb-1.5 block text-xs font-medium" style={{ color: "var(--fg-soft)" }}>
            Username
          </span>
          <input
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            autoComplete="username"
            minLength={3}
            required
            className={field}
          />
        </label>

        <label className="block">
          <span className="mb-1.5 block text-xs font-medium" style={{ color: "var(--fg-soft)" }}>
            Password{mode === "signup" && <span style={{ color: "var(--muted)" }}> · 8+ characters</span>}
          </span>
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            autoComplete={mode === "signup" ? "new-password" : "current-password"}
            minLength={mode === "signup" ? 8 : undefined}
            required
            className={field}
          />
        </label>

        {error && (
          <p
            className="rounded-md border px-3 py-2 text-xs"
            style={{ borderColor: "var(--accent)", color: "var(--accent)", background: "var(--accent-weak)" }}
          >
            {error}
          </p>
        )}

        <button
          disabled={busy}
          className="w-full rounded-md px-3 py-2.5 text-sm font-medium transition-all hover:brightness-95 active:scale-[0.99] disabled:opacity-60"
          style={{ background: "var(--accent)", color: "var(--card)" }}
        >
          {busy ? "One moment…" : mode === "signup" ? "Create account" : "Log in"}
        </button>
      </form>

      <button
        onClick={() => {
          setMode(mode === "signup" ? "login" : "signup");
          setError(null);
        }}
        className="mt-5 text-xs transition-colors hover:text-[var(--fg)]"
        style={{ color: "var(--muted)" }}
      >
        {mode === "signup"
          ? "Already have an account? Log in"
          : "New here? Create an account"}
      </button>
    </div>
  );
}
