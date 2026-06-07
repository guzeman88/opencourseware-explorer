// Netlify's scheduled function is the primary free keepalive for Render.
// GitHub Actions remains a best-effort backup because scheduled runs can drift.

export default async () => {
  try {
    const response = await fetch("https://opencourseware-api.onrender.com/health", {
      signal: AbortSignal.timeout(10000),
    });

    if (!response.ok) {
      console.error(`Render keepalive returned ${response.status}`);
    }
  } catch (error) {
    console.error("Render keepalive failed", error);
  }
};

export const config = {
  schedule: "*/5 * * * *",
};
