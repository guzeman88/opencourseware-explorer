import { NextRequest, NextResponse } from "next/server";
import {
  isStrictSubjectTitle,
  strictSubjectPhrases,
} from "@/lib/subject-matching";
import { isCatalogReadyCourse } from "@/lib/catalog-quality";
import type { CourseSummary, PaginatedList } from "@/types";

export const dynamic = "force-dynamic";

const UPSTREAM = process.env.API_UPSTREAM ?? "https://opencourseware-api.onrender.com";
const PAGE_SIZE = 100;
const CONCURRENCY = 12;

async function fetchCandidates(phrase: string) {
  const url = new URL(`${UPSTREAM}/api/v1/courses`);
  url.searchParams.set("q", phrase);
  url.searchParams.set("has_video_lectures", "true");
  url.searchParams.set("page_size", String(PAGE_SIZE));
  url.searchParams.set("sort_by", "view_count");
  url.searchParams.set("sort_dir", "desc");
  const response = await fetch(url, { signal: AbortSignal.timeout(12000) });
  if (!response.ok) return [];
  const data = (await response.json()) as PaginatedList<CourseSummary>;
  return data.items;
}

async function countSubject(slug: string) {
  const candidates = new Map<string, CourseSummary>();
  const phraseResults = await Promise.all(
    strictSubjectPhrases(slug).map((phrase) => fetchCandidates(phrase))
  );
  for (const result of phraseResults) {
    for (const course of result) candidates.set(course.id, course);
  }
  return Array.from(candidates.values()).filter((course) =>
    isCatalogReadyCourse(course) &&
    isStrictSubjectTitle(course.title, slug)
  ).length;
}

export async function POST(request: NextRequest) {
  try {
    const body = (await request.json()) as { slugs?: string[] };
    const slugs = Array.from(new Set(body.slugs ?? [])).filter(Boolean);
    const counts: Record<string, number> = {};

    for (let index = 0; index < slugs.length; index += CONCURRENCY) {
      const batch = slugs.slice(index, index + CONCURRENCY);
      const results = await Promise.all(batch.map((slug) => countSubject(slug)));
      batch.forEach((slug, resultIndex) => {
        counts[slug] = results[resultIndex];
      });
    }

    return NextResponse.json(
      { counts, generated_at: new Date().toISOString() },
      {
        headers: {
          "Cache-Control": "no-store",
          "Netlify-CDN-Cache-Control": "no-store",
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
