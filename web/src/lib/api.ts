import axios from "axios";
import type {
  Course,
  CourseSummary,
  CourseFilters,
  PaginatedList,
  Roadmap,
  RoadmapSummary,
  Subject,
  University,
  Stats,
  ScraperJob,
} from "@/types";

const BASE_URL =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export const apiClient = axios.create({
  baseURL: `${BASE_URL}/api/v1`,
  timeout: 15000,
  headers: { "Content-Type": "application/json" },
});

// Attach auth token when present (admin)
apiClient.interceptors.request.use((config) => {
  if (typeof window !== "undefined") {
    const token = localStorage.getItem("ocw_token");
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
  }
  return config;
});

// ─── Courses ─────────────────────────────────────────────────────────────────

export async function fetchCourses(
  filters: CourseFilters = {}
): Promise<PaginatedList<CourseSummary>> {
  const { data } = await apiClient.get<PaginatedList<CourseSummary>>(
    "/courses",
    { params: filters }
  );
  return data;
}

export async function fetchFeaturedCourses(
  limit = 12
): Promise<PaginatedList<CourseSummary>> {
  const { data } = await apiClient.get<PaginatedList<CourseSummary>>(
    "/courses/featured",
    { params: { page_size: limit } }
  );
  return data;
}

export async function fetchCourse(slugOrId: string): Promise<Course> {
  const { data } = await apiClient.get<Course>(`/courses/${slugOrId}`);
  return data;
}

// ─── Universities ─────────────────────────────────────────────────────────────

export async function fetchUniversities(
  page = 1,
  page_size = 50,
  q?: string
): Promise<PaginatedList<University>> {
  const { data } = await apiClient.get<PaginatedList<University>>(
    "/universities",
    { params: { page, page_size, q } }
  );
  return data;
}

export async function fetchUniversity(slug: string): Promise<University> {
  const { data } = await apiClient.get<University>(`/universities/${slug}`);
  return data;
}

export async function fetchUniversityCourses(
  slug: string,
  filters: CourseFilters = {}
): Promise<PaginatedList<CourseSummary>> {
  const { data } = await apiClient.get<PaginatedList<CourseSummary>>(
    `/universities/${slug}/courses`,
    { params: filters }
  );
  return data;
}

// ─── Subjects ─────────────────────────────────────────────────────────────────

export async function fetchSubjects(
  topLevelOnly = false
): Promise<PaginatedList<Subject>> {
  const { data } = await apiClient.get<PaginatedList<Subject>>("/subjects", {
    params: { top_level_only: topLevelOnly, page_size: 200 },
  });
  return data;
}

// ─── Search ───────────────────────────────────────────────────────────────────

export async function searchCourses(
  q: string,
  filters: CourseFilters = {}
): Promise<PaginatedList<CourseSummary>> {
  const { data } = await apiClient.get<PaginatedList<CourseSummary>>(
    "/search",
    { params: { q, ...filters } }
  );
  return data;
}

// ─── Roadmaps ─────────────────────────────────────────────────────────────────

export async function fetchRoadmaps(params: {
  university?: string;
  major?: string;
  page?: number;
  page_size?: number;
} = {}): Promise<{ items: RoadmapSummary[]; total: number; page: number; page_size: number }> {
  const { data } = await apiClient.get("/roadmaps", { params });
  return data;
}

export async function fetchRoadmap(slug: string): Promise<Roadmap> {
  const { data } = await apiClient.get<Roadmap>(`/roadmaps/${slug}`);
  return data;
}

// ─── Admin ────────────────────────────────────────────────────────────────────

export async function adminLogin(
  email: string,
  password: string
): Promise<string> {
  const { data } = await apiClient.post<{ access_token: string }>(
    "/admin/auth/login",
    { email, password }
  );
  return data.access_token;
}

export async function fetchStats(): Promise<Stats> {
  const { data } = await apiClient.get<Stats>("/admin/stats");
  return data;
}

export async function fetchScraperJobs(): Promise<
  PaginatedList<ScraperJob>
> {
  const { data } = await apiClient.get<PaginatedList<ScraperJob>>(
    "/admin/scraper/jobs"
  );
  return data;
}

export async function triggerScraperJob(source: string): Promise<ScraperJob> {
  const { data } = await apiClient.post<ScraperJob>(
    "/admin/scraper/jobs",
    { source }
  );
  return data;
}
