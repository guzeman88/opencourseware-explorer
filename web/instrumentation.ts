// This file bootstraps Sentry server-side instrumentation in Next.js 14.
// It is automatically loaded by Next.js when the file exists at the project root.
// See: https://nextjs.org/docs/app/building-your-application/optimizing/instrumentation
export async function register() {
  if (process.env.NEXT_RUNTIME === "nodejs") {
    await import("./sentry.server.config");
  }
  if (process.env.NEXT_RUNTIME === "edge") {
    await import("./sentry.edge.config");
  }
}
