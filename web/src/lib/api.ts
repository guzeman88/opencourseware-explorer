import axios from "axios";
import { filterCatalogReadyPage, isCatalogReadyCourse } from "@/lib/catalog-quality";
import { isStrictSubjectCourse, strictSubjectPhrases } from "@/lib/subject-matching";
import type {
  Course,
  CourseSummary,
  CourseFilters,
  CourseLevel,
  PaginatedList,
  Roadmap,
  RoadmapSummary,
  Subject,
  University,
  Stats,
  ScraperJob,
  WatchHistoryEntry,
} from "@/types";

const BASE_URL =
  process.env.NEXT_PUBLIC_API_URL ?? "";

export const apiClient = axios.create({
  baseURL: `${BASE_URL.replace(/\/$/, "")}/api/v1`,
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

// Clear stale tokens on 401 so the UI reflects the signed-out state
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401 && typeof window !== "undefined") {
      localStorage.removeItem("ocw_user_token");
      localStorage.removeItem("ocw_token");
    }
    return Promise.reject(error);
  }
);

// ─── Courses ─────────────────────────────────────────────────────────────────

export async function fetchCourses(
  filters: CourseFilters = {}
): Promise<PaginatedList<CourseSummary>> {
  const { data } = await apiClient.get<PaginatedList<CourseSummary>>(
    "/courses",
    { params: filters }
  );
  return filterCatalogReadyPage(data, filters.catalog_ready !== false);
}

export async function fetchFeaturedCourses(
  limit = 12
): Promise<PaginatedList<CourseSummary>> {
  const { data } = await apiClient.get<PaginatedList<CourseSummary>>(
    "/courses/featured",
    { params: { page_size: limit } }
  );
  return filterCatalogReadyPage(data);
}

export async function fetchCourse(slugOrId: string): Promise<Course> {
  const { data } = await apiClient.get<Course>(`/courses/${slugOrId}`);
  return data;
}

// ─── Universities ─────────────────────────────────────────────────────────────

export async function fetchUniversities(
  page = 1,
  page_size = 50,
  q?: string,
  is_institution?: boolean,
): Promise<PaginatedList<University>> {
  const { data } = await apiClient.get<PaginatedList<University>>(
    "/universities",
    { params: { page, page_size, q, is_institution } }
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
  return filterCatalogReadyPage(data, filters.catalog_ready !== false);
}

// ─── Subjects ─────────────────────────────────────────────────────────────────

export async function fetchSubjects(
  topLevelOnly = false,
  strictCounts = false
): Promise<PaginatedList<Subject>> {
  const { data } = await apiClient.get<PaginatedList<Subject>>("/subjects", {
    params: { top_level_only: topLevelOnly, strict_counts: strictCounts, page_size: 500 },
  });
  return data;
}

export async function fetchStrictSubjectCounts(
  slugs: string[]
): Promise<Record<string, number>> {
  const counts: Record<string, number> = {};
  const uniqueSlugs = Array.from(new Set(slugs));
  const chunks: string[][] = [];
  for (let index = 0; index < uniqueSlugs.length; index += 6) {
    chunks.push(uniqueSlugs.slice(index, index + 6));
  }

  for (let index = 0; index < chunks.length; index += 6) {
    const batch = chunks.slice(index, index + 6);
    const results = await Promise.all(
      batch.map((chunk) =>
        axios.post<{ counts: Record<string, number> }>(
          "/api/strict-subject-counts",
          { slugs: chunk },
          { timeout: 30000 }
        )
      )
    );
    for (const result of results) {
      Object.assign(counts, result.data.counts);
    }
  }

  return counts;
}

export async function fetchStrictSubjectCourses(
  subjectSlug: string,
  pageSize = 100,
  exhaustive = true,
  extraFilters: CourseFilters = {}
): Promise<PaginatedList<CourseSummary>> {
  const fetchAllPages = async (filters: CourseFilters) => {
    const first = await fetchCourses({
      ...extraFilters,
      ...filters,
      page: 1,
      page_size: pageSize,
    });
    const pages = Math.max(1, first.pages ?? 1);
    if (!exhaustive || pages === 1) return first;

    const rest = await Promise.all(
      Array.from({ length: pages - 1 }, (_, index) =>
        fetchCourses({
          ...extraFilters,
          ...filters,
          page: index + 2,
          page_size: pageSize,
        })
      )
    );

    return {
      ...first,
      items: [...first.items, ...rest.flatMap((page) => page.items)],
    };
  };

  const byCurrentSubject = await fetchAllPages({
    subject_slug: subjectSlug,
    has_video_lectures: true,
    sort_by: "relevance",
    sort_dir: "desc",
  });
  const phraseResults = await Promise.all(
    strictSubjectPhrases(subjectSlug).map((phrase) =>
      fetchAllPages({
        q: phrase,
        has_video_lectures: true,
        sort_by: "view_count",
        sort_dir: "desc",
      })
    )
  );

  const merged = new Map<string, CourseSummary>();
  for (const course of byCurrentSubject.items) merged.set(course.id, course);
  for (const result of phraseResults) {
    for (const course of result.items) merged.set(course.id, course);
  }

  const items = Array.from(merged.values()).filter((course) =>
    isCatalogReadyCourse(course) &&
    isStrictSubjectCourse(course, subjectSlug)
  );

  return {
    ...byCurrentSubject,
    items,
    total: items.length,
    page: 1,
    page_size: pageSize,
    pages: items.length > 0 ? Math.ceil(items.length / pageSize) : 0,
  };
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
  return filterCatalogReadyPage(data, filters.catalog_ready !== false);
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

// ─── Watch History ────────────────────────────────────────────────────────────

export async function recordWatch(
  courseId: string,
  videoIndex: number,
  token: string
): Promise<void> {
  await apiClient.post(
    "/users/me/history",
    { course_id: courseId, video_index: videoIndex },
    { headers: { Authorization: `Bearer ${token}` } }
  );
}

export async function fetchWatchHistory(
  token: string
): Promise<WatchHistoryEntry[]> {
  const { data } = await apiClient.get<WatchHistoryEntry[]>("/users/me/history", {
    headers: { Authorization: `Bearer ${token}` },
  });
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

export async function fetchPendingReviewCourses(
  page = 1,
  page_size = 50,
  source_key?: string,
  q?: string
): Promise<PaginatedList<CourseSummary>> {
  const { data } = await apiClient.get<PaginatedList<CourseSummary>>(
    "/admin/courses/pending-review",
    { params: { page, page_size, source_key, q } }
  );
  return data;
}

export async function setCoursePublished(
  courseId: string,
  published: boolean
): Promise<void> {
  await apiClient.patch(`/admin/courses/${courseId}/publish`, null, {
    params: { published },
  });
}

export interface CourseUpdatePayload {
  title?: string;
  description?: string;
  level?: CourseLevel;
  instructor?: string;
  year?: number | null;
  semester?: string | null;
  thumbnail_url?: string | null;
  has_video_lectures?: boolean;
  has_lecture_notes?: boolean;
  has_exams?: boolean;
  lecture_notes_url?: string | null;
  exams_url?: string | null;
  youtube_playlist_id?: string | null;
  is_published?: boolean;
}

export async function fetchAdminCourse(courseId: string): Promise<Course> {
  const { data } = await apiClient.get<Course>(`/courses/${courseId}`);
  return data;
}

export async function updateCourse(
  courseId: string,
  payload: CourseUpdatePayload
): Promise<Course> {
  const { data } = await apiClient.put<Course>(
    `/admin/courses/${courseId}`,
    payload
  );
  return data;
}
