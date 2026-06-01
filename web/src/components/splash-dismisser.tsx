"use client";
import { useEffect } from "react";

export function SplashDismisser() {
  useEffect(() => {
    const el = document.getElementById("app-splash");
    if (!el) return;
    el.style.animation = "splash-out 0.4s ease-out both";
    el.addEventListener("animationend", () => el.remove(), { once: true });
  }, []);
  return null;
}
