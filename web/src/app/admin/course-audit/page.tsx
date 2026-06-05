"use client";

import { useEffect, useMemo, useState } from "react";
import { useInfiniteQuery } from "@tanstack/react-query";
import { Download, Loader2, Search, Tags } from "lucide-react";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import { fetchCourses } from "@/lib/api";
import { sourceLabel } from "@/lib/utils";
import type { CourseSummary } from "@/types";

const PAGE_SIZE = 100;

type TagFilter = "all" | "tagged" | "untagged";

function courseTags(course: CourseSummary) {
  return course.subjects?.map((subject) => subject.name).filter(Boolean) ?? [];
}

function csvCell(value: string | number) {
  const text = String(value);
  return /[",\n]/.test(text) ? `"${text.replace(/"/g, '""')}"` : text;
}

export default function AdminCourseAuditPage() {
  const [q, setQ] = useState("");
  const [tagFilter, setTagFilter] = useState<TagFilter>("all");

  const {
    data,
    fetchNextPage,
    hasNextPage,
    isFetchingNextPage,
    isLoading,
  } = useInfiniteQuery({
    queryKey: ["admin-course-audit"],
    queryFn: ({ pageParam = 1 }) =>
      fetchCourses({
        has_video_lectures: true,
        catalog_ready: false,
        page: pageParam,
        page_size: PAGE_SIZE,
        sort_by: "title",
        sort_dir: "asc",
      }),
    initialPageParam: 1,
    getNextPageParam: (lastPage) =>
      lastPage.page < lastPage.pages ? lastPage.page + 1 : undefined,
  });

  useEffect(() => {
    if (hasNextPage && !isFetchingNextPage) {
      void fetchNextPage();
    }
  }, [fetchNextPage, hasNextPage, isFetchingNextPage]);

  const courses = useMemo(
    () => data?.pages.flatMap((page) => page.items) ?? [],
    [data]
  );

  const total = data?.pages[0]?.total ?? 0;
  const loaded = courses.length;
  const untaggedLoaded = courses.filter((course) => courseTags(course).length === 0).length;
  const taggedLoaded = loaded - untaggedLoaded;

  const visibleCourses = useMemo(() => {
    const query = q.trim().toLowerCase();
    return courses.filter((course) => {
      const tags = courseTags(course);
      if (tagFilter === "tagged" && tags.length === 0) return false;
      if (tagFilter === "untagged" && tags.length > 0) return false;
      if (!query) return true;

      const searchable = [
        course.title,
        course.university_name,
        course.source_key,
        ...tags,
      ]
        .join(" ")
        .toLowerCase();

      return searchable.includes(query);
    });
  }, [courses, q, tagFilter]);

  function exportVisibleCsv() {
    const rows = [
      ["Title", "Institution", "Lectures", "Tags"],
      ...visibleCourses.map((course) => [
        course.title,
        course.university_name,
        course.total_videos,
        courseTags(course).join("; "),
      ]),
    ];
    const csv = rows
      .map((row) => row.map((cell) => csvCell(cell)).join(","))
      .join("\n");
    const blob = new Blob([csv], { type: "text/csv;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = "course-tag-audit.csv";
    link.click();
    URL.revokeObjectURL(url);
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Course Tag Audit</h1>
          <p className="mt-1 text-sm text-muted-foreground">
            All video courses with their current subject tags.
          </p>
        </div>

        <div className="grid grid-cols-3 gap-2 text-sm lg:min-w-[420px]">
          <div className="rounded-md border border-border bg-card px-3 py-2">
            <p className="text-[11px] font-medium uppercase tracking-wide text-muted-foreground">
              Loaded
            </p>
            <p className="mt-0.5 font-semibold tabular-nums">
              {loaded.toLocaleString()} / {total.toLocaleString()}
            </p>
          </div>
          <div className="rounded-md border border-border bg-card px-3 py-2">
            <p className="text-[11px] font-medium uppercase tracking-wide text-muted-foreground">
              Tagged
            </p>
            <p className="mt-0.5 font-semibold tabular-nums">
              {taggedLoaded.toLocaleString()}
            </p>
          </div>
          <div className="rounded-md border border-amber-500/30 bg-amber-500/5 px-3 py-2">
            <p className="text-[11px] font-medium uppercase tracking-wide text-amber-300">
              No Tags
            </p>
            <p className="mt-0.5 font-semibold tabular-nums text-amber-200">
              {untaggedLoaded.toLocaleString()}
            </p>
          </div>
        </div>
      </div>

      <div className="flex flex-col gap-3 rounded-md border border-border bg-card p-3 xl:flex-row xl:items-center">
        <div className="relative min-w-0 flex-1">
          <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            value={q}
            onChange={(event) => setQ(event.target.value)}
            placeholder="Search title, institution, source, or tag"
            className="pl-9"
          />
        </div>

        <div className="flex flex-wrap items-center gap-2">
          {(["all", "untagged", "tagged"] as const).map((filter) => (
            <button
              key={filter}
              type="button"
              onClick={() => setTagFilter(filter)}
              className={[
                "h-9 rounded-md px-3 text-sm font-medium transition-colors",
                tagFilter === filter
                  ? "bg-primary text-primary-foreground"
                  : "bg-secondary text-muted-foreground hover:text-foreground",
              ].join(" ")}
            >
              {filter === "all" ? "All" : filter === "untagged" ? "No tags" : "Tagged"}
            </button>
          ))}
        </div>

        <div className="flex items-center gap-2">
          <Button
            type="button"
            variant="outline"
            onClick={() => void fetchNextPage()}
            disabled={!hasNextPage || isFetchingNextPage}
            className="gap-2"
          >
            {isFetchingNextPage ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Tags className="h-4 w-4" />
            )}
            {hasNextPage ? "Loading all" : "All loaded"}
          </Button>
          <Button
            type="button"
            variant="outline"
            onClick={exportVisibleCsv}
            disabled={visibleCourses.length === 0}
            className="gap-2"
          >
            <Download className="h-4 w-4" />
            CSV
          </Button>
        </div>
      </div>

      <div className="overflow-hidden rounded-md border border-border bg-card">
        <div className="border-b border-border px-4 py-2 text-sm text-muted-foreground">
          Showing {visibleCourses.length.toLocaleString()} loaded rows
          {hasNextPage ? " while the remaining pages are available to load." : "."}
        </div>

        {isLoading ? (
          <div className="space-y-2 p-4">
            {Array.from({ length: 12 }).map((_, index) => (
              <Skeleton key={index} className="h-10 w-full" />
            ))}
          </div>
        ) : (
          <div className="max-h-[calc(100vh-300px)] overflow-auto">
            <table className="w-full min-w-[1120px] border-separate border-spacing-0 text-sm">
              <thead className="sticky top-0 z-10 bg-card shadow-[0_1px_0_hsl(var(--border))]">
                <tr>
                  <th className="w-[44%] px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                    Title
                  </th>
                  <th className="w-[24%] px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                    Institution
                  </th>
                  <th className="w-[96px] px-4 py-3 text-right text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                    Lectures
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                    Tags
                  </th>
                </tr>
              </thead>
              <tbody>
                {visibleCourses.map((course) => {
                  const tags = courseTags(course);
                  return (
                    <tr
                      key={course.id}
                      className="border-b border-border/60 hover:bg-accent/30"
                    >
                      <td className="border-b border-border/60 px-4 py-3 align-top">
                        <Link
                          href={`/courses/${course.slug}`}
                          className="font-medium leading-5 text-foreground hover:text-primary hover:underline"
                        >
                          {course.title}
                        </Link>
                        <p className="mt-1 text-xs text-muted-foreground">
                          {sourceLabel(course.source_key)}
                        </p>
                      </td>
                      <td className="border-b border-border/60 px-4 py-3 align-top text-muted-foreground">
                        {course.university_name}
                      </td>
                      <td className="border-b border-border/60 px-4 py-3 text-right align-top tabular-nums">
                        {course.total_videos.toLocaleString()}
                      </td>
                      <td className="border-b border-border/60 px-4 py-3 align-top">
                        {tags.length > 0 ? (
                          <div className="flex flex-wrap gap-1.5">
                            {tags.map((tag) => (
                              <span
                                key={`${course.id}-${tag}`}
                                className="rounded-md border border-border bg-secondary px-2 py-0.5 text-xs font-medium text-secondary-foreground"
                              >
                                {tag}
                              </span>
                            ))}
                          </div>
                        ) : (
                          <span className="rounded-md border border-amber-500/30 bg-amber-500/10 px-2 py-0.5 text-xs font-semibold text-amber-200">
                            No tags
                          </span>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
