(() => {
  const loading = document.getElementById("loading");
  const app = document.getElementById("app");
  if (!loading || !app || loading.style.display === "none") return;

  app.style.display = "block";
  window.requestAnimationFrame(() => {
    window.requestAnimationFrame(() => {
      loading.style.display = "none";
      document.documentElement.style.overflow = "auto";
      document.body.style.overflow = "auto";
    });
  });
})();
