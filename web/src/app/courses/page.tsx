"use client";

import { useState, Suspense } from "react";
import { useSearchParams, useRouter, usePathname } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { CourseCard } from "@/components/course-card";
import { CourseCardSkeleton } from "@/components/ui/skeleton";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useCourses } from "@/hooks/use-courses";
import { fetchUniversities } from "@/lib/api";
import { ChevronLeft, ChevronRight, Filter } from "lucide-react";
import { levelLabel } from "@/lib/utils";
import type { CourseFilters, CourseLevel } from "@/types";

const LEVELS: CourseLevel[] = ["undergraduate", "graduate", "professional", "other"];

const TOP_SUBJECTS = [
  { name: "Mathematics",      slug: "mathematics" },
  { name: "Physics",          slug: "physics" },
  { name: "Computer Science", slug: "computer-science" },
  { name: "Engineering",      slug: "engineering" },
  { name: "Biology",          slug: "biology" },
  { name: "Chemistry",        slug: "chemistry" },
  { name: "Economics",        slug: "economics" },
  { name: "Business",         slug: "business" },
  { name: "History",          slug: "history" },
  { name: "Philosophy",       slug: "philosophy" },
];

export default function CoursesPage() {
  return (
    <Suspense fallback={<div className="max-w-screen-2xl mx-auto px-4 md:px-8 py-8"><div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-4">{Array.from({ length: 24 }).map((_, i) => (<CourseCardSkeleton key={i} />))}</div></div>}>
      <CoursesContent />
    </Suspense>
  );
}

function CoursesContent() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const pathname = usePathname();

  const [sidebarOpen, setSidebarOpen] = useState(false);

  // Default to video-only; "all=1" disables the filter to show everything
  const showAll = searchParams.get("all") === "1";
  const filters: CourseFilters = {
    q: searchParams.get("q") ?? undefined,
    university_slug: searchParams.get("university") ?? undefined,
    subject_slug: searchParams.get("subject") ?? undefined,
    level: (searchParams.get("level") as CourseLevel) ?? undefined,
    has_video_lectures: showAll ? undefined : true,
    has_thumbnail: showAll ? undefined : true,
    page: Number(searchParams.get("page") ?? "1"),
    page_size: 24,
    sort_by: (searchParams.get("sort") as CourseFilters["sort_by"]) ?? "view_count",
    sort_dir: "desc",
  };

  const { data, isLoading } = useCourses(filters);

  const { data: unisData } = useQuery({
    queryKey: ["universities", "institutions", "sidebar"],
    queryFn: () => fetchUniversities(1, 200, undefined, true),
  });
  const unis = (unisData?.items ?? [])
    .filter((u) => (u.course_count ?? 0) > 0)
    .sort((a, b) => (b.course_count ?? 0) - (a.course_count ?? 0));

  const courses = data?.items ?? [];
  const total = data?.total ?? 0;
  const pages = data?.pages ?? 1;
  const page = filters.page ?? 1;

  function updateParam(key: string, value: string | null) {
    const params = new URLSearchParams(searchParams.toString());
    if (value === null || value === "") {
      params.delete(key);
    } else {
      params.set(key, value);
    }
    params.delete("page");
    router.push(`${pathname}?${params.toString()}`, { scroll: false });
  }

  function setPage(p: number) {
    const params = new URLSearchParams(searchParams.toString());
    params.set("page", String(p));
    router.push(`${pathname}?${params.toString()}`, { scroll: false });
    document.getElementById("courses-grid")?.scrollIntoView({ behavior: "smooth", block: "start" });
  }

  return (
    <div className="max-w-screen-2xl mx-auto px-4 md:px-8 py-8">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold">All Courses</h1>
          {!isLoading && (
            <p className="text-muted-foreground text-sm mt-1">
              {total.toLocaleString()} courses found
            </p>
          )}
        </div>
        <Button
          variant="secondary"
          size="sm"
          onClick={() => setSidebarOpen((v) => !v)}
          className="md:hidden"
        >
          <Filter className="h-4 w-4" />
          Filters
        </Button>
      </div>

      <div className="flex gap-6">
        {/* Sidebar filters */}
        <aside
          className={`${
            sidebarOpen ? "block" : "hidden"
          } md:block w-56 shrink-0 space-y-6`}
        >
          {/* Search */}
          <div>
            <label className="text-xs font-semibold uppercase tracking-wide text-muted-foreground mb-2 block">
              Search
            </label>
            <Input
              placeholder="Course title..."
              defaultValue={filters.q ?? ""}
              onBlur={(e) => updateParam("q", e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter")
                  updateParam("q", (e.target as HTMLInputElement).value);
              }}
            />
          </div>

          {/* Level */}
          <div>
            <label className="text-xs font-semibold uppercase tracking-wide text-muted-foreground mb-2 block">
              Level
            </label>
            <div className="space-y-1">
              <button
                onClick={() => updateParam("level", null)}
                className={`w-full text-left px-3 py-1.5 rounded text-sm transition-colors ${
                  !filters.level
                    ? "bg-primary/20 text-primary"
                    : "text-muted-foreground hover:text-foreground hover:bg-accent/50"
                }`}
              >
                All Levels
              </button>
              {LEVELS.map((l) => (
                <button
                  key={l}
                  onClick={() => updateParam("level", l)}
                  className={`w-full text-left px-3 py-1.5 rounded text-sm transition-colors ${
                    filters.level === l
                      ? "bg-primary/20 text-primary"
                      : "text-muted-foreground hover:text-foreground hover:bg-accent/50"
                  }`}
                >
                  {levelLabel(l)}
                </button>
              ))}
            </div>
          </div>

          {/* Content */}
          <div>
            <label className="text-xs font-semibold uppercase tracking-wide text-muted-foreground mb-2 block">
              Content
            </label>
            <div className="space-y-1">
              <button
                onClick={() => updateParam("all", null)}
                className={`w-full text-left px-3 py-1.5 rounded text-sm transition-colors ${
                  !showAll
                    ? "bg-primary/20 text-primary"
                    : "text-muted-foreground hover:text-foreground hover:bg-accent/50"
                }`}
              >
                Video Courses Only
              </button>
              <button
                onClick={() => updateParam("all", "1")}
                className={`w-full text-left px-3 py-1.5 rounded text-sm transition-colors ${
                  showAll
                    ? "bg-primary/20 text-primary"
                    : "text-muted-foreground hover:text-foreground hover:bg-accent/50"
                }`}
              >
                All Courses
              </button>
            </div>
          </div>

          {/* Sort */}
          <div>
            <label className="text-xs font-semibold uppercase tracking-wide text-muted-foreground mb-2 block">
              Sort
            </label>
            <select
              value={filters.sort_by ?? "view_count"}
              onChange={(e) => updateParam("sort", e.target.value)}
              className="w-full bg-secondary border border-border rounded px-3 py-1.5 text-sm text-foreground"
            >
              <option value="view_count">Most Viewed</option>
              <option value="created_at">Newest</option>
              <option value="total_videos">Most Videos</option>
              <option value="title">Title A-Z</option>
            </select>
          </div>

          {/* Subject */}
          <div>
            <label className="text-xs font-semibold uppercase tracking-wide text-muted-foreground mb-2 block">
              Subject
            </label>
            <div className="space-y-1">
              <button
                onClick={() => updateParam("subject", null)}
                className={`w-full text-left px-3 py-1.5 rounded text-sm transition-colors ${
                  !filters.subject_slug
                    ? "bg-primary/20 text-primary"
                    : "text-muted-foreground hover:text-foreground hover:bg-accent/50"
                }`}
              >
                All Subjects
              </button>
              {TOP_SUBJECTS.map((s) => (
                <button
                  key={s.slug}
                  onClick={() => updateParam("subject", s.slug)}
                  className={`w-full text-left px-3 py-1.5 rounded text-sm transition-colors ${
                    filters.subject_slug === s.slug
                      ? "bg-primary/20 text-primary"
                      : "text-muted-foreground hover:text-foreground hover:bg-accent/50"
                  }`}
                >
                  {s.name}
                </button>
              ))}
            </div>
          </div>

          {/* University */}
          <div>
            <label className="text-xs font-semibold uppercase tracking-wide text-muted-foreground mb-2 block">
              University
            </label>
            <div className="space-y-1">
              <button
                onClick={() => updateParam("university", null)}
                className={`w-full text-left px-3 py-1.5 rounded text-sm transition-colors ${
                  !filters.university_slug
                    ? "bg-primary/20 text-primary"
                    : "text-muted-foreground hover:text-foreground hover:bg-accent/50"
                }`}
              >
                All Universities
              </button>
              {unis.map((u) => (
                <button
                  key={u.id}
                  onClick={() => updateParam("university", u.slug)}
                  className={`w-full text-left px-3 py-1.5 rounded text-sm transition-colors ${
                    filters.university_slug === u.slug
                      ? "bg-primary/20 text-primary"
                      : "text-muted-foreground hover:text-foreground hover:bg-accent/50"
                  }`}
                >
                  {u.name}
                </button>
              ))}
            </div>
          </div>
        </aside>

        {/* Course grid */}
        <div id="courses-grid" className="flex-1 min-w-0">
          {isLoading ? (
            <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-4">
              {Array.from({ length: 24 }).map((_, i) => (
                <CourseCardSkeleton key={i} />
              ))}
            </div>
          ) : courses.length === 0 ? (
            <div className="text-center py-20 text-muted-foreground">
              <p className="text-lg">No courses found</p>
              <p className="text-sm mt-1">Try adjusting your filters</p>
            </div>
          ) : (
            <>
              <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-4">
                {courses.map((course) => (
                  <CourseCard key={course.id} course={course} />
                ))}
              </div>

              {/* Pagination */}
              {pages > 1 && (
                <div className="flex items-center justify-center gap-2 mt-8">
                  <Button
                    variant="secondary"
                    size="sm"
                    disabled={page <= 1}
                    onClick={() => setPage(page - 1)}
                  >
                    <ChevronLeft className="h-4 w-4" />
                  </Button>
                  <span className="text-sm text-muted-foreground">
                    Page {page} of {pages}
                  </span>
                  <Button
                    variant="secondary"
                    size="sm"
                    disabled={page >= pages}
                    onClick={() => setPage(page + 1)}
                  >
                    <ChevronRight className="h-4 w-4" />
                  </Button>
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
}
