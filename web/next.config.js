/** @type {import('next').NextConfig} */
const contentSecurityPolicyReportOnly = [
  "default-src 'self'",
  "base-uri 'self'",
  "frame-ancestors 'none'",
  "form-action 'self'",
  "object-src 'none'",
  "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://www.googletagmanager.com",
  "style-src 'self' 'unsafe-inline'",
  "img-src 'self' data: blob: https:",
  "font-src 'self' data:",
  "connect-src 'self' https://opencourseware-api.onrender.com https://*.sentry.io https://www.google-analytics.com",
  "frame-src 'self' https://www.youtube.com https://www.youtube-nocookie.com",
  "media-src 'self' https:",
  "worker-src 'self' blob:",
].join("; ");

const nextConfig = {
  async headers() {
    return [
      {
        source: "/(.*)",
        headers: [
          { key: "X-Content-Type-Options", value: "nosniff" },
          { key: "X-Frame-Options", value: "DENY" },
          { key: "X-XSS-Protection", value: "1; mode=block" },
          { key: "Referrer-Policy", value: "strict-origin-when-cross-origin" },
          { key: "Permissions-Policy", value: "camera=(), microphone=(), geolocation=()" },
          { key: "Content-Security-Policy-Report-Only", value: contentSecurityPolicyReportOnly },
        ],
      },
    ];
  },
  images: {
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
};

module.exports = nextConfig;
