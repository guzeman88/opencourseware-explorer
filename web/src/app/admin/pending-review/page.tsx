"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { fetchPendingReviewCourses, setCoursePublished } from "@/lib/api";
import { sourceLabel } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import { Badge } from "@/components/ui/badge";
import { ChevronLeft, ChevronRight, ExternalLink, CheckCircle, Eye, X, Clock } from "lucide-react";
import Link from "next/link";
import type { CourseSummary } from "@/types";
import { cn, levelColor, levelLabel } from "@/lib/utils";

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
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Pending Review</h1>
          <p className="text-muted-foreground text-sm mt-1 max-w-lg">
            {isLoading
              ? "Loading…"
              : `${total.toLocaleString()} non-video courses awaiting review`}
          </p>
        </div>
        {total > 0 && !isLoading && (
          <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-orange-500/10 border border-orange-500/20 shrink-0">
            <Clock className="h-3.5 w-3.5 text-orange-400" />
            <span className="text-xs font-semibold text-orange-400">{total.toLocaleString()} pending</span>
          </div>
        )}
      </div>

      {/* Filters */}
      <div className="flex flex-wrap gap-3">
        <div className="relative">
          <Input
            placeholder="Filter by title…"
            value={q}
            onChange={(e) => { setQ(e.target.value); setPage(1); }}
            className="max-w-xs bg-secondary/50 pr-8"
          />
          {q && (
            <button onClick={() => setQ("")} className="absolute right-2.5 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground">
              <X className="h-3.5 w-3.5" />
            </button>
          )}
        </div>
        <select
          className="border border-white/[0.1] rounded-lg px-3 py-2 text-sm bg-secondary/50 text-foreground focus:outline-none focus:ring-2 focus:ring-primary/40"
          value={sourceKey ?? ""}
          onChange={(e) => { setSourceKey(e.target.value || undefined); setPage(1); }}
        >
          <option value="">All sources</option>
          {SOURCE_KEYS.map((key) => (
            <option key={key} value={key}>{sourceLabel(key)}</option>
          ))}
        </select>
      </div>

      <div className="rounded-xl border border-white/[0.08] bg-card/60 overflow-hidden">
        {isLoading ? (
          <div className="p-6 space-y-3">
            {Array.from({ length: 10 }).map((_, i) => (
              <Skeleton key={i} className="h-12 w-full" />
            ))}
          </div>
        ) : courses.length === 0 ? (
          <div className="py-20 text-center">
            <CheckCircle className="h-10 w-10 text-emerald-500/50 mx-auto mb-3" />
            <p className="text-sm font-medium text-foreground">All caught up!</p>
            <p className="text-xs text-muted-foreground mt-1">No courses pending review</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-white/[0.07] bg-white/[0.02]">
                  <th className="text-left px-4 py-3 font-semibold text-xs uppercase tracking-wider text-muted-foreground">Title</th>
                  <th className="text-left px-4 py-3 font-semibold text-xs uppercase tracking-wider text-muted-foreground hidden md:table-cell">University</th>
                  <th className="text-left px-4 py-3 font-semibold text-xs uppercase tracking-wider text-muted-foreground">Source</th>
                  <th className="text-left px-4 py-3 font-semibold text-xs uppercase tracking-wider text-muted-foreground hidden sm:table-cell">Level</th>
                  <th className="text-left px-4 py-3 font-semibold text-xs uppercase tracking-wider text-muted-foreground hidden lg:table-cell">Materials</th>
                  <th className="text-right px-4 py-3 font-semibold text-xs uppercase tracking-wider text-muted-foreground">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/[0.04]">
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
      </div>

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
    <tr className="hover:bg-white/[0.03] transition-colors group">
      <td className="px-4 py-3 max-w-xs">
        <span className="line-clamp-1 font-medium">{course.title}</span>
        {course.course_number && (
          <span className="text-xs text-muted-foreground ml-1">#{course.course_number}</span>
        )}
      </td>
      <td className="px-4 py-3 text-muted-foreground whitespace-nowrap hidden md:table-cell text-xs">
        {course.university_name}
      </td>
      <td className="px-4 py-3">
        <span className="px-2 py-0.5 rounded-full text-[11px] font-medium bg-secondary text-secondary-foreground whitespace-nowrap">
          {sourceLabel(course.source_key)}
        </span>
      </td>
      <td className="px-4 py-3 hidden sm:table-cell">
        <span className={cn("text-[11px] font-semibold capitalize", levelColor(course.level))}>
          {levelLabel(course.level)}
        </span>
      </td>
      <td className="px-4 py-3 text-muted-foreground text-xs hidden lg:table-cell">{materials.join(", ")}</td>
      <td className="px-4 py-3">
        <div className="flex items-center justify-end gap-1">
          {course.source_url && (
            <a
              href={course.source_url}
              target="_blank"
              rel="noopener noreferrer"
              className="p-1.5 rounded-lg hover:bg-white/[0.08] text-muted-foreground hover:text-foreground transition-colors"
              title="View source"
            >
              <ExternalLink className="h-3.5 w-3.5" />
            </a>
          )}
          <Link
            href={`/courses/${course.slug}`}
            target="_blank"
            className="p-1.5 rounded-lg hover:bg-white/[0.08] text-muted-foreground hover:text-foreground transition-colors"
            title="Preview"
          >
            <Eye className="h-3.5 w-3.5" />
          </Link>
          <button
            className={cn(
              "flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all duration-150",
              "bg-emerald-500/15 text-emerald-400 hover:bg-emerald-500/25 border border-emerald-500/20"
            )}
            onClick={onPublish}
            disabled={publishing}
          >
            <CheckCircle className="h-3.5 w-3.5" />
            Publish
          </button>
        </div>
      </td>
    </tr>
  );
}
