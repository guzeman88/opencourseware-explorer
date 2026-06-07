import type { Metadata } from "next";
import { Inter } from "next/font/google";
import { Suspense } from "react";
import "./globals.css";
import { QueryProvider } from "@/providers/query-provider";
import { AppShell } from "@/components/app-shell";
import { GoogleAnalytics } from "@/components/google-analytics";

const inter = Inter({ subsets: ["latin"], variable: "--font-inter" });
const splashBackground = "#0a0a0a";

const criticalSplashCss = `
  html,body{margin:0;padding:0;background:${splashBackground};overflow:hidden}
  #loading{position:fixed;inset:0;z-index:99999;background:${splashBackground};display:flex;flex-direction:column;align-items:center;justify-content:center;gap:20px;padding-bottom:10vh;box-sizing:border-box}
  .ld-icon{width:158px;height:158px;display:flex;align-items:center;justify-content:center}
  .ld-icon svg{width:100%;height:100%}
  .ld-title{color:#fafafa;font:800 20px/1.2 -apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}
  .ld-dots{display:flex;gap:6px;margin-top:4px}
  .ld-dots span{width:6px;height:6px;border-radius:50%;background:rgba(214,43,43,.45);animation:ld-dot 1.4s ease-in-out infinite}
  .ld-dots span:nth-child(2){animation-delay:.2s}
  .ld-dots span:nth-child(3){animation-delay:.4s}
  @keyframes ld-dot{0%,80%,100%{transform:scale(.6);opacity:.3}40%{transform:scale(1);opacity:1}}
`;

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
    <html lang="en" className="dark" style={{ background: splashBackground }}>
      <head>
        <style dangerouslySetInnerHTML={{ __html: criticalSplashCss }} />
        <meta name="theme-color" content={splashBackground} />
        <link rel="apple-touch-startup-image" media="screen and (device-width: 375px) and (device-height: 667px) and (-webkit-device-pixel-ratio: 2)" href="/icons/splash-iphone_se.png" />
        <link rel="apple-touch-startup-image" media="screen and (device-width: 375px) and (device-height: 812px) and (-webkit-device-pixel-ratio: 3)" href="/icons/splash-iphone_x.png" />
        <link rel="apple-touch-startup-image" media="screen and (device-width: 360px) and (device-height: 780px) and (-webkit-device-pixel-ratio: 3)" href="/icons/splash-iphone_mini.png" />
        <link rel="apple-touch-startup-image" media="screen and (device-width: 414px) and (device-height: 896px) and (-webkit-device-pixel-ratio: 2)" href="/icons/splash-iphone_11.png" />
        <link rel="apple-touch-startup-image" media="screen and (device-width: 414px) and (device-height: 896px) and (-webkit-device-pixel-ratio: 3)" href="/icons/splash-iphone_11pm.png" />
        <link rel="apple-touch-startup-image" media="screen and (device-width: 390px) and (device-height: 844px) and (-webkit-device-pixel-ratio: 3)" href="/icons/splash-iphone_15.png" />
        <link rel="apple-touch-startup-image" media="screen and (device-width: 393px) and (device-height: 852px) and (-webkit-device-pixel-ratio: 3)" href="/icons/splash-iphone_15pro.png" />
        <link rel="apple-touch-startup-image" media="screen and (device-width: 428px) and (device-height: 926px) and (-webkit-device-pixel-ratio: 3)" href="/icons/splash-iphone_15plus.png" />
        <link rel="apple-touch-startup-image" media="screen and (device-width: 430px) and (device-height: 932px) and (-webkit-device-pixel-ratio: 3)" href="/icons/splash-iphone_pmax.png" />
        <link rel="apple-touch-startup-image" media="screen and (device-width: 402px) and (device-height: 874px) and (-webkit-device-pixel-ratio: 3)" href="/icons/splash-iphone_16pro.png" />
        <link rel="apple-touch-startup-image" media="screen and (device-width: 440px) and (device-height: 956px) and (-webkit-device-pixel-ratio: 3)" href="/icons/splash-iphone_16pmax.png" />
        <link rel="apple-touch-startup-image" media="screen and (device-width: 1024px) and (device-height: 1366px) and (-webkit-device-pixel-ratio: 2)" href="/icons/splash-ipad_pro.png" />
      </head>
      <body
        className={`${inter.variable} min-h-screen bg-background antialiased`}
        style={{ background: splashBackground }}
      >
        <div id="loading" aria-hidden="true">
          <div className="ld-icon">
            <svg viewBox="0 0 32 32" role="presentation">
              <g transform="translate(4,4) scale(0.833333)" stroke="#d62b2b" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" fill="none">
                <path d="M22 10v6M2 10l10-5 10 5-10 5z" />
                <path d="M6 12v5c3 3 9 3 12 0v-5" />
              </g>
            </svg>
          </div>
          <div className="ld-title">The Commons</div>
          <div className="ld-dots"><span /><span /><span /></div>
        </div>
        <script dangerouslySetInnerHTML={{ __html: `
          if(navigator.standalone||window.matchMedia('(display-mode: standalone)').matches||new URLSearchParams(location.search).has('standalone')){
            document.getElementById('loading').style.display='none';
            document.documentElement.style.overflow='auto';
            document.body.style.overflow='auto';
            var appStyle=document.createElement('style');
            appStyle.textContent='#app{display:block!important}';
            document.head.appendChild(appStyle);
          }
        `}} />
        <div id="app" style={{ display: "none" }}>
          <Suspense>
            <GoogleAnalytics />
          </Suspense>
          <QueryProvider>
            <AppShell>{children}</AppShell>
          </QueryProvider>
        </div>
        <script src="/splash-runtime.js" defer />
      </body>
    </html>
  );
}
