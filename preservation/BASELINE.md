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
| Dependency audit | 3 high, 3 moderate | Dependency upgrades require isolated regression-tested batches |
| Production public API | Reachable | Public baseline is captured by the JSON baseline tool |
| Configured local database | Stale Railway connection | Must be reconciled before normal maintenance |
| Neon logical backup | Verified | 11 pre-existing tables saved with row counts and checksums |
| Production migration state | `h3i4j5k6l7m8` | Missing additive schema has been restored |
| Roadmaps API | 200; 36 roadmaps | Restored from HTTP 500 |

## Verified Current Production Inconsistencies

- Discrete Mathematics subject results and displayed/static counts disagree.
- Public Discrete Mathematics results include records reporting zero videos.
- Strict subject-count computation and course relevance results do not share one
  authoritative membership source.

## Stop Conditions Currently Active

- Do not perform destructive production-data work; the verified backup is
  logical and has not yet been restore-tested into an isolated database.
- Do not deploy broad dependency or authentication changes until frontend
  regression tests are reliable.
- Do not remove uncertain courses, videos, tags, or memberships.

## Next Safe Work

1. Rotate externally exposed credentials and reconcile local environment URLs.
2. Deploy and production-verify the repaired publishing and relevance code.
3. Make subject proposal generation efficient and compare it before any apply.
4. Repair catalog/video inconsistencies without deleting source records.
