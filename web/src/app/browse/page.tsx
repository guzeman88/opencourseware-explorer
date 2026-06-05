"use client";

import { useState } from "react";
import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { ChevronDown, ChevronRight } from "lucide-react";
import { useUniversities } from "@/hooks/use-universities";
import { fetchUniversityCourses, fetchCourses, fetchStrictSubjectCourses, fetchSubjects } from "@/lib/api";
import type { CourseSummary, Subject, University } from "@/types";
import { cn } from "@/lib/utils";

const LEVEL_COLOR: Record<string, string> = {
  undergraduate: "text-sky-400",
  graduate: "text-violet-400",
  professional: "text-emerald-400",
  other: "text-muted-foreground",
};

// ── Shared table header ───────────────────────────────────────────────────────

function TableHeader({ showUniversity }: { showUniversity?: boolean }) {
  return (
    <div className="flex items-center border-b border-border bg-muted/60 text-xs font-semibold text-muted-foreground uppercase tracking-wider">
      <div className="w-10 shrink-0 text-center border-r border-border py-2">#</div>
      <div className="flex-1 px-3 py-2 min-w-0">Course Title</div>
      {showUniversity && (
        <div className="w-44 shrink-0 px-3 py-2 border-l border-border hidden md:block">University</div>
      )}
      <div className="w-44 shrink-0 px-3 py-2 border-l border-border hidden lg:block">Instructor</div>
      <div className="w-28 shrink-0 px-3 py-2 border-l border-border hidden sm:block">Level</div>
      <div className="w-16 shrink-0 px-3 py-2 border-l border-border text-right">Year</div>
    </div>
  );
}

// ── Single course row ─────────────────────────────────────────────────────────

function CourseRow({
  course,
  idx,
  showUniversity,
}: {
  course: CourseSummary;
  idx: number;
  showUniversity?: boolean;
}) {
  return (
    <div
      className={cn(
        "flex items-center border-b border-border/40 text-sm hover:bg-primary/5 transition-colors group",
        idx % 2 === 0 ? "bg-background" : "bg-muted/10"
      )}
    >
      <div className="w-10 shrink-0 text-center text-xs text-muted-foreground border-r border-border/40 py-2 tabular-nums">
        {idx + 1}
      </div>
      <div className="flex-1 px-3 py-2 min-w-0 truncate">
        <Link
          href={`/courses/${course.slug}`}
          className="hover:text-primary hover:underline underline-offset-2"
        >
          {course.title}
        </Link>
      </div>
      {showUniversity && (
        <div className="w-44 shrink-0 px-3 py-2 text-xs text-muted-foreground border-l border-border/40 truncate hidden md:block">
          {course.university_name}
        </div>
      )}
      <div className="w-44 shrink-0 px-3 py-2 text-xs text-muted-foreground border-l border-border/40 truncate hidden lg:block">
        {course.instructor ?? "—"}
      </div>
      <div className="w-28 shrink-0 px-3 py-2 text-xs border-l border-border/40 hidden sm:block">
        <span className={LEVEL_COLOR[course.level] ?? "text-muted-foreground"}>
          {course.level}
        </span>
      </div>
      <div className="w-16 shrink-0 px-3 py-2 text-xs text-muted-foreground border-l border-border/40 text-right tabular-nums">
        {course.year ?? "—"}
      </div>
    </div>
  );
}

// ── Subject sub-group inside a university ─────────────────────────────────────

function SubjectGroup({
  name,
  courses,
  startIdx,
}: {
  name: string;
  courses: CourseSummary[];
  startIdx: number;
}) {
  const [open, setOpen] = useState(true);
  return (
    <div>
      <button
        onClick={() => setOpen((v) => !v)}
        className="w-full flex items-center gap-2 pl-10 pr-4 py-1 bg-muted/20 hover:bg-muted/40 transition-colors text-left border-b border-border/40"
      >
        {open ? (
          <ChevronDown className="h-3.5 w-3.5 text-muted-foreground shrink-0" />
        ) : (
          <ChevronRight className="h-3.5 w-3.5 text-muted-foreground shrink-0" />
        )}
        <span className="text-xs font-semibold text-muted-foreground">{name}</span>
        <span className="text-xs text-muted-foreground/60 ml-1">({courses.length})</span>
      </button>
      {open &&
        courses.map((c, i) => (
          <CourseRow key={c.id} course={c} idx={startIdx + i} />
        ))}
    </div>
  );
}

