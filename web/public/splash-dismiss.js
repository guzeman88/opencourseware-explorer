(() => {
  const splash = document.getElementById("app-splash");
  const app = document.getElementById("app-shell");
  if (!splash || !app || splash.style.display === "none") return;

  app.style.display = "block";
  window.requestAnimationFrame(() => {
    window.requestAnimationFrame(() => {
      splash.style.display = "none";
      splash.remove();
    });
  });
})();
