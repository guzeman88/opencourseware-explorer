// Cache-clearing service worker.
//
// PROBLEM: Old broken SWs (from previous builds that tried to cache pages)
// may still be ACTIVE on users' phones. Those SWs serve stale cached HTML
// that doesn't match the current code, causing React hydration to fail.
// In iOS standalone WKWebView, hydration failure = process crash = white screen.
// After 2 crashes, iOS shows "a problem repeatedly occurred".
//
// STRATEGY:
// 1. On INSTALL: immediately delete ALL caches.
//    This happens before skipWaiting(), so even the currently-active old SW
//    can no longer serve stale content — its caches are gone.
//    The old SW's fetch handlers fall through to the network (fresh content).
// 2. We do NOT call skipWaiting() — the new SW stays in "waiting" state.
//    This avoids a mid-navigation controller change, which iOS WKWebView
//    treats as a crash.
// 3. The page JS (pwa-register.tsx) runs after hydration and calls
//    getRegistrations().forEach(r => r.unregister()) to remove all SWs.
//    On the NEXT load, no SW exists at all.

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.map((key) => caches.delete(key)))
    )
    // Do NOT call skipWaiting() — that forces a controller change mid-page
    // which iOS standalone WKWebView counts as a crash.
  );
});

// No fetch handler — all requests go straight to the network.
// (The old active SW's fetch handler can no longer serve from cache
// because we deleted all caches in the install event above.)

