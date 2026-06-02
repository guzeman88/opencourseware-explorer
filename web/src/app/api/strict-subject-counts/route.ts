import { NextResponse } from "next/server";
import { isStrictSubjectTitle } from "@/lib/subject-matching";
import type { CourseSummary, PaginatedList, Subject } from "@/types";

export const dynamic = "force-dynamic";

const UPSTREAM = process.env.API_UPSTREAM ?? "https://opencourseware-api.onrender.com";
const PAGE_SIZE = 100;
const CONCURRENCY = 10;

async function fetchJson<T>(path: string, params: Record<string, string | number> = {}) {
  const url = new URL(`${UPSTREAM}${path}`);
  for (const [key, value] of Object.entries(params)) {
    url.searchParams.set(key, String(value));
  }
  const response = await fetch(url, { signal: AbortSignal.timeout(25000) });
  if (!response.ok) {
    throw new Error(`Upstream ${path} failed with ${response.status}`);
  }
  return (await response.json()) as T;
}

async function fetchPages<T>(path: string) {
  const first = await fetchJson<PaginatedList<T>>(path, { page: 1, page_size: PAGE_SIZE });
  const pages = Array.from({ length: Math.max(0, first.pages - 1) }, (_, index) => index + 2);
  const items = [...first.items];

  for (let index = 0; index < pages.length; index += CONCURRENCY) {
    const batch = pages.slice(index, index + CONCURRENCY);
    const results = await Promise.all(
      batch.map((page) => fetchJson<PaginatedList<T>>(path, { page, page_size: PAGE_SIZE }))
    );
    for (const result of results) items.push(...result.items);
  }

  return items;
}

export async function GET() {
  try {
    const [subjects, courses] = await Promise.all([
      fetchPages<Subject>("/api/v1/subjects"),
      fetchPages<CourseSummary>("/api/v1/courses"),
    ]);
    const counts: Record<string, number> = {};
    for (const subject of subjects) counts[subject.slug] = 0;

    for (const course of courses) {
      for (const subject of subjects) {
        if (isStrictSubjectTitle(course.title, subject.slug)) {
          counts[subject.slug] += 1;
        }
      }
    }

    return NextResponse.json(
      { counts, generated_at: new Date().toISOString() },
      {
        headers: {
          "Cache-Control": "public, max-age=300, stale-while-revalidate=3600",
          "Netlify-CDN-Cache-Control": "public, max-age=300, stale-while-revalidate=3600",
        },
      }
    );
  } catch (error) {
    return NextResponse.json(
      { counts: {}, error: error instanceof Error ? error.message : "unknown_error" },
      { status: 502, headers: { "Cache-Control": "no-store" } }
    );
  }
}
