export type CourseLevel = "undergraduate" | "graduate" | "professional" | "other";

export interface Subject {
  id: string;
  name: string;
  slug: string;
  description?: string;
  parent_id?: string;
  children?: Subject[];
  course_count?: number;
  created_at: string;
  updated_at: string;
}

export interface University {
  id: string;
  name: string;
  slug: string;
  description?: string;
  website?: string;
  logo_url?: string;
  country?: string;
  youtube_channel_id?: string;
  source_key: string;
  is_institution: boolean;
  course_count?: number;
  created_at: string;
  updated_at: string;
}

export interface VideoSummary {
  id: string;
  youtube_id: string;
  title: string;
  thumbnail_url?: string;
  duration_seconds?: number;
  order: number;
  created_at: string;
  updated_at: string;
}

export interface CourseSummary {
  id: string;
  course_number?: string;
  title: string;
  slug: string;
  level: CourseLevel;
  source_key: string;
  source_url?: string;
  thumbnail_url?: string;
  instructor?: string;
  year?: number;
  has_video_lectures: boolean;
  has_lecture_notes: boolean;
  has_exams: boolean;
  total_videos: number;
  is_published: boolean;
  university_id: string;
  university_name: string;
  university_slug: string;
  subjects: Subject[];
  view_count?: number;
  created_at: string;
  updated_at: string;
}

export interface Course extends CourseSummary {
  description?: string;
  source_url?: string;
  semester?: string;
  has_lecture_notes: boolean;
  has_exams: boolean;
  lecture_notes_url?: string;
  exams_url?: string;
  youtube_playlist_id?: string;
  total_duration_seconds: number;
  view_count: number;
  department_id?: string;
  department_name?: string;
  videos: VideoSummary[];
}

export interface PaginatedList<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
}

export interface WatchHistoryEntry {
  course: CourseSummary;
  video_index: number;
  watched_at: string;
}

export interface ScraperJob {
  id: string;
  source: string;
  status: "pending" | "running" | "completed" | "failed";
  started_at?: string;
  completed_at?: string;
  courses_scraped: number;
  videos_scraped: number;
  error_message?: string;
  created_at: string;
  updated_at: string;
}

export interface Stats {
  total_universities: number;
  total_courses: number;
  total_videos: number;
  total_subjects: number;
  courses_with_video: number;
  pending_review: number;
  sources: { source_key: string; count: number }[];
}

export interface RoadmapEntry {
  id: string;
  position: number;
  course_number?: string;
  course_title: string;
  category?: string;
  semester?: string;
  year_in_program?: number;
  is_required: boolean;
  units?: number;
  notes?: string;
  course_id?: string;
  course_slug?: string;
  subject_slug?: string;
}

export interface RoadmapSummary {
  id: string;
  slug: string;
  title: string;
  degree_type?: string;
  major?: string;
  department?: string;
  description?: string;
  estimated_years?: number;
  website_url?: string;
  university_id: string;
  university_name?: string;
  university_slug?: string;
  entry_count: number;
}

export interface Roadmap extends RoadmapSummary {
  entries: RoadmapEntry[];
}

export interface CourseFilters {
  q?: string;
  university_slug?: string;
  subject_slug?: string;
  level?: CourseLevel;
  source_key?: string;
  has_video_lectures?: boolean;
  page?: number;
  page_size?: number;
  sort_by?: "title" | "view_count" | "created_at" | "total_videos";
  sort_dir?: "asc" | "desc";
}
