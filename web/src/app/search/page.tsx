"use client";

import { Suspense } from "react";
import { useSearchParams } from "next/navigation";
import { CourseCard } from "@/components/course-card";
import { CourseCardSkeleton } from "@/components/ui/skeleton";
import { useSearchCourses } from "@/hooks/use-courses";
import { Search } from "lucide-react";

export default function SearchPage() {
  return (
    <Suspense fallback={<div className="max-w-screen-xl mx-auto px-4 md:px-8 py-8"><div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 xl:grid-cols-5 gap-4">{Array.from({ length: 10 }).map((_, i) => (<CourseCardSkeleton key={i} />))}</div></div>}>
      <SearchContent />
    </Suspense>
  );
}

function SearchContent() {
  const searchParams = useSearchParams();
  const q = searchParams.get("q") ?? "";
  const { data, isLoading } = useSearchCourses(q);
  const courses = data?.items ?? [];

  return (
    <div className="max-w-screen-xl mx-auto px-4 md:px-8 py-8">
      <div className="mb-8">
        <div className="flex items-center gap-2 text-muted-foreground mb-1">
          <Search className="h-4 w-4" />
          <span className="text-sm">Search results</span>
        </div>
        <h1 className="text-2xl font-bold">
          {q ? `"${q}"` : "Enter a search query"}
        </h1>
        {!isLoading && q && (
          <p className="text-muted-foreground mt-1">
            {data?.total ?? 0} courses found
          </p>
        )}
      </div>

      {!q ? (
        <p className="text-muted-foreground text-center py-20">
          Use the search bar above to find courses.
        </p>
      ) : isLoading ? (
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 xl:grid-cols-5 gap-4">
          {Array.from({ length: 10 }).map((_, i) => (
            <CourseCardSkeleton key={i} />
          ))}
        </div>
      ) : courses.length === 0 ? (
        <div className="text-center py-20 text-muted-foreground">
          <Search className="h-12 w-12 mx-auto opacity-30 mb-3" />
          <p>No courses found for "{q}"</p>
          <p className="text-sm mt-1">Try a different search term</p>
        </div>
      ) : (
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 xl:grid-cols-5 gap-4">
          {courses.map((course) => (
            <CourseCard key={course.id} course={course} />
          ))}
        </div>
      )}
    </div>
  );
}
