"""
match_roadmap_entries.py
------------------------
Fills roadmap_entries.course_id and course_slug by matching each entry to a
real course in the courses table.

Matching order (first hit wins per entry):
  1. Same university + exact course_number
  2. Same university + case-insensitive title
  3. Any university  + case-insensitive title
  4. Any university  + title starts-with / contains (for partial matches like
     "Intro to Machine Learning" matching "Introduction to Machine Learning")

Ties (multiple courses for same match key) are broken by:
  - Prefer shorter slug (avoids -2/-3 duplicates)

Run:
  py -3.13 -u match_roadmap_entries.py
"""

import re
import psycopg2

CONN = "postgresql://ocw:ocwpassword@127.0.0.1:5432/opencourseware"

def normalize(s: str) -> str:
    """Lowercase, strip punctuation for fuzzy title matching."""
    s = s.lower()
    s = re.sub(r"[^a-z0-9 ]+", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s

def main():
    conn = psycopg2.connect(CONN)
    cur = conn.cursor()

    # ── Load all courses ────────────────────────────────────────────────────
    cur.execute("""
        SELECT id, slug, university_id, course_number, title
        FROM courses
        ORDER BY slug  -- shorter slug = original (no -2, -3 suffix)
    """)
    courses = cur.fetchall()

    # Build lookup structures
    # key: (university_id, norm_course_number) -> first course (shortest slug)
    by_uni_num: dict[tuple, tuple] = {}
    # key: (university_id, norm_title) -> first course
    by_uni_title: dict[tuple, tuple] = {}
    # key: norm_title -> first course (any university, prefer MIT)
    by_title: dict[str, tuple] = {}

    MIT_UUID = "7fc201a9-e581-4429-84aa-74712f9995b0"

    for row in courses:
        cid, slug, uni_id, cnum, title = row
        ntitle = normalize(title)
        nnum = (cnum or "").strip().upper()

        key_un = (str(uni_id), nnum)
        if nnum and key_un not in by_uni_num:
            by_uni_num[key_un] = row

        key_ut = (str(uni_id), ntitle)
        if ntitle and key_ut not in by_uni_title:
            by_uni_title[key_ut] = row

        # Cross-uni: prefer MIT, otherwise take first
        if ntitle not in by_title:
            by_title[ntitle] = row
        elif str(uni_id) == MIT_UUID:
            by_title[ntitle] = row  # upgrade to MIT version

    # ── Load roadmap entries with their university ──────────────────────────
    cur.execute("""
        SELECT re.id, re.course_number, re.course_title, r.university_id
        FROM roadmap_entries re
        JOIN roadmaps r ON re.roadmap_id = r.id
        WHERE re.course_id IS NULL
        ORDER BY re.id
    """)
    entries = cur.fetchall()

    matched = 0
    unmatched = []

    for eid, cnum, ctitle, uni_id in entries:
        uni_id = str(uni_id)
        nnum = (cnum or "").strip().upper()
        ntitle = normalize(ctitle or "")

        # Also produce a "stripped" title with common qualifiers removed
        # e.g. "Machine Learning (Graduate)" → "machine learning"
        # e.g. "Advanced Operating Systems" → "operating systems"
        # e.g. "Laboratory Chemistry II" → "laboratory chemistry"
        stripped = re.sub(r'\b(i{1,3}|iv|v|1|2|3|4|graduate|advanced|intro|introduction|fundamentals)\b', '', ntitle)
        stripped = re.sub(r'\s+', ' ', stripped).strip()

        hit = None

        # 1. same-uni + course number
        if nnum:
            hit = by_uni_num.get((uni_id, nnum))

        # 2. same-uni + exact title
        if not hit and ntitle:
            hit = by_uni_title.get((uni_id, ntitle))

        # 3. cross-uni exact title
        if not hit and ntitle:
            hit = by_title.get(ntitle)

        # 4. same-uni + stripped title
        if not hit and stripped and stripped != ntitle:
            hit = by_uni_title.get((uni_id, stripped))

        # 5. cross-uni stripped title
        if not hit and stripped and stripped != ntitle:
            hit = by_title.get(stripped)

        # 6. bidirectional partial: DB title contained in entry title, OR entry in DB title
        #    (catches "Advanced Operating Systems" → "Operating Systems")
        if not hit and ntitle and len(ntitle) > 8:
            best = None
            best_len = 0
            for nt, row in by_title.items():
                if len(nt) < 5:
                    continue
                # DB title is a substring of entry title (more specific match = longer nt)
                if nt in ntitle and len(nt) > best_len:
                    best = row
                    best_len = len(nt)
                # Entry title is a substring of DB title
                elif ntitle in nt and len(ntitle) > best_len:
                    best = row
                    best_len = len(ntitle)
            hit = best

        # 7. same for stripped title
        if not hit and stripped and len(stripped) > 8:
            best = None
            best_len = 0
            for nt, row in by_title.items():
                if len(nt) < 5:
                    continue
                if nt in stripped and len(nt) > best_len:
                    best = row
                    best_len = len(nt)
                elif stripped in nt and len(stripped) > best_len:
                    best = row
                    best_len = len(stripped)
            hit = best

        if hit:
            cur.execute(
                "UPDATE roadmap_entries SET course_id=%s WHERE id=%s AND course_id IS NULL",
                (hit[0], eid)
            )
            matched += 1
        else:
            unmatched.append((cnum, ctitle))

    conn.commit()
    cur.close()
    conn.close()

    print(f"Matched: {matched} / {len(entries)}")
    if unmatched:
        print(f"\nUnmatched ({len(unmatched)}):")
        for cnum, ctitle in sorted(set(unmatched), key=lambda x: (x[0] or "", x[1] or "")):
            print(f"  [{cnum or '---'}] {ctitle}")

if __name__ == "__main__":
    main()
