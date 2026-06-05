import type { CourseSummary, PaginatedList } from "@/types";

const NON_CATALOG_SOURCE_KEYS = new Set(["nptel"]);

const NON_COURSE_TITLE_FRAGMENTS = [
  "#short",
  "admissions",
  "alumni",
  "anniversary",
  "campus life",
  "ceremony",
  "commencement",
  "convocation",
  "episode",
  "family weekend",
  "graduation",
  "highlights",
  "homecoming",
  "information session",
  "live clips",
  "orientation",
  "promo",
  "promotional",
  "recap",
  "reunion",
  "season ",
  "student spotlight",
  "teaser",
  "trailer",
  "year in review",
];

const NON_ENGLISH_SCRIPT_RE =
  /[\u0400-\u052f\u2de0-\u2dff\ua640-\ua69f\u0370-\u03ff\u3040-\u30ff\u3400-\u9fff\uac00-\ud7af]/;

export function isCatalogReadyCourse(course: CourseSummary): boolean {
  const title = course.title.toLowerCase();
  return (
    course.has_video_lectures === true &&
    course.total_videos > 0 &&
    !NON_CATALOG_SOURCE_KEYS.has(course.source_key) &&
    !NON_ENGLISH_SCRIPT_RE.test(course.title) &&
    !NON_COURSE_TITLE_FRAGMENTS.some((fragment) => title.includes(fragment))
  );
}

export function filterCatalogReadyPage<T extends CourseSummary>(
  page: PaginatedList<T>,
  enabled = true
): PaginatedList<T> {
  if (!enabled) return page;
  const items = page.items.filter(isCatalogReadyCourse);
  return { ...page, items };
}
