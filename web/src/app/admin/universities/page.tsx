"use client";

import { useUniversities } from "@/hooks/use-universities";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { sourceLabel } from "@/lib/utils";
import Link from "next/link";
import { ExternalLink } from "lucide-react";

export default function AdminUniversitiesPage() {
  const { data, isLoading } = useUniversities(1, 50);
  const universities = data?.items ?? [];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Universities</h1>
        <p className="text-muted-foreground text-sm mt-1">
          {isLoading ? "Loading…" : `${universities.length} universities`}
        </p>
      </div>

      <Card>
        <CardContent className="p-0">
          {isLoading ? (
            <div className="p-6 space-y-3">
              {Array.from({ length: 5 }).map((_, i) => (
                <Skeleton key={i} className="h-10 w-full" />
              ))}
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-border">
                    <th className="text-left px-4 py-3 font-medium text-muted-foreground">
                      Name
                    </th>
                    <th className="text-left px-4 py-3 font-medium text-muted-foreground">
                      Source Key
                    </th>
                    <th className="text-left px-4 py-3 font-medium text-muted-foreground">
                      Country
                    </th>
                    <th className="text-left px-4 py-3 font-medium text-muted-foreground">
                      Courses
                    </th>
                    <th className="text-left px-4 py-3 font-medium text-muted-foreground">
                      Website
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {universities.map((uni) => (
                    <tr
                      key={uni.id}
                      className="border-b border-border/50 hover:bg-accent/20"
                    >
                      <td className="px-4 py-3 font-medium">
                        <Link
                          href={`/universities/${uni.slug}`}
                          className="hover:text-primary hover:underline"
                        >
                          {uni.name}
                        </Link>
                      </td>
                      <td className="px-4 py-3 text-muted-foreground">
                        {sourceLabel(uni.source_key)}
                      </td>
                      <td className="px-4 py-3 text-muted-foreground">
                        {uni.country ?? "—"}
                      </td>
                      <td className="px-4 py-3">
                        {uni.course_count?.toLocaleString() ?? "—"}
                      </td>
                      <td className="px-4 py-3">
                        {uni.website ? (
                          <a
                            href={uni.website}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="flex items-center gap-1 text-primary hover:underline"
                          >
                            <ExternalLink className="h-3.5 w-3.5" />
                            Visit
                          </a>
                        ) : (
                          "—"
                        )}
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
