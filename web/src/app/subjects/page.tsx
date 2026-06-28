import { SubjectsContent } from "./subjects-content";
import subjectCounts from "@/data/subject-counts.json";

// Counts are generated directly from the database using the exact same
// SQL query as the subject detail page (course_subjects + catalog_ready_condition).
// The number on the listing page always matches the detail page.
//
// To refresh counts: run `python scraper/_sync_sql_counts.py` and redeploy.

function buildInitialData() {
  const items = Object.entries(subjectCounts).map(([slug, course_count]) => ({
    id: slug, // slug is unique, used as React key
    slug,
    name: slug
      .split("-")
      .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
      .join(" "),
    course_count,
  }));

  return {
    items,
    total: items.length,
    page: 1,
    page_size: items.length,
    pages: 1,
  };
}

export default function SubjectsPage() {
  const subjects = buildInitialData();
  return <SubjectsContent initialData={subjects} />;
}
