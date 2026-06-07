import type { Metadata } from "next";
import { Inter } from "next/font/google";
import { Suspense } from "react";
import "./globals.css";
import { QueryProvider } from "@/providers/query-provider";
import { AppShell } from "@/components/app-shell";
import { GoogleAnalytics } from "@/components/google-analytics";

const inter = Inter({ subsets: ["latin"], variable: "--font-inter" });

export const metadata: Metadata = {
  metadataBase: new URL("https://opencourseware-explorer.netlify.app"),
  title: {
    default: "The Commons",
    template: "%s | The Commons",
  },
  icons: {
    icon: [
      { url: "/favicon.svg", type: "image/svg+xml" },
      { url: "/icons/icon-192.png", sizes: "192x192", type: "image/png" },
      { url: "/icons/icon-512.png", sizes: "512x512", type: "image/png" },
    ],
    shortcut: "/favicon.svg",
    apple: [
      { url: "/apple-touch-icon.png", sizes: "180x180", type: "image/png" },
    ],
  },
  description:
    "Browse thousands of free university courses from MIT, Yale, Stanford, Harvard, NPTEL, Berkeley and more.",
  keywords: ["free courses", "university lectures", "open courseware", "NPTEL", "Yale", "Stanford", "MIT"],
  openGraph: {
    type: "website",
    title: "The Commons",
    description: "Browse thousands of free university courses from MIT, Yale, Stanford, Harvard and more.",
    url: "https://opencourseware-explorer.netlify.app",
    siteName: "The Commons",
  },
  twitter: {
    card: "summary_large_image",
    title: "The Commons",
    description: "Browse thousands of free university courses from MIT, Yale, Stanford, Harvard and more.",
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark" style={{ backgroundColor: "#0a0a0a" }}>
      <head>
        <link rel="apple-touch-startup-image" href="/launch-screen.png" />
      </head>
      <body
        className={`${inter.variable} min-h-screen bg-background antialiased`}
        style={{ backgroundColor: "#0a0a0a" }}
      >
        <div id="app-splash" aria-hidden="true">
          <img
            src="/launch-screen.png"
            alt=""
            width="1290"
            height="2796"
          />
        </div>
        <script src="/splash-dismiss.js" defer />
        <Suspense>
          <GoogleAnalytics />
        </Suspense>
        <QueryProvider>
          <AppShell>{children}</AppShell>
        </QueryProvider>
      </body>
    </html>
  );
}
