# Subject Membership and Relevance Policy

Captured on 2026-06-09. This policy preserves current memberships while making
subject results, ordering, and displayed counts agree.

## Sources of Truth

1. `course_subjects` is the approved membership set shown on course records.
2. `course_subject_relevance` is inspectable evidence used for subject result
   inclusion and ordering. Each row records score, relationship, reason,
   source, and version.
3. `subject_catalog_counts` is a derived sidecar. It is valid only when its
   `policy_version` matches `subject-results-v1`.
4. Strict title matching is a fallback and audit signal, not a reason to erase
   an approved or uncertain membership.

## Result and Count Precedence

For relevance-sorted subject results:

1. If a subject has relevance rows scoring at least 40, include catalog-ready
   courses with those rows and order by score.
2. If a subject has no qualifying relevance rows, use strict title matching.
3. Generate the displayed subject count from the same branch used by results.

For non-relevance subject filtering, preserve the approved `course_subjects`
membership behavior until that consumer is migrated and regression-tested.

## Proposal and Promotion Rules

- Proposal generation is report-only by default.
- Existing tags remain untouched during proposal generation.
- Broad parent rollups are suppressed unless directly supported by evidence.
- Any course with no proposal blocks promotion and remains for review.
- Before promotion, export all affected `course_subjects`.
- Promote memberships and relevance evidence in one database transaction.
- A failed promotion must roll back without changing membership counts.
- After promotion, verify course, video, membership, and orphan counts before
  rebuilding `subject_catalog_counts`.

## Verified Isolated Result

The restored catalog produced proposals for all 4,067 catalog-ready courses
with zero additions and zero removals. Atomic promotion preserved all 27,773
memberships and created 18,599 inspectable relevance rows. Rebuilt counts for
all 433 subjects then matched relevance-result totals with zero mismatches.

