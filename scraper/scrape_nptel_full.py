#!/usr/bin/env python
"""
NPTEL full course scraper.

Fetches all 3200+ NPTEL courses from nptel.ac.in/courses HTML listing
and inserts them directly into the PostgreSQL database.

Usage:
    py -3.13 scrape_nptel_full.py
"""
from __future__ import annotations

import re
import sys
import time
import uuid
from io import StringIO

import psycopg2
import psycopg2.extras
import urllib.request
from bs4 import BeautifulSoup
from slugify import slugify

DATABASE_URL = "postgresql://ocw:ocwpassword@127.0.0.1:5432/opencourseware"

NPTEL_COURSES_URL = "https://nptel.ac.in/courses"
NPTEL_BASE = "https://nptel.ac.in"


def fetch_html(url: str) -> str:
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (Educational course aggregator)",
            "Accept": "text/html,application/xhtml+xml",
        }
    )
    resp = urllib.request.urlopen(req, timeout=30)
    return resp.read().decode("utf-8", errors="ignore")


def infer_level(title: str, dept: str) -> str:
    title_lower = title.lower()
    dept_lower = dept.lower()
    if any(w in title_lower for w in ["advanced", "phd", "doctoral"]):
        return "graduate"
    if any(w in title_lower for w in ["introduction", "basic", "fundamentals", "intro to", "beginner"]):
        return "undergraduate"
    return "undergraduate"


def infer_subjects(title: str, dept: str) -> list[str]:
    subjects = []
    dept_map = {
        "Computer Science": ["Computer Science"],
        "Mathematics": ["Mathematics"],
        "Physics": ["Physics"],
        "Chemistry": ["Chemistry"],
        "Electrical Engineering": ["Electrical Engineering"],
        "Mechanical Engineering": ["Mechanical Engineering"],
        "Civil Engineering": ["Civil Engineering"],
        "Chemical Engineering": ["Chemical Engineering"],
        "Management": ["Management", "Business"],
        "Humanities": ["Humanities"],
        "Economics": ["Economics"],
        "Biotechnology": ["Biotechnology", "Biology"],
        "Aerospace": ["Aerospace Engineering"],
        "Ocean Engineering": ["Engineering"],
        "Mining": ["Mining Engineering"],
        "Metallurgy": ["Metallurgy"],
    }
    for key, vals in dept_map.items():
        if key.lower() in dept.lower():
            subjects.extend(vals)
            break
    if not subjects and dept:
        subjects.append(dept)
    return subjects[:2]


def scrape_nptel_courses() -> list[dict]:
    print("Fetching NPTEL courses page...", flush=True)
    html = fetch_html(NPTEL_COURSES_URL)
    soup = BeautifulSoup(html, "html.parser")
    
    courses = []
    seen_urls = set()
    
    for card in soup.select("a[href^='/courses/']"):
        href = card.get("href", "")
        if not re.match(r"^/courses/\d+$", href):
            continue
        if href in seen_urls:
            continue
        seen_urls.add(href)
        
        source_url = f"{NPTEL_BASE}{href}"
        course_id = href.split("/")[-1]
        
        # Extract structured fields
        name_el = card.select_one(".name")
        dept_el = card.select_one(".discipline")
        meta_spans = card.select(".meta-data span")
        
        title = name_el.get_text(strip=True) if name_el else ""
        dept = dept_el.get_text(strip=True) if dept_el else ""
        instructor = meta_spans[0].get_text(strip=True) if len(meta_spans) > 0 else ""
        institution = meta_spans[1].get_text(strip=True) if len(meta_spans) > 1 else "IIT/IISc"
        
        if not title:
            continue
        
        # Clean up "NOC:" prefix
        title = re.sub(r"^NOC:\s*", "", title).strip()
        
        courses.append({
            "title": title,
            "dept": dept,
            "instructor": instructor,
            "institution": institution,
            "source_url": source_url,
            "course_id": course_id,
        })
    
    print(f"Found {len(courses)} NPTEL courses", flush=True)
    return courses


