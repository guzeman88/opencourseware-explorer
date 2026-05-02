"use client";

import { useQuery } from "@tanstack/react-query";
import { fetchSubjects } from "@/lib/api";
import Link from "next/link";
import { BookOpen } from "lucide-react";

export default function SubjectsPage() {
  const { data, isLoading } = useQuery({
    queryKey: ["subjects"],
    queryFn: () => fetchSubjects(false),
  });

  // Sort by course_count descending so the most-populated subjects appear first
  const subjects = [...(data?.items ?? [])].sort(
    (a, b) => (b.course_count ?? 0) - (a.course_count ?? 0)
  );

  return (
    <div className="max-w-screen-xl mx-auto px-4 md:px-8 py-8">
      <h1 className="text-2xl font-bold mb-2">Subjects</h1>
      <p className="text-muted-foreground mb-8">
        Explore courses by academic subject area.
      </p>

      {isLoading ? (
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-3">
          {Array.from({ length: 12 }).map((_, i) => (
            <div key={i} className="h-14 rounded-lg bg-muted animate-pulse" />
          ))}
        </div>
      ) : (
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-3 mb-12">
          {subjects.map((subject) => (
            <Link
              key={subject.id}
              href={`/subjects/${subject.slug}`}
              className="group flex items-center justify-between px-4 py-3 rounded-lg bg-card border border-border/50 hover:border-primary/50 hover:bg-primary/5 transition-all"
            >
              <div className="flex items-center gap-2 min-w-0">
                <BookOpen className="h-4 w-4 text-muted-foreground shrink-0 group-hover:text-primary transition-colors" />
                <span className="text-sm font-medium truncate">{subject.name}</span>
              </div>
              {subject.course_count != null && subject.course_count > 0 && (
                <span className="ml-2 text-xs text-muted-foreground shrink-0 tabular-nums">
                  {subject.course_count}
                </span>
              )}
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
