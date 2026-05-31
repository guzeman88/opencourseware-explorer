"use client";

import Script from "next/script";
import { usePathname, useSearchParams } from "next/navigation";
import { useEffect } from "react";

const GA_ID = process.env.NEXT_PUBLIC_GA_MEASUREMENT_ID;

/** Fire a GA4 page_view event (called on client-side navigations) */
function pageview(url: string) {
  if (!GA_ID || typeof window === "undefined") return;
  (window as any).gtag?.("config", GA_ID, { page_path: url });
}

/** Thin wrapper so you can track custom events anywhere in the app:
 *  trackEvent({ action: "bookmark_added", category: "library", label: courseId })
 */
export function trackEvent({
  action,
  category,
  label,
  value,
}: {
  action: string;
  category?: string;
  label?: string;
  value?: number;
}) {
  if (!GA_ID || typeof window === "undefined") return;
  (window as any).gtag?.("event", action, {
    event_category: category,
    event_label: label,
    value,
  });
}

/** Drop this inside layout.tsx once NEXT_PUBLIC_GA_MEASUREMENT_ID is set. */
export function GoogleAnalytics() {
  if (!GA_ID) return null;

  return (
    <>
      <Script
        src={`https://www.googletagmanager.com/gtag/js?id=${GA_ID}`}
        strategy="afterInteractive"
      />
      <Script id="ga4-init" strategy="afterInteractive">
        {`
          window.dataLayer = window.dataLayer || [];
          function gtag(){dataLayer.push(arguments);}
          gtag('js', new Date());
          gtag('config', '${GA_ID}', {
            page_path: window.location.pathname,
            anonymize_ip: true,
            cookie_flags: 'SameSite=None;Secure'
          });
        `}
      </Script>
      <PageViewTracker />
    </>
  );
}

/** Fires a page_view on every client-side route change (App Router). */
function PageViewTracker() {
  const pathname = usePathname();
  const searchParams = useSearchParams();

  useEffect(() => {
    const url = pathname + (searchParams.toString() ? `?${searchParams}` : "");
    pageview(url);
  }, [pathname, searchParams]);

  return null;
}
