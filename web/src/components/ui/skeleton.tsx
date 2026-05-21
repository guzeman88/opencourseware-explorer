import { cn } from "@/lib/utils";

interface SkeletonProps {
  className?: string;
}

export function Skeleton({ className }: SkeletonProps) {
  return (
    <div
      className={cn(
        "animate-pulse rounded-md bg-muted",
        className
      )}
    />
  );
}

export function CourseCardSkeleton() {
  return (
    <div className="w-full rounded-lg overflow-hidden bg-card border border-border/50">
      <Skeleton className="aspect-video w-full" />
      <div className="p-3 space-y-2">
        <Skeleton className="h-3 w-16 rounded-full" />
        <Skeleton className="h-4 w-full" />
        <Skeleton className="h-4 w-3/4" />
        <Skeleton className="h-3 w-1/2" />
      </div>
    </div>
  );
}

export function CourseDetailSkeleton() {
  return (
    <div className="space-y-4">
      <Skeleton className="h-64 md:h-[450px] w-full rounded-lg" />
      <Skeleton className="h-8 w-3/4" />
      <Skeleton className="h-5 w-1/2" />
      <Skeleton className="h-4 w-full" />
      <Skeleton className="h-4 w-5/6" />
    </div>
  );
}

export function UniversityCardSkeleton() {
  return (
    <div className="rounded-lg overflow-hidden bg-card border border-border/50 p-6 space-y-3">
      <Skeleton className="h-12 w-12 rounded-full" />
      <Skeleton className="h-5 w-3/4" />
      <Skeleton className="h-4 w-full" />
      <Skeleton className="h-3 w-1/3" />
    </div>
  );
}
