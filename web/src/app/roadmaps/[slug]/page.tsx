"use client";

import { useQuery } from "@tanstack/react-query";
import { useParams } from "next/navigation";
import { fetchRoadmap } from "@/lib/api";
import Link from "next/link";
import {
  GraduationCap,
  ExternalLink,
  ChevronLeft,
  Lock,
  Unlock,
} from "lucide-react";
import type { RoadmapEntry } from "@/types";

const CATEGORY_COLORS: Record<string, string> = {
  Core: "bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-300",
  Math: "bg-violet-100 text-violet-800 dark:bg-violet-900/30 dark:text-violet-300",
  Science: "bg-cyan-100 text-cyan-800 dark:bg-cyan-900/30 dark:text-cyan-300",
  Theory: "bg-orange-100 text-orange-800 dark:bg-orange-900/30 dark:text-orange-300",
  Systems: "bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300",
  AI: "bg-pink-100 text-pink-800 dark:bg-pink-900/30 dark:text-pink-300",
  "AI Track": "bg-pink-100 text-pink-800 dark:bg-pink-900/30 dark:text-pink-300",
  Intelligence: "bg-pink-100 text-pink-800 dark:bg-pink-900/30 dark:text-pink-300",
  Advanced: "bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-300",
  Capstone: "bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-300",
  Lab: "bg-teal-100 text-teal-800 dark:bg-teal-900/30 dark:text-teal-300",
  Elective: "bg-gray-100 text-gray-800 dark:bg-gray-800/30 dark:text-gray-300",
  "EE Core": "bg-indigo-100 text-indigo-800 dark:bg-indigo-900/30 dark:text-indigo-300",
  Foundations: "bg-emerald-100 text-emerald-800 dark:bg-emerald-900/30 dark:text-emerald-300",
  Intermediate: "bg-lime-100 text-lime-800 dark:bg-lime-900/30 dark:text-lime-300",
};

