"use client";
import { useEffect } from "react";

export function SplashDismisser() {
  useEffect(() => {
    const el = document.getElementById("app-splash");
    if (!el) return;
    const splashEl = el;

    let timeoutId: number | undefined;
    let didDismiss = false;

    function dismiss() {
      if (didDismiss) return;
      didDismiss = true;

      window.requestAnimationFrame(() => {
        window.requestAnimationFrame(() => {
          splashEl.style.animation = "splash-out 0.35s ease-out both";
          splashEl.addEventListener("animationend", () => splashEl.remove(), { once: true });
        });
      });
    }

    if (document.readyState === "complete") {
      dismiss();
    } else {
      window.addEventListener("load", dismiss, { once: true });
      timeoutId = window.setTimeout(dismiss, 2500);
    }

    return () => {
      window.removeEventListener("load", dismiss);
      if (timeoutId) window.clearTimeout(timeoutId);
    };
  }, []);
  return null;
}
