"use client";

import Link from "next/link";
import { GraduationCap, BookOpen } from "lucide-react";
import { useUniversities } from "@/hooks/use-universities";
import { UniversityCardSkeleton } from "@/components/ui/skeleton";
import { sourceLabel } from "@/lib/utils";

export default function UniversitiesPage() {
  const { data, isLoading } = useUniversities(1, 50);
  const universities = data?.items ?? [];

  return (
    <div className="max-w-screen-xl mx-auto px-4 md:px-8 py-8">
      <h1 className="text-2xl font-bold mb-2">Universities</h1>
      <p className="text-muted-foreground mb-8">
        Browse free courses from top universities worldwide.
      </p>

      {isLoading ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-6">
          {Array.from({ length: 6 }).map((_, i) => (
            <UniversityCardSkeleton key={i} />
          ))}
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-6">
          {universities.map((uni) => (
            <Link
              key={uni.id}
              href={`/universities/${uni.slug}`}
              className="group flex flex-col gap-4 p-6 rounded-xl bg-card border border-border/50 hover:border-primary/50 transition-all hover:shadow-lg hover:shadow-black/20"
            >
              <div className="flex items-center gap-4">
                <div className="w-14 h-14 rounded-full bg-primary/10 flex items-center justify-center shrink-0">
                  <GraduationCap className="h-7 w-7 text-primary" />
                </div>
                <div>
                  <h2 className="font-semibold text-foreground group-hover:text-primary transition-colors">
                    {uni.name}
                  </h2>
                  {uni.country && (
                    <p className="text-xs text-muted-foreground">{uni.country}</p>
                  )}
                </div>
              </div>

              {uni.description && (
                <p className="text-sm text-muted-foreground line-clamp-2">
                  {uni.description}
                </p>
              )}

              <div className="flex items-center gap-2 text-sm text-muted-foreground mt-auto">
                <BookOpen className="h-4 w-4" />
                <span>
                  {uni.course_count != null
                    ? `${uni.course_count} courses`
                    : sourceLabel(uni.source_key)}
                </span>
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
