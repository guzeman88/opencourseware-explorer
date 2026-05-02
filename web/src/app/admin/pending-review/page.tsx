"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { fetchPendingReviewCourses, setCoursePublished } from "@/lib/api";
import { sourceLabel } from "@/lib/utils";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import { Badge } from "@/components/ui/badge";
import { ChevronLeft, ChevronRight, ExternalLink, CheckCircle, Eye } from "lucide-react";
import Link from "next/link";
import type { CourseSummary } from "@/types";

const SOURCE_KEYS = [
  "mit_ocw", "nptel", "khan", "princeton", "oxford", "cambridge",
  "cmu", "gatech", "stanford", "freecodecamp", "yale", "harvard",
  "simons", "mit_youtube", "3b1b", "berkeley", "crashcourse",
];

export default function PendingReviewPage() {
  const [page, setPage] = useState(1);
  const [q, setQ] = useState("");
  const [sourceKey, setSourceKey] = useState<string | undefined>(undefined);
  const queryClient = useQueryClient();

  const { data, isLoading } = useQuery({
    queryKey: ["admin_pending_review", page, q, sourceKey],
    queryFn: () => fetchPendingReviewCourses(page, 50, sourceKey, q || undefined),
  });

  const publishMutation = useMutation({
    mutationFn: ({ id, published }: { id: string; published: boolean }) =>
      setCoursePublished(id, published),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin_pending_review"] });
      queryClient.invalidateQueries({ queryKey: ["admin_stats"] });
    },
  });

  const courses = data?.items ?? [];
  const pages = data?.pages ?? 1;
  const total = data?.total ?? 0;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Pending Review</h1>
        <p className="text-muted-foreground text-sm mt-1">
          {isLoading
            ? "Loading…"
            : `${total.toLocaleString()} non-video courses hidden from public site. Review and publish or leave for later.`}
        </p>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap gap-3">
        <Input
          placeholder="Filter by title…"
          value={q}
          onChange={(e) => { setQ(e.target.value); setPage(1); }}
          className="max-w-xs"
        />
        <select
          className="border border-border rounded-md px-3 py-2 text-sm bg-background"
          value={sourceKey ?? ""}
          onChange={(e) => { setSourceKey(e.target.value || undefined); setPage(1); }}
        >
          <option value="">All sources</option>
          {SOURCE_KEYS.map((key) => (
            <option key={key} value={key}>{sourceLabel(key)}</option>
          ))}
        </select>
      </div>

      <Card>
        <CardContent className="p-0">
          {isLoading ? (
            <div className="p-6 space-y-3">
              {Array.from({ length: 10 }).map((_, i) => (
                <Skeleton key={i} className="h-12 w-full" />
              ))}
            </div>
          ) : courses.length === 0 ? (
            <div className="p-12 text-center text-muted-foreground">
              No courses pending review
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-border">
                    <th className="text-left px-4 py-3 font-medium text-muted-foreground">Title</th>
                    <th className="text-left px-4 py-3 font-medium text-muted-foreground">University</th>
                    <th className="text-left px-4 py-3 font-medium text-muted-foreground">Source</th>
                    <th className="text-left px-4 py-3 font-medium text-muted-foreground">Level</th>
                    <th className="text-left px-4 py-3 font-medium text-muted-foreground">Materials</th>
                    <th className="text-right px-4 py-3 font-medium text-muted-foreground">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {courses.map((course) => (
                    <CourseRow
                      key={course.id}
                      course={course}
                      onPublish={() => publishMutation.mutate({ id: course.id, published: true })}
                      publishing={publishMutation.isPending}
                    />
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
          <Button variant="secondary" size="sm" disabled={page <= 1} onClick={() => setPage(page - 1)}>
            <ChevronLeft className="h-4 w-4" />
          </Button>
          <span className="text-sm text-muted-foreground">
            Page {page} of {pages}
          </span>
          <Button variant="secondary" size="sm" disabled={page >= pages} onClick={() => setPage(page + 1)}>
            <ChevronRight className="h-4 w-4" />
          </Button>
        </div>
      )}
    </div>
  );
}

function CourseRow({
  course,
  onPublish,
  publishing,
}: {
  course: CourseSummary;
  onPublish: () => void;
  publishing: boolean;
}) {
  const materials: string[] = [];
  if (course.has_lecture_notes) materials.push("Notes");
  if (course.has_exams) materials.push("Exams");
  if (!materials.length) materials.push("—");

  return (
    <tr className="border-b border-border/50 hover:bg-accent/20">
      <td className="px-4 py-3 max-w-xs">
        <span className="line-clamp-2 font-medium">{course.title}</span>
        {course.course_number && (
          <span className="text-xs text-muted-foreground ml-1">{course.course_number}</span>
        )}
      </td>
      <td className="px-4 py-3 text-muted-foreground whitespace-nowrap">
        {course.university_name}
      </td>
      <td className="px-4 py-3">
        <Badge variant="secondary" className="text-xs">
          {sourceLabel(course.source_key)}
        </Badge>
      </td>
      <td className="px-4 py-3 text-muted-foreground capitalize">{course.level}</td>
      <td className="px-4 py-3 text-muted-foreground text-xs">{materials.join(", ")}</td>
      <td className="px-4 py-3">
        <div className="flex items-center justify-end gap-2">
          {course.source_url && (
            <a
              href={course.source_url}
              target="_blank"
              rel="noopener noreferrer"
              className="p-1.5 rounded hover:bg-accent text-muted-foreground hover:text-foreground"
              title="View original source"
            >
              <ExternalLink className="h-3.5 w-3.5" />
            </a>
          )}
          <Link
            href={`/courses/${course.slug}`}
            className="p-1.5 rounded hover:bg-accent text-muted-foreground hover:text-foreground"
            title="Preview course page"
          >
            <Eye className="h-3.5 w-3.5" />
          </Link>
          <Button
            size="sm"
            variant="outline"
            className="h-7 text-xs gap-1"
            onClick={onPublish}
            disabled={publishing}
          >
            <CheckCircle className="h-3 w-3" />
            Publish
          </Button>
        </div>
      </td>
    </tr>
  );
}
