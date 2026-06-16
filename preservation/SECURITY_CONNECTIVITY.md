# Security and Connectivity Baseline

Captured on 2026-06-09 before external credential rotation.

## Exposed Credential Classes

The redacted Git-history scan found:

- credentialed PostgreSQL URLs in historical scraper and maintenance files;
- a historical YouTube Data API key;
- historical Netlify and Vercel deploy-hook URLs.

The scan reports only object IDs, paths, line numbers, and credential classes.
It never prints credential values.

## Authorized Consumer Inventory

| Credential | Known consumers |
|---|---|
| Neon database credentials | Render API, local scraper and maintenance scripts, backup/baseline tools |
| YouTube Data API key | Local scraper enrichment and playlist/video recovery scripts |
| Backend `SECRET_KEY` | Render API JWT signing |
| Admin credentials | Render API admin bootstrap and admin login |
| Netlify deploy hook | GitHub Actions deploy workflow |
| Vercel deploy hook | GitHub Actions deploy workflow |
| Render deploy hook | GitHub Actions deploy workflow |
| Sentry DSNs/tokens | Netlify frontend and Render API when configured |

## Verified Connectivity

- GitHub CLI authentication works for `guzeman88/opencourseware-explorer`.
- Netlify CLI is linked to `opencourseware-explorer`.
- Production Netlify homepage returns HTTP 200.
- Netlify `/api/v1/courses?page_size=1` proxy returns HTTP 200.
- Render `/health` and `/openapi.json` return HTTP 200.

## 2026-06-16 Deploy Secret Update

- GitHub Actions secrets now include `NETLIFY_DEPLOY_HOOK_URL` and
  `VERCEL_DEPLOY_HOOK_URL`.
- Netlify is Git-backed to `guzeman88/opencourseware-explorer`, production
  branch `main`, base `web`, and has `prevent_non_git_prod_deploys` enabled.
- A main-branch Netlify build hook already existed and was registered in
  GitHub Actions without printing the hook URL in tracked files.
- Vercel main-branch deploy hooks already existed and one was registered in
  GitHub Actions without printing the hook URL in tracked files.
- `RENDER_DEPLOY_HOOK_URL` is still not configured in GitHub Actions.

## Known Gaps and Stop Conditions

- Render deploy-hook configuration remains required before Git-based backend
  deployment can be accepted.
- Render `/health` does not currently expose a Git commit fingerprint.
- Render OpenAPI does not expose the checked-in `catalog_ready` or
  `strict_counts` parameters, confirming that production Render does not match
  the repair branch.
- Database and YouTube connectivity cannot be fully re-verified from the
  current shell. `../.env.production` has blank DB/YouTube entries, and the
  local `backend/.env` database URL is not usable for a read-only backup.
- External credential rotation and revocation must be performed in Neon, GCP,
  Netlify, Vercel, Render, and GitHub dashboards. Do not revoke an old
  credential until its replacement consumer has passed.