def get_or_create_university(cur) -> str:
    cur.execute("SELECT id FROM universities WHERE source_key = 'nptel'")
    row = cur.fetchone()
    if row:
        return row[0]
    
    uni_id = str(uuid.uuid4())
    cur.execute(
        """INSERT INTO universities (id, name, slug, website, country, source_key, description)
           VALUES (%s, %s, %s, %s, %s, %s, %s)
           ON CONFLICT (slug) DO UPDATE SET name = EXCLUDED.name RETURNING id""",
        (
            uni_id,
            "NPTEL — National Programme on Technology Enhanced Learning",
            "nptel",
            "https://nptel.ac.in",
            "IN",
            "nptel",
            "NPTEL (National Programme on Technology Enhanced Learning) is a project of MHRD, Govt of India, "
            "initiated by seven IITs and IISc. It provides free online courses across engineering, science, "
            "management, and humanities.",
        )
    )
    row = cur.fetchone()
    return row[0] if row else uni_id


def get_or_create_subject(cur, subject_name: str) -> str:
    slug = slugify(subject_name)
    cur.execute("SELECT id FROM subjects WHERE slug = %s", (slug,))
    row = cur.fetchone()
    if row:
        return row[0]
    sid = str(uuid.uuid4())
    cur.execute(
        "INSERT INTO subjects (id, name, slug) VALUES (%s, %s, %s) ON CONFLICT (slug) DO UPDATE SET name = EXCLUDED.name RETURNING id",
        (sid, subject_name, slug)
    )
    row = cur.fetchone()
    return row[0] if row else sid


def load_courses_to_db(courses: list[dict]) -> dict:
    conn = psycopg2.connect(
        host="127.0.0.1", port=5432, dbname="opencourseware",
        user="ocw", password="ocwpassword"
    )
    conn.autocommit = False
    cur = conn.cursor()
    
    university_id = get_or_create_university(cur)
    conn.commit()
    
    # Get existing course URLs for deduplication
    cur.execute("SELECT source_url FROM courses WHERE university_id = %s", (university_id,))
    existing_urls = {row[0] for row in cur.fetchall()}
    print(f"Existing NPTEL courses in DB: {len(existing_urls)}", flush=True)
    
    created = 0
    skipped = 0
    subject_cache: dict[str, str] = {}
    
    for i, c in enumerate(courses):
        if c["source_url"] in existing_urls:
            skipped += 1
            continue
        
        slug = slugify(f"{c['title']} nptel {c['course_id']}")
        course_id = str(uuid.uuid4())
        
        level = infer_level(c["title"], c["dept"])
        subjects = infer_subjects(c["title"], c["dept"])
        if c["dept"] and c["dept"] not in subjects:
            subjects.insert(0, c["dept"])
        subjects = subjects[:3]
        
        description = f"NPTEL course on {c['title']}."
        if c["dept"]:
            description += f" Department: {c['dept']}."
        if c["instructor"]:
            description += f" Instructor: {c['instructor']}."
        if c["institution"]:
            description += f" Institution: {c['institution']}."
        
        try:
            cur.execute(
                """INSERT INTO courses (
                    id, university_id, title, slug, source_key, source_url,
                    description, level, instructor, has_video_lectures
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (slug) DO NOTHING""",
                (
                    course_id, university_id, c["title"], slug, "nptel",
                    c["source_url"], description, level, c["instructor"] or None,
                    True,
                )
            )
            
            # Link subjects
            for subj_name in subjects:
                if not subj_name:
                    continue
                if subj_name not in subject_cache:
                    subject_cache[subj_name] = get_or_create_subject(cur, subj_name)
                subj_id = subject_cache[subj_name]
                cur.execute(
                    "INSERT INTO course_subjects (course_id, subject_id) VALUES (%s, %s) ON CONFLICT DO NOTHING",
                    (course_id, subj_id)
                )
            
            created += 1
            existing_urls.add(c["source_url"])
            
            if created % 100 == 0:
                conn.commit()
                print(f"  Inserted {created} courses so far...", flush=True)
        
        except Exception as e:
            conn.rollback()
            print(f"  Error inserting {c['title']!r}: {e}", flush=True)
    
    conn.commit()
    cur.close()
    conn.close()
    
    return {"created": created, "skipped": skipped}


if __name__ == "__main__":
    courses = scrape_nptel_courses()
    stats = load_courses_to_db(courses)
    print(f"\nDone! Created: {stats['created']}, Skipped (already in DB): {stats['skipped']}")
