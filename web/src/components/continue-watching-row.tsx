"use client";

import { useRef } from "react";
import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import Image from "next/image";
import { ChevronLeft, ChevronRight, Play } from "lucide-react";
import { useAuth } from "@/providers/auth-provider";
import { fetchWatchHistory } from "@/lib/api";
import { cn, thumbnailUrl, universityGradient } from "@/lib/utils";
import type { WatchHistoryEntry } from "@/types";

function initials(title: string): string {
  return title
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((w) => w[0].toUpperCase())
    .join("");
}

function WatchCard({ entry }: { entry: WatchHistoryEntry }) {
  const { course, video_index } = entry;
  const thumb = thumbnailUrl(course);
  const [gradFrom, gradTo] = universityGradient(course.source_key);
  const progress =
    course.total_videos > 0
      ? Math.round(((video_index + 1) / course.total_videos) * 100)
      : 0;

  return (
    <Link
      href={`/courses/${course.slug}?v=${video_index}`}
      className="relative shrink-0 w-[180px] sm:w-[200px] rounded-lg overflow-hidden group/card border border-border hover:border-primary/50 transition-colors bg-card"
    >
      {/* Thumbnail */}
      <div className="aspect-video relative">
        {thumb ? (
          <Image
            src={thumb}
            alt={course.title}
            fill
            className="object-cover"
            sizes="200px"
          />
        ) : (
          <div
            className="w-full h-full flex items-center justify-center text-2xl font-bold text-white"
            style={{
              background: `linear-gradient(135deg, ${gradFrom}, ${gradTo})`,
            }}
          >
            {initials(course.title)}
          </div>
        )}
        {/* Play overlay */}
        <div className="absolute inset-0 bg-black/40 opacity-0 group-hover/card:opacity-100 transition-opacity flex items-center justify-center">
          <Play className="h-8 w-8 text-white fill-current" />
        </div>
        {/* Progress bar */}
        {progress > 0 && (
          <div className="absolute bottom-0 left-0 right-0 h-1 bg-white/20">
            <div
              className="h-full bg-primary"
              style={{ width: `${progress}%` }}
            />
          </div>
        )}
      </div>

      {/* Info */}
      <div className="p-2 space-y-0.5">
        <p className="text-xs font-medium line-clamp-2 leading-snug">
          {course.title}
        </p>
        <p className="text-xs text-muted-foreground">
          Lecture {video_index + 1}
          {course.total_videos > 0 && ` / ${course.total_videos}`}
        </p>
      </div>
    </Link>
  );
}

export function ContinueWatchingRow() {
  const { user, token } = useAuth();
  const rowRef = useRef<HTMLDivElement>(null);

  const { data: history } = useQuery({
    queryKey: ["watch-history", user?.id],
    queryFn: () => fetchWatchHistory(token!),
    enabled: !!token,
    staleTime: 30_000,
  });

  function scroll(dir: "left" | "right") {
    if (!rowRef.current) return;
    const amount = rowRef.current.clientWidth * 0.75;
    rowRef.current.scrollBy({
      left: dir === "left" ? -amount : amount,
      behavior: "smooth",
    });
  }

  if (!user || !history || history.length === 0) return null;

  return (
    <section className="relative group/row">
      <h2 className="text-lg md:text-xl font-semibold text-foreground mb-3">
        Continue Watching
      </h2>

      <div className="relative">
        <button
          onClick={() => scroll("left")}
          className="absolute -left-4 top-1/2 -translate-y-1/2 z-10 bg-background/80 hover:bg-background border border-border rounded-full p-1.5 opacity-0 group-hover/row:opacity-100 transition-opacity shadow-lg"
          aria-label="Scroll left"
        >
          <ChevronLeft className="h-5 w-5" />
        </button>

        <div
          ref={rowRef}
          className={cn(
            "flex gap-3 overflow-x-auto scrollbar-hide pb-1",
            "scroll-smooth"
          )}
        >
          {history.map((entry) => (
            <WatchCard key={entry.course.id} entry={entry} />
          ))}
        </div>

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
