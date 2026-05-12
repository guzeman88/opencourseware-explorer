const CACHE_NAME = "the-commons-v3";

// Offline fallback — shown when the user is offline and the page isn't cached.
// Dark-themed to match the app so it doesn't look like a white crash.
const OFFLINE_HTML = `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Offline – The Commons</title>
  <style>
    body { background:#0a0a0a; color:#fff; font-family:system-ui,sans-serif;
           display:flex; align-items:center; justify-content:center;
           min-height:100vh; margin:0; }
    .box { text-align:center; padding:2rem; }
    h1 { font-size:1.5rem; margin-bottom:.5rem; }
    p  { color:#888; margin-bottom:1rem; }
    button { padding:.5rem 1.5rem; border-radius:6px; background:#dc2626;
             color:#fff; border:none; font-size:1rem; cursor:pointer; }
  </style>
</head>
<body>
  <div class="box">
    <h1>You're offline</h1>
    <p>Check your connection and try again.</p>
    <button onclick="location.reload()">Retry</button>
  </div>
</body>
</html>`;

// Install: activate immediately — no precaching of dynamic pages because
// those depend on the Railway backend being up. Precaching would cause
// cache.addAll() to throw on cold-start, triggering iOS's crash loop.
self.addEventListener("install", (event) => {
  event.waitUntil(self.skipWaiting());
});

// Activate: clear ALL old caches. Do NOT call clients.claim() here —
// claiming open clients on iOS standalone can force a page reload that
// iOS misinterprets as a crash, triggering "a problem repeatedly occurred".
self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(
        keys.filter((key) => key !== CACHE_NAME).map((key) => caches.delete(key))
      )
    )
  );
});

self.addEventListener("fetch", (event) => {
  if (event.request.method !== "GET") return;

  const url = new URL(event.request.url);

  // Only handle same-origin requests
  if (url.origin !== self.location.origin) return;

  // Skip API calls — always go to network
  if (url.pathname.startsWith("/api/")) return;

  // Static Next.js assets: cache-first
  if (url.pathname.startsWith("/_next/static/")) {
    event.respondWith(
      caches.match(event.request).then(
        (cached) =>
          cached ||
          fetch(event.request).then((response) => {
            if (response && response.status === 200) {
              const clone = response.clone();
              caches.open(CACHE_NAME).then((c) => c.put(event.request, clone));
            }
            return response;
          })
      )
    );
    return;
  }

  // Only cache full page navigations (mode === "navigate").
  // RSC prefetches (?_rsc=…), image requests, and other background fetches
  // must NOT be intercepted — returning the wrong cached content for an RSC
  // request would cause React to throw a parse error and crash the app.
  if (event.request.mode !== "navigate") return;

  // Full page navigation: network-first, dark offline fallback on failure
  event.respondWith(
    fetch(event.request)
      .then((response) => {
        if (response && response.status === 200) {
          const clone = response.clone();
          caches.open(CACHE_NAME).then((c) => c.put(event.request, clone));
        }
        return response;
      })
      .catch(() =>
        caches.match(event.request).then(
          (cached) =>
            cached ||
            new Response(OFFLINE_HTML, { headers: { "Content-Type": "text/html" } })
        )
      )
  );
});