// ── Expandable university section ─────────────────────────────────────────────

function UniversitySection({ uni }: { uni: University }) {
  const [open, setOpen] = useState(false);

  const { data: rawData, isLoading } = useQuery({
    queryKey: ["browse_uni", uni.slug],
    queryFn: async () => {
      const first = await fetchUniversityCourses(uni.slug, {
        page_size: 100,
        sort_by: "view_count",
        sort_dir: "desc",
      });
      if (first.total <= 100) return first;
      const extraPages = Math.ceil((first.total - 100) / 100);
      const rest = await Promise.all(
        Array.from({ length: extraPages }, (_, i) =>
          fetchUniversityCourses(uni.slug, {
            page: i + 2,
            page_size: 100,
            sort_by: "view_count",
            sort_dir: "desc",
          })
        )
      );
      return { ...first, items: [...first.items, ...rest.flatMap((r) => r.items)] };
    },
    enabled: open,
  });
  const data = rawData;

  const courses = data?.items ?? [];

  // Group by first subject name
  const grouped: Record<string, CourseSummary[]> = {};
  for (const c of courses) {
    const key = c.subjects[0]?.name ?? "General";
    (grouped[key] ??= []).push(c);
  }
  const subjectKeys = Object.keys(grouped).sort();

  // Running index across groups
  let runningIdx = 0;

  return (
    <div className="border-b border-border">
      {/* University header row */}
      <button
        onClick={() => setOpen((v) => !v)}
        className="w-full flex items-center gap-2 px-4 py-2.5 bg-muted/50 hover:bg-muted/80 transition-colors text-left"
      >
        {open ? (
          <ChevronDown className="h-4 w-4 shrink-0 text-primary" />
        ) : (
          <ChevronRight className="h-4 w-4 shrink-0 text-muted-foreground" />
        )}
        <span className="font-semibold text-sm">{uni.name}</span>
        {uni.country && (
          <span className="text-xs text-muted-foreground hidden sm:inline">
            &nbsp;·&nbsp;{uni.country}
          </span>
        )}
        <span className="ml-auto text-xs text-muted-foreground tabular-nums">
          {(uni.course_count ?? 0).toLocaleString()} courses
        </span>
      </button>

      {open && (
        <div>
          {isLoading ? (
            <div className="pl-10 py-4 text-sm text-muted-foreground">Loading…</div>
          ) : courses.length === 0 ? (
            <div className="pl-10 py-4 text-sm text-muted-foreground">
              No courses available.
            </div>
          ) : (
            subjectKeys.map((subject) => {
              const start = runningIdx;
              runningIdx += grouped[subject].length;
              return (
                <SubjectGroup
                  key={subject}
                  name={subject}
                  courses={grouped[subject]}
                  startIdx={start}
                />
              );
            })
          )}
        </div>
      )}
    </div>
  );
}

// ── Expandable subject section ────────────────────────────────────────────────

function SubjectSection({ subject }: { subject: Subject }) {
  const [open, setOpen] = useState(false);

  const { data, isLoading } = useQuery({
    queryKey: ["browse_subject", subject.slug],
    queryFn: async () => {
      return fetchStrictSubjectCourses(subject.slug, 100);
    },
    enabled: open,
  });

  const courses = data?.items ?? [];

  return (
    <div className="border-b border-border">
      <button
        onClick={() => setOpen((v) => !v)}
        className="w-full flex items-center gap-2 px-4 py-2.5 bg-muted/50 hover:bg-muted/80 transition-colors text-left"
      >
        {open ? (
          <ChevronDown className="h-4 w-4 shrink-0 text-primary" />
        ) : (
          <ChevronRight className="h-4 w-4 shrink-0 text-muted-foreground" />
        )}
        <span className="font-semibold text-sm">{subject.name}</span>
        <span className="ml-auto text-xs text-muted-foreground tabular-nums">
          {(subject.course_count ?? 0).toLocaleString()} courses
        </span>
      </button>

      {open && (
        <div>
          {!isLoading && courses.length > 0 && (
            <TableHeader showUniversity />
          )}
          {isLoading ? (
            <div className="pl-10 py-4 text-sm text-muted-foreground">Loading…</div>
          ) : courses.length === 0 ? (
            <div className="pl-10 py-4 text-sm text-muted-foreground">
              No courses available.
            </div>
          ) : (
            courses.map((c, i) => (
              <CourseRow key={c.id} course={c} idx={i} showUniversity />
            ))
          )}
        </div>
      )}
    </div>
  );
}

