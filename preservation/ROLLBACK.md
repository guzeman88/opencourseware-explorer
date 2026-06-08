# Preservation and Rollback Runbook

## General Rule

Prefer additive recovery and new corrective commits. Never use destructive Git
cleanup, force-push, database reset, or broad deletion as a shortcut.

## Before Any Repair

1. Record `git status --short --branch`, `HEAD`, upstream commit, and deploy IDs.
2. Run `scripts/capture_preservation_baseline.py` and retain its JSON output.
3. Identify affected workflows from `ESSENTIAL_WORKFLOWS.md`.
4. For data-affecting work, create and verify a Neon restore point or logical dump.
5. Export affected record IDs and relationships before applying a mutation.
6. Define the exact rollback trigger and restoration procedure.

## Frontend Rollback

1. Stop promotion if preview or mobile checks fail.
2. If production fails, create a new revert commit for the offending change.
3. Push the revert, deploy Netlify from that commit, and verify with a
   cache-busting request.
4. Confirm PWA install/update behavior separately because clients may retain caches.

## Backend Rollback

1. Preserve the failing API response, logs, and deployed commit ID.
2. Revert through a new Git commit.
3. Deploy the corrected commit to Render.
4. Verify health, schemas, representative reads, auth, and frontend compatibility.
5. Do not roll back application code across a required database migration unless
   the migration compatibility path is documented.

## Database and Pipeline Rollback

1. Never mutate production without a verified restore point or logical backup.
2. Prefer append-only proposal/review tables and atomic promotion transactions.
3. Export affected primary keys and relationships before updates.
4. Apply changes inside a transaction and validate before commit when feasible.
5. If preservation checks fail, roll back the transaction or restore only the
   affected exported records. Use full restore only when necessary.
6. Never delete uncertain course or video source records; mark them ineligible or
   quarantine them for review.

## Secret Rotation Recovery

1. Identify all consumers before rotating.
2. Create the replacement secret.
3. Update and verify consumers one at a time.
4. Revoke the old secret only after all authorized workflows pass.
5. If connectivity fails, restore the prior authorized configuration while the
   replacement path is corrected; never recommit the secret.

## Required Evidence

- Recovery branch/commit and database restore reference
- Before/after baseline files
- Exact affected record IDs for data changes
- Tests and workflow checks run
- Deployment IDs and production verification
- Rollback action taken, or confirmation that rollback was unnecessary
