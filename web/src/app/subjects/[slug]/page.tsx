"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { useParams } from "next/navigation";
import Link from "next/link";
import { ChevronLeft, LayoutGrid, List } from "lucide-react";
import { CourseCard } from "@/components/course-card";
import { CourseCardSkeleton } from "@/components/ui/skeleton";
import { fetchStrictSubjectCourses } from "@/lib/api";
import { cn } from "@/lib/utils";
import type { CourseSummary } from "@/types";

const LEVEL_LABEL: Record<string, string> = {
  undergraduate: "Undergrad",
  graduate: "Graduate",
  introductory: "Intro",
  advanced: "Advanced",
};

function CourseListRow({ course }: { course: CourseSummary }) {
  return (
    <Link
      href={`/courses/${course.slug}`}
      className="grid grid-cols-[2fr,1fr,auto] items-start gap-x-6 gap-y-0 px-4 py-3 hover:bg-muted/60 transition-colors group"
    >
      <p className="text-sm font-medium leading-snug group-hover:text-primary transition-colors break-words">
        {course.title}
      </p>
      <p className="text-sm text-muted-foreground leading-snug break-words">
        {course.university_name}
      </p>
      <div className="flex items-center gap-2 text-xs text-muted-foreground whitespace-nowrap">
        {course.level && (
          <span className="hidden sm:inline px-2 py-0.5 rounded-full bg-muted border border-border/50">
            {LEVEL_LABEL[course.level] ?? course.level}
          </span>
        )}
        {course.total_videos > 0 && (
          <span className="tabular-nums">{course.total_videos} lectures</span>
        )}
      </div>
    </Link>
  );
}

export default function SubjectPage() {
  const { slug } = useParams<{ slug: string }>();
  const [view, setView] = useState<"grid" | "list">("grid");

  const label = slug
    .replace(/-/g, " ")
    .replace(/\b\w/g, (c) => c.toUpperCase());

  const { data: coursesData, isLoading } = useQuery({
    queryKey: ["subject-courses", slug],
    queryFn: () => fetchStrictSubjectCourses(slug),
    enabled: !!slug,
  });

  const courses = coursesData?.items ?? [];
  const total = courses.length;

  return (
    <div className="max-w-screen-2xl mx-auto px-4 md:px-8 lg:px-12 py-8">
      <Link
        href="/subjects"
        className="inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground mb-6 transition-colors"
      >
        <ChevronLeft className="h-4 w-4" />
        All Subjects
      </Link>

      <div className="flex items-center justify-between gap-4 mb-8">
        <div>
          <h1 className="text-3xl font-bold">{label}</h1>
          {!isLoading && (
            <p className="text-muted-foreground mt-1">{total.toLocaleString()} courses</p>
          )}
        </div>

        {/* View toggle */}
        <div className="flex items-center gap-1 rounded-lg border border-border p-1">
          <button
            onClick={() => setView("grid")}
            aria-label="Grid view"
            className={cn(
              "p-1.5 rounded-md transition-colors",
              view === "grid"
                ? "bg-primary text-primary-foreground"
                : "text-muted-foreground hover:text-foreground"
            )}
          >
            <LayoutGrid className="h-4 w-4" />
          </button>
          <button
            onClick={() => setView("list")}
            aria-label="List view"
            className={cn(
              "p-1.5 rounded-md transition-colors",
              view === "list"
                ? "bg-primary text-primary-foreground"
                : "text-muted-foreground hover:text-foreground"
            )}
          >
            <List className="h-4 w-4" />
          </button>
        </div>
      </div>

      {isLoading ? (
        view === "grid" ? (
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 xl:grid-cols-5 2xl:grid-cols-6 gap-4">
            {Array.from({ length: 18 }).map((_, i) => (
              <CourseCardSkeleton key={i} />
            ))}
          </div>
        ) : (
          <div className="divide-y divide-border rounded-xl border border-border overflow-hidden">
            {Array.from({ length: 18 }).map((_, i) => (
              <div key={i} className="px-4 py-3 animate-pulse flex items-center gap-4">
                <div className="flex-1 space-y-2">
                  <div className="h-4 bg-muted rounded w-3/4" />
                  <div className="h-3 bg-muted rounded w-1/3" />
                </div>
                <div className="h-3 bg-muted rounded w-16" />
              </div>
            ))}
          </div>
        )
      ) : courses.length === 0 ? (
        <p className="text-muted-foreground text-center py-20">
          No courses found in this subject.
        </p>
      ) : view === "grid" ? (
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 xl:grid-cols-5 2xl:grid-cols-6 gap-4">
          {courses.map((course) => (
            <CourseCard key={course.id} course={course} />
          ))}
        </div>
      ) : (
        <div className="rounded-xl border border-border overflow-hidden divide-y divide-border">
          {courses.map((course) => (
            <CourseListRow key={course.id} course={course} />
          ))}
        </div>
      )}
    </div>
  );
}

