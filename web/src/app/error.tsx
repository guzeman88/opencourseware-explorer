"use client";

import { useEffect } from "react";
import { Button } from "@/components/ui/button";

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    import("@sentry/nextjs").then(({ captureException }) => captureException(error));
  }, [error]);

  return (
    <div className="flex flex-col items-center justify-center min-h-[50vh] space-y-4 px-4">
      <h2 className="text-xl font-semibold text-foreground">Something went wrong</h2>
      <p className="text-muted-foreground text-sm text-center max-w-sm">
        We couldn't load this page. This might be a temporary issue.
      </p>
      <Button variant="outline" onClick={reset}>
        Try again
      </Button>
    </div>
  );
}
