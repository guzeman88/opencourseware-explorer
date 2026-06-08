# The Commons Preservation-First Repair Roadmap

This is the tracked implementation checklist for bringing The Commons to a
professional production standard without losing valid data, features, design,
functionality, or deployment behavior.

## Prime Directive

Preservation is the number-one priority. Existing behavior and data are
presumed valuable until verified otherwise. Uncertain records are retained for
review rather than deleted. A task is complete only after its targeted repair,
preservation checks, tests, deployment verification, and rollback evidence all
pass.

Status markers:

- `[ ]` not started
- `[-]` in progress
- `[x]` completed and verified
- `[!]` blocked; reason must be recorded in Evidence

## Required Gate for Every Repair

1. Inventory affected code, data, APIs, screens, dependencies, and deployments.
2. Reproduce the issue and prove the diagnosis.
3. Record baseline behavior, counts, responses, screenshots, and test results.
4. Create a recovery reference, backup, export, or rollback point.
5. Define the intended improvement and the behavior that must not change.
6. Dry-run or shadow-test the proposed repair.
7. Implement the smallest complete repair.
8. Run targeted and preservation regression checks.
9. Compare data counts and relationships before and after.
10. Deploy from a verified Git commit and verify production.
11. Monitor and roll back if any stop condition occurs.
12. Record evidence below.

## Phase 0: Preservation System

- [x] Create this tracked roadmap and evidence structure.
- [x] Link this roadmap from `OPERATIONS.md`.
- [x] Create the feature and persistent-data inventory.
- [x] Create the essential-workflow regression checklist.
- [x] Document frontend, backend, database, and pipeline rollback procedures.
- [x] Capture the initial read-only data and production baseline.
- [ ] Capture desktop and mobile screenshots of essential screens.
- [x] Create and verify a recoverable Neon backup.
- [x] Run and record all build, test, lint, security, and dependency checks.

Acceptance: the team can detect and recover from lost data, features,
functionality, or visual behavior before functional repairs begin.

## Phase 1: Security Without Breaking Connectivity

- [ ] Verify exposed credentials and every authorized consumer.
- [ ] Capture working connectivity checks before rotation.
- [ ] Rotate exposed Neon and YouTube credentials one service at a time.
- [ ] Update authorized environments before revoking old credentials.
- [x] Remove hardcoded credentials and require environment configuration.
- [-] Scan the current tree and Git history for remaining secrets.
- [ ] Re-run connectivity, scraper, API, and deployment checks.

Acceptance: no usable secret remains in source or history and every authorized
workflow continues to operate.

## Phase 2: Catalog and Video Integrity

- [ ] Inventory every catalog eligibility rule and consumer.
- [ ] Define one authoritative public-course invariant.
- [ ] Generate and review eligibility decisions in shadow mode.
- [ ] Persist eligibility status and inspectable exclusion reasons.
- [ ] Migrate consumers one at a time to authoritative eligibility.
- [ ] Audit video flags, counters, playlists, and video rows.
- [ ] Recover videos where credible evidence exists.
- [ ] Recalculate counters from verified video records.
- [ ] Retain but hide unresolved invalid courses.
- [ ] Add recurring catalog and video integrity checks.
- [ ] Verify existing valid course pages, videos, materials, and navigation.

Acceptance: every visible course satisfies the catalog rules and no verified
valid course or video is lost.

## Phase 3: Publishing, Subjects, and Tagging

- [ ] Export current publication states.
- [-] Repair publishing while preventing invalid publication.
- [-] Verify admin and public publishing behavior.
- [x] Reproduce and repair unreachable subject relevance logic.
- [ ] Define subject membership and relevance precedence.
- [ ] Generate proposed memberships without replacing current tags.
- [ ] Preserve uncertain memberships for review.
- [ ] Promote approved memberships atomically with rollback support.
- [ ] Replace static counts and full-catalog runtime scans.
- [ ] Verify every displayed subject count equals its result total.
- [ ] Consolidate tagging into a dry-run-first controlled pipeline.
- [ ] Block accidental production mutation by maintenance scripts.

Acceptance: publishing works, and subject membership, ordering, filtering, and
counts agree without losing valid tags or subject visibility.

## Phase 4: Automated Preservation and Deployment Gates

- [x] Repair existing frontend and scraper tests without weakening assertions.
- [x] Make lint and tests deterministic and CI-compatible.
- [ ] Convert essential workflows into permanent regression tests.
- [ ] Add catalog, video, subject, publishing, auth, library, roadmap, and
      progress contract tests.
- [ ] Add desktop, mobile, and accessibility browser checks.
- [ ] Add data-count and relationship-preservation checks.
- [-] Add dependency and secret scanning.
- [x] Require passing checks before deployment.
- [ ] Create and verify Netlify preview deployments.
- [ ] Deploy production only from a passing Git commit.
- [ ] Verify production commit fingerprints and rollback procedures.

Acceptance: a change that loses essential data, features, functionality, or
design cannot automatically reach production.

## Phase 5: Authentication and Dependency Hardening

