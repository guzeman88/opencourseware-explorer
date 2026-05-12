const CACHE_NAME = "the-commons-v2";

// Install: activate immediately — no precaching of dynamic pages because
// those depend on the Railway backend being up. Precaching would cause
// cache.addAll() to throw on cold-start, failing the SW install and
// triggering iOS's "a problem repeatedly occurred" loop.
self.addEventListener("install", (event) => {
  event.waitUntil(self.skipWaiting());
});

// Activate: clear ALL old caches (including stale v1 chunks) and claim clients immediately
self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches
      .keys()
      .then((keys) =>
        Promise.all(
          keys
            .filter((key) => key !== CACHE_NAME)
            .map((key) => caches.delete(key))
        )
      )
      .then(() => self.clients.claim())
  );
});

// Fetch: network-first with cache fallback
// Static assets (_next/) use cache-first to speed up repeat visits
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

  // Navigation / page requests: network-first, fallback to cached page or "/"
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
        caches
          .match(event.request)
          .then((cached) => cached || caches.match("/"))
      )
  );
});
