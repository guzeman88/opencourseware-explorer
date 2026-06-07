import type { Metadata } from "next";
import { Inter } from "next/font/google";
import { Suspense } from "react";
import "./globals.css";
import { QueryProvider } from "@/providers/query-provider";
import { AppShell } from "@/components/app-shell";
import { GoogleAnalytics } from "@/components/google-analytics";
import { SplashDismisser } from "@/components/splash-dismisser";

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
    <html lang="en" className="dark" style={{ backgroundColor: "#0f172a" }}>
      <head>
        <link rel="preload" as="image" href="/launch-screen.png" />
        <link rel="apple-touch-startup-image" href="/launch-screen.png" />
      </head>
      <body
        className={`${inter.variable} min-h-screen bg-background antialiased`}
        style={{ backgroundColor: "#0f172a" }}
      >
        {/* Keyframe + splash styles inlined in the HTML so they apply before any external CSS loads */}
        {/* eslint-disable-next-line react/no-danger */}
        <style dangerouslySetInnerHTML={{ __html: `
          @keyframes splash-out{from{opacity:1}to{opacity:0;visibility:hidden}}
        `}} />
        {/* Splash – stays until React hydrates, then SplashDismisser fades it out */}
        <div
          id="app-splash"
          aria-hidden="true"
          style={{
            position: "fixed",
            inset: 0,
            zIndex: 9999,
            background: "#0f172a",
            pointerEvents: "none",
          }}
        >
          <img
            id="app-launch-image"
            src="/launch-screen.png"
            alt=""
            aria-hidden="true"
            style={{ width: "100%", height: "100%", objectFit: "cover" }}
          />
        </div>
        <Suspense>
          <GoogleAnalytics />
        </Suspense>
        <QueryProvider>
          <SplashDismisser />
          <AppShell>{children}</AppShell>
        </QueryProvider>
      </body>
    </html>
  );
}
