(() => {
  const splash = document.getElementById("app-splash");
  if (!splash) return;

  const dismiss = () => {
    splash.classList.add("app-splash--exit");
    window.setTimeout(() => splash.remove(), 250);
  };

  window.setTimeout(dismiss, 650);
  window.setTimeout(() => splash.remove(), 1800);
})();
