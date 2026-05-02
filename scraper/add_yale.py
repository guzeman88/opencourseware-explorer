#!/usr/bin/env python
"""Add the remaining Yale OYC courses not yet in DB."""
import uuid
import psycopg2
from slugify import slugify

DB = dict(host="127.0.0.1", port=5432, dbname="opencourseware", user="ocw", password="ocwpassword")

COURSES = [
    ("Foundations of Modern Social Theory", "Sociology", "Iván Szelényi", "https://oyc.yale.edu/sociology/socy-151", "undergraduate", ["Sociology", "Social Theory"]),
    ("Cervantes' Don Quixote", "Spanish and Portuguese", "Roberto González Echevarría", "https://oyc.yale.edu/spanish-and-portuguese/span-300", "undergraduate", ["Literature", "Spanish"]),
    ("The Early Middle Ages, 284-1000 AD", "History", "Paul Freedman", "https://oyc.yale.edu/history/hist-210-fa11", "undergraduate", ["History", "Medieval History"]),
    ("Epidemics in Western Society Since 1600", "History", "Frank Snowden", "https://oyc.yale.edu/history/hist-234-fa10", "undergraduate", ["History", "Public Health"]),
    ("France Since 1871", "History", "John Merriman", "https://oyc.yale.edu/history/hist-202-fa10", "undergraduate", ["History", "European History"]),
]

def upsert_subject(cur, name, cache):
    if name in cache:
        return cache[name]
    slug = slugify(name)
    cur.execute("SELECT id FROM subjects WHERE slug=%s", (slug,))
    row = cur.fetchone()
    if row:
        cache[name] = row[0]
        return row[0]
    sid = str(uuid.uuid4())
    cur.execute("INSERT INTO subjects (id,name,slug) VALUES (%s,%s,%s) ON CONFLICT (slug) DO UPDATE SET name=EXCLUDED.name RETURNING id", (sid, name, slug))
    row = cur.fetchone()
    cache[name] = row[0] if row else sid
    return cache[name]

conn = psycopg2.connect(**DB)
cur = conn.cursor()

# Get Yale university id
cur.execute("SELECT id FROM universities WHERE source_key='yale'")
uni_id = cur.fetchone()[0]

cur.execute("SELECT source_url FROM courses")
seen_urls = {r[0] for r in cur.fetchall()}
cur.execute("SELECT slug FROM courses")
seen_slugs = {r[0] for r in cur.fetchall()}

subject_cache = {}
created = skipped = 0

for (title, dept, instructor, url, level, subjects) in COURSES:
    if url in seen_urls:
        skipped += 1
        print(f"SKIP: {title}")
        continue
    # unique slug
    base = slugify(f"{title} yale")
    slug = base
    i = 2
    while slug in seen_slugs:
        slug = f"{base}-{i}"
        i += 1
    seen_slugs.add(slug)

    cid = str(uuid.uuid4())
    cur.execute(
        """INSERT INTO courses (id, university_id, title, slug, source_key, source_url, description, level, instructor, has_video_lectures)
           VALUES (%s,%s,%s,%s,'yale',%s,%s,%s,%s,%s) ON CONFLICT (slug) DO NOTHING""",
        (cid, uni_id, title, slug, url, f"{title}. Open Yale Course.", level, instructor, True)
    )
    for s in subjects[:2]:
        sid = upsert_subject(cur, s, subject_cache)
        cur.execute("INSERT INTO course_subjects (id,course_id,subject_id) VALUES (%s,%s,%s) ON CONFLICT DO NOTHING", (str(uuid.uuid4()), cid, sid))
    seen_urls.add(url)
    created += 1
    print(f"ADDED: {title}")

conn.commit()
cur.close()
conn.close()
print(f"\nCreated: {created}, Skipped: {skipped}")
