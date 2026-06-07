"use client";
import { useEffect } from "react";

export function SplashDismisser() {
  useEffect(() => {
    const el = document.getElementById("app-splash");
    if (!el) return;
    const splashEl = el;

    let removeTimeoutId: number | undefined;
    let didDismiss = false;

    function dismiss() {
      if (didDismiss) return;
      didDismiss = true;

      splashEl.style.animation = "splash-out 0.2s ease-out both";
      splashEl.addEventListener("animationend", () => splashEl.remove(), { once: true });
      removeTimeoutId = window.setTimeout(() => splashEl.remove(), 400);
    }

    // Do not wait for thumbnails, API requests, or the full window load event.
    window.requestAnimationFrame(() => window.requestAnimationFrame(dismiss));

    return () => {
      if (removeTimeoutId) window.clearTimeout(removeTimeoutId);
    };
  }, []);
  return null;
}
