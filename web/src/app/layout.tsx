import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { QueryProvider } from "@/providers/query-provider";
import { Navbar } from "@/components/navbar";

const inter = Inter({ subsets: ["latin"], variable: "--font-inter" });

export const metadata: Metadata = {
  title: {
    default: "OpenCourseWare Explorer",
    template: "%s | OpenCourseWare Explorer",
  },
  icons: {
    icon: "/favicon.svg",
    shortcut: "/favicon.svg",
    apple: "/favicon.svg",
  },
  description:
    "Browse thousands of free university courses from MIT, Yale, Stanford, Harvard, NPTEL, Berkeley and more.",
  keywords: ["MIT OCW", "free courses", "university lectures", "open courseware", "NPTEL", "Yale", "Stanford"],
  openGraph: {
    type: "website",
    title: "OpenCourseWare Explorer",
    description: "Browse thousands of free university courses",
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
        <QueryProvider>
          <Navbar />
          <main className="min-h-[calc(100vh-4rem)]">{children}</main>
          <footer className="border-t border-border py-8 text-center text-sm text-muted-foreground">
            <p>
              OpenCourseWare Explorer — Aggregating free university education
              from MIT, Yale, Stanford, Harvard, NPTEL, Berkeley, and more.
            </p>
            <p className="mt-1">
              All course content belongs to their respective universities and
              creators.
            </p>
          </footer>
        </QueryProvider>
      </body>
    </html>
  );
}
