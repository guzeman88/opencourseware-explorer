// Self-unregistering service worker.
//
// Previous SW versions caused an iOS PWA crash loop ("a problem repeatedly
// occurred") because skipWaiting() forces an immediate SW controller change
// mid-page. iOS standalone mode treats this as a crash. We've removed all
// SW logic — the app gets caching from Vercel CDN + React Query instead.
//
// This file takes over all old registrations, clears their caches, then
// unregisters itself so no SW is left running.

self.addEventListener("install", () => self.skipWaiting());

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches
      .keys()
      .then((keys) => Promise.all(keys.map((key) => caches.delete(key))))
      .then(() => self.registration.unregister())
  );
});
