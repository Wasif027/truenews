import type { Metadata } from "next";
import Link from "next/link";
import { IBM_Plex_Sans, Newsreader } from "next/font/google";
import "./globals.css";
import { AuthProvider } from "@/components/AuthProvider";
import { CountrySwitcher } from "@/components/CountrySwitcher";
import { Dateline } from "@/components/Dateline";
import { HeaderNav } from "@/components/HeaderNav";
import { SourcesLink } from "@/components/SourcesLink";
import { Wordmark } from "@/components/Wordmark";

// Body / UI face. A humanist grotesque with real editorial character and
// built-in tabular figures — Inter reads as a default; this doesn't.
const plex = IBM_Plex_Sans({
  subsets: ["latin"],
  variable: "--font-sans",
  display: "swap",
  weight: ["400", "500", "600", "700"],
  fallback: ["system-ui", "Segoe UI", "sans-serif"],
});
const newsreader = Newsreader({
  subsets: ["latin"],
  variable: "--font-display",
  display: "swap",
  style: ["normal", "italic"],
  fallback: ["Georgia", "Times New Roman", "serif"],
  adjustFontFallback: false,
});

export const metadata: Metadata = {
  metadataBase: new URL(process.env.NEXT_PUBLIC_SITE_URL ?? "http://localhost:3000"),
  title: {
    default: "TrueNews · how the press covers the same stories",
    template: "%s · TrueNews",
  },
  description:
    "A news reader that groups articles about the same event and shows how the same story reads from one outlet to the next, across 22 countries.",
  icons: { icon: "/icon.svg" },
  openGraph: {
    title: "TrueNews · how the press covers the same stories",
    description:
      "Groups articles about the same event and shows how coverage differs across outlets.",
    type: "website",
  },
};

const THEME_SCRIPT = `
try {
  var t = localStorage.getItem('theme');
  if (t === 'dark' || (!t && window.matchMedia('(prefers-color-scheme: dark)').matches)) {
    document.documentElement.classList.add('dark');
  }
} catch (e) {}
`;

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={`${plex.variable} ${newsreader.variable}`} suppressHydrationWarning>
      <head>
        <script dangerouslySetInnerHTML={{ __html: THEME_SCRIPT }} />
      </head>
      <body className="min-h-[100dvh] font-sans">
        <a href="#main" className="skip-link">
          Skip to content
        </a>
        <AuthProvider>
          <header className="border-b hairline">
            <div className="mx-auto max-w-6xl px-5">
              <div className="flex items-start justify-between gap-4 pb-3 pt-7">
                <div>
                  <Link
                    href="/"
                    className="block text-[2.6rem] leading-[0.85]"
                    aria-label="TrueNews home"
                  >
                    <Wordmark />
                  </Link>
                  <p
                    className="mt-2.5 hidden text-[0.8rem] italic sm:block"
                    style={{ color: "var(--muted)", fontFamily: "var(--font-display), Georgia, serif" }}
                  >
                    How the same story reads from one outlet to the next.
                  </p>
                </div>
                <HeaderNav />
              </div>
              <div className="rule-double pb-2 pt-2">
                <div className="flex items-center justify-between gap-3">
                  <CountrySwitcher />
                  <Dateline />
                </div>
                <SourcesLink />
              </div>
            </div>
          </header>

          <main id="main" className="mx-auto max-w-6xl px-5 py-9">
            {children}
          </main>
        </AuthProvider>

        <footer className="mx-auto max-w-6xl px-5 pb-14 pt-8">
          <nav
            className="flex items-center justify-center gap-3 border-t hairline pt-5 text-xs"
            style={{ color: "var(--muted)" }}
          >
            <Link href="/how-it-works" className="transition-colors hover:text-[var(--fg)]">
              How it works
            </Link>
            <span aria-hidden className="opacity-40">
              ·
            </span>
            <Link href="/sources" className="transition-colors hover:text-[var(--fg)]">
              Sources
            </Link>
            <span aria-hidden className="opacity-40">
              ·
            </span>
            <Link href="/status" className="transition-colors hover:text-[var(--fg)]">
              Status
            </Link>
          </nav>
        </footer>
      </body>
    </html>
  );
}
