"use client";

import { Bookmark, GraduationCap } from "lucide-react";
import { useAuth } from "@/providers/auth-provider";
import { useLibrary } from "@/hooks/use-library";
import { CourseCard } from "@/components/course-card";
import { CourseCardSkeleton } from "@/components/ui/skeleton";

export default function LibraryPage() {
  const { user, isLoading: authLoading } = useAuth();
  const { data: courses, isLoading } = useLibrary();

  if (authLoading) {
    return (
      <div className="max-w-screen-2xl mx-auto px-4 md:px-8 py-16">
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-4">
          {Array.from({ length: 12 }).map((_, i) => (
            <CourseCardSkeleton key={i} />
          ))}
        </div>
      </div>
    );
  }

  if (!user) {
    return (
      <div className="max-w-screen-2xl mx-auto px-4 md:px-8 py-24 flex flex-col items-center text-center gap-4">
        <GraduationCap className="h-16 w-16 text-primary/40" />
        <h1 className="text-2xl font-bold">Your Library</h1>
        <p className="text-muted-foreground max-w-sm">
          Sign in to save courses and build your personal library.
        </p>
      </div>
    );
  }

  return (
    <div className="max-w-screen-2xl mx-auto px-4 md:px-8 py-10">
      <div className="flex items-center gap-3 mb-8">
        <Bookmark className="h-6 w-6 text-primary" />
        <h1 className="text-2xl font-bold">My Library</h1>
        {courses && courses.length > 0 && (
          <span className="text-sm text-muted-foreground">
            {courses.length} course{courses.length !== 1 ? "s" : ""}
          </span>
        )}
      </div>

      {isLoading ? (
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-4">
          {Array.from({ length: 12 }).map((_, i) => (
            <CourseCardSkeleton key={i} />
          ))}
        </div>
      ) : !courses || courses.length === 0 ? (
        <div className="flex flex-col items-center text-center gap-4 py-20">
          <Bookmark className="h-14 w-14 text-muted-foreground/30" />
          <p className="text-lg font-semibold">No saved courses yet</p>
          <p className="text-muted-foreground text-sm max-w-sm">
            Hover over any course card and click the bookmark icon to save it here.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-4">
          {courses.map((course) => (
            <CourseCard key={course.id} course={course} />
          ))}
        </div>
      )}
    </div>
  );
}
