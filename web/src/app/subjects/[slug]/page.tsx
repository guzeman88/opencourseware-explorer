"use client";

import { useQuery } from "@tanstack/react-query";
import { useParams } from "next/navigation";
import { CourseCard } from "@/components/course-card";
import { CourseCardSkeleton } from "@/components/ui/skeleton";
import { fetchCourses, fetchSubjects } from "@/lib/api";
import Link from "next/link";
import { ChevronLeft } from "lucide-react";

export default function SubjectPage() {
  const { slug } = useParams<{ slug: string }>();

  const label = slug
    .replace(/-/g, " ")
    .replace(/\b\w/g, (c) => c.toUpperCase());

  const { data: coursesData, isLoading } = useQuery({
    queryKey: ["subject-courses", slug],
    queryFn: () =>
      fetchCourses({ subject_slug: slug, page_size: 48, sort_by: "relevance" }),
    enabled: !!slug,
  });

  const courses = coursesData?.items ?? [];
  const total = coursesData?.total ?? 0;

  return (
    <div className="max-w-screen-2xl mx-auto px-4 md:px-8 lg:px-12 py-8">
      <Link
        href="/subjects"
        className="inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground mb-6 transition-colors"
      >
        <ChevronLeft className="h-4 w-4" />
        All Subjects
      </Link>

      <div className="mb-8">
        <h1 className="text-3xl font-bold">{label}</h1>
        {!isLoading && (
          <p className="text-muted-foreground mt-1">{total.toLocaleString()} courses</p>
        )}
      </div>

      {isLoading ? (
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 xl:grid-cols-5 2xl:grid-cols-6 gap-4">
          {Array.from({ length: 18 }).map((_, i) => (
            <CourseCardSkeleton key={i} />
          ))}
        </div>
      ) : courses.length === 0 ? (
        <p className="text-muted-foreground text-center py-20">
          No courses found in this subject.
        </p>
      ) : (
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 xl:grid-cols-5 2xl:grid-cols-6 gap-4">
          {courses.map((course) => (
            <CourseCard key={course.id} course={course} />
          ))}
        </div>
      )}
    </div>
  );
}
