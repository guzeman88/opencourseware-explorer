import axios from "axios";
import type {
  Course,
  CourseSummary,
  CourseFilters,
  PaginatedList,
  Subject,
  University,
} from "@/types";

// Update this to your machine's LAN IP or deployed URL when testing on device
const BASE_URL =
  process.env.EXPO_PUBLIC_API_URL ?? "http://localhost:8000";

export const apiClient = axios.create({
  baseURL: `${BASE_URL}/api/v1`,
  timeout: 15000,
});

export async function fetchCourses(
  filters: CourseFilters = {}
): Promise<PaginatedList<CourseSummary>> {
  const { data } = await apiClient.get("/courses", { params: filters });
  return data;
}

export async function fetchFeaturedCourses(
  limit = 20
): Promise<PaginatedList<CourseSummary>> {
  const { data } = await apiClient.get("/courses/featured", {
    params: { page_size: limit },
  });
  return data;
}

export async function fetchCourse(slugOrId: string): Promise<Course> {
  const { data } = await apiClient.get(`/courses/${slugOrId}`);
  return data;
}

export async function fetchUniversities(
  page = 1,
  page_size = 50
): Promise<PaginatedList<University>> {
  const { data } = await apiClient.get("/universities", {
    params: { page, page_size },
  });
  return data;
}

export async function fetchUniversityCourses(
  slug: string,
  filters: CourseFilters = {}
): Promise<PaginatedList<CourseSummary>> {
  const { data } = await apiClient.get(`/universities/${slug}/courses`, {
    params: filters,
  });
  return data;
}

export async function searchCourses(
  q: string,
  filters: CourseFilters = {}
): Promise<PaginatedList<CourseSummary>> {
  const { data } = await apiClient.get("/search", {
    params: { q, ...filters },
  });
  return data;
}
