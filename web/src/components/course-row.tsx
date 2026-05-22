"use client";

import { useRef, useState, useEffect, memo } from "react";
import { ChevronLeft, ChevronRight } from "lucide-react";
import { useQuery } from "@tanstack/react-query";
import { CourseCard } from "@/components/course-card";
import { CourseCardSkeleton } from "@/components/ui/skeleton";
import {
  fetchFeaturedCourses,
  fetchCourses,
  fetchUniversityCourses,
} from "@/lib/api";
import type { CourseLevel, PaginatedList, CourseSummary } from "@/types";

interface CourseRowProps {
  title: string;
  queryKey: string;
  fetchType: "featured" | "university" | "subject" | "level" | "query";
  universitySlug?: string;
  subjectSlug?: string;
  level?: CourseLevel;
  /** Free-text search query for fetchType="query" rows */
  queryString?: string;
  /** First visible row — prioritise image loading */
  priority?: boolean;
  /** Server-fetched data to hydrate immediately without a client request */
  initialData?: PaginatedList<CourseSummary>;
}

export const CourseRow = memo(function CourseRow({
  title,
  queryKey,
  fetchType,
  universitySlug,
  subjectSlug,
  level,
  queryString,
  priority = false,
  initialData,
}: CourseRowProps) {
  const rowRef = useRef<HTMLDivElement>(null);
  const sectionRef = useRef<HTMLElement>(null);

  // If we have server data, show immediately; otherwise wait until visible.
  const [isVisible, setIsVisible] = useState(priority || !!initialData);

  // Whether this row started with real SSR data (never show animation for these).
  // Rows that begin as skeletons and later receive client data should animate in.
  const hadSSRData = !!(initialData && (initialData.items?.length ?? 0) > 0);

  // `loaded` just means "we have real cards now" — animation class only applied
  // when we transitioned from skeleton→data (i.e. !hadSSRData)
  const [loaded, setLoaded] = useState(false);

  useEffect(() => {
    if (priority || initialData) return;
    const el = sectionRef.current;
    if (!el) return;
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setIsVisible(true);
          observer.disconnect();
        }
      },
      // 300px pre-load margin — enough to feel instant without firing 20+ requests at once
      { rootMargin: "300px" }
    );
    observer.observe(el);
    return () => observer.disconnect();
  }, [priority, initialData]);

  const { data, isLoading } = useQuery({
    queryKey: ["row", queryKey],
    queryFn: () => {
      if (fetchType === "featured") return fetchFeaturedCourses(18);
      if (fetchType === "university" && universitySlug)
        return fetchUniversityCourses(universitySlug, { page_size: 18, sort_by: "view_count", sort_dir: "desc", has_video_lectures: true });
      return fetchCourses({
        subject_slug: fetchType === "subject" ? subjectSlug : undefined,
        level: fetchType === "level" ? level : undefined,
        q: fetchType === "query" ? queryString : undefined,
        page_size: 18,
        sort_by: "view_count",
        sort_dir: "desc",
        has_video_lectures: true,
      });
    },
    enabled: isVisible,
    initialData,
  });

  const courses = data?.items ?? [];
  const showSkeleton = !isVisible || isLoading;

  // Trigger reveal animation the moment real cards replace skeletons
  useEffect(() => {
    if (!isLoading && courses.length > 0 && !loaded) {
      setLoaded(true);
    }
  }, [isLoading, courses.length, loaded]);

  function scroll(dir: "left" | "right") {
    if (!rowRef.current) return;
    const amount = rowRef.current.clientWidth * 0.75;
    rowRef.current.scrollBy({
      left: dir === "left" ? -amount : amount,
      behavior: "smooth",
    });
  }

  if (!showSkeleton && courses.length === 0) return null;

  return (
    <section
      ref={sectionRef}
      className={`relative group/row content-row${loaded && !hadSSRData ? " row-revealed" : ""}`}
    >
      <h2 className="text-base md:text-lg font-semibold text-foreground/90 mb-3 tracking-tight flex items-center gap-2">
        <span className="h-4 w-0.5 rounded-full bg-primary inline-block" />
        {title}
      </h2>

      <div className="relative">
        {/* Left gradient + arrow */}
        <div className="absolute left-0 top-0 bottom-4 w-16 bg-gradient-to-r from-background to-transparent z-10 pointer-events-none opacity-0 group-hover/row:opacity-100 transition-opacity" />
        <button
          onClick={() => scroll("left")}
          className="absolute -left-3 top-1/2 -translate-y-1/2 z-20 h-9 w-9 bg-card hover:bg-accent border border-white/[0.1] rounded-full flex items-center justify-center opacity-0 group-hover/row:opacity-100 transition-all duration-200 shadow-xl hover:scale-110 active:scale-95"
          aria-label="Scroll left"
        >
          <ChevronLeft className="h-4 w-4" />
        </button>

        {/* Scroll row */}
        <div ref={rowRef} className="scroll-row">
          {showSkeleton
            ? Array.from({ length: 8 }).map((_, i) => (
                <CourseCardSkeleton key={i} />
              ))
            : courses.map((course, i) => (
                <CourseCard key={course.id} course={course} priority={priority && i < 4} />
              ))}
        </div>

        {/* Right gradient + arrow */}
        <div className="absolute right-0 top-0 bottom-4 w-16 bg-gradient-to-l from-background to-transparent z-10 pointer-events-none opacity-0 group-hover/row:opacity-100 transition-opacity" />
        <button
          onClick={() => scroll("right")}
          className="absolute -right-3 top-1/2 -translate-y-1/2 z-20 h-9 w-9 bg-card hover:bg-accent border border-white/[0.1] rounded-full flex items-center justify-center opacity-0 group-hover/row:opacity-100 transition-all duration-200 shadow-xl hover:scale-110 active:scale-95"
          aria-label="Scroll right"
        >
          <ChevronRight className="h-4 w-4" />
        </button>
      </div>
    </section>
  );
});