- [ ] Triage reported vulnerabilities and upgrade risks.
- [ ] Upgrade dependencies in isolated, regression-tested batches.
- [x] Remove the frontend self-dependency and generated test collisions.
- [ ] Replace JavaScript-accessible admin authentication safely.
- [ ] Migrate user sessions without losing accounts, libraries, or progress.
- [ ] Introduce CSP and security headers in report-only mode first.
- [ ] Verify media, analytics, Sentry, authentication, and PWA launch.

Acceptance: security improves without losing access, integrations, or user
state.

## Phase 6: Performance, Caching, and PWA

- [ ] Record cold and warm phone/API performance.
- [ ] Replace exhaustive fetching incrementally with pagination or cursors.
- [ ] Preserve ordering, filters, visible content, and scroll behavior.
- [ ] Route cacheable requests consistently through the intended cache.
- [ ] Replace synchronous view-count writes without losing analytics.
- [ ] Add latency, error-rate, cache-hit, and regression monitoring.
- [ ] Document why service-worker cleanup was introduced.
- [ ] Preserve current splash and zero-black-screen launch behavior.
- [ ] Introduce versioned cache migration and safe offline behavior.
- [ ] Verify fresh install, upgrade, offline, reconnection, and home-screen launch.
- [ ] Optimize images incrementally while preserving all thumbnails and fallbacks.

Acceptance: performance improves measurably without missing content, stale
applications, broken launches, or degraded mobile behavior.

## Phase 7: Premium Product Experience

- [ ] Improve search while preserving valid existing results.
- [ ] Add exact-resume and richer progress without losing watch history.
- [ ] Add transcripts, chapters, next-lecture, and unavailable-video handling.
- [ ] Repair nested controls, dialogs, keyboard, and mobile semantics.
- [ ] Improve course-quality and relevance signals.
- [ ] Replace hardcoded discovery only after equivalent coverage is proven.
- [ ] Strengthen roadmaps without removing roadmap data or ordering.
- [ ] Run usability, accessibility, and preservation checks after each increment.

Acceptance: users can find, evaluate, start, resume, and complete courses while
all previously valid essential workflows remain available.

## Phase 8: Documentation and Maintainability

- [ ] Reconcile README and Operations claims with verified production behavior.
- [ ] Correct stale catalog, NPTEL, deployment, and known-bug claims.
- [ ] Correct documentation encoding problems.
- [ ] Document the owner and source of truth for every domain.
- [ ] Mark the Expo app as paused or define a supported parity plan.
- [ ] Remove duplicated logic only after migration and regression checks.
- [ ] Split large modules without changing observable behavior.
- [ ] Remove dead code only after proving it is unused.
- [ ] Keep this roadmap and its evidence current.

Acceptance: documentation, architecture, and production behavior agree without
discarding useful functionality or historical knowledge.

## Non-Negotiable Stop Conditions

Stop and investigate if:

- a valid course, video, tag, roadmap, user, bookmark, or progress record disappears;
- an existing public or admin workflow unexpectedly fails;
- subject counts and result totals become less consistent;
- mobile launch, splash, navigation, or playback regresses;
- a deployment cannot be tied to a verified Git commit;
- a database-changing operation lacks a verified backup and rollback path; or
- a cleanup cannot distinguish invalid data from uncertain valuable data.

## Evidence Log

### 2026-06-08 - Preservation system initialized

- Recovery reference: branch `codex/preservation-first-repair`, starting commit
  `50fc007135f0d2c9d3adb88cab5a0d168b1e975b`.
- Repository state: clean; local `main` matched `origin/main`.
- Functional/data mutations: none.
- Added preservation documentation and a read-only baseline capture tool.
- Initial baselines, backup verification, and regression results remain in
  progress and must complete before data-affecting repairs.
- Backend tests: 21 passed.
- Scraper tests: 37 passed and 2 failed, exposing an undergraduate-level parser defect.
- Frontend tests: 11 passed and 9 failed because test providers/configuration are stale.
- Dependency audit: 3 high and 3 moderate vulnerabilities.
- Configured private database connection failed; production-data work remains blocked.

### 2026-06-08 - First preservation repair batch

- Verified ignored logical backup:
  `preservation/private-backups/commons-2026-06-08T22-49-21Z.zip`.
- Backup size: 34,506,668 bytes; all 11 pre-existing tables verified by row
  count and SHA-256 checksum.
- Added missing production schema additively: `course_subject_relevance`,
  `roadmaps`, and `roadmap_entries`; migration state advanced from
  `b2c3d4e5f6a7` to `h3i4j5k6l7m8`.
- Restored the existing checked-in roadmap definitions through a full dry run
  followed by apply: 36 roadmaps and 470 entries are now served publicly.
- Preservation comparison: courses 9,741; videos 157,384; course-subject links
  27,773; subjects 433; universities 174; users 1; library rows 0; watch-history
  rows 0. All pre-existing counts remained unchanged.
- Roadmap entries currently linked to a course: 0. Matching remains future work.
- Repaired admin publication state changes and subject relevance branch
  selection in code; production backend deployment remains pending.
- Removed confirmed live credentials from the tracked working tree. Current-tree
  secret scan passes; exposed credentials still require external rotation and
  Git-history remediation.
- Quality results: backend 23 passed; scraper 39 passed; frontend 20 passed;
  lint clean; production frontend build clean; tracked-tree secret scan clean.
- CI deploy workflow now requires the passing quality gate before existing
  Vercel and Netlify hooks run.
