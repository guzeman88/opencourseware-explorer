"use client";

import { useUniversity } from "@/hooks/use-universities";
import { useUniversityCourses } from "@/hooks/use-courses";
import { CourseCard } from "@/components/course-card";
import { CourseCardSkeleton } from "@/components/ui/skeleton";
import { Button } from "@/components/ui/button";
import { GraduationCap, ExternalLink, ChevronLeft, ChevronRight } from "lucide-react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { useState } from "react";

export default function UniversityPage() {
  const { slug } = useParams<{ slug: string }>();
  const { data: uni, isLoading: uniLoading } = useUniversity(slug);
  const [page, setPage] = useState(1);
  const { data: coursesData, isLoading: coursesLoading } = useUniversityCourses(
    slug,
    { page, page_size: 24, sort_by: "view_count", sort_dir: "desc" }
  );

  const courses = coursesData?.items ?? [];
  const pages = coursesData?.pages ?? 1;
  const total = coursesData?.total ?? 0;

  return (
    <div className="max-w-screen-xl mx-auto px-4 md:px-8 py-8 space-y-8">
      {/* University header */}
      <div className="flex items-start gap-5">
        <div className="w-16 h-16 rounded-full bg-primary/10 flex items-center justify-center shrink-0">
          <GraduationCap className="h-8 w-8 text-primary" />
        </div>
        <div className="space-y-1">
          {uniLoading ? (
            <div className="h-7 w-48 bg-muted animate-pulse rounded" />
          ) : (
            <>
              <h1 className="text-2xl font-bold">{uni?.name}</h1>
              {uni?.country && (
                <p className="text-sm text-muted-foreground">{uni.country}</p>
              )}
              {uni?.description && (
                <p className="text-muted-foreground max-w-2xl">{uni.description}</p>
              )}
              {uni?.website && (
                <a
                  href={uni.website}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-1.5 text-sm text-primary hover:underline"
                >
                  <ExternalLink className="h-3.5 w-3.5" />
                  {uni.website}
                </a>
              )}
            </>
          )}
        </div>
      </div>

      {/* Course grid */}
      <div>
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-semibold">
            Courses
            {!coursesLoading && total > 0 && (
              <span className="ml-2 text-muted-foreground font-normal text-base">
                ({total.toLocaleString()})
              </span>
            )}
          </h2>
        </div>

        {coursesLoading ? (
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 xl:grid-cols-6 gap-4">
            {Array.from({ length: 12 }).map((_, i) => (
              <CourseCardSkeleton key={i} />
            ))}
          </div>
        ) : courses.length === 0 ? (
          <p className="text-muted-foreground text-center py-16">
            No courses found for this university.
          </p>
        ) : (
          <>
            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 xl:grid-cols-6 gap-4">
              {courses.map((c) => (
                <CourseCard key={c.id} course={c} />
              ))}
            </div>

            {pages > 1 && (
              <div className="flex items-center justify-center gap-2 mt-8">
                <Button
                  variant="secondary"
                  size="sm"
                  disabled={page <= 1}
                  onClick={() => setPage(page - 1)}
                >
                  <ChevronLeft className="h-4 w-4" />
                </Button>
                <span className="text-sm text-muted-foreground">
                  Page {page} of {pages}
                </span>
                <Button
                  variant="secondary"
                  size="sm"
                  disabled={page >= pages}
                  onClick={() => setPage(page + 1)}
                >
                  <ChevronRight className="h-4 w-4" />
                </Button>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}
