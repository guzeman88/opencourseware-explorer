"use client";

import { useQuery } from "@tanstack/react-query";
import { fetchRoadmaps } from "@/lib/api";
import Link from "next/link";
import {
  GraduationCap, BookOpen, Code2, Atom, Calculator, BarChart3,
  Cpu, Leaf, DollarSign, FlaskConical, Wrench, Clock, Globe,
  Search, ChevronRight,
} from "lucide-react";
import { useState, useMemo } from "react";
import { cn } from "@/lib/utils";
import type { RoadmapSummary } from "@/types";

// ── Field taxonomy ────────────────────────────────────────────────────────────
const FIELD_MAP: Record<string, string> = {
  "Computer Science":                              "Computer Science",
  "Electrical Engineering and Computer Science":   "Computer Science",
  "Electrical Engineering and Computer Sciences":  "Computer Science",
  "Electrical Engineering":                        "Electrical Engineering",
  "Data Science":                                  "Data Science",
  "Mathematics":                                   "Mathematics",
  "Applied Mathematics":                           "Mathematics",
  "Statistics":                                    "Statistics",
  "Physics":                                       "Physics",
  "Web Development":                               "Web Development",
  "Mechanical Engineering":                        "Engineering",
  "Aerospace Engineering":                         "Engineering",
  "Chemical Engineering":                          "Chemistry & Chemical Eng",
  "Chemistry":                                     "Chemistry & Chemical Eng",
  "Biology":                                       "Biology & Life Sciences",
  "Molecular Biology":                             "Biology & Life Sciences",
  "Economics":                                     "Economics",
};

function fieldFor(major?: string | null): string {
  if (!major) return "Other";
  return FIELD_MAP[major] ?? major;
}

const FIELD_ICONS: Record<string, React.ReactNode> = {
  "Computer Science":            <Code2 className="h-4 w-4" />,
  "Electrical Engineering":      <Cpu className="h-4 w-4" />,
  "Data Science":                <BarChart3 className="h-4 w-4" />,
  "Mathematics":                 <Calculator className="h-4 w-4" />,
  "Statistics":                  <BarChart3 className="h-4 w-4" />,
  "Physics":                     <Atom className="h-4 w-4" />,
  "Web Development":             <Globe className="h-4 w-4" />,
  "Engineering":                 <Wrench className="h-4 w-4" />,
  "Chemistry & Chemical Eng":    <FlaskConical className="h-4 w-4" />,
  "Biology & Life Sciences":     <Leaf className="h-4 w-4" />,
  "Economics":                   <DollarSign className="h-4 w-4" />,
};

const FIELD_COLORS: Record<string, string> = {
  "Computer Science":           "bg-blue-500/10 text-blue-400 border-blue-500/30",
  "Electrical Engineering":     "bg-yellow-500/10 text-yellow-400 border-yellow-500/30",
  "Data Science":               "bg-cyan-500/10 text-cyan-400 border-cyan-500/30",
  "Mathematics":                "bg-violet-500/10 text-violet-400 border-violet-500/30",
  "Statistics":                 "bg-indigo-500/10 text-indigo-400 border-indigo-500/30",
  "Physics":                    "bg-orange-500/10 text-orange-400 border-orange-500/30",
  "Web Development":            "bg-green-500/10 text-green-400 border-green-500/30",
  "Engineering":                "bg-amber-500/10 text-amber-400 border-amber-500/30",
  "Chemistry & Chemical Eng":   "bg-emerald-500/10 text-emerald-400 border-emerald-500/30",
  "Biology & Life Sciences":    "bg-lime-500/10 text-lime-400 border-lime-500/30",
  "Economics":                  "bg-rose-500/10 text-rose-400 border-rose-500/30",
};

const DEGREE_COLORS: Record<string, string> = {
  "Bachelor of Science":                  "bg-blue-900/40 text-blue-300",
  "Bachelor of Arts":                     "bg-purple-900/40 text-purple-300",
  "Bachelor of Science in Engineering":   "bg-orange-900/40 text-orange-300",
  "Bachelor of Arts / Master of Engineering": "bg-teal-900/40 text-teal-300",
  "Master of Engineering":                "bg-green-900/40 text-green-300",
  "Master of Science":                    "bg-emerald-900/40 text-emerald-300",
  "Self-paced":                           "bg-yellow-900/40 text-yellow-300",
  "Self-paced Certification":             "bg-yellow-900/40 text-yellow-300",
  "Bachelor of Technology":               "bg-indigo-900/40 text-indigo-300",
};

