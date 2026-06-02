"use client";

import { useEffect } from "react";

const CLEANUP_KEY = "ocw-sw-cleanup-v2";

export function PwaRegister() {
  useEffect(() => {
    if (!("serviceWorker" in navigator)) return;

    let alreadyCleaned = false;
    try {
      alreadyCleaned = localStorage.getItem(CLEANUP_KEY) === "1";
    } catch {
      alreadyCleaned = false;
    }
    const hasController = !!navigator.serviceWorker.controller;

    if (alreadyCleaned && !hasController) return;

    Promise.all([
      navigator.serviceWorker
        .getRegistrations()
        .then((registrations) => Promise.all(registrations.map((r) => r.unregister())))
        .catch(() => []),
      "caches" in window
        ? caches
            .keys()
            .then((keys) => Promise.all(keys.map((k) => caches.delete(k))))
            .catch(() => [])
        : Promise.resolve([]),
    ])
      .then(() => {
        try {
          localStorage.setItem(CLEANUP_KEY, "1");
        } catch {}
      })
      .catch(() => {});
  }, []);

  return null;
}
