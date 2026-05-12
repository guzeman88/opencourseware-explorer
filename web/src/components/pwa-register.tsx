"use client";

import { useEffect } from "react";

export function PwaRegister() {
  useEffect(() => {
    if (!("serviceWorker" in navigator)) return;

    // Unregister ALL service workers on this origin.
    // Previous SW versions caused an iOS PWA crash loop because skipWaiting()
    // forced an immediate controller change mid-page, which iOS standalone
    // mode treats as a crash. We've eliminated the SW entirely — caching is
    // handled by Vercel CDN (ISR + stale-while-revalidate) and React Query.
    navigator.serviceWorker
      .getRegistrations()
      .then((registrations) => {
        registrations.forEach((r) => r.unregister());
      })
      .catch(() => {});
  }, []);

  return null;
}
