(() => {
  const initialSplash = document.getElementById("app-splash");
  const iconMarkup = initialSplash?.querySelector(".splash-icon")?.outerHTML;
  const standalone =
    navigator.standalone ||
    window.matchMedia("(display-mode: standalone)").matches ||
    new URLSearchParams(location.search).has("standalone");

  const removeSplash = (splash) => {
    if (!splash?.isConnected) return;
    splash.style.animation = "none";
    splash.style.transition = "opacity 180ms ease-out";
    splash.style.opacity = "0";
    window.setTimeout(() => splash.remove(), 220);
  };

  if (initialSplash) {
    window.setTimeout(() => {
      window.requestAnimationFrame(() => {
        window.requestAnimationFrame(() => removeSplash(initialSplash));
      });
    }, 650);
    window.setTimeout(() => initialSplash.remove(), 1800);
  }

  let wasHidden = false;
  const showResumeSplash = () => {
    if (
      !standalone ||
      !iconMarkup ||
      document.getElementById("app-splash") ||
      document.querySelector(".app-resume-splash")
    ) {
      return;
    }

    const splash = document.createElement("div");
    splash.className = "app-resume-splash";
    splash.setAttribute("aria-hidden", "true");
    splash.innerHTML = iconMarkup;
    document.body.appendChild(splash);
    window.setTimeout(() => removeSplash(splash), 650);
    window.setTimeout(() => splash.remove(), 1200);
  };

  document.addEventListener("visibilitychange", () => {
    if (document.visibilityState === "hidden") {
      wasHidden = true;
    } else if (wasHidden) {
      wasHidden = false;
      showResumeSplash();
    }
  });

  window.addEventListener("pageshow", (event) => {
    if (event.persisted) showResumeSplash();
  });
})();
