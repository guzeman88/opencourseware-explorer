# Restore Verification and Local Mutation Incident

Captured on 2026-06-09. No production database was mutated during this work.

## Isolated Restore Verification

- Target: Docker Compose project `commons_restore_test`, PostgreSQL on
  `127.0.0.1:5433`.
- Source: ignored verified logical backup
  `preservation/private-backups/commons-2026-06-08T22-49-21Z.zip`.
- Clean `alembic upgrade head` succeeded through migration `i4j5k6l7m8n9`.
- Restore tool: `scripts/restore_logical_backup.py`.
- Restored and verified: 195,506 rows.

| Table | Verified rows |
|---|---:|
| universities | 174 |
| departments | 0 |
| subjects | 433 |
| users | 1 |
| courses | 9,741 |
| videos | 157,384 |
| course_subjects | 27,773 |
| scraper_jobs | 0 |
| user_library_courses | 0 |
| user_watch_history | 0 |

The clean migration test exposed a PostgreSQL defect in the trigram-index
migration: `CREATE INDEX CONCURRENTLY` was inside Alembic's transaction. It now
uses an Alembic autocommit block and the clean migration succeeds.

## Isolated Repair Verification

- Persisted eligibility decisions: 4,067 eligible, 3,388 review, 2,286
  excluded.
- Reconciled four counter mismatches backed by actual video rows.
- Preserved all 435 courses that have a positive counter but no local video
  rows for recovery or review.
- Generated proposals for all 4,067 catalog-ready courses with zero additions,
  zero removals, and zero untagged courses.
- The first atomic membership promotion attempt failed on a missing required
  `course_subjects.id`; the transaction rolled back to all original counts.
- After repairing the insert and adding a regression test, atomic promotion
  preserved 27,773 memberships, 9,741 courses, 157,384 videos, and zero
  membership orphans.
- Rebuilt all 433 subject counts from the same precedence as subject results;
  all counts match with zero aggregate delta.

## Localhost Port 5432 Incident

While inspecting help interfaces, this command was run:

`python scraper/verify_and_fix_video_courses.py --help`

The historical script ignored `--help`, connected at import time, silently
fell back to an existing local PostgreSQL database on `127.0.0.1:5432`, and
mutated that local database. It updated 29 counters, cleared 126 playlist IDs,
demoted 351 video flags, and unpublished 230 courses.

This did not reach Neon, Render, or the isolated restore on port 5433. An
immediate verified post-incident backup was created at:

`preservation/private-backups/local-5432-post-verify-script-incident-2026-06-09.zip`

No guessed rollback was attempted because an exact verified pre-incident export
of that local database was not available. The script now requires both
`--apply` and an explicit `DATABASE_URL`; regression tests prove `--help` and a
no-argument invocation cannot connect.

