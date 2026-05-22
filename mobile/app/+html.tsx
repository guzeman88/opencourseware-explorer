import { ScrollViewStyleReset } from "expo-router/html";

export default function Root({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <head>
        <meta charSet="utf-8" />
        <meta httpEquiv="X-UA-Compatible" content="IE=edge" />
        <meta
          name="viewport"
          content="width=device-width, initial-scale=1, shrink-to-fit=no"
        />

        {/* PWA / iOS home screen */}
        <meta name="apple-mobile-web-app-capable" content="yes" />
        <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent" />
        <meta name="apple-mobile-web-app-title" content="OCW Explorer" />
        <meta name="mobile-web-app-capable" content="yes" />
        <meta name="theme-color" content="#141414" />

        {/* No service worker registered — updates are handled by HTTP Cache-Control headers */}

        <ScrollViewStyleReset />
      </head>
      <body>{children}</body>
    </html>
  );
}
