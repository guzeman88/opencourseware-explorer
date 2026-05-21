"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { fetchScraperJobs, triggerScraperJob } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { Play, RefreshCw, CheckCircle, XCircle, Clock, Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";

const SOURCES = [
  "mit_ocw", "yale_ocw", "stanford", "nptel", "berkeley", "harvard", "all",
];

const statusConfig: Record<string, { icon: React.ElementType; color: string; bg: string; label: string }> = {
  pending:   { icon: Clock,         color: "text-amber-400",   bg: "bg-amber-500/10",   label: "Pending" },
  running:   { icon: Loader2,       color: "text-blue-400",    bg: "bg-blue-500/10",    label: "Running" },
  completed: { icon: CheckCircle,   color: "text-emerald-400", bg: "bg-emerald-500/10", label: "Completed" },
  failed:    { icon: XCircle,       color: "text-red-400",     bg: "bg-red-500/10",     label: "Failed" },
};

function formatTime(iso?: string) {
  if (!iso) return "—";
  return new Date(iso).toLocaleString(undefined, { month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" });
}

export default function ScraperPage() {
  const [selectedSource, setSelectedSource] = useState("mit_ocw");
  const qc = useQueryClient();

  const { data, isLoading, refetch } = useQuery({
    queryKey: ["scraper_jobs"],
    queryFn: fetchScraperJobs,
    refetchInterval: 5000,
  });

  const { mutate: trigger, isPending } = useMutation({
    mutationFn: triggerScraperJob,
    onSuccess: () => qc.invalidateQueries({ queryKey: ["scraper_jobs"] }),
  });

  const jobs = data?.items ?? [];
  const hasRunning = jobs.some((j) => j.status === "running");

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Scraper Jobs</h1>
        <p className="text-muted-foreground text-sm mt-1">
          Trigger data imports from university sources
        </p>
      </div>

      {/* Trigger panel */}
      <div className="rounded-xl border border-white/[0.08] bg-card/60 p-5 space-y-4">
        <h2 className="font-semibold text-sm">Run Scraper</h2>
        <div className="flex flex-wrap gap-2">
          {SOURCES.map((src) => (
            <button
              key={src}
              onClick={() => setSelectedSource(src)}
              className={cn(
                "px-3 py-1.5 rounded-lg text-sm font-medium transition-all duration-150",
                selectedSource === src
                  ? "bg-primary text-primary-foreground shadow-sm"
                  : "bg-secondary/60 text-muted-foreground hover:text-foreground hover:bg-secondary"
              )}
            >
              {src}
            </button>
          ))}
        </div>

        <Button
          onClick={() => trigger(selectedSource)}
          disabled={isPending || hasRunning}
          className="gap-2"
        >
          {isPending ? (
            <><Loader2 className="h-4 w-4 animate-spin" /> Starting…</>
          ) : hasRunning ? (
            <><Loader2 className="h-4 w-4 animate-spin" /> Job running…</>
          ) : (
            <><Play className="h-4 w-4" /> Run {selectedSource}</>
          )}
        </Button>
      </div>

      {/* Jobs table */}
      <div className="rounded-xl border border-white/[0.08] bg-card/60 overflow-hidden">
        <div className="flex items-center justify-between px-5 py-4 border-b border-white/[0.07]">
          <h2 className="font-semibold text-sm">Recent Jobs</h2>
          <button
            onClick={() => refetch()}
            className="p-1.5 rounded-lg text-muted-foreground hover:text-foreground hover:bg-white/[0.06] transition-colors"
            title="Refresh"
          >
            <RefreshCw className={cn("h-4 w-4", isLoading && "animate-spin")} />
          </button>
        </div>

        {isLoading ? (
          <div className="p-5 space-y-3">
            {Array.from({ length: 5 }).map((_, i) => <Skeleton key={i} className="h-10 w-full" />)}
          </div>
        ) : jobs.length === 0 ? (
          <div className="py-16 text-center text-muted-foreground text-sm">
            No scraper jobs yet. Run one above.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-white/[0.07] bg-white/[0.02]">
                  <th className="text-left px-5 py-3 font-semibold text-xs uppercase tracking-wider text-muted-foreground">Source</th>
                  <th className="text-left px-4 py-3 font-semibold text-xs uppercase tracking-wider text-muted-foreground">Status</th>
                  <th className="text-left px-4 py-3 font-semibold text-xs uppercase tracking-wider text-muted-foreground hidden sm:table-cell">Started</th>
                  <th className="text-left px-4 py-3 font-semibold text-xs uppercase tracking-wider text-muted-foreground hidden md:table-cell">Finished</th>
                  <th className="text-right px-4 py-3 font-semibold text-xs uppercase tracking-wider text-muted-foreground">Courses</th>
                  <th className="text-right px-4 py-3 font-semibold text-xs uppercase tracking-wider text-muted-foreground">Videos</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/[0.04]">
                {jobs.map((job) => {
                  const cfg = statusConfig[job.status] ?? statusConfig.pending;
                  const Icon = cfg.icon;
                  return (
                    <tr key={job.id} className="hover:bg-white/[0.03] transition-colors">
                      <td className="px-5 py-3 font-mono text-sm">{job.source}</td>
                      <td className="px-4 py-3">
                        <span className={cn("inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-semibold", cfg.bg, cfg.color)}>
                          <Icon className={cn("h-3 w-3", job.status === "running" && "animate-spin")} />
                          {cfg.label}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-muted-foreground text-xs hidden sm:table-cell whitespace-nowrap">
                        {formatTime(job.started_at)}
                      </td>
                      <td className="px-4 py-3 text-muted-foreground text-xs hidden md:table-cell whitespace-nowrap">
                        {formatTime(job.completed_at)}
                      </td>
                      <td className="px-4 py-3 text-right tabular-nums font-semibold text-foreground/80">
                        {job.courses_scraped.toLocaleString()}
                      </td>
                      <td className="px-4 py-3 text-right tabular-nums text-muted-foreground">
                        {job.videos_scraped.toLocaleString()}
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


const SOURCES = [
  "mit_ocw",
  "yale_ocw",
  "stanford",
  "nptel",
  "berkeley",
  "harvard",
  "all",
];

const statusColors: Record<string, string> = {
  pending: "bg-yellow-500/20 text-yellow-300",
  running: "bg-blue-500/20 text-blue-300",
  completed: "bg-green-500/20 text-green-300",
  failed: "bg-red-500/20 text-red-300",
};

export default function ScraperPage() {
  const [selectedSource, setSelectedSource] = useState("mit_ocw");
  const qc = useQueryClient();

  const { data, isLoading, refetch } = useQuery({
    queryKey: ["scraper_jobs"],
    queryFn: fetchScraperJobs,
    refetchInterval: 5000,
  });

  const { mutate: trigger, isPending } = useMutation({
    mutationFn: triggerScraperJob,
    onSuccess: () => qc.invalidateQueries({ queryKey: ["scraper_jobs"] }),
  });

  const jobs = data?.items ?? [];

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold">Scraper Jobs</h1>
        <p className="text-muted-foreground text-sm mt-1">
          Trigger data imports from university sources
        </p>
      </div>

      {/* Trigger panel */}
      <Card>
        <CardHeader>
          <CardTitle>Run Scraper</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex flex-wrap gap-2">
            {SOURCES.map((src) => (
              <button
                key={src}
                onClick={() => setSelectedSource(src)}
                className={cn(
                  "px-3 py-1.5 rounded-md text-sm font-medium transition-colors",
                  selectedSource === src
                    ? "bg-primary text-primary-foreground"
                    : "bg-secondary text-secondary-foreground hover:bg-secondary/70"
                )}
              >
                {src}
              </button>
            ))}
          </div>

          <Button
            onClick={() => trigger(selectedSource)}
            disabled={isPending}
            className="flex items-center gap-2"
          >
            <Play className="h-4 w-4" />
            {isPending ? "Starting…" : `Run ${selectedSource}`}
          </Button>
        </CardContent>
      </Card>

      {/* Jobs table */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle>Recent Jobs</CardTitle>
          <Button variant="ghost" size="icon" onClick={() => refetch()}>
            <RefreshCw className={cn("h-4 w-4", isLoading && "animate-spin")} />
          </Button>
        </CardHeader>
        <CardContent>
          {jobs.length === 0 ? (
            <p className="text-muted-foreground text-sm text-center py-8">
              No scraper jobs yet.
            </p>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-border">
                    <th className="text-left py-2 pr-4 font-medium text-muted-foreground">
                      Source
                    </th>
                    <th className="text-left py-2 pr-4 font-medium text-muted-foreground">
                      Status
                    </th>
                    <th className="text-left py-2 pr-4 font-medium text-muted-foreground">
                      Courses
                    </th>
                    <th className="text-left py-2 pr-4 font-medium text-muted-foreground">
                      Videos
                    </th>
                    <th className="text-left py-2 font-medium text-muted-foreground">
                      Started
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {jobs.map((job) => (
                    <tr
                      key={job.id}
                      className="border-b border-border/50 hover:bg-accent/20"
                    >
                      <td className="py-2 pr-4 font-medium">{job.source}</td>
                      <td className="py-2 pr-4">
                        <span
                          className={cn(
                            "px-2 py-0.5 rounded-full text-xs font-medium",
                            statusColors[job.status] ??
                              "bg-gray-500/20 text-gray-300"
                          )}
                        >
                          {job.status}
                        </span>
                      </td>
                      <td className="py-2 pr-4">{job.courses_scraped}</td>
                      <td className="py-2 pr-4">{job.videos_scraped}</td>
                      <td className="py-2 text-muted-foreground">
                        {job.started_at
                          ? new Date(job.started_at).toLocaleString()
                          : "—"}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
