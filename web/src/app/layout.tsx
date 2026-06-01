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
    <html lang="en" className="dark">
      <body className={`${inter.variable} min-h-screen bg-background antialiased`}>
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
            background: "#0a0a0a",
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            justifyContent: "center",
            gap: "20px",
            pointerEvents: "none",
          }}
        >
          <svg xmlns="http://www.w3.org/2000/svg" width="88" height="88" viewBox="0 0 32 32">
            <rect width="32" height="32" rx="6" fill="#0f172a"/>
            <g transform="translate(4,4) scale(0.833333)" stroke="#d93025" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" fill="none">
              <path d="M21.42 10.922a1 1 0 0 0-.019-1.838L12.83 5.18a2 2 0 0 0-1.66 0L2.6 9.08a1 1 0 0 0 0 1.832l8.57 3.908a2 2 0 0 0 1.66 0z"/>
              <path d="M22 10v6"/>
              <path d="M6 12.5V16a6 3 0 0 0 12 0v-3.5"/>
            </g>
          </svg>
          <span style={{ color: "#fafafa", fontSize: "1.5rem", fontWeight: 600, letterSpacing: "-0.02em", fontFamily: "system-ui, sans-serif" }}>
            The Commons
          </span>
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