// ── Card ─────────────────────────────────────────────────────────────────────
function RoadmapCard({ rm }: { rm: RoadmapSummary }) {
  const field = fieldFor(rm.major);
  const fieldCls = FIELD_COLORS[field] ?? "bg-muted/30 text-muted-foreground border-border";
  const degreeCls = DEGREE_COLORS[rm.degree_type ?? ""] ?? "bg-muted/30 text-muted-foreground";

  return (
    <Link
      href={`/roadmaps/${rm.slug}`}
      className="group flex flex-col gap-3 p-5 rounded-xl bg-card border border-border/50 hover:border-primary/40 hover:shadow-lg hover:shadow-black/20 transition-all"
    >
      <div className="flex items-start justify-between gap-2">
        <span className={cn("flex items-center gap-1.5 text-xs font-medium px-2 py-1 rounded-md border", fieldCls)}>
          {FIELD_ICONS[field]}
          {field}
        </span>
        {rm.degree_type && (
          <span className={cn("text-[10px] font-medium px-2 py-0.5 rounded-full shrink-0", degreeCls)}>
            {rm.degree_type.replace("Bachelor of ", "B. of ").replace("Master of ", "M. of ")}
          </span>
        )}
      </div>

      <div className="flex-1 space-y-1">
        <h3 className="font-semibold text-sm leading-tight group-hover:text-primary transition-colors line-clamp-2">
          {rm.title}
        </h3>
        {rm.university_name && (
          <p className="text-xs text-muted-foreground">{rm.university_name}</p>
        )}
        {rm.description && (
          <p className="text-xs text-muted-foreground line-clamp-2 mt-1 leading-relaxed">
            {rm.description}
          </p>
        )}
      </div>

      <div className="flex items-center justify-between text-xs text-muted-foreground pt-2 border-t border-border/40">
        <span className="flex items-center gap-1">
          <BookOpen className="h-3.5 w-3.5" />
          {rm.entry_count} courses
        </span>
        {rm.estimated_years && (
          <span className="flex items-center gap-1">
            <Clock className="h-3.5 w-3.5" />
            {rm.estimated_years} {rm.estimated_years === 1 ? "yr" : "yrs"}
          </span>
        )}
        <ChevronRight className="h-3.5 w-3.5 opacity-0 group-hover:opacity-100 transition-opacity" />
      </div>
    </Link>
  );
}

// ── Field hero pill ───────────────────────────────────────────────────────────
function FieldPill({
  field, count, active, onClick,
}: { field: string; count: number; active: boolean; onClick: () => void }) {
  const cls = FIELD_COLORS[field] ?? "bg-muted/30 text-muted-foreground border-border";
  return (
    <button
      onClick={onClick}
      className={cn(
        "flex items-center gap-2 px-3 py-1.5 rounded-full border text-xs font-medium transition-all",
        active
          ? cn(cls, "ring-2 ring-offset-2 ring-offset-background ring-primary/50 scale-105")
          : cn(cls, "opacity-60 hover:opacity-100"),
      )}
    >
      {FIELD_ICONS[field] ?? <GraduationCap className="h-4 w-4" />}
      {field}
      <span className="ml-0.5 rounded-full bg-black/20 px-1.5 py-0.5 text-[10px]">{count}</span>
    </button>
  );
}

