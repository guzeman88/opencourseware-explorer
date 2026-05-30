"use client";

import Image from "next/image";
import Link from "next/link";
import { Play, BookOpen, Bookmark } from "lucide-react";
import { cn, levelLabel, levelColor, thumbnailUrl, universityGradient, formatNumber } from "@/lib/utils";
import { useAuth } from "@/providers/auth-provider";
import { useAuthModal } from "@/providers/auth-modal-provider";
import { useLibraryStatus, useLibraryToggle } from "@/hooks/use-library";
import type { CourseSummary } from "@/types";

interface CourseCardProps {
  course: CourseSummary;
  className?: string;
  /** Set true for cards in the first visible row */
  priority?: boolean;
}

/** First ~2 "words" of the title as block initials, e.g. "Linear Algebra" → "LA" */
function initials(title: string): string {
  return title
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((w) => w[0].toUpperCase())
    .join("");
}

export function CourseCard({ course, className, priority = false }: CourseCardProps) {
  const thumb = thumbnailUrl(course);
  const [gradFrom, gradTo] = universityGradient(course.source_key);
  const { user } = useAuth();
  const { openAuthModal } = useAuthModal();
  const { data: saved } = useLibraryStatus(course.id);
  const { mutate: toggleLibrary } = useLibraryToggle(course.id);

  function handleBookmark(e: React.MouseEvent) {
    e.preventDefault();
    e.stopPropagation();
    if (!user) {
      openAuthModal();
      return;
    }
    toggleLibrary(!!saved);
  }

  return (
    <Link
      href={`/courses/${course.slug}`}
      className={cn(
        "group relative flex-shrink-0 w-52 rounded-lg overflow-hidden bg-card border border-border/50",
        "transition-all duration-300 hover:scale-105 hover:border-primary/50 hover:shadow-2xl hover:shadow-black/50",
        className
      )}
    >
      {/* Thumbnail */}
      <div className="relative aspect-video bg-muted">
        {thumb ? (
          <Image
            src={thumb}
            alt={course.title}
            fill
            className="object-cover transition-opacity group-hover:opacity-90"
            unoptimized
            sizes="208px"
            priority={priority}
            loading={priority ? "eager" : "lazy"}
          />
        ) : (
          /* Gradient placeholder with initials */
          <div
            className="absolute inset-0 flex flex-col items-center justify-center gap-1 select-none"
            style={{ background: `linear-gradient(135deg, ${gradFrom}, ${gradTo})` }}
          >
            <span className="text-3xl font-black tracking-tight text-white/90 drop-shadow">
              {initials(course.title)}
            </span>
            <span className="text-[10px] font-medium text-white/60 uppercase tracking-widest text-center px-2 line-clamp-1">
              {course.subjects[0]?.name ?? course.university_name}
            </span>
            {course.course_number && (
              <span className="text-[9px] text-white/40 font-mono mt-0.5">
                {course.course_number}
              </span>
            )}
          </div>
        )}

        {/* Play overlay */}
        <div className="absolute inset-0 bg-black/0 group-hover:bg-black/30 transition-colors flex items-center justify-center">
          <div className="opacity-0 group-hover:opacity-100 transition-opacity bg-primary rounded-full p-2">
            <Play className="h-4 w-4 fill-white text-white" />
          </div>
        </div>

        {/* Bookmark button */}
        <button
          onClick={handleBookmark}
          className={cn(
            "absolute top-1.5 left-1.5 transition-opacity rounded-full p-1.5",
            "bg-black/60 hover:bg-black/80",
            saved ? "opacity-100" : "opacity-0 group-hover:opacity-100"
          )}
          aria-label={saved ? "Remove from library" : "Save to library"}
        >
          <Bookmark
            className={cn(
              "h-3.5 w-3.5",
              saved ? "fill-primary text-primary" : "text-white"
            )}
          />
        </button>

        {/* Video count badge */}
        {course.total_videos > 0 && (
          <div className="absolute top-1.5 right-1.5 bg-black/70 text-white text-xs px-1.5 py-0.5 rounded flex items-center gap-1">
            <Play className="h-3 w-3 fill-current" />
            {course.total_videos}
          </div>
        )}
      </div>

      {/* Info */}
      <div className="p-3 space-y-1.5">
        {/* Level badge */}
        <div className="flex items-center justify-between">
          <span
            className={cn(
              "text-xs px-1.5 py-0.5 rounded-full font-medium",
              levelColor(course.level)
            )}
          >
            {levelLabel(course.level)}
          </span>
          {course.view_count !== undefined && course.view_count > 0 && (
            <span className="text-xs text-muted-foreground">
              {formatNumber(course.view_count)} views
            </span>
          )}
        </div>

        {/* Title */}
        <h3 className="text-sm font-semibold text-foreground line-clamp-2 leading-snug">
          {course.title}
        </h3>

        {/* University */}
        <p className="text-xs text-muted-foreground">{course.university_name}</p>

        {/* Material icons */}
        <div className="flex items-center gap-2 pt-0.5">
          {course.has_video_lectures && (
            <span title="Video Lectures">
              <BookOpen className="h-3 w-3 text-primary" />
            </span>
          )}
        </div>
      </div>
    </Link>
  );
}
