"use client";

import { useQuery } from "@tanstack/react-query";
import { fetchStats } from "@/lib/api";
import {
  GraduationCap,
  BookOpen,
  Play,
  Tag,
  Video,
  Clock,
  TrendingUp,
} from "lucide-react";
import { Skeleton } from "@/components/ui/skeleton";
import { sourceLabel } from "@/lib/utils";
import Link from "next/link";

const SOURCE_TOTALS: Record<string, number | null> = {
  mit_ocw:      2573,
  nptel:        3200,
  yale:         42,
  harvard:      142,
  freecodecamp: 700,
  crashcourse:  44,
  khan:         200,
  stanford:     130,
  berkeley:     300,
  cmu:          60,
  oxford:       100,
  gatech:       80,
  simons:       60,
  cambridge:    60,
  princeton:    50,
  mit_youtube:  150,
  "3b1b":       15,
};

export default function AdminDashboardPage() {
  const { data: stats, isLoading } = useQuery({
    queryKey: ["admin_stats"],
    queryFn: fetchStats,
  });

  const statCards = [
    {
      label: "Universities",
      value: stats?.total_universities,
      icon: GraduationCap,
      color: "text-blue-400",
      bg: "bg-blue-500/10",
      href: undefined,
    },
    {
      label: "Total Courses",
      value: stats?.total_courses,
      icon: BookOpen,
      color: "text-violet-400",
      bg: "bg-violet-500/10",
      href: "/admin/courses",
    },
    {
      label: "With Video",
      value: stats?.courses_with_video,
      icon: Video,
      color: "text-emerald-400",
      bg: "bg-emerald-500/10",
      href: undefined,
    },
    {
      label: "Total Videos",
      value: stats?.total_videos,
      icon: Play,
      color: "text-primary",
      bg: "bg-primary/10",
      href: undefined,
    },
    {
      label: "Subjects",
      value: stats?.total_subjects,
      icon: Tag,
      color: "text-amber-400",
      bg: "bg-amber-500/10",
      href: undefined,
    },
    {
      label: "Pending Review",
      value: stats?.pending_review,
      icon: Clock,
      color: (stats?.pending_review ?? 0) > 0 ? "text-orange-400" : "text-muted-foreground",
      bg: (stats?.pending_review ?? 0) > 0 ? "bg-orange-500/10" : "bg-muted/50",
      href: "/admin/pending-review",
      highlight: (stats?.pending_review ?? 0) > 0,
    },
  ];

  const totalKnown = stats?.sources?.reduce((acc, s) => {
    const total = SOURCE_TOTALS[s.source_key];
    return total != null ? acc + total : acc;
  }, 0) ?? 0;

  const totalInDb = stats?.sources?.reduce((acc, s) => acc + s.count, 0) ?? 0;
  const coverage = totalKnown > 0 ? Math.round((totalInDb / totalKnown) * 100) : null;

  return (
    <div className="space-y-8">
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Dashboard</h1>
          <p className="text-muted-foreground text-sm mt-1">
            Platform overview and data health
          </p>
        </div>
        {coverage != null && !isLoading && (
          <div className="flex items-center gap-2 px-4 py-2 rounded-xl bg-emerald-500/10 border border-emerald-500/20">
            <TrendingUp className="h-4 w-4 text-emerald-400" />
            <span className="text-sm font-semibold text-emerald-400">{coverage}% coverage</span>
          </div>
        )}
      </div>

      {/* Stat cards */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
        {statCards.map(({ label, value, icon: Icon, color, bg, href, highlight }) => {
          const card = (
            <div
              key={label}
              className={`relative overflow-hidden rounded-xl border p-4 transition-all duration-200 ${
                highlight
                  ? "border-orange-500/30 bg-orange-500/5 hover:border-orange-500/50"
                  : "border-white/[0.08] bg-card/60 hover:border-white/[0.14]"
              } ${href ? "cursor-pointer" : ""}`}
            >
              <div className={`inline-flex p-2 rounded-lg ${bg} mb-3`}>
                <Icon className={`h-4 w-4 ${color}`} />
              </div>
              {isLoading ? (
                <Skeleton className="h-8 w-20 mb-1" />
              ) : (
                <p className={`text-2xl font-bold tabular-nums ${highlight ? "text-orange-400" : "text-foreground"}`}>
                  {value?.toLocaleString() ?? "—"}
                </p>
              )}
              <p className="text-xs text-muted-foreground font-medium mt-0.5">{label}</p>
            </div>
          );
          return href ? (
            <Link key={label} href={href} className="block">
              {card}
            </Link>
          ) : (
            <div key={label}>{card}</div>
          );
        })}
      </div>

      {/* By source */}
      {stats?.sources && stats.sources.length > 0 && (
        <div className="rounded-xl border border-white/[0.08] bg-card/60 overflow-hidden">
          <div className="px-5 py-4 border-b border-white/[0.06]">
            <h2 className="font-semibold text-sm">Courses by Source</h2>
            <p className="text-xs text-muted-foreground mt-0.5">DB count vs. known total from source websites</p>
          </div>
          <div className="divide-y divide-white/[0.04]">
            {/* Header */}
            <div className="grid grid-cols-[1fr_90px_90px_90px] px-5 py-2.5 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
              <span>Source</span>
              <span className="text-right">In DB</span>
              <span className="text-right">Known Total</span>
              <span className="text-right">Coverage</span>
            </div>
            {stats.sources.map(({ source_key, count }) => {
              const total = SOURCE_TOTALS[source_key];
              const pct = total != null ? Math.min(100, Math.round((count / total) * 100)) : null;
              return (
                <div key={source_key} className="grid grid-cols-[1fr_90px_90px_90px] items-center px-5 py-3 hover:bg-white/[0.03] transition-colors">
                  <span className="text-sm font-medium">{sourceLabel(source_key)}</span>
                  <span className="text-sm tabular-nums font-bold text-right text-foreground">{count.toLocaleString()}</span>
                  <span className="text-sm tabular-nums text-right text-muted-foreground">
                    {total != null ? total.toLocaleString() : "—"}
                  </span>
                  <div className="flex items-center justify-end gap-2">
                    {pct != null ? (
                      <>
                        <div className="hidden sm:block h-1.5 w-12 rounded-full bg-muted overflow-hidden">
                          <div
                            className="h-full rounded-full bg-emerald-500/70"
                            style={{ width: `${pct}%` }}
                          />
                        </div>
                        <span className={`text-xs tabular-nums font-medium ${pct >= 80 ? "text-emerald-400" : pct >= 50 ? "text-amber-400" : "text-muted-foreground"}`}>
                          {pct}%
                        </span>
                      </>
                    ) : (
                      <span className="text-xs text-muted-foreground">—</span>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}


const SOURCE_TOTALS: Record<string, number | null> = {
  // Verified from source websites (May 2026) — see course-availability-report.csv
  mit_ocw:      2573,  // High: live search ocw.mit.edu/search → '2573 results'
  nptel:        3200,  // High: homepage stat '3200+ unique courses'
  yale:         42,    // High: full course listing counted from oyc.yale.edu
  harvard:      142,   // High: pll.harvard.edu/catalog/free → '142 results for FREE'
  freecodecamp: 700,   // High: Wikipedia '700+ full-length free-to-watch programming courses'
  crashcourse:  44,    // High: Wikipedia '44 main series'
  // Estimated — medium/low confidence
  khan:         200,
  stanford:     130,
  berkeley:     300,
  cmu:          60,
  oxford:       100,
  gatech:       80,
  simons:       60,
  cambridge:    60,
  princeton:    50,
  mit_youtube:  150,
  "3b1b":       15,
};

export default function AdminDashboardPage() {
  const { data: stats, isLoading } = useQuery({
    queryKey: ["admin_stats"],
    queryFn: fetchStats,
  });

  const statCards = [
    {
      label: "Universities",
      value: stats?.total_universities,
      icon: GraduationCap,
      href: undefined,
    },
    { label: "Total Courses", value: stats?.total_courses, icon: BookOpen, href: undefined },
    {
      label: "Courses with Video",
      value: stats?.courses_with_video,
      icon: Video,
      href: undefined,
    },
    { label: "Total Videos", value: stats?.total_videos, icon: Play, href: undefined },
    { label: "Subjects", value: stats?.total_subjects, icon: Tag, href: undefined },
    {
      label: "Pending Review",
      value: stats?.pending_review,
      icon: Clock,
      href: "/admin/pending-review",
      highlight: (stats?.pending_review ?? 0) > 0,
    },
  ];

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold">Dashboard</h1>
        <p className="text-muted-foreground text-sm mt-1">
          Database overview
        </p>
      </div>

      {/* Stat cards */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
        {statCards.map(({ label, value, icon: Icon, href, highlight }) => {
          const card = (
            <Card key={label} className={highlight ? "border-amber-500/50 bg-amber-500/5" : undefined}>
              <CardHeader className="pb-2">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
                    {label}
                  </span>
                  <Icon className={`h-4 w-4 ${highlight ? "text-amber-500" : "text-muted-foreground"}`} />
                </div>
              </CardHeader>
              <CardContent>
                {isLoading ? (
                  <Skeleton className="h-8 w-20" />
                ) : (
                  <p className={`text-3xl font-bold ${highlight ? "text-amber-500" : ""}`}>
                    {value?.toLocaleString() ?? "—"}
                  </p>
                )}
              </CardContent>
            </Card>
          );
          return href ? (
            <Link key={label} href={href} className="block hover:opacity-90 transition-opacity">
              {card}
            </Link>
          ) : (
            <div key={label}>{card}</div>
          );
        })}
      </div>

      {/* By source */}
      {stats?.sources && stats.sources.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Courses by Source</CardTitle>
          </CardHeader>
          <CardContent>
            {/* Header */}
            <div className="grid grid-cols-[1fr_80px_80px] text-xs font-semibold uppercase tracking-wider text-muted-foreground border-b border-border pb-1.5 mb-0.5">
              <span>Source</span>
              <span className="text-right">In DB</span>
              <span className="text-right">Total</span>
            </div>
            <div className="space-y-0">
              {stats.sources.map(({ source_key, count }) => {
                const total = SOURCE_TOTALS[source_key];
                return (
                  <div key={source_key} className="grid grid-cols-[1fr_80px_80px] items-center py-1.5 border-b border-border/40 last:border-0">
                    <span className="text-sm font-medium">
                      {sourceLabel(source_key)}
                    </span>
                    <span className="text-sm tabular-nums font-semibold text-right">
                      {count.toLocaleString()}
                    </span>
                    <span className="text-sm tabular-nums text-muted-foreground text-right">
                      {total != null ? total.toLocaleString() : "—"}
                    </span>
                  </div>
                );
              })}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
