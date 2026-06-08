"use client";

import { useEffect } from "react";
import { Button } from "@/components/ui/button";

export default function CourseError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error(error);
  }, [error]);

  return (
    <div className="max-w-screen-xl mx-auto px-4 md:px-8 py-16 flex flex-col items-center space-y-4">
      <h2 className="text-xl font-semibold text-foreground">Course unavailable</h2>
      <p className="text-muted-foreground text-sm text-center max-w-sm">
        We couldn&apos;t load this course. It may have been removed or there was a
        network error.
      </p>
      <div className="flex gap-3">
        <Button variant="outline" onClick={reset}>
          Try again
        </Button>
        <Button variant="ghost" onClick={() => window.history.back()}>
          Go back
        </Button>
      </div>
    </div>
  );
}