function CategoryBadge({ category }: { category?: string }) {
  if (!category) return null;
  const cls =
    CATEGORY_COLORS[category] ??
    "bg-muted text-muted-foreground";
  return (
    <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${cls}`}>
      {category}
    </span>
  );
}

function EntryRow({ entry, index }: { entry: RoadmapEntry; index: number }) {
  // All entries link to subject pages (multiple real courses). Thesis/capstone = no link.
  const href = entry.subject_slug ? `/subjects/${entry.subject_slug}` : null;

  const inner = (
    <>
      {/* Step number */}
      <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center shrink-0 text-sm font-semibold text-primary">
        {index + 1}
      </div>

      <div className="flex-1 min-w-0 space-y-1">
        <div className="flex items-center gap-2 flex-wrap">
          {entry.course_number && (
            <span className="text-xs font-mono text-muted-foreground">
              {entry.course_number}
            </span>
          )}
          <span className="font-medium text-sm">{entry.course_title}</span>
        </div>

        <div className="flex items-center gap-2 flex-wrap">
          <CategoryBadge category={entry.category} />
          {entry.semester && (
            <span className="text-xs text-muted-foreground">{entry.semester}</span>
          )}
          {entry.units != null && (
            <span className="text-xs text-muted-foreground">{entry.units} units</span>
          )}
          {entry.notes && (
            <span className="text-xs text-muted-foreground italic">{entry.notes}</span>
          )}
        </div>
      </div>

      <div className="shrink-0">
        {entry.is_required ? (
          <span className="flex items-center gap-1 text-xs text-muted-foreground">
            <Lock className="h-3 w-3" />
            Required
          </span>
        ) : (
          <span className="flex items-center gap-1 text-xs text-muted-foreground/60">
            <Unlock className="h-3 w-3" />
            Elective
          </span>
        )}
      </div>
    </>
  );

  if (!href) {
    return (
      <div className="flex items-start gap-4 p-4 rounded-lg border border-border/50 opacity-60">
        {inner}
      </div>
    );
  }

  return (
    <Link
      href={href}
      className="flex items-start gap-4 p-4 rounded-lg border border-border/50 hover:border-primary/50 hover:bg-primary/5 transition-all cursor-pointer"
    >
      {inner}
    </Link>
  );
}

export default function RoadmapDetailPage() {
  const { slug } = useParams<{ slug: string }>();
  const { data: roadmap, isLoading } = useQuery({
    queryKey: ["roadmap", slug],
    queryFn: () => fetchRoadmap(slug),
  });

  if (isLoading) {
    return (
      <div className="max-w-screen-lg mx-auto px-4 md:px-8 py-8 space-y-4">
        <div className="h-8 w-64 bg-muted animate-pulse rounded" />
        <div className="h-4 w-96 bg-muted animate-pulse rounded" />
        <div className="space-y-3 mt-8">
          {Array.from({ length: 8 }).map((_, i) => (
            <div key={i} className="h-16 bg-muted animate-pulse rounded-lg" />
          ))}
        </div>
      </div>
    );
  }

  if (!roadmap) {
    return (
      <div className="max-w-screen-lg mx-auto px-4 md:px-8 py-16 text-center">
        <p className="text-muted-foreground">Roadmap not found.</p>
        <Link href="/roadmaps" className="text-primary hover:underline mt-4 inline-block">
          ← Back to Roadmaps
        </Link>
      </div>
    );
  }

  // Group entries by year
  const byYear: Record<number, RoadmapEntry[]> = {};
  const noYear: RoadmapEntry[] = [];
  for (const e of roadmap.entries) {
    if (e.year_in_program != null) {
      if (!byYear[e.year_in_program]) byYear[e.year_in_program] = [];
      byYear[e.year_in_program].push(e);
    } else {
      noYear.push(e);
    }
  }
  const years = Object.keys(byYear)
    .map(Number)
    .sort((a, b) => a - b);

  const linkedCount = roadmap.entries.filter((e) => e.course_slug).length;

  return (
    <div className="max-w-screen-lg mx-auto px-4 md:px-8 py-8 space-y-6">
      {/* Back */}
      <Link
        href="/roadmaps"
        className="inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground transition-colors"
      >
        <ChevronLeft className="h-4 w-4" />
        All Roadmaps
      </Link>

      {/* Header */}
      <div className="flex items-start gap-5">
        <div className="w-14 h-14 rounded-xl bg-primary/10 flex items-center justify-center shrink-0">
          <GraduationCap className="h-7 w-7 text-primary" />
        </div>
        <div className="space-y-1 flex-1">
          <h1 className="text-2xl font-bold leading-tight">{roadmap.title}</h1>
          {roadmap.university_name && (
            <Link
              href={`/universities/${roadmap.university_slug}`}
              className="text-sm text-primary hover:underline"
            >
              {roadmap.university_name}
            </Link>
          )}
          {roadmap.description && (
            <p className="text-muted-foreground text-sm max-w-3xl mt-2">
              {roadmap.description}
            </p>
          )}

          <div className="flex flex-wrap gap-4 pt-2 text-sm text-muted-foreground">
            {roadmap.estimated_years && (
              <span>
                {roadmap.estimated_years}{" "}
                {roadmap.estimated_years === 1 ? "year" : "years"}
              </span>
            )}
            <span>{roadmap.entry_count} courses</span>
            {linkedCount > 0 && (
              <span className="text-primary">
                {linkedCount} available in our library
              </span>
            )}
            {roadmap.website_url && (
              <a
                href={roadmap.website_url}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-1 text-primary hover:underline"
              >
                <ExternalLink className="h-3.5 w-3.5" />
                Official curriculum
              </a>
            )}
          </div>
        </div>
      </div>

      {/* Legend */}
      <div className="flex items-center gap-4 text-xs text-muted-foreground bg-muted/30 rounded-lg px-4 py-3">
        <span className="flex items-center gap-1">
          <Lock className="h-3 w-3" />
          Required
        </span>
        <span className="flex items-center gap-1">
          <Unlock className="h-3 w-3" />
          Elective
        </span>
      </div>

      {/* Entries grouped by year */}
      {years.length > 0 ? (
        <div className="space-y-8">
          {years.map((year) => (
            <section key={year}>
              <h2 className="text-base font-semibold mb-3 text-muted-foreground uppercase tracking-wide text-xs">
                Year {year}
              </h2>
              <div className="space-y-2">
                {byYear[year].map((entry, i) => (
                  <EntryRow key={entry.id} entry={entry} index={entry.position - 1} />
                ))}
              </div>
            </section>
          ))}
          {noYear.length > 0 && (
            <section>
              <h2 className="text-base font-semibold mb-3 text-muted-foreground uppercase tracking-wide text-xs">
                Additional Courses
              </h2>
              <div className="space-y-2">
                {noYear.map((entry) => (
                  <EntryRow key={entry.id} entry={entry} index={entry.position - 1} />
                ))}
              </div>
            </section>
          )}
        </div>
      ) : (
        <div className="space-y-2">
          {roadmap.entries.map((entry) => (
            <EntryRow key={entry.id} entry={entry} index={entry.position - 1} />
          ))}
        </div>
      )}
    </div>
  );
}
