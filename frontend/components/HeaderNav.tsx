"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useRef, useState } from "react";
import { useAuth } from "./AuthProvider";
import { ThemeToggle } from "./ThemeToggle";

export function HeaderNav() {
  const { user, loading, logout } = useAuth();
  const router = useRouter();
  const pathname = usePathname();
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!open) return;
    const close = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    };
    document.addEventListener("mousedown", close);
    return () => document.removeEventListener("mousedown", close);
  }, [open]);

  const link = (href: string, label: string) => (
    <Link
      href={href}
      className="transition-colors hover:text-[var(--fg)]"
      style={{ color: pathname === href ? "var(--fg)" : undefined }}
      aria-current={pathname === href ? "page" : undefined}
    >
      {label}
    </Link>
  );

  return (
    <div className="flex items-center gap-4 pb-1 text-sm" style={{ color: "var(--muted)" }}>
      <span className="hidden sm:inline">{link("/how-it-works", "How it works")}</span>

      {!loading &&
        (user ? (
          <div className="relative" ref={ref}>
            <button
              onClick={() => setOpen((v) => !v)}
              className="flex items-center gap-1 transition-colors hover:text-[var(--fg)]"
              aria-haspopup="menu"
              aria-expanded={open}
            >
              {user.username}
              <span
                className="text-[0.65rem] transition-transform duration-200"
                style={{ transform: open ? "rotate(180deg)" : "none" }}
              >
                ▾
              </span>
            </button>
            {open && (
              <div
                className="pill-in card absolute right-0 z-30 mt-2.5 w-40 overflow-hidden rounded-lg py-1 text-sm"
                style={{ boxShadow: "var(--shadow)" }}
                role="menu"
              >
                <MenuLink href="/me?tab=saved" onClick={() => setOpen(false)}>
                  Saved
                </MenuLink>
                <MenuLink href="/me?tab=liked" onClick={() => setOpen(false)}>
                  Liked
                </MenuLink>
                <MenuLink href="/me?tab=history" onClick={() => setOpen(false)}>
                  Recent history
                </MenuLink>
                <div className="my-1 h-px" style={{ background: "var(--border)" }} />
                <button
                  onClick={async () => {
                    setOpen(false);
                    await logout();
                    router.push("/");
                  }}
                  className="block w-full px-3.5 py-2 text-left transition-colors hover:bg-[var(--surface-2)]"
                  role="menuitem"
                >
                  Log out
                </button>
              </div>
            )}
          </div>
        ) : (
          <Link
            href="/login"
            className="font-medium transition-colors hover:opacity-80"
            style={{ color: "var(--accent)" }}
          >
            Log in
          </Link>
        ))}

      <ThemeToggle />
    </div>
  );
}

function MenuLink({
  href,
  onClick,
  children,
}: {
  href: string;
  onClick: () => void;
  children: React.ReactNode;
}) {
  return (
    <Link
      href={href}
      onClick={onClick}
      role="menuitem"
      className="block px-3.5 py-2 transition-colors hover:bg-[var(--surface-2)]"
    >
      {children}
    </Link>
  );
}
