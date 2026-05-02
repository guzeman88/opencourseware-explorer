"use client";

import { useQuery, useInfiniteQuery } from "@tanstack/react-query";
import {
  fetchCourses,
  fetchCourse,
  fetchFeaturedCourses,
  fetchUniversityCourses,
  searchCourses,
} from "@/lib/api";
import type { CourseFilters } from "@/types";

export const COURSES_KEY = "courses";
export const FEATURED_KEY = "courses_featured";

export function useCourses(filters: CourseFilters = {}) {
  return useQuery({
    queryKey: [COURSES_KEY, filters],
    queryFn: () => fetchCourses(filters),
  });
}

export function useFeaturedCourses(limit = 12) {
  return useQuery({
    queryKey: [FEATURED_KEY, limit],
    queryFn: () => fetchFeaturedCourses(limit),
  });
}

export function useCourse(slugOrId: string) {
  return useQuery({
    queryKey: [COURSES_KEY, slugOrId],
    queryFn: () => fetchCourse(slugOrId),
    enabled: !!slugOrId,
  });
}

export function useUniversityCourses(
  universitySlug: string,
  filters: CourseFilters = {}
) {
  return useQuery({
    queryKey: ["university_courses", universitySlug, filters],
    queryFn: () => fetchUniversityCourses(universitySlug, filters),
    enabled: !!universitySlug,
  });
}

export function useSearchCourses(q: string, filters: CourseFilters = {}) {
  return useQuery({
    queryKey: ["search", q, filters],
    queryFn: () => searchCourses(q, filters),
    enabled: q.trim().length >= 2,
  });
}

export function useInfiniteCourses(filters: CourseFilters = {}) {
  return useInfiniteQuery({
    queryKey: [COURSES_KEY, "infinite", filters],
    queryFn: ({ pageParam = 1 }) =>
      fetchCourses({ ...filters, page: pageParam }),
    initialPageParam: 1,
    getNextPageParam: (last) =>
      last.page < last.pages ? last.page + 1 : undefined,
  });
}
