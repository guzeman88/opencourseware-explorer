"use client";

import { useEffect } from "react";

export function PwaRegister() {
  useEffect(() => {
    if (!("serviceWorker" in navigator)) return;

    // Unregister every SW and delete every cache — no reloads, no controller
    // changes. This runs silently after hydration, so iOS WKWebView never
    // sees a mid-page disruption that it would count as a crash.
    navigator.serviceWorker
      .getRegistrations()
      .then((registrations) => registrations.forEach((r) => r.unregister()))
      .catch(() => {});

    if ("caches" in window) {
      caches
        .keys()
        .then((keys) => keys.forEach((k) => caches.delete(k)))
        .catch(() => {});
    }
  }, []);

  return null;
}
