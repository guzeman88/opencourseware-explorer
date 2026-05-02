"use client";

import { useFeaturedCourses } from "@/hooks/use-courses";
import Image from "next/image";
import Link from "next/link";
import { Play, Info } from "lucide-react";
import { cn, levelLabel, levelColor, thumbnailUrl } from "@/lib/utils";
import { useState } from "react";

export function HeroBanner() {
  const { data, isLoading } = useFeaturedCourses(20);
  const [active, setActive] = useState(0);

  const courses = data?.items ?? [];
  const featured = courses[active];

  if (isLoading || !featured) {
    return (
      <div className="relative h-[70vh] bg-gradient-to-b from-zinc-900 to-background flex items-center justify-center">
        <div className="w-16 h-16 rounded-full border-4 border-primary border-t-transparent animate-spin" />
      </div>
    );
  }

  const thumb = thumbnailUrl(featured);

  return (
    <div className="relative h-[80vh] overflow-hidden">
      {/* Background image */}
      <div className="absolute inset-0">
        {thumb && (
          <Image
            src={thumb}
            alt={featured.title}
            fill
            className="object-cover opacity-40"
            priority
            unoptimized={thumb.startsWith("/")}
          />
        )}
        {/* Gradient overlays */}
        <div className="absolute inset-0 bg-gradient-to-r from-background via-background/60 to-transparent" />
        <div className="absolute inset-0 bg-gradient-to-t from-background via-transparent to-transparent" />
      </div>

      {/* Content */}
      <div className="relative z-10 flex h-full items-center px-4 md:px-8 lg:px-12">
        <div className="max-w-2xl space-y-4 animate-slide-up">
          {/* University + level badges */}
          <div className="flex items-center gap-2 flex-wrap">
            <span className="text-sm font-medium text-primary">
              {featured.university_name}
            </span>
            <span
              className={cn(
                "px-2 py-0.5 rounded-full text-xs font-medium",
                levelColor(featured.level)
              )}
            >
              {levelLabel(featured.level)}
            </span>
          </div>

          <h1 className="text-3xl md:text-5xl font-bold text-foreground leading-tight">
            {featured.title}
          </h1>

          {featured.instructor && (
            <p className="text-lg text-muted-foreground">
              by {featured.instructor}
            </p>
          )}

          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            {featured.total_videos > 0 && (
              <span>{featured.total_videos} lectures</span>
            )}
            {featured.year && (
              <>
                <span>·</span>
                <span>{featured.year}</span>
              </>
            )}
          </div>

          <div className="flex items-center gap-3 pt-2">
            <Link
              href={`/courses/${featured.slug}`}
              className="flex items-center gap-2 bg-primary hover:bg-primary/90 text-primary-foreground px-6 py-3 rounded-lg font-semibold transition-colors"
            >
              <Play className="h-5 w-5 fill-current" />
              Watch Now
            </Link>
            <Link
              href={`/courses/${featured.slug}`}
              className="flex items-center gap-2 bg-secondary hover:bg-secondary/80 text-secondary-foreground px-6 py-3 rounded-lg font-semibold transition-colors"
            >
              <Info className="h-5 w-5" />
              More Info
            </Link>
          </div>
        </div>
      </div>

      {/* Thumbnail strip to cycle featured courses */}
      <div className="absolute bottom-8 right-4 md:right-8 lg:right-12 hidden md:flex items-center gap-2">
        {courses.slice(0, 6).filter(c => thumbnailUrl(c)).map((course, i) => (
          <button
            key={course.id}
            onClick={() => setActive(i)}
            className={cn(
              "w-16 h-10 rounded overflow-hidden border-2 transition-all",
              i === active
                ? "border-primary scale-110"
                : "border-transparent opacity-50 hover:opacity-75"
            )}
          >
            <Image
              src={thumbnailUrl(course)!}
              alt={course.title}
              width={64}
              height={40}
              className="object-cover"
              unoptimized
            />
          </button>
        ))}
      </div>
    </div>
  );
}
