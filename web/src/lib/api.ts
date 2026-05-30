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

// In the browser, use relative URLs so requests go through the Vercel edge proxy
// (/api/v1/...) which caches responses at Vercel's CDN — much faster than hitting
// Railway directly. SSR code paths use the full URL via NEXT_PUBLIC_API_URL.
const BASE_URL =
  typeof window !== "undefined"
    ? ""
    : (process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000");

export const apiClient = axios.create({
  baseURL: `${BASE_URL}/api/v1`,
  timeout: 30000,
  headers: { "Content-Type": "application/json" },
});

// Keep homepage rows responsive when backend is unhealthy or waking up.
const PUBLIC_LIST_TIMEOUT_MS = 8000;

function nowIso(): string {
  return new Date().toISOString();
}

const FALLBACK_COURSES: CourseSummary[] = [
  {
    id: "fallback-1",
    title: "CS50: Introduction to Computer Science",
    slug: "cs50-introduction-to-computer-science",
    level: "undergraduate",
    source_key: "cs50",
    source_url: "https://www.youtube.com/c/cs50",
    thumbnail_url: "https://i.ytimg.com/vi/8mAITcNt710/maxresdefault.jpg",
    instructor: "David J. Malan",
    has_video_lectures: true,
    has_lecture_notes: false,
    has_exams: false,
    total_videos: 24,
    is_published: true,
    university_id: "u-fallback-harvard",
    university_name: "Harvard University",
    university_slug: "harvard",
    subjects: [],
    created_at: nowIso(),
    updated_at: nowIso(),
  },
  {
    id: "fallback-2",
    title: "MIT 6.006 Introduction to Algorithms",
    slug: "mit-6006-introduction-to-algorithms",
    level: "undergraduate",
    source_key: "mit_ocw",
    source_url: "https://ocw.mit.edu",
    thumbnail_url: "https://i.ytimg.com/vi/ZA-tUyM_y7s/maxresdefault.jpg",
    instructor: "Erik Demaine",
    has_video_lectures: true,
    has_lecture_notes: true,
    has_exams: true,
    total_videos: 20,
    is_published: true,
    university_id: "u-fallback-mit",
    university_name: "MIT OpenCourseWare",
    university_slug: "mit",
    subjects: [],
    created_at: nowIso(),
    updated_at: nowIso(),
  },
  {
    id: "fallback-3",
    title: "Stanford CS229 Machine Learning",
    slug: "stanford-cs229-machine-learning",
    level: "graduate",
    source_key: "stanford",
    source_url: "https://www.youtube.com/@stanfordonline",
    thumbnail_url: "https://i.ytimg.com/vi/jGwO_UgTS7I/maxresdefault.jpg",
    instructor: "Andrew Ng",
    has_video_lectures: true,
    has_lecture_notes: false,
    has_exams: false,
    total_videos: 18,
    is_published: true,
    university_id: "u-fallback-stanford",
    university_name: "Stanford University",
    university_slug: "stanford",
    subjects: [],
    created_at: nowIso(),
    updated_at: nowIso(),
  },
  {
    id: "fallback-4",
    title: "MIT 18.06 Linear Algebra",
    slug: "mit-1806-linear-algebra",
    level: "undergraduate",
    source_key: "mit_ocw",
    source_url: "https://ocw.mit.edu",
    thumbnail_url: "https://i.ytimg.com/vi/J7DzL2_Na80/maxresdefault.jpg",
    instructor: "Gilbert Strang",
    has_video_lectures: true,
    has_lecture_notes: true,
    has_exams: false,
    total_videos: 35,
    is_published: true,
    university_id: "u-fallback-mit",
    university_name: "MIT OpenCourseWare",
    university_slug: "mit",
    subjects: [],
    created_at: nowIso(),
    updated_at: nowIso(),
  },
  {
    id: "fallback-5",
    title: "Yale PHYS 200 Fundamentals of Physics",
    slug: "yale-phys-200-fundamentals-of-physics",
    level: "undergraduate",
    source_key: "yale",
    source_url: "https://oyc.yale.edu",
    thumbnail_url: "https://i.ytimg.com/vi/pyX8kQ-JzHI/maxresdefault.jpg",
    instructor: "R. Shankar",
    has_video_lectures: true,
    has_lecture_notes: false,
    has_exams: false,
    total_videos: 24,
    is_published: true,
    university_id: "u-fallback-yale",
    university_name: "Yale Open Courses",
    university_slug: "yale",
    subjects: [],
    created_at: nowIso(),
    updated_at: nowIso(),
  },
  {
    id: "fallback-6",
    title: "MIT 8.04 Quantum Physics I",
    slug: "mit-804-quantum-physics-i",
    level: "undergraduate",
    source_key: "mit_ocw",
    source_url: "https://ocw.mit.edu",
    thumbnail_url: "https://i.ytimg.com/vi/lZ3bPUKo5zc/maxresdefault.jpg",
    instructor: "Allan Adams",
    has_video_lectures: true,
    has_lecture_notes: true,
    has_exams: false,
    total_videos: 16,
    is_published: true,
    university_id: "u-fallback-mit",
    university_name: "MIT OpenCourseWare",
    university_slug: "mit",
    subjects: [],
    created_at: nowIso(),
    updated_at: nowIso(),
  },
  {
    id: "fallback-7",
    title: "Berkeley CS 61A Structure and Interpretation",
    slug: "berkeley-cs61a-structure-and-interpretation",
    level: "undergraduate",
    source_key: "berkeley",
    source_url: "https://www.youtube.com/@ucberkeley",
    thumbnail_url: "https://i.ytimg.com/vi/4lF7ylz8Ypk/maxresdefault.jpg",
    instructor: "Brian Harvey",
    has_video_lectures: true,
    has_lecture_notes: false,
    has_exams: false,
    total_videos: 40,
    is_published: true,
    university_id: "u-fallback-berkeley",
    university_name: "UC Berkeley",
    university_slug: "berkeley",
    subjects: [],
    created_at: nowIso(),
    updated_at: nowIso(),
  },
  {
    id: "fallback-8",
    title: "MIT 6.S191 Deep Learning",
    slug: "mit-6s191-deep-learning",
    level: "graduate",
    source_key: "mit_ocw",
    source_url: "https://introtodeeplearning.com",
    thumbnail_url: "https://i.ytimg.com/vi/alfdI7S6wCY/maxresdefault.jpg",
    instructor: "Alexander Amini",
    has_video_lectures: true,
    has_lecture_notes: false,
    has_exams: false,
    total_videos: 12,
    is_published: true,
    university_id: "u-fallback-mit",
    university_name: "MIT OpenCourseWare",
    university_slug: "mit",
    subjects: [],
    created_at: nowIso(),
    updated_at: nowIso(),
  },
];

const FALLBACK_UNIVERSITIES: University[] = [
  {
    id: "u-fallback-mit",
    name: "MIT OpenCourseWare",
    slug: "mit",
    source_key: "mit_ocw",
    is_institution: true,
    created_at: nowIso(),
    updated_at: nowIso(),
  },
  {
    id: "u-fallback-stanford",
    name: "Stanford University",
    slug: "stanford",
    source_key: "stanford",
    is_institution: true,
    created_at: nowIso(),
    updated_at: nowIso(),
  },
  {
    id: "u-fallback-harvard",
    name: "Harvard University",
    slug: "harvard",
    source_key: "harvard",
    is_institution: true,
    created_at: nowIso(),
    updated_at: nowIso(),
  },
  {
    id: "u-fallback-berkeley",
    name: "UC Berkeley",
    slug: "berkeley",
    source_key: "berkeley",
    is_institution: true,
    created_at: nowIso(),
    updated_at: nowIso(),
  },
  {
    id: "u-fallback-yale",
    name: "Yale Open Courses",
    slug: "yale",
    source_key: "yale",
    is_institution: true,
    created_at: nowIso(),
    updated_at: nowIso(),
  },
];

function fallbackCourses(pageSize: number): PaginatedList<CourseSummary> {
  const items = Array.from({ length: pageSize }, (_, i) => FALLBACK_COURSES[i % FALLBACK_COURSES.length]);
  return {
    items,
    total: items.length,
    page: 1,
    page_size: pageSize,
    pages: 1,
  };
}

function fallbackUniversities(pageSize: number): PaginatedList<University> {
  const items = Array.from({ length: pageSize }, (_, i) => FALLBACK_UNIVERSITIES[i % FALLBACK_UNIVERSITIES.length]);
  return {
    items,
    total: items.length,
    page: 1,
    page_size: pageSize,
    pages: 1,
  };
}

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
    { params: filters, timeout: PUBLIC_LIST_TIMEOUT_MS }
  );
  return data;
}

