"use client";

import Link from "next/link";
import { GraduationCap } from "lucide-react";
import { useUniversities } from "@/hooks/use-universities";
import { UniversityCardSkeleton } from "@/components/ui/skeleton";
import { sourceLabel } from "@/lib/utils";

export function UniversityGrid() {
  const { data, isLoading } = useUniversities(1, 12);
  const universities = data?.items ?? [];

  if (isLoading) {
    return (
      <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-4">
        {Array.from({ length: 6 }).map((_, i) => (
          <UniversityCardSkeleton key={i} />
        ))}
      </div>
    );
  }

  return (
    <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-4">
      {universities.map((uni) => (
        <Link
          key={uni.id}
          href={`/universities/${uni.slug}`}
          className="group flex flex-col items-center gap-3 p-4 rounded-lg bg-card border border-border/50 hover:border-primary/50 transition-all hover:scale-105 text-center"
        >
          <div className="w-12 h-12 rounded-full bg-primary/10 flex items-center justify-center">
            <GraduationCap className="h-6 w-6 text-primary" />
          </div>
          <div>
            <p className="text-sm font-semibold text-foreground leading-tight">
              {sourceLabel(uni.source_key)}
            </p>
            {uni.course_count !== undefined && (
              <p className="text-xs text-muted-foreground mt-0.5">
                {uni.course_count} courses
              </p>
            )}
          </div>
        </Link>
      ))}
    </div>
  );
}
