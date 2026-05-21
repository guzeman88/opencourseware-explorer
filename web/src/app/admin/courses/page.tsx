"use client";

import { useState } from "react";
import { useCourses } from "@/hooks/use-courses";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import { Badge } from "@/components/ui/badge";
import { levelLabel, levelColor, cn } from "@/lib/utils";
import Link from "next/link";
import {
  ChevronLeft,
  ChevronRight,
  ExternalLink,
  Pencil,
  X,
  Loader2,
  Check,
  Eye,
  EyeOff,
} from "lucide-react";
import {
  useQuery,
  useMutation,
  useQueryClient,
} from "@tanstack/react-query";
import { fetchAdminCourse, updateCourse, type CourseUpdatePayload } from "@/lib/api";
import type { CourseSummary, Course, CourseLevel } from "@/types";

// ── Edit Modal ────────────────────────────────────────────────────────────────

const LEVELS: CourseLevel[] = ["undergraduate", "graduate", "professional", "other"];
const SEMESTERS = ["Spring", "Summer", "Fall", "Winter"];

function EditModal({
  courseId,
  onClose,
}: {
  courseId: string;
  onClose: () => void;
}) {
  const qc = useQueryClient();

  const { data: course, isLoading } = useQuery({
    queryKey: ["admin_course_edit", courseId],
    queryFn: () => fetchAdminCourse(courseId),
  });

  const { mutate: save, isPending, isSuccess } = useMutation({
    mutationFn: (payload: CourseUpdatePayload) => updateCourse(courseId, payload),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["courses"] });
      qc.invalidateQueries({ queryKey: ["admin_stats"] });
      setTimeout(onClose, 700);
    },
  });

  const [form, setForm] = useState<CourseUpdatePayload | null>(null);

  // Initialise form once course loads
  if (course && form === null) {
    setForm({
      title: course.title,
      description: course.description ?? "",
      level: course.level,
      instructor: course.instructor ?? "",
      year: course.year ?? null,
      semester: course.semester ?? "",
      thumbnail_url: course.thumbnail_url ?? "",
      has_video_lectures: course.has_video_lectures,
      has_lecture_notes: course.has_lecture_notes,
      has_exams: course.has_exams,
      lecture_notes_url: course.lecture_notes_url ?? "",
      exams_url: course.exams_url ?? "",
      youtube_playlist_id: course.youtube_playlist_id ?? "",
      is_published: course.is_published,
    });
  }

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!form) return;
    // Send nulls for empty optional strings
    const cleaned: CourseUpdatePayload = {
      ...form,
      instructor: form.instructor || undefined,
      semester: form.semester || null,
      thumbnail_url: form.thumbnail_url || null,
      lecture_notes_url: form.lecture_notes_url || null,
      exams_url: form.exams_url || null,
      youtube_playlist_id: form.youtube_playlist_id || null,
      description: form.description || undefined,
    };
    save(cleaned);
  }

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4 animate-fade-in"
      onClick={(e) => e.target === e.currentTarget && onClose()}
    >
      <div className="relative bg-card border border-white/[0.1] rounded-2xl w-full max-w-2xl max-h-[90vh] overflow-hidden shadow-2xl animate-slide-up flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-white/[0.07] shrink-0">
          <div>
            <h2 className="font-semibold text-base">Edit Course</h2>
            {course && (
              <p className="text-xs text-muted-foreground mt-0.5 truncate max-w-sm">
                {course.title}
              </p>
            )}
          </div>
          <div className="flex items-center gap-2">
            {course?.slug && (
              <Link
                href={`/courses/${course.slug}`}
                target="_blank"
                className="p-1.5 rounded-lg text-muted-foreground hover:text-foreground hover:bg-white/[0.07] transition-colors"
                title="Preview"
              >
                <ExternalLink className="h-4 w-4" />
              </Link>
            )}
            <button
              onClick={onClose}
              className="p-1.5 rounded-lg text-muted-foreground hover:text-foreground hover:bg-white/[0.07] transition-colors"
            >
              <X className="h-4 w-4" />
            </button>
          </div>
        </div>

        {/* Body */}
        <div className="overflow-y-auto flex-1">
          {isLoading || form === null ? (
            <div className="p-6 space-y-4">
              {Array.from({ length: 6 }).map((_, i) => (
                <Skeleton key={i} className="h-9 w-full" />
              ))}
            </div>
          ) : (
            <form id="edit-form" onSubmit={handleSubmit} className="p-6 space-y-5">
              {/* Title */}
              <Field label="Title" required>
                <Input
                  value={form.title ?? ""}
                  onChange={(e) => setForm({ ...form, title: e.target.value })}
                  required
                  className="bg-secondary/50"
                />
              </Field>

              {/* Description */}
              <Field label="Description">
                <textarea
                  value={form.description ?? ""}
                  onChange={(e) => setForm({ ...form, description: e.target.value })}
                  rows={3}
                  className="w-full bg-secondary/50 border border-border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary/40 resize-none placeholder:text-muted-foreground"
                  placeholder="Course description…"
                />
              </Field>

              {/* Row: Level + Year + Semester */}
              <div className="grid grid-cols-3 gap-4">
                <Field label="Level">
                  <select
                    value={form.level ?? "other"}
                    onChange={(e) => setForm({ ...form, level: e.target.value as CourseLevel })}
                    className="w-full bg-secondary/50 border border-border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary/40 text-foreground"
                  >
                    {LEVELS.map((l) => (
                      <option key={l} value={l}>{l.charAt(0).toUpperCase() + l.slice(1)}</option>
                    ))}
                  </select>
                </Field>
                <Field label="Year">
                  <Input
                    type="number"
                    value={form.year ?? ""}
                    onChange={(e) => setForm({ ...form, year: e.target.value ? Number(e.target.value) : null })}
                    placeholder="e.g. 2024"
                    min={1990}
                    max={2030}
                    className="bg-secondary/50"
                  />
                </Field>
                <Field label="Semester">
                  <select
                    value={form.semester ?? ""}
                    onChange={(e) => setForm({ ...form, semester: e.target.value || null })}
                    className="w-full bg-secondary/50 border border-border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary/40 text-foreground"
                  >
                    <option value="">— none —</option>
                    {SEMESTERS.map((s) => (
                      <option key={s} value={s}>{s}</option>
                    ))}
                  </select>
                </Field>
              </div>

              {/* Instructor */}
              <Field label="Instructor">
                <Input
                  value={form.instructor ?? ""}
                  onChange={(e) => setForm({ ...form, instructor: e.target.value })}
                  placeholder="Prof. John Smith"
                  className="bg-secondary/50"
                />
              </Field>

              {/* Thumbnail URL */}
              <Field label="Thumbnail URL">
                <Input
                  value={form.thumbnail_url ?? ""}
                  onChange={(e) => setForm({ ...form, thumbnail_url: e.target.value })}
                  placeholder="https://…"
                  className="bg-secondary/50 font-mono text-xs"
                />
              </Field>

              {/* YouTube Playlist */}
              <Field label="YouTube Playlist ID">
                <Input
                  value={form.youtube_playlist_id ?? ""}
                  onChange={(e) => setForm({ ...form, youtube_playlist_id: e.target.value })}
                  placeholder="PLxxxxx"
                  className="bg-secondary/50 font-mono text-xs"
                />
              </Field>

              {/* Materials */}
              <div>
                <label className="block text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-2">
                  Materials
                </label>
                <div className="space-y-3">
                  <ToggleRow
                    label="Has Video Lectures"
                    checked={form.has_video_lectures ?? false}
                    onChange={(v) => setForm({ ...form, has_video_lectures: v })}
                  />
                  <ToggleRow
                    label="Has Lecture Notes"
                    checked={form.has_lecture_notes ?? false}
                    onChange={(v) => setForm({ ...form, has_lecture_notes: v })}
                  >
                    {form.has_lecture_notes && (
                      <Input
                        value={form.lecture_notes_url ?? ""}
                        onChange={(e) => setForm({ ...form, lecture_notes_url: e.target.value })}
                        placeholder="Lecture notes URL"
                        className="mt-2 bg-secondary/50 font-mono text-xs"
                      />
                    )}
                  </ToggleRow>
                  <ToggleRow
                    label="Has Exams"
                    checked={form.has_exams ?? false}
                    onChange={(v) => setForm({ ...form, has_exams: v })}
                  >
                    {form.has_exams && (
                      <Input
                        value={form.exams_url ?? ""}
                        onChange={(e) => setForm({ ...form, exams_url: e.target.value })}
                        placeholder="Exams URL"
                        className="mt-2 bg-secondary/50 font-mono text-xs"
                      />
                    )}
                  </ToggleRow>
                </div>
              </div>

              {/* Published toggle */}
              <div className="flex items-center justify-between rounded-lg border border-white/[0.08] px-4 py-3 bg-secondary/30">
                <div>
                  <p className="text-sm font-medium">Published</p>
                  <p className="text-xs text-muted-foreground mt-0.5">Visible to all users on the public site</p>
                </div>
                <button
                  type="button"
                  onClick={() => setForm({ ...form, is_published: !form.is_published })}
                  className={cn(
                    "relative inline-flex h-6 w-11 rounded-full transition-colors duration-200 focus:outline-none focus:ring-2 focus:ring-primary/50 shrink-0",
                    form.is_published ? "bg-primary" : "bg-muted"
                  )}
                >
                  <span
                    className={cn(
                      "absolute top-0.5 left-0.5 h-5 w-5 rounded-full bg-white shadow-sm transition-transform duration-200",
                      form.is_published ? "translate-x-5" : "translate-x-0"
                    )}
                  />
                </button>
              </div>
            </form>
          )}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between px-6 py-4 border-t border-white/[0.07] shrink-0 bg-card/50">
          <button
            type="button"
            onClick={onClose}
            className="px-4 py-2 rounded-lg text-sm font-medium text-muted-foreground hover:text-foreground hover:bg-white/[0.06] transition-colors"
          >
            Cancel
          </button>
          <Button
            form="edit-form"
            type="submit"
            disabled={isPending || isSuccess || isLoading || form === null}
            className={cn(
              "gap-2 transition-all duration-200 min-w-[120px]",
              isSuccess && "bg-emerald-600 hover:bg-emerald-600"
            )}
          >
            {isSuccess ? (
              <><Check className="h-4 w-4" /> Saved!</>
            ) : isPending ? (
              <><Loader2 className="h-4 w-4 animate-spin" /> Saving…</>
            ) : (
              "Save Changes"
            )}
          </Button>
        </div>
      </div>
    </div>
  );
}

