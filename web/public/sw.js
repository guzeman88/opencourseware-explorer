// No-op service worker.
//
// This file exists only so the browser's SW update check gets a valid 200
// response instead of a 404 (which can trigger an error event and reload).
//
// Crucially, this SW does NOT call skipWaiting() or clients.claim().
// Those APIs force a mid-page controller change, which iOS standalone
// (WKWebView) mode treats as a crash — causing "a problem repeatedly
// occurred" after 2 forced reloads.
//
// All SW cleanup is handled silently by the page JS:
//   navigator.serviceWorker.getRegistrations()
//     .then(regs => regs.forEach(r => r.unregister()))
// That removes every registration without reloading the page.
//
// Without skipWaiting(), this SW installs but stays in "waiting" state.
// The page-side unregister() call removes it along with any active old SW.
// On the next page load there is no SW at all.
self.addEventListener("install", () => {
  // Intentionally empty — do NOT call skipWaiting()
});

