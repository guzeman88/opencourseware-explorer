import type { CourseSummary } from "@/types";

export const STRICT_SUBJECT_SYNONYMS: Record<string, string[]> = {
  "artificial-intelligence": ["ai", "artificial intelligence"],
  "computer-science": ["computer science", "computing", "cs"],
  "computer-networks": ["computer networks", "networking"],
  cybersecurity: ["cybersecurity", "cyber security", "computer security", "information security"],
  "data-structures": ["data structures", "data structure"],
  "differential-equations": [
    "differential equations",
    "ordinary differential equations",
    "partial differential equations",
  ],
  "discrete-mathematics": ["discrete mathematics", "discrete math", "discrete structures"],
  "large-language-models": ["large language models", "large language model", "llm", "language models"],
  "machine-learning": ["machine learning", "statistical learning"],
  "natural-language-processing": ["natural language processing", "nlp"],
  "operating-systems": ["operating systems", "operating system"],
  probability: ["probability", "probability theory"],
  "proof-writing": ["proof writing", "proofs", "proof", "mathematical proofs", "logic and proof"],
  "real-analysis": ["real analysis"],
  "software-engineering": ["software engineering"],
};

export function normalizeSubjectText(value: string) {
  return value
    .toLowerCase()
    .replace(/[^a-z0-9+#.]+/g, " ")
    .replace(/\s+/g, " ")
    .trim();
}

export function strictTitleScope(title: string) {
  return title.split(" | ", 1)[0] ?? title;
}

export function phraseMatches(haystack: string, phrase: string) {
  const normalized = normalizeSubjectText(phrase);
  if (!normalized) return false;
  const escaped = normalized.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  return new RegExp(`(^|[^a-z0-9])${escaped}([^a-z0-9]|$)`).test(haystack);
}

export function strictSubjectPhrases(slug: string) {
  const fallback = slug.replace(/-/g, " ");
  return Array.from(new Set([fallback, ...(STRICT_SUBJECT_SYNONYMS[slug] ?? [])]));
}

export function isStrictSubjectTitle(title: string, subjectSlug: string) {
  const scopedTitle = normalizeSubjectText(strictTitleScope(title));
  return strictSubjectPhrases(subjectSlug).some((phrase) =>
    phraseMatches(scopedTitle, phrase)
  );
}

export function isStrictSubjectCourse(course: CourseSummary, subjectSlug: string) {
  return isStrictSubjectTitle(course.title, subjectSlug);
}
