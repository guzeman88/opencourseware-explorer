# Initial Preservation Baseline

Captured on 2026-06-08 before functional or production-data repairs.

## Recovery Reference

- Branch: `codex/preservation-first-repair`
- Starting commit: `50fc007135f0d2c9d3adb88cab5a0d168b1e975b`
- Starting state: clean and aligned with `origin/main`
- Production-data changes: none

## Current Verification Results

| Check | Result | Preservation meaning |
|---|---|---|
| Backend tests | 21 passed | Existing backend contracts currently pass |
| Scraper tests | 39 passed after repair | Undergraduate classification defect is fixed |
| Frontend tests | 20 passed after repair | Required providers and current behavior are covered |
| Frontend Jest config | Valid | Setup loads and generated directories are excluded |
| Frontend lint | Clean | Non-interactive CI-compatible linting is configured |
| Frontend build | Passed | Current production build completes |
| Dependency audit | 0 high, 3 moderate | Remaining Next/PostCSS findings require upstream-safe remediation |
| Production public API | Reachable | Public baseline is captured by the JSON baseline tool |
| Isolated local restore | Verified on port 5433 | Use for restore and repair verification only |
| Neon logical backup | Restore-verified | 11 pre-existing tables restored with exact counts into isolated PostgreSQL |
| Production migration state | `h3i4j5k6l7m8` | Missing additive schema has been restored |
| Roadmaps API | 200; 36 roadmaps | Restored from HTTP 500 |

## Verified Current Production Inconsistencies

- Discrete Mathematics subject results and displayed/static counts disagree.
- Public Discrete Mathematics results include records reporting zero videos.
- Strict subject-count computation and course relevance results do not share one
  authoritative membership source.
- Live Render `/openapi.json` does not expose the checked-in `catalog_ready`
  course parameter or `strict_counts` subject parameter.
- Live Render reports all 9,741 courses from the public endpoint, while the
  current preservation shadow audit identifies 4,067 current catalog-ready
  courses. Render is not serving the current Git backend.

## Stop Conditions Currently Active

- Do not perform destructive production-data work without explicit production
  authorization, a fresh verified backup, and a reviewed rollback plan.
- Do not deploy broad dependency or authentication changes until frontend
  regression tests are reliable.
- Do not remove uncertain courses, videos, tags, or memberships.
- Do not deploy the Subjects page count-source repair until Render serves the
  matching backend; a frontend-only release would make counts less reliable.

## Next Safe Work

1. Rotate externally exposed credentials and reconcile authorized consumers.
2. Configure Git-backed Render deployment and production commit fingerprints.
3. Deploy and production-verify repaired catalog, publishing, and relevance code.
4. Recover counter-only video courses without deleting source records.