function Field({
  label,
  required,
  children,
}: {
  label: string;
  required?: boolean;
  children: React.ReactNode;
}) {
  return (
    <div>
      <label className="block text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-1.5">
        {label}{required && <span className="text-primary ml-0.5">*</span>}
      </label>
      {children}
    </div>
  );
}

function ToggleRow({
  label,
  checked,
  onChange,
  children,
}: {
  label: string;
  checked: boolean;
  onChange: (v: boolean) => void;
  children?: React.ReactNode;
}) {
  return (
    <div>
      <label className="flex items-center gap-3 cursor-pointer select-none group">
        <div
          className={cn(
            "h-5 w-5 rounded-md border-2 flex items-center justify-center transition-all duration-150",
            checked
              ? "bg-primary border-primary"
              : "border-border group-hover:border-primary/50"
          )}
          onClick={() => onChange(!checked)}
        >
          {checked && <Check className="h-3 w-3 text-white" />}
        </div>
        <span className="text-sm font-medium">{label}</span>
      </label>
      {children}
    </div>
  );
}

// ── Main Page ─────────────────────────────────────────────────────────────────

export default function AdminCoursesPage() {
  const [page, setPage] = useState(1);
  const [q, setQ] = useState("");
  const [editId, setEditId] = useState<string | null>(null);

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
          <h1 className="text-2xl font-bold tracking-tight">Courses</h1>
          <p className="text-muted-foreground text-sm mt-1">
            {isLoading ? "Loading…" : `${total.toLocaleString()} courses`}
          </p>
        </div>
      </div>

      {/* Search */}
      <div className="relative max-w-xs">
        <Input
          placeholder="Filter by title…"
          value={q}
          onChange={(e) => {
            setQ(e.target.value);
            setPage(1);
          }}
          className="bg-secondary/50 pr-8"
        />
        {q && (
          <button
            onClick={() => setQ("")}
            className="absolute right-2.5 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
          >
            <X className="h-3.5 w-3.5" />
          </button>
        )}
      </div>

      <div className="rounded-xl border border-white/[0.08] bg-card/60 overflow-hidden">
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
                <tr className="border-b border-white/[0.07] bg-white/[0.02]">
                  <th className="text-left px-4 py-3 font-semibold text-xs uppercase tracking-wider text-muted-foreground">Title</th>
                  <th className="text-left px-4 py-3 font-semibold text-xs uppercase tracking-wider text-muted-foreground">University</th>
                  <th className="text-left px-4 py-3 font-semibold text-xs uppercase tracking-wider text-muted-foreground">Level</th>
                  <th className="text-left px-4 py-3 font-semibold text-xs uppercase tracking-wider text-muted-foreground">Videos</th>
                  <th className="text-left px-4 py-3 font-semibold text-xs uppercase tracking-wider text-muted-foreground">Status</th>
                  <th className="text-right px-4 py-3 font-semibold text-xs uppercase tracking-wider text-muted-foreground">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/[0.04]">
                {courses.map((course) => (
                  <tr
                    key={course.id}
                    className="hover:bg-white/[0.03] transition-colors group"
                  >
                    <td className="px-4 py-3 max-w-xs">
                      <Link
                        href={`/courses/${course.slug}`}
                        className="hover:text-primary transition-colors line-clamp-1 font-medium"
                      >
                        {course.title}
                      </Link>
                    </td>
                    <td className="px-4 py-3 text-muted-foreground whitespace-nowrap text-sm">
                      {course.university_name}
                    </td>
                    <td className="px-4 py-3">
                      <span className={cn("px-2 py-0.5 rounded-full text-[11px] font-semibold", levelColor(course.level))}>
                        {levelLabel(course.level)}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-muted-foreground tabular-nums text-sm">{course.total_videos}</td>
                    <td className="px-4 py-3">
                      {course.is_published ? (
                        <span className="inline-flex items-center gap-1.5 text-[11px] font-semibold text-emerald-400">
                          <Eye className="h-3 w-3" /> Published
                        </span>
                      ) : (
                        <span className="inline-flex items-center gap-1.5 text-[11px] font-semibold text-muted-foreground">
                          <EyeOff className="h-3 w-3" /> Hidden
                        </span>
                      )}
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex items-center justify-end gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                        <button
                          onClick={() => setEditId(course.id)}
                          className="p-1.5 rounded-lg hover:bg-white/[0.08] text-muted-foreground hover:text-foreground transition-colors"
                          title="Edit course"
                        >
                          <Pencil className="h-3.5 w-3.5" />
                        </button>
                        <Link
                          href={`/courses/${course.slug}`}
                          target="_blank"
                          className="p-1.5 rounded-lg hover:bg-white/[0.08] text-muted-foreground hover:text-foreground transition-colors"
                          title="View on site"
                        >
                          <ExternalLink className="h-3.5 w-3.5" />
                        </Link>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

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

      {/* Edit modal */}
      {editId && (
        <EditModal
          courseId={editId}
          onClose={() => setEditId(null)}
        />
      )}
    </div>
  );
}
