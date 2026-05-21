"use client";

import { memo } from "react";
import Image from "next/image";
import Link from "next/link";
import { Play, Bookmark, Eye } from "lucide-react";
import { cn, levelLabel, levelColor, thumbnailUrl, universityGradient, formatNumber } from "@/lib/utils";
import type { CourseSummary } from "@/types";
import { useAuth } from "@/providers/auth-provider";
import { useAuthModal } from "@/providers/auth-modal-provider";
import { useLibraryStatus, useLibraryToggle } from "@/hooks/use-library";

interface CourseCardProps {
  course: CourseSummary;
  className?: string;
  /** Set true for cards in the first visible row */
  priority?: boolean;
}

function AuthSaveButton({ courseId }: { courseId: string }) {
  const { data: saved } = useLibraryStatus(courseId);
  const toggle = useLibraryToggle(courseId);

  return (
    <button
      onClick={(e) => {
        e.preventDefault();
        e.stopPropagation();
        toggle.mutate(saved ?? false);
      }}
      title={saved ? "Remove from library" : "Save to library"}
      className={cn(
        "absolute top-2 right-2 z-10 p-1.5 rounded-full transition-all duration-200 shadow-lg",
        "opacity-0 group-hover/card:opacity-100 focus:opacity-100",
        saved
          ? "opacity-100 bg-primary text-primary-foreground scale-110"
          : "bg-black/60 text-white hover:bg-primary hover:text-primary-foreground backdrop-blur-sm"
      )}
    >
      <Bookmark className={cn("h-3.5 w-3.5", saved && "fill-current")} />
    </button>
  );
}

function SaveButton({ courseId }: { courseId: string }) {
  const { token } = useAuth();
  const { openAuthModal } = useAuthModal();

  if (!token) {
    return (
      <button
        onClick={(e) => { e.preventDefault(); e.stopPropagation(); openAuthModal(); }}
        title="Save to library"
        className="absolute top-2 right-2 z-10 p-1.5 rounded-full transition-all duration-200 opacity-0 group-hover/card:opacity-100 bg-black/60 text-white hover:bg-primary hover:text-primary-foreground backdrop-blur-sm shadow-lg"
      >
        <Bookmark className="h-3.5 w-3.5" />
      </button>
    );
  }

  return <AuthSaveButton courseId={courseId} />;
}

function initials(title: string): string {
  return title
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((w) => w[0].toUpperCase())
    .join("");
}

export const CourseCard = memo(function CourseCard({ course, className, priority = false }: CourseCardProps) {
  const thumb = thumbnailUrl(course);
  const [gradFrom, gradTo] = universityGradient(course.source_key);
  const subject = course.subjects[0]?.name;

  return (
    <div className={cn("group/card relative flex-shrink-0 w-[220px]", className)}>
      <SaveButton courseId={course.id} />
      <Link
        href={`/courses/${course.slug}`}
        className="block rounded-xl overflow-hidden bg-card border border-border/60 card-hover"
      >
        {/* Thumbnail */}
        <div className="relative aspect-video bg-muted overflow-hidden">
          {thumb ? (
            <Image
              src={thumb}
              alt={course.title}
              fill
              className="object-cover transition-transform duration-500 [@media(hover:hover)_and_(pointer:fine)]:group-hover/card:scale-105"
              sizes="220px"
              priority={priority}
              loading={priority ? "eager" : "lazy"}
            />
          ) : (
            <div
              className="absolute inset-0 flex flex-col items-center justify-center gap-1.5 select-none"
              style={{ background: `linear-gradient(145deg, ${gradFrom}, ${gradTo})` }}
            >
              <span className="text-4xl font-black tracking-tight text-white/95 drop-shadow-lg">
                {initials(course.title)}
              </span>
              <span className="text-[10px] font-semibold text-white/60 uppercase tracking-[0.15em] text-center px-3 line-clamp-1">
                {subject ?? course.university_name}
              </span>
            </div>
          )}

          {/* Dark overlay gradient at bottom for text legibility */}
          <div className="absolute inset-x-0 bottom-0 h-14 bg-gradient-to-t from-black/70 to-transparent" />

          {/* Play overlay */}
          <div className="absolute inset-0 flex items-center justify-center">
            <div className="opacity-0 [@media(hover:hover)_and_(pointer:fine)]:group-hover/card:opacity-100 transition-all duration-200 bg-primary rounded-full p-2.5 shadow-xl scale-90 [@media(hover:hover)_and_(pointer:fine)]:group-hover/card:scale-100">
              <Play className="h-4 w-4 fill-white text-white" />
            </div>
          </div>

          {/* Video count badge */}
          {course.total_videos > 0 && (
            <div className="absolute bottom-2 left-2 bg-black/80 backdrop-blur-sm text-white text-[11px] px-2 py-0.5 rounded-md flex items-center gap-1 font-medium">
              <Play className="h-2.5 w-2.5 fill-current" />
              {course.total_videos} videos
            </div>
          )}
        </div>

        {/* Info */}
        <div className="p-3 space-y-2">
          <div className="flex items-center justify-between gap-1">
            <span className={cn("text-[11px] px-2 py-0.5 rounded-full font-semibold tracking-wide shrink-0", levelColor(course.level))}>
              {levelLabel(course.level)}
            </span>
            {course.view_count !== undefined && course.view_count > 0 && (
              <span className="text-[11px] text-muted-foreground flex items-center gap-1 shrink-0">
                <Eye className="h-3 w-3" />
                {formatNumber(course.view_count)}
              </span>
            )}
          </div>

          <h3 className="text-sm font-semibold text-foreground line-clamp-2 leading-[1.35] tracking-tight">
            {course.title}
          </h3>

          <div className="flex items-center justify-between pt-0.5">
            <p className="text-[11px] text-muted-foreground truncate">{course.university_name}</p>
            {subject && (
              <span className="text-[10px] text-primary/70 font-medium shrink-0 ml-1 truncate max-w-[80px]">{subject}</span>
            )}
          </div>
        </div>
      </Link>
    </div>
  );
});

