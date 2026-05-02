export type CourseLevel = "undergraduate" | "graduate" | "professional" | "other";

export interface Subject {
  id: string;
  name: string;
  slug: string;
}

export interface University {
  id: string;
  name: string;
  slug: string;
  source_key: string;
  country?: string;
  course_count?: number;
}

export interface VideoSummary {
  id: string;
  youtube_id: string;
  title: string;
  duration_seconds?: number;
  order: number;
}

export interface CourseSummary {
  id: string;
  title: string;
  slug: string;
  level: CourseLevel;
  source_key: string;
  thumbnail_url?: string;
  instructor?: string;
  year?: number;
  has_video_lectures: boolean;
  total_videos: number;
  university_id: string;
  university_name: string;
  university_slug: string;
  subjects: Subject[];
  created_at: string;
  updated_at: string;
}

export interface Course extends CourseSummary {
  description?: string;
  source_url?: string;
  youtube_playlist_id?: string;
  total_duration_seconds: number;
  view_count: number;
  videos: VideoSummary[];
}

export interface PaginatedList<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
}

export interface CourseFilters {
  q?: string;
  university_slug?: string;
  subject_slug?: string;
  level?: CourseLevel;
  has_video_lectures?: boolean;
  page?: number;
  page_size?: number;
  sort_by?: string;
  sort_dir?: "asc" | "desc";
}
