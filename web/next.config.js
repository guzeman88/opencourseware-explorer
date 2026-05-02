/** @type {import('next').NextConfig} */
const nextConfig = {
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
    ],
  },
  experimental: {
    optimizePackageImports: ["lucide-react"],
  },
};

module.exports = nextConfig;
