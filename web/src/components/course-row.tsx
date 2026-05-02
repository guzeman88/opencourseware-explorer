"use client";

import { useRef, useState, useEffect } from "react";
import { ChevronLeft, ChevronRight } from "lucide-react";
import { useQuery } from "@tanstack/react-query";
import { CourseCard } from "@/components/course-card";
import { CourseCardSkeleton } from "@/components/ui/skeleton";
import {
  fetchFeaturedCourses,
  fetchCourses,
  fetchUniversityCourses,
} from "@/lib/api";
import type { CourseLevel } from "@/types";

interface CourseRowProps {
  title: string;
  queryKey: string;
  fetchType: "featured" | "university" | "subject" | "level";
  universitySlug?: string;
  subjectSlug?: string;
  level?: CourseLevel;
  /** First visible row — prioritise image loading */
  priority?: boolean;
}

export function CourseRow({
  title,
  queryKey,
  fetchType,
  universitySlug,
  subjectSlug,
  level,
  priority = false,
}: CourseRowProps) {
  const rowRef = useRef<HTMLDivElement>(null);
  const sectionRef = useRef<HTMLElement>(null);

  // Priority rows (above the fold) load immediately; others wait until near-visible.
  const [isVisible, setIsVisible] = useState(priority);

  useEffect(() => {
    if (priority) return;
    const el = sectionRef.current;
    if (!el) return;
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setIsVisible(true);
          observer.disconnect();
        }
      },
      { rootMargin: "300px" } // preload 300px before entering viewport
    );
    observer.observe(el);
    return () => observer.disconnect();
  }, [priority]);

  const { data, isLoading } = useQuery({
    queryKey: ["row", queryKey],
    queryFn: () => {
      if (fetchType === "featured") return fetchFeaturedCourses(18);
      if (fetchType === "university" && universitySlug)
        return fetchUniversityCourses(universitySlug, { page_size: 18, sort_by: "view_count", sort_dir: "desc" });
      return fetchCourses({
        subject_slug: fetchType === "subject" ? subjectSlug : undefined,
        level: fetchType === "level" ? level : undefined,
        page_size: 18,
        sort_by: "view_count",
        sort_dir: "desc",
      });
    },
    enabled: isVisible,
  });

  const courses = data?.items ?? [];
  const showSkeleton = !isVisible || isLoading;

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
    <section ref={sectionRef} className="relative group/row">
      <h2 className="text-lg md:text-xl font-semibold text-foreground mb-3">
        {title}
      </h2>

      <div className="relative">
        {/* Left arrow */}
        <button
          onClick={() => scroll("left")}
          className="absolute -left-4 top-1/2 -translate-y-1/2 z-10 bg-background/80 hover:bg-background border border-border rounded-full p-1.5 opacity-0 group-hover/row:opacity-100 transition-opacity shadow-lg"
          aria-label="Scroll left"
        >
          <ChevronLeft className="h-5 w-5" />
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

        {/* Right arrow */}
        <button
          onClick={() => scroll("right")}
          className="absolute -right-4 top-1/2 -translate-y-1/2 z-10 bg-background/80 hover:bg-background border border-border rounded-full p-1.5 opacity-0 group-hover/row:opacity-100 transition-opacity shadow-lg"
          aria-label="Scroll right"
        >
          <ChevronRight className="h-5 w-5" />
        </button>
      </div>
    </section>
  );
}
