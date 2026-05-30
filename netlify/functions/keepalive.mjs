// Pings the Render backend every 5 minutes so it never spins down.
// Render free tier sleeps after ~15 min of inactivity causing 15-30s cold starts.

export default async () => {
  try {
    await fetch("https://opencourseware-api.onrender.com/health", {
      signal: AbortSignal.timeout(10000),
    });
  } catch {
    // Ignore — the point is just to send traffic, not to handle the response.
  }
};

export const config = {
  schedule: "*/5 * * * *",
};
