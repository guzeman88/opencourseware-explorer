import type { CourseSummary, PaginatedList } from "@/types";

const NON_CATALOG_SOURCE_KEYS = new Set(["nptel"]);

const NON_COURSE_TITLE_FRAGMENTS = [
  "about ",
  "#short",
  "admissions",
  "alumni",
  "anniversary",
  "annual review",
  "apply to",
  "around campus",
  "best of",
  "campus life",
  "centenary lectures",
  "challenge",
  "ceremony",
  "colloquium",
  "commencement",
  "competition",
  "conference",
  "congregation",
  "convocation",
  "conversation with",
  "covid",
  "departmental day",
  "election",
  "episode",
  "event recordings",
  "events",
  "family weekend",
  "forum",
  "graduation",
  "groupe calcul",
  "help sessions",
  "heures avec",
  "highlights",
  "homework, exams",
  "homecoming",
  "information session",
  "interview",
  "lecture series",
  "live clips",
  "meeting",
  "minutes to change",
  "orientation",
  "playlist",
  "programme",
  "programs",
  "promo",
  "promotional",
  "recap",
  "research at",
  "reunion",
  "season ",
  "seminar",
  "special talks",
  "stories",
  "student life",
  "student spotlight",
  "student lectures",
  "symposium",
  "teaser",
  "trailer",
  "video series",
  "workshop",
  "year in review",
  "\" series",
  "colóquio",
  "comunauté",
  "conferência",
  "conférence",
  "encuentro",
];

const NON_ENGLISH_SCRIPT_RE =
  /[\u0400-\u052f\u2de0-\u2dff\ua640-\ua69f\u0370-\u03ff\u3040-\u30ff\u3400-\u9fff\uac00-\ud7af]/;

export function isCatalogReadyCourse(course: CourseSummary): boolean {
  const title = course.title.toLowerCase();
  const trimmedTitle = course.title.trim();
  return (
    course.has_video_lectures === true &&
    course.total_videos > 0 &&
    !NON_CATALOG_SOURCE_KEYS.has(course.source_key) &&
    !trimmedTitle.startsWith("#") &&
    !trimmedTitle.startsWith("@") &&
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
