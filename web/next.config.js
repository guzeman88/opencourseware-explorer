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
      { protocol: "https", hostname: "images.unsplash.com" },
      { protocol: "https", hostname: "*.ox.ac.uk" },
      { protocol: "https", hostname: "*.cam.ac.uk" },
      { protocol: "https", hostname: "*.princeton.edu" },
      { protocol: "https", hostname: "*.gatech.edu" },
      { protocol: "https", hostname: "*.oxford.ac.uk" },
      { protocol: "https", hostname: "*.openculture.com" },
      { protocol: "https", hostname: "*.wikimedia.org" },
      { protocol: "https", hostname: "upload.wikimedia.org" },
      // Udacity course thumbnails
      { protocol: "https", hostname: "video.udacity-data.com" },
      // edX / edx-cdn course thumbnails
      { protocol: "https", hostname: "prod-discovery.edx-cdn.org" },
      { protocol: "https", hostname: "*.edx-cdn.org" },
      // ImgBB (used for some MIT thumbnails)
      { protocol: "https", hostname: "i.ibb.co" },
      // Sanity CDN (used for some GaTech thumbnails)
      { protocol: "https", hostname: "cdn.sanity.io" },
      // AWS S3 (used for some course thumbnails)
      { protocol: "https", hostname: "*.amazonaws.com" },
    ],
  },
  experimental: {
    optimizePackageImports: ["lucide-react"],
    scrollRestoration: true,
  },
  async headers() {
    const ContentSecurityPolicy = [
      "default-src 'self'",
      // Next.js App Router requires unsafe-inline for hydration; unsafe-eval for dev tools
      "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://browser.sentry-cdn.com https://js.sentry-cdn.com",
      "style-src 'self' 'unsafe-inline'",
      // Allow YouTube embeds (course detail pages)
      "frame-src https://www.youtube.com https://www.youtube-nocookie.com",
      // Images served from many university/CDN sources
      [
        "img-src 'self' data: blob:",
        "https://i.ytimg.com https://img.youtube.com",
        "https://i.ibb.co https://lh3.googleusercontent.com",
        "https://logo.clearbit.com https://upload.wikimedia.org",
        "https://video.udacity-data.com https://prod-discovery.edx-cdn.org",
        "https://cdn.sanity.io https://cdn.freecodecamp.org",
        "https://*.amazonaws.com https://ocw.mit.edu https://archive.org",
        "https://*.ytimg.com https://*.googleusercontent.com",
      ].join(" "),
      "media-src 'self' https://www.youtube.com",
      "connect-src 'self' https://*.sentry.io https://*.ingest.sentry.io https://*.onrender.com",
      "font-src 'self' data:",
      "object-src 'none'",
      "base-uri 'self'",
      "form-action 'self'",
      // frame-ancestors replaces X-Frame-Options for modern browsers
      "frame-ancestors 'none'",
    ].join("; ");

    const securityHeaders = [
      { key: "Content-Security-Policy", value: ContentSecurityPolicy },
    ];

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
      {
        // Apply security headers to all routes
        source: "/(.*)",
        headers: securityHeaders,
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
