# Performance Baseline

Captured on June 9, 2026 from the repair workstation in America/New_York.
These are HTTP timing baselines, not a substitute for real-device browser
performance testing.

| Surface | Run 1 | Run 2 | Run 3 | Notes |
|---|---:|---:|---:|---|
| Render `/health` | 630 ms | 131 ms | 133 ms | Clear cold/warm difference |
| Render `/api/v1/courses?page_size=1` | 986 ms | 838 ms | 919 ms | Warm API remains near 0.9 s |
| Netlify `/` | 781 ms | 230 ms | 230 ms | Clear CDN warm response |

The local production build returned HTTP 200 for home, courses, subjects,
universities, roadmaps, search, library, admin login, and the `/api/v1`
courses proxy. A true mobile-device performance and accessibility run remains
required; the in-app browser connection timed out and the fallback browser CLI
was unavailable.

