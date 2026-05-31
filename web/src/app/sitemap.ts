import type { MetadataRoute } from "next";

const BASE = "https://opencourseware-explorer.netlify.app";

export default function sitemap(): MetadataRoute.Sitemap {
  const now = new Date();

  return [
    { url: BASE,                          lastModified: now, changeFrequency: "daily",   priority: 1.0 },
    { url: `${BASE}/courses`,             lastModified: now, changeFrequency: "daily",   priority: 0.9 },
    { url: `${BASE}/browse`,              lastModified: now, changeFrequency: "weekly",  priority: 0.8 },
    { url: `${BASE}/subjects`,            lastModified: now, changeFrequency: "weekly",  priority: 0.8 },
    { url: `${BASE}/universities`,        lastModified: now, changeFrequency: "weekly",  priority: 0.7 },
    { url: `${BASE}/roadmaps`,            lastModified: now, changeFrequency: "monthly", priority: 0.6 },
    { url: `${BASE}/library`,             lastModified: now, changeFrequency: "never",   priority: 0.3 },
    { url: `${BASE}/search`,              lastModified: now, changeFrequency: "never",   priority: 0.5 },
  ];
}