// ── Page ──────────────────────────────────────────────────────────────────────

export default function BrowsePage() {
  const [mode, setMode] = useState<"university" | "subject">("university");
  const [search, setSearch] = useState("");

  const { data: uniData, isLoading: uniLoading } = useUniversities(1, 100);
  const { data: subjectData, isLoading: subjectLoading } = useQuery({
    queryKey: ["subjects_all"],
    queryFn: () => fetchSubjects(false),
  });

  const universities = (uniData?.items ?? []).filter(
    (u) => !search || u.name.toLowerCase().includes(search.toLowerCase())
  );

  const subjects = (subjectData?.items ?? [])
    .filter(
      (s) => !search || s.name.toLowerCase().includes(search.toLowerCase())
    )
    .sort((a, b) => a.name.localeCompare(b.name));

  return (
    <div className="max-w-screen-2xl mx-auto px-4 md:px-8 py-8 space-y-6">
      {/* Page header */}
      <div>
        <h1 className="text-2xl font-bold">Browse Courses</h1>
        <p className="text-sm text-muted-foreground mt-1">
          Expand any row to view courses in a spreadsheet-style list
        </p>
      </div>

      {/* Controls bar */}
      <div className="flex items-center gap-3 flex-wrap">
        {/* Toggle */}
        <div className="flex rounded-md border border-border overflow-hidden text-sm font-medium">
          <button
            onClick={() => {
              setMode("university");
              setSearch("");
            }}
            className={cn(
              "px-4 py-1.5 transition-colors",
              mode === "university"
                ? "bg-primary text-primary-foreground"
                : "bg-background text-muted-foreground hover:bg-muted"
            )}
          >
            By University
          </button>
          <button
            onClick={() => {
              setMode("subject");
              setSearch("");
            }}
            className={cn(
              "px-4 py-1.5 border-l border-border transition-colors",
              mode === "subject"
                ? "bg-primary text-primary-foreground"
                : "bg-background text-muted-foreground hover:bg-muted"
            )}
          >
            By Subject
          </button>
        </div>

        {/* Filter */}
        <input
          type="search"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder={
            mode === "university"
              ? "Filter universities…"
              : "Filter subjects…"
          }
          className="bg-secondary border border-border rounded-md px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-primary w-56 placeholder:text-muted-foreground"
        />

        <span className="text-xs text-muted-foreground">
          {mode === "university"
            ? `${universities.length} universities`
            : `${subjects.length} subjects`}
        </span>
      </div>

      {/* Table */}
      <div className="border border-border rounded-md overflow-hidden">
        {mode === "university" && (
          <>
            <TableHeader />
            {uniLoading ? (
              <div className="py-12 text-center text-sm text-muted-foreground">
                Loading universities…
              </div>
            ) : universities.length === 0 ? (
              <div className="py-12 text-center text-sm text-muted-foreground">
                No universities match your filter.
              </div>
            ) : (
              universities.map((uni) => (
                <UniversitySection key={uni.id} uni={uni} />
              ))
            )}
          </>
        )}

        {mode === "subject" && (
          <>
            {subjectLoading ? (
              <div className="py-12 text-center text-sm text-muted-foreground">
                Loading subjects…
              </div>
            ) : subjects.length === 0 ? (
              <div className="py-12 text-center text-sm text-muted-foreground">
                No subjects match your filter.
              </div>
            ) : (
              subjects.map((s) => <SubjectSection key={s.id} subject={s} />)
            )}
          </>
        )}
      </div>
    </div>
  );
}
