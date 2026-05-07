import type { MetadataRoute } from "next";

export default function manifest(): MetadataRoute.Manifest {
  return {
    name: "The Commons",
    short_name: "The Commons",
    description:
      "Browse thousands of free university courses from MIT, Yale, Stanford, Harvard, NPTEL, Berkeley and more.",
    start_url: "/",
    display: "standalone",
    background_color: "#0a0a0a",
    theme_color: "#0a0a0a",
    orientation: "portrait-primary",
    scope: "/",
    lang: "en",
    categories: ["education"],
    icons: [
      {
        src: "/icon.png",
        sizes: "192x192",
        type: "image/png",
        purpose: "any",
      },
      {
        src: "/icon.png",
        sizes: "192x192",
        type: "image/png",
        purpose: "maskable",
      },
      {
        src: "/apple-icon.png",
        sizes: "180x180",
        type: "image/png",
      },
    ],
    shortcuts: [
      {
        name: "Browse Courses",
        url: "/browse",
        description: "Browse all available courses",
      },
      {
        name: "Search",
        url: "/search",
        description: "Search for specific courses",
      },
    ],
  };
}
