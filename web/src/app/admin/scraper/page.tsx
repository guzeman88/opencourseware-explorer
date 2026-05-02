"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { fetchScraperJobs, triggerScraperJob } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Play, RefreshCw } from "lucide-react";
import { cn } from "@/lib/utils";

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
