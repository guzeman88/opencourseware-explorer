"use client";

import { useQuery } from "@tanstack/react-query";
import { fetchUniversities, fetchUniversity } from "@/lib/api";

export function useUniversities(page = 1, page_size = 50, q?: string) {
  return useQuery({
    queryKey: ["universities", page, page_size, q],
    queryFn: () => fetchUniversities(page, page_size, q),
  });
}

export function useUniversity(slug: string) {
  return useQuery({
    queryKey: ["universities", slug],
    queryFn: () => fetchUniversity(slug),
    enabled: !!slug,
  });
}