// ── Page ──────────────────────────────────────────────────────────────────────
export default function RoadmapsPage() {
  const [activeField, setActiveField] = useState<string | null>(null);
  const [search, setSearch] = useState("");

  const { data, isLoading } = useQuery({
    queryKey: ["roadmaps-all"],
    queryFn: () => fetchRoadmaps({ page_size: 200 }),
    staleTime: 60_000,
  });

  const allRoadmaps = data?.items ?? [];

  // Derive fields with counts
  const fieldCounts = useMemo(() => {
    const m: Record<string, number> = {};
    for (const r of allRoadmaps) {
      const f = fieldFor(r.major);
      m[f] = (m[f] ?? 0) + 1;
    }
    return m;
  }, [allRoadmaps]);

  const fields = useMemo(
    () => Object.entries(fieldCounts).sort((a, b) => b[1] - a[1]).map(([f]) => f),
    [fieldCounts],
  );

  // Filter by field + search
  const filtered = useMemo(() => {
    let list = allRoadmaps;
    if (activeField) list = list.filter((r) => fieldFor(r.major) === activeField);
    if (search.trim()) {
      const q = search.toLowerCase();
      list = list.filter(
        (r) =>
          r.title.toLowerCase().includes(q) ||
          (r.major ?? "").toLowerCase().includes(q) ||
          (r.university_name ?? "").toLowerCase().includes(q) ||
          (r.description ?? "").toLowerCase().includes(q),
      );
    }
    return list;
  }, [allRoadmaps, activeField, search]);

  // Group for "All" view
  const grouped = useMemo(() => {
    if (activeField || search) return null;
    const m: Record<string, RoadmapSummary[]> = {};
    for (const r of filtered) {
      const f = fieldFor(r.major);
      if (!m[f]) m[f] = [];
      m[f].push(r);
    }
    // Sort each group by university name
    for (const f of Object.keys(m)) m[f].sort((a, b) => (a.university_name ?? "").localeCompare(b.university_name ?? ""));
    return m;
  }, [filtered, activeField, search]);

  return (
    <div className="max-w-screen-xl mx-auto px-4 md:px-8 py-8 space-y-8">
      {/* Header */}
      <div className="space-y-2">
        <h1 className="text-3xl font-bold">Degree Roadmaps</h1>
        <p className="text-muted-foreground max-w-2xl">
          Real course sequences from top universities, organized by field. Pick a subject
          to compare programs side-by-side across MIT, Stanford, Harvard, and more.
        </p>
      </div>

      {/* Field filters */}
      <div className="flex flex-wrap gap-2">
        <button
          onClick={() => setActiveField(null)}
          className={cn(
            "flex items-center gap-2 px-3 py-1.5 rounded-full border text-xs font-medium transition-all",
            !activeField
              ? "bg-primary text-primary-foreground border-primary ring-2 ring-primary/30"
              : "border-border text-muted-foreground hover:border-primary/50 hover:text-foreground",
          )}
        >
          <GraduationCap className="h-4 w-4" />
          All Fields
          <span className="rounded-full bg-black/20 px-1.5 py-0.5 text-[10px]">{allRoadmaps.length}</span>
        </button>
        {fields.map((f) => (
          <FieldPill
            key={f}
            field={f}
            count={fieldCounts[f]}
            active={activeField === f}
            onClick={() => setActiveField(activeField === f ? null : f)}
          />
        ))}
      </div>

      {/* Search */}
      <div className="relative max-w-md">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground pointer-events-none" />
        <input
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Search programs, universities, fields…"
          className="w-full pl-9 pr-4 py-2.5 rounded-lg bg-card border border-border text-sm placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary/50"
        />
      </div>

      {/* Content */}
      {isLoading ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 xl:grid-cols-4 gap-4">
          {Array.from({ length: 12 }).map((_, i) => (
            <div key={i} className="h-52 rounded-xl bg-muted animate-pulse" />
          ))}
        </div>
      ) : filtered.length === 0 ? (
        <p className="text-muted-foreground py-12 text-center">No roadmaps match your search.</p>
      ) : grouped ? (
        // Grouped by field view
        <div className="space-y-12">
          {Object.entries(grouped).map(([field, items]) => {
            const fieldCls = FIELD_COLORS[field] ?? "bg-muted/30 text-muted-foreground border-border";
            return (
              <section key={field}>
                <div className="flex items-center gap-3 mb-5">
                  <span className={cn("flex items-center gap-2 text-sm font-semibold px-3 py-1.5 rounded-lg border", fieldCls)}>
                    {FIELD_ICONS[field] ?? <GraduationCap className="h-4 w-4" />}
                    {field}
                  </span>
                  <span className="text-sm text-muted-foreground">
                    {items.length} {items.length === 1 ? "program" : "programs"} from {[...new Set(items.map(r => r.university_name))].length} universities
                  </span>
                  <button
                    onClick={() => setActiveField(field)}
                    className="ml-auto text-xs text-primary hover:underline flex items-center gap-1"
                  >
                    View all <ChevronRight className="h-3 w-3" />
                  </button>
                </div>
                <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 xl:grid-cols-4 gap-4">
                  {items.map((rm) => (
                    <RoadmapCard key={rm.id} rm={rm} />
                  ))}
                </div>
              </section>
            );
          })}
        </div>
      ) : (
        // Flat filtered view
        <div>
          <p className="text-sm text-muted-foreground mb-4">
            {filtered.length} program{filtered.length !== 1 ? "s" : ""}
            {activeField ? ` in ${activeField}` : ""}
          </p>
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 xl:grid-cols-4 gap-4">
            {filtered.map((rm) => (
              <RoadmapCard key={rm.id} rm={rm} />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

