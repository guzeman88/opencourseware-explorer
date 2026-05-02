"use client";

import { useState } from "react";
import { useCourses } from "@/hooks/use-courses";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import { levelLabel, levelColor, cn } from "@/lib/utils";
import Link from "next/link";
import { ChevronLeft, ChevronRight, ExternalLink } from "lucide-react";

export default function AdminCoursesPage() {
  const [page, setPage] = useState(1);
  const [q, setQ] = useState("");

  const { data, isLoading } = useCourses({
    q: q || undefined,
    page,
    page_size: 25,
    sort_by: "created_at",
    sort_dir: "desc",
  });

  const courses = data?.items ?? [];
  const pages = data?.pages ?? 1;
  const total = data?.total ?? 0;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Courses</h1>
          <p className="text-muted-foreground text-sm mt-1">
            {isLoading ? "Loading…" : `${total.toLocaleString()} courses`}
          </p>
        </div>
      </div>

      {/* Search */}
      <Input
        placeholder="Filter by title…"
        value={q}
        onChange={(e) => {
          setQ(e.target.value);
          setPage(1);
        }}
        className="max-w-xs"
      />

      <Card>
        <CardContent className="p-0">
          {isLoading ? (
            <div className="p-6 space-y-3">
              {Array.from({ length: 10 }).map((_, i) => (
                <Skeleton key={i} className="h-10 w-full" />
              ))}
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-border">
                    <th className="text-left px-4 py-3 font-medium text-muted-foreground">
                      Title
                    </th>
                    <th className="text-left px-4 py-3 font-medium text-muted-foreground">
                      University
                    </th>
                    <th className="text-left px-4 py-3 font-medium text-muted-foreground">
                      Level
                    </th>
                    <th className="text-left px-4 py-3 font-medium text-muted-foreground">
                      Videos
                    </th>
                    <th className="text-left px-4 py-3 font-medium text-muted-foreground">
                      Views
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {courses.map((course) => (
                    <tr
                      key={course.id}
                      className="border-b border-border/50 hover:bg-accent/20"
                    >
                      <td className="px-4 py-3 max-w-xs">
                        <Link
                          href={`/courses/${course.slug}`}
                          className="hover:text-primary hover:underline line-clamp-1"
                        >
                          {course.title}
                        </Link>
                      </td>
                      <td className="px-4 py-3 text-muted-foreground whitespace-nowrap">
                        {course.university_name}
                      </td>
                      <td className="px-4 py-3">
                        <span
                          className={cn(
                            "px-1.5 py-0.5 rounded-full text-xs font-medium",
                            levelColor(course.level)
                          )}
                        >
                          {levelLabel(course.level)}
                        </span>
                      </td>
                      <td className="px-4 py-3">{course.total_videos}</td>
                      <td className="px-4 py-3 text-muted-foreground">
                        {(course as any).view_count?.toLocaleString() ?? "—"}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Pagination */}
      {pages > 1 && (
        <div className="flex items-center justify-center gap-2">
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
    </div>
  );
}
