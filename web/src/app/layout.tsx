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
    icon: "/favicon.svg",
    shortcut: "/favicon.svg",
    apple: "/favicon.svg",
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
        {/* Splash – covers the initial black screen, fades out once JS loads */}
        <div id="app-splash" aria-hidden="true">
          <svg xmlns="http://www.w3.org/2000/svg" width="88" height="88" viewBox="0 0 32 32">
            <rect width="32" height="32" rx="6" fill="#0f172a"/>
            <g transform="translate(4,4) scale(0.833333)" stroke="#d93025" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" fill="none">
              <path d="M21.42 10.922a1 1 0 0 0-.019-1.838L12.83 5.18a2 2 0 0 0-1.66 0L2.6 9.08a1 1 0 0 0 0 1.832l8.57 3.908a2 2 0 0 0 1.66 0z"/>
              <path d="M22 10v6"/>
              <path d="M6 12.5V16a6 3 0 0 0 12 0v-3.5"/>
            </g>
          </svg>
          <span id="app-splash-title">The Commons</span>
        </div>
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
