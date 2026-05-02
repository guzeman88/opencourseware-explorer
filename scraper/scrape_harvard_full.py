#!/usr/bin/env python
"""
Harvard full free course scraper.

Scrapes all 142 free courses from pll.harvard.edu/catalog/free (5 pages)
and inserts them directly into PostgreSQL.

Usage:
    py -3.13 scrape_harvard_full.py
"""
from __future__ import annotations

import re
import time
import uuid
import urllib.request

import psycopg2
from bs4 import BeautifulSoup
from slugify import slugify

DATABASE_URL = "postgresql://ocw:ocwpassword@127.0.0.1:5432/opencourseware"
HARVARD_BASE = "https://pll.harvard.edu"

SUBJECT_MAP = {
    "COMPUTER SCIENCE": ["Computer Science"],
    "DATA SCIENCE": ["Data Science", "Statistics"],
    "PROGRAMMING": ["Programming", "Computer Science"],
    "HEALTH & MEDICINE": ["Medicine", "Health"],
    "BUSINESS": ["Business", "Management"],
    "HUMANITIES": ["Humanities"],
    "SCIENCE": ["Science"],
    "SOCIAL SCIENCES": ["Social Sciences"],
    "ART & DESIGN": ["Art", "Design"],
    "MATHEMATICS": ["Mathematics"],
    "EDUCATION": ["Education"],
    "LAW": ["Law"],
    "ENGINEERING": ["Engineering"],
    "LANGUAGE": ["Language"],
}


def fetch_html(url: str) -> str:
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0 (Educational course aggregator)"}
    )
    resp = urllib.request.urlopen(req, timeout=20)
    return resp.read().decode("utf-8", errors="ignore")


def scrape_all_pages() -> list[dict]:
    courses = []
    seen_urls = set()
    
    for page in range(6):  # pages 0-5
        url = f"{HARVARD_BASE}/catalog/free?price[1]=1&page={page}"
        print(f"  Fetching page {page+1}...", flush=True)
        try:
            html = fetch_html(url)
        except Exception as e:
            print(f"    Error: {e}")
            break
        
        soup = BeautifulSoup(html, "html.parser")
        
        # Find course links - they are <h3> with links inside
        found_on_page = 0
        for h3 in soup.select("h3"):
            a = h3.find("a")
            if not a:
                continue
            href = a.get("href", "")
            if not href.startswith(HARVARD_BASE + "/course/") and not href.startswith("/course/"):
                continue
            if href.startswith("/"):
                href = HARVARD_BASE + href
            
            if href in seen_urls:
                continue
            seen_urls.add(href)
            
            title = a.get_text(strip=True)
            if not title:
                continue
            
            # Find subject category from preceding sibling
            subject_tag = None
            parent = h3.parent
            if parent:
                # Find subject link nearby
                for a_tag in parent.select("a[href*='/subject/']"):
                    subject_tag = a_tag.get_text(strip=True).upper()
                    break
            
            # Try to find description
            desc = ""
            sibling = h3.find_next_sibling("p")
            if sibling:
                desc = sibling.get_text(strip=True)
            if not desc:
                # check next p in parent
                p = parent.find("p") if parent else None
                if p:
                    desc = p.get_text(strip=True)
            
            subjects = SUBJECT_MAP.get(subject_tag, []) if subject_tag else []
            
            slug_id = href.rstrip("/").split("/")[-1]
            
            courses.append({
                "title": title,
                "source_url": href,
                "slug_id": slug_id,
                "description": desc,
                "subjects": subjects,
                "subject_category": subject_tag,
            })
            found_on_page += 1
        
        print(f"    Found {found_on_page} courses on page {page+1}", flush=True)
        
        if found_on_page == 0:
            break
        
        time.sleep(0.5)
    
    print(f"Total Harvard courses found: {len(courses)}", flush=True)
    return courses


def get_or_create_university(cur) -> str:
    cur.execute("SELECT id FROM universities WHERE source_key = 'harvard'")
    row = cur.fetchone()
    if row:
        return row[0]
    uni_id = str(uuid.uuid4())
    cur.execute(
        """INSERT INTO universities (id, name, slug, website, country, source_key, description)
           VALUES (%s, %s, %s, %s, %s, %s, %s) ON CONFLICT (slug) DO UPDATE SET name=EXCLUDED.name RETURNING id""",
        (uni_id, "Harvard University", "harvard", "https://online.harvard.edu", "US", "harvard",
         "Harvard University free online courses via Harvard Online Learning.")
    )
    row = cur.fetchone()
    return row[0] if row else uni_id


def get_or_create_subject(cur, name: str, cache: dict) -> str:
    if name in cache:
        return cache[name]
    slug = slugify(name)
    cur.execute("SELECT id FROM subjects WHERE slug = %s", (slug,))
    row = cur.fetchone()
    if row:
        cache[name] = row[0]
        return row[0]
    sid = str(uuid.uuid4())
    cur.execute(
        "INSERT INTO subjects (id, name, slug) VALUES (%s, %s, %s) ON CONFLICT (slug) DO UPDATE SET name=EXCLUDED.name RETURNING id",
        (sid, name, slug)
    )
    row = cur.fetchone()
    cache[name] = row[0] if row else sid
    return cache[name]


def load_to_db(courses: list[dict]) -> dict:
    conn = psycopg2.connect(host="127.0.0.1", port=5432, dbname="opencourseware", user="ocw", password="ocwpassword")
    cur = conn.cursor()

    university_id = get_or_create_university(cur)
    conn.commit()

    cur.execute("SELECT source_url FROM courses WHERE university_id = %s", (university_id,))
    existing = {r[0] for r in cur.fetchall()}
    print(f"Existing Harvard courses in DB: {len(existing)}", flush=True)

    created = skipped = 0
    subject_cache: dict[str, str] = {}

    for c in courses:
        if c["source_url"] in existing:
            skipped += 1
            continue

        course_id = str(uuid.uuid4())
        slug = slugify(f"harvard {c['slug_id']}")

        try:
            cur.execute(
                """INSERT INTO courses (
                    id, university_id, title, slug, source_key, source_url,
                    description, level, has_video_lectures
                ) VALUES (%s, %s, %s, %s, 'harvard', %s, %s, 'undergraduate', true)
                ON CONFLICT (slug) DO NOTHING""",
                (course_id, university_id, c["title"], slug, c["source_url"], c["description"] or "")
            )

            for subj_name in c["subjects"]:
                subj_id = get_or_create_subject(cur, subj_name, subject_cache)
                cur.execute(
                    "INSERT INTO course_subjects (id, course_id, subject_id) VALUES (%s, %s, %s) ON CONFLICT DO NOTHING",
                    (str(uuid.uuid4()), course_id, subj_id)
                )

            existing.add(c["source_url"])
            created += 1
        except Exception as e:
            conn.rollback()
            print(f"  Error inserting {c['title']!r}: {e}", flush=True)
            continue

        if created % 25 == 0:
            conn.commit()
            print(f"  Inserted {created}...", flush=True)

    conn.commit()
    cur.close()
    conn.close()
    return {"created": created, "skipped": skipped}


if __name__ == "__main__":
    print("Scraping Harvard free courses...", flush=True)
    courses = scrape_all_pages()
    stats = load_to_db(courses)
    print(f"\nDone! Created: {stats['created']}, Skipped: {stats['skipped']}")
