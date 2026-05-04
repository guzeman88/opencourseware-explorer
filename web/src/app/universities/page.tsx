"use client";

import Link from "next/link";
import { useState } from "react";
import { GraduationCap } from "lucide-react";
import { useQuery } from "@tanstack/react-query";
import { fetchUniversities } from "@/lib/api";
import { UniversityCardSkeleton } from "@/components/ui/skeleton";

function UniLogo({ src, name }: { src?: string; name: string }) {
  const [failed, setFailed] = useState(false);
  if (!src || failed) {
    return <GraduationCap className="h-10 w-10 text-muted-foreground/40" />;
  }
  return (
    // eslint-disable-next-line @next/next/no-img-element
    <img
      src={src}
      alt={name}
      className="w-full h-full object-contain"
      onError={() => setFailed(true)}
    />
  );
}

export default function UniversitiesPage() {
  const { data, isLoading } = useQuery({
    queryKey: ["universities", "institutions"],
    queryFn: () => fetchUniversities(1, 200, undefined, true),
  });
  const universities = (data?.items ?? []).filter((u) => (u.course_count ?? 0) > 0);

  return (
    <div className="max-w-screen-xl mx-auto px-4 md:px-8 py-8">
      <h1 className="text-2xl font-bold mb-2">Universities</h1>
      <p className="text-muted-foreground mb-8">
        Browse free courses from top universities and research institutions worldwide.
      </p>

      {isLoading ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4">
          {Array.from({ length: 12 }).map((_, i) => (
            <UniversityCardSkeleton key={i} />
          ))}
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3">
          {universities.map((uni) => (
            <Link
              key={uni.id}
              href={`/universities/${uni.slug}`}
              className="group flex items-center gap-4 p-4 rounded-xl bg-card border border-border/50
                         hover:border-primary/30 transition-all"
            >
              <div className="w-12 h-12 rounded-lg bg-white border border-border/40 flex items-center justify-center shrink-0 overflow-hidden p-1">
                <UniLogo src={uni.logo_url} name={uni.name} />
              </div>
              <div className="min-w-0">
                <p className="font-semibold text-sm text-foreground group-hover:text-primary transition-colors truncate">
                  {uni.name}
                </p>
                <p className="text-xs text-muted-foreground mt-0.5">
                  {uni.course_count != null ? `${uni.course_count} courses` : ""}
                  {uni.course_count != null && uni.country ? " · " : ""}
                  {uni.country ?? ""}
                </p>
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
