"use client";

import { useEffect } from "react";
import { recordVisit } from "@/lib/api";
import { useAuth } from "./AuthProvider";

/** Fires once when a signed-in user opens a story, so it lands in their history. */
export function RecordVisit({ storyId }: { storyId: number }) {
  const { user } = useAuth();
  useEffect(() => {
    if (user) recordVisit(storyId).catch(() => {});
  }, [user, storyId]);
  return null;
}
