"use client";

import { useQuery } from "@tanstack/react-query";
import { fetchStats } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  GraduationCap,
  BookOpen,
  Play,
  Tag,
  Video,
  Clock,
} from "lucide-react";
import { Skeleton } from "@/components/ui/skeleton";
import { sourceLabel } from "@/lib/utils";
import Link from "next/link";

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
