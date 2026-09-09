import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Compare coverage",
  description:
    "Paste two or more article links about the same event and see how each outlet angles the story, with the quotes it's based on.",
};

export default function CompareLayout({ children }: { children: React.ReactNode }) {
  return children;
}