export async function fetchFeaturedCourses(
  limit = 12
): Promise<PaginatedList<CourseSummary>> {
  const { data } = await apiClient.get<PaginatedList<CourseSummary>>(
    "/courses/featured",
    { params: { page_size: limit }, timeout: PUBLIC_LIST_TIMEOUT_MS }
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
  q?: string,
  is_institution?: boolean,
): Promise<PaginatedList<University>> {
  try {
    const { data } = await apiClient.get<PaginatedList<University>>(
      "/universities",
      {
        params: { page, page_size, q, is_institution },
        timeout: PUBLIC_LIST_TIMEOUT_MS,
      }
    );
    return data;
  } catch {
    return fallbackUniversities(page_size);
  }
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
    { params: filters, timeout: PUBLIC_LIST_TIMEOUT_MS }
  );
  return data;
}

// ─── Subjects ─────────────────────────────────────────────────────────────────

export async function fetchSubjects(
  topLevelOnly = false
): Promise<PaginatedList<Subject>> {
  const { data } = await apiClient.get<PaginatedList<Subject>>("/subjects", {
    params: { top_level_only: topLevelOnly, page_size: 500 },
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

export async function adminLogout(): Promise<void> {
  // Ask the backend to clear the httpOnly session cookie.
  await apiClient.post("/admin/auth/logout").catch(() => {/* best-effort */});
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

export async function setPendingReview(
  courseId: string,
  pending: boolean
): Promise<void> {
  await apiClient.patch(`/admin/courses/${courseId}/publish`, null, {
    params: { published: !pending },
  });
}

export async function setCoursePublished(
  courseId: string,
  published: boolean
): Promise<void> {
  await apiClient.patch(`/admin/courses/${courseId}/publish`, null, {
    params: { published },
  });
}

export async function fetchAdminCourse(courseId: string): Promise<Course> {
  const { data } = await apiClient.get<Course>(`/courses/${courseId}`);
  return data;
}

export interface CourseUpdatePayload {
  title?: string;
  description?: string;
  level?: string;
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

export async function updateCourse(
  courseId: string,
  data: CourseUpdatePayload
): Promise<Course> {
  const { data: result } = await apiClient.put<Course>(
    `/admin/courses/${courseId}`,
    data
  );
  return result;
}
