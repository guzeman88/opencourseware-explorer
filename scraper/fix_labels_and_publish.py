#!/usr/bin/env python
"""
Fix mislabeled courses and publish all real video courses.

What this does:
  1. Audits current state
  2. Re-reads the MIT OCW CSV and corrects has_video_lectures / has_lecture_notes /
     has_exams for all existing MIT rows (fixes the load_mit_csv.py URL-vs-boolean bug)
  3. Syncs has_video_lectures from DB evidence (youtube_playlist_id, total_videos)
     for ALL universities
  4. Publishes every course that has real video content

Usage:
  py -3.13 fix_labels_and_publish.py --help
  DATABASE_URL=postgresql://user:pass@host/db py -3.13 fix_labels_and_publish.py --apply
"""
from __future__ import annotations

import csv
import os
import sys

import psycopg2
import psycopg2.extras

from mutation_guard import require_explicit_apply

# ── DB connection ──────────────────────────────────────────────────────────────
DATABASE_URL = require_explicit_apply("Fix labels and publish eligible courses.")
conn = psycopg2.connect(DATABASE_URL)

cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

CSV_PATH = os.environ.get(
    "OCW_MIT_CSV",
    r"C:\Users\Jorge DeGuzeman\Desktop\code-projects\Courses\MIT Course List Master - MIT Course List Master.csv",
)


def audit(label: str) -> None:
    cur.execute("SELECT COUNT(*) FROM courses")
    total = cur.fetchone()["count"]
    cur.execute("SELECT COUNT(*) FROM courses WHERE is_published = TRUE")
    published = cur.fetchone()["count"]
    cur.execute("SELECT COUNT(*) FROM courses WHERE has_video_lectures = TRUE")
    video = cur.fetchone()["count"]
    cur.execute("SELECT COUNT(*) FROM courses WHERE is_published = TRUE AND has_video_lectures = TRUE")
    pub_video = cur.fetchone()["count"]
    cur.execute("SELECT COUNT(*) FROM courses WHERE youtube_playlist_id IS NOT NULL")
    has_playlist = cur.fetchone()["count"]
    cur.execute("SELECT COUNT(*) FROM courses WHERE total_videos > 0")
    has_vids = cur.fetchone()["count"]
    print(f"\n=== {label} ===")
    print(f"  Total courses          : {total}")
    print(f"  Published              : {published}")
    print(f"  has_video_lectures=T   : {video}")
    print(f"  Published + video      : {pub_video}  <- what the frontend shows")
    print(f"  youtube_playlist_id set: {has_playlist}")
    print(f"  total_videos > 0       : {has_vids}")


# ══════════════════════════════════════════════════════════════════════════════
# STEP 0 — Add is_published column if it doesn't exist yet
# ══════════════════════════════════════════════════════════════════════════════
cur.execute("""
    SELECT column_name FROM information_schema.columns
     WHERE table_name = 'courses' AND column_name = 'is_published'
""")
if not cur.fetchone():
    print("Adding is_published column to courses table...")
    cur.execute("ALTER TABLE courses ADD COLUMN is_published BOOLEAN NOT NULL DEFAULT FALSE")
    conn.commit()
    print("  Column added.")
else:
    print("is_published column already exists.")

# ══════════════════════════════════════════════════════════════════════════════
# STEP 1 — Audit before
# ══════════════════════════════════════════════════════════════════════════════
audit("BEFORE")

# ══════════════════════════════════════════════════════════════════════════════
# STEP 2 — Re-read MIT CSV and fix flags for existing MIT courses
#           The original loader checked .lower() in ("yes","true","1","y") but
#           the CSV column actually contains URLs — so everything was False.
# ══════════════════════════════════════════════════════════════════════════════
print("\n--- Step 2: Re-reading MIT CSV to fix has_video_lectures flags ---")

if not os.path.exists(CSV_PATH):
    print(f"  WARNING: CSV not found at {CSV_PATH!r} — skipping MIT CSV fix")
else:
    mit_updates = []  # (has_video, has_notes, has_exams, source_url)
    with open(CSV_PATH, newline="", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            source_url = (row.get("Course URL") or "").strip()
            if not source_url:
                continue
            has_video = bool((row.get("Video Lectures") or "").strip())
            has_notes = bool((row.get("Lecture Notes") or "").strip())
            has_exams = bool((row.get("Exams") or "").strip())
            mit_updates.append((has_video, has_notes, has_exams, source_url))

    psycopg2.extras.execute_batch(
        cur,
        """UPDATE courses
              SET has_video_lectures = %s,
                  has_lecture_notes  = %s,
                  has_exams          = %s
            WHERE source_url = %s""",
        mit_updates,
        page_size=500,
    )
    conn.commit()
    print(f"  Updated flags for up to {len(mit_updates)} MIT rows (matched by source_url)")

# ══════════════════════════════════════════════════════════════════════════════
# STEP 3 — Sync has_video_lectures from hard DB evidence for ALL universities
#           If a course has a real YouTube playlist or ingested videos, it IS
#           a video course regardless of what the scraper said.
#           If it has neither, remove the stale True flag.
# ══════════════════════════════════════════════════════════════════════════════
print("\n--- Step 3: Syncing has_video_lectures from DB evidence (all universities) ---")

# Promote: has playlist or has ingested videos but flag is still False
cur.execute("""
    UPDATE courses
       SET has_video_lectures = TRUE
     WHERE (youtube_playlist_id IS NOT NULL OR total_videos > 0)
       AND has_video_lectures = FALSE
""")
promoted = cur.rowcount
conn.commit()
print(f"  Promoted {promoted} courses to has_video_lectures=TRUE (had playlist/videos but flag was False)")

# Demote: flag is True but zero DB evidence — these are the hardcoded scrapers
# that guessed True with no playlist (scrape_nptel_full, scrape_harvard_full, add_yale)
# We only demote non-MIT sources here since MIT was already fixed from the CSV above.
cur.execute("""
    UPDATE courses
       SET has_video_lectures = FALSE
     WHERE has_video_lectures = TRUE
       AND youtube_playlist_id IS NULL
       AND total_videos = 0
       AND source_key NOT IN ('mit_ocw')
""")
demoted = cur.rowcount
conn.commit()
print(f"  Demoted {demoted} non-MIT courses (has_video_lectures was True but no playlist or videos)")

# ══════════════════════════════════════════════════════════════════════════════
# STEP 4 — Publish all real video courses
# ══════════════════════════════════════════════════════════════════════════════
print("\n--- Step 4: Publishing all video courses ---")

cur.execute("""
    UPDATE courses
       SET is_published = TRUE
     WHERE has_video_lectures = TRUE
       AND is_published = FALSE
""")
newly_published = cur.rowcount
conn.commit()
print(f"  Published {newly_published} courses")

# Also publish MIT OCW non-video courses that have lecture notes or exams —
# these are real accessible course pages, not 404s.
cur.execute("""
    UPDATE courses
       SET is_published = TRUE
     WHERE source_key = 'mit_ocw'
       AND has_video_lectures = FALSE
       AND (has_lecture_notes = TRUE OR has_exams = TRUE)
       AND is_published = FALSE
""")
mit_nonvideo_published = cur.rowcount
conn.commit()
print(f"  Published {mit_nonvideo_published} MIT non-video courses with lecture notes/exams")

# ══════════════════════════════════════════════════════════════════════════════
# STEP 5 — Final audit
# ══════════════════════════════════════════════════════════════════════════════
audit("AFTER")

cur.close()
conn.close()
print("\nDone.")
