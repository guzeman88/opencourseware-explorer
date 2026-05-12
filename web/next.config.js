/** @type {import('next').NextConfig} */
const { withSentryConfig } = require("@sentry/nextjs");
const withBundleAnalyzer = require("@next/bundle-analyzer")({
  enabled: process.env.ANALYZE === "true",
});

const nextConfig = {
  compress: true,
  poweredByHeader: false,
  images: {
    // Cache optimized images at Vercel's image CDN for 1 hour
    minimumCacheTTL: 3600,
    remotePatterns: [
      { protocol: "https", hostname: "i.ytimg.com" },
      { protocol: "https", hostname: "img.youtube.com" },
      { protocol: "https", hostname: "ocw.mit.edu" },
      { protocol: "https", hostname: "*.yale.edu" },
      { protocol: "https", hostname: "*.stanford.edu" },
      { protocol: "https", hostname: "*.harvard.edu" },
      { protocol: "https", hostname: "nptel.ac.in" },
      { protocol: "https", hostname: "lh3.googleusercontent.com" },
      { protocol: "https", hostname: "archive.org" },
      { protocol: "https", hostname: "*.berkeley.edu" },
      { protocol: "https", hostname: "*.caltech.edu" },
      { protocol: "https", hostname: "*.cmu.edu" },
      { protocol: "https", hostname: "*.mit.edu" },
      { protocol: "https", hostname: "*.udacity.com" },
      { protocol: "https", hostname: "simons.berkeley.edu" },
      { protocol: "https", hostname: "*.freecodecamp.org" },
      { protocol: "https", hostname: "cdn.freecodecamp.org" },
      { protocol: "https", hostname: "*.coursera.org" },
      { protocol: "https", hostname: "*.edx.org" },
      { protocol: "https", hostname: "*.3blue1brown.com" },
      { protocol: "https", hostname: "logo.clearbit.com" },
    ],
  },
  experimental: {
    optimizePackageImports: ["lucide-react"],
  },
  async headers() {
    return [
      {
        source: "/sw.js",
        headers: [
          { key: "Cache-Control", value: "no-cache, no-store, must-revalidate" },
          { key: "Service-Worker-Allowed", value: "/" },
        ],
      },
      {
        source: "/manifest.webmanifest",
        headers: [
          { key: "Cache-Control", value: "public, max-age=3600" },
        ],
      },
      {
        // Static Next.js build chunks — immutable, cache forever
        source: "/_next/static/:path*",
        headers: [
          { key: "Cache-Control", value: "public, max-age=31536000, immutable" },
        ],
      },
    ];
  },
};

module.exports = withSentryConfig(
  withBundleAnalyzer(nextConfig),
  {
    // Sentry source-map upload — requires SENTRY_AUTH_TOKEN in CI
    silent: true,
    org: process.env.SENTRY_ORG,
    project: process.env.SENTRY_PROJECT,
  },
  {
    // SDK options
    disableLogger: true,
    hideSourceMaps: true,
  }
);
