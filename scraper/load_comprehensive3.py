#!/usr/bin/env python
"""
Third batch: Berkeley (need 42 more) and Yale (need 1 more).
"""
from __future__ import annotations
import uuid
import psycopg2
from slugify import slugify

DB = dict(host="127.0.0.1", port=5432, dbname="opencourseware", user="ocw", password="ocwpassword")

CATALOGUE = {
    "yale": {
        "name": "Yale University", "slug": "yale",
        "website": "https://oyc.yale.edu", "country": "US",
        "description": "Open Yale Courses — free and open access to a selection of undergraduate Yale courses.",
        "courses": [
            ("Listening to Music", "Music", "Craig Wright", "https://oyc.yale.edu/music/musi-112", "undergraduate", ["Music", "Music Theory"]),
            ("Introduction to Theory of Literature", "English", "Paul Fry", "https://oyc.yale.edu/english/engl-300", "undergraduate", ["Literature", "Literary Theory"]),
            ("The American Novel Since 1945", "English", "Amy Hungerford", "https://oyc.yale.edu/english/engl-291", "undergraduate", ["Literature", "American Studies"]),
            ("Modern Poetry", "English", "Langdon Hammer", "https://oyc.yale.edu/english/engl-310", "undergraduate", ["Literature", "Poetry"]),
            ("Milton", "English", "John Rogers", "https://oyc.yale.edu/english/engl-220", "undergraduate", ["Literature", "English"]),
        ]
    },
    "berkeley": {
        "name": "University of California, Berkeley", "slug": "berkeley",
        "website": "https://www.berkeley.edu", "country": "US",
        "description": "UC Berkeley free open courseware and YouTube lecture series.",
        "courses": [
            # Additional upper-division and grad courses
            ("CS 164: Programming Languages and Compilers II", "Electrical Engineering and Computer Science", "Various", "https://inst.eecs.berkeley.edu/~cs164/sp23/", "undergraduate", ["Compilers", "Computer Science"]),
            ("CS 169A: Software Engineering — Extra Section", "Electrical Engineering and Computer Science", "Various", "https://cs169a.github.io/sp23/", "undergraduate", ["Software Engineering"]),
            ("CS 294-162: Trustworthy Machine Learning", "Electrical Engineering and Computer Science", "Various", "https://inst.eecs.berkeley.edu/~cs294-162/", "graduate", ["Machine Learning", "AI Safety"]),
            ("CS 294-177: Decentralized Finance", "Electrical Engineering and Computer Science", "Various", "https://inst.eecs.berkeley.edu/~cs294-177/", "graduate", ["Blockchain", "Finance"]),
            ("CS 294-196: AI in Education", "Electrical Engineering and Computer Science", "Various", "https://inst.eecs.berkeley.edu/~cs294-196/", "graduate", ["Artificial Intelligence", "Education"]),
            ("EE 140: Linear Integrated Circuits", "Electrical Engineering and Computer Science", "Various", "https://inst.eecs.berkeley.edu/~ee140/", "undergraduate", ["Electrical Engineering", "Circuits"]),
            ("EE 142: Integrated Circuits for Communications", "Electrical Engineering and Computer Science", "Various", "https://inst.eecs.berkeley.edu/~ee142/", "undergraduate", ["Electrical Engineering", "Communications"]),
            ("EE 192: Mechatronics Design Lab", "Electrical Engineering and Computer Science", "Various", "https://inst.eecs.berkeley.edu/~ee192/", "undergraduate", ["Mechatronics", "Robotics"]),
            ("EE 227C: Convex Optimization and Approximation", "Electrical Engineering and Computer Science", "Various", "https://inst.eecs.berkeley.edu/~ee227c/", "graduate", ["Optimization", "Mathematics"]),
            ("EE 290T: New Directions in Machine Learning", "Electrical Engineering and Computer Science", "Various", "https://inst.eecs.berkeley.edu/~ee290t/", "graduate", ["Machine Learning"]),
            # Engineering
            ("ME 175: Intermediate Dynamics", "Mechanical Engineering", "Various", "https://me.berkeley.edu/courses/me175", "undergraduate", ["Mechanics", "Mechanical Engineering"]),
            ("ME 185: Introduction to Continuum Mechanics", "Mechanical Engineering", "Various", "https://me.berkeley.edu/courses/me185", "undergraduate", ["Continuum Mechanics", "Mechanical Engineering"]),
            ("ME 200B: Thermodynamics", "Mechanical Engineering", "Various", "https://me.berkeley.edu/courses/me200b", "graduate", ["Thermodynamics", "Mechanical Engineering"]),
            ("ME 231A: Experiential Advanced Control Design", "Mechanical Engineering", "Various", "https://me.berkeley.edu/courses/me231a", "graduate", ["Control Systems", "Mechanical Engineering"]),
            ("ME 232: Advanced Control Systems II", "Mechanical Engineering", "Various", "https://me.berkeley.edu/courses/me232", "graduate", ["Control Systems", "Robotics"]),
            ("CE 192: Engineering Project Management", "Civil Engineering", "Various", "https://ce.berkeley.edu/courses/ce192", "undergraduate", ["Project Management", "Engineering"]),
            ("CE 223: Finite Element Analysis", "Civil Engineering", "Various", "https://ce.berkeley.edu/courses/ce223", "graduate", ["Structural Analysis", "Civil Engineering"]),
            ("CE 263N: Scalable Spatial Analytics", "Civil Engineering", "Various", "https://ce.berkeley.edu/courses/ce263n", "graduate", ["Data Science", "Urban Planning"]),
            ("EECS 16A: Designing Systems and Signals", "Electrical Engineering and Computer Science", "Various", "https://eecs16a.berkeley.edu/sp23/", "undergraduate", ["Electrical Engineering", "Linear Algebra"]),
            ("EECS 151: Introduction to Digital Design and Integrated Circuits", "Electrical Engineering and Computer Science", "Various", "https://eecs151.github.io/", "undergraduate", ["Digital Design", "Computer Architecture"]),
            # Specialized CS and AI
            ("Data 101: Data Engineering", "Data Science", "Various", "https://data101.datahub.berkeley.edu/", "undergraduate", ["Data Engineering", "Data Science"]),
            ("Info 290T: Machine Learning at Scale", "School of Information", "Various", "https://ischool.berkeley.edu/courses/info290t", "graduate", ["Machine Learning", "Big Data"]),
            ("Stats 243: Statistical Computing", "Statistics", "Various", "https://stat.berkeley.edu/courses/stat243", "graduate", ["Statistics", "Computing"]),
            ("Stats 260: Causal Inference", "Statistics", "Various", "https://stat.berkeley.edu/courses/stat260", "graduate", ["Causal Inference", "Statistics"]),
            ("Stats 210B: Theoretical Statistics", "Statistics", "Various", "https://stat.berkeley.edu/courses/stat210b", "graduate", ["Statistics", "Theory"]),
            # Sciences
            ("Physics 221A: Quantum Mechanics", "Physics", "Various", "https://physics.berkeley.edu/courses/phys221a", "graduate", ["Quantum Mechanics", "Physics"]),
            ("Physics 221B: Quantum Mechanics II", "Physics", "Various", "https://physics.berkeley.edu/courses/phys221b", "graduate", ["Quantum Mechanics", "Physics"]),
            ("Physics 232: Advanced Electrodynamics", "Physics", "Various", "https://physics.berkeley.edu/courses/phys232", "graduate", ["Electrodynamics", "Physics"]),
            ("Physics 215A: Quantum Field Theory", "Physics", "Various", "https://physics.berkeley.edu/courses/phys215a", "graduate", ["Quantum Field Theory", "Physics"]),
            ("Chemistry 220B: Physical Organic Chemistry", "Chemistry", "Various", "https://chemistry.berkeley.edu/courses/chem220b", "graduate", ["Organic Chemistry", "Chemistry"]),
            ("Chemistry 240: Physical Chemistry of Solids", "Chemistry", "Various", "https://chemistry.berkeley.edu/courses/chem240", "graduate", ["Physical Chemistry", "Chemistry"]),
            ("Chemistry 130: Bioinorganic Chemistry", "Chemistry", "Various", "https://chemistry.berkeley.edu/courses/chem130", "undergraduate", ["Inorganic Chemistry", "Chemistry"]),
            ("MCB 160: Biochemistry and Molecular Biology of the Cell", "Molecular and Cell Biology", "Various", "https://mcb.berkeley.edu/courses/mcb160", "undergraduate", ["Molecular Biology", "Biology"]),
            ("MCB 165: Molecular Basis of Disease", "Molecular and Cell Biology", "Various", "https://mcb.berkeley.edu/courses/mcb165", "undergraduate", ["Medicine", "Biology"]),
            ("MCB 200: Biochemistry and Molecular Biology", "Molecular and Cell Biology", "Various", "https://mcb.berkeley.edu/courses/mcb200", "graduate", ["Biochemistry", "Biology"]),
            ("IB 168: Evolutionary Genetics", "Integrative Biology", "Various", "https://ib.berkeley.edu/courses/ib168", "undergraduate", ["Genetics", "Evolution"]),
            ("IB 200: Core Concepts in Ecology and Evolution", "Integrative Biology", "Various", "https://ib.berkeley.edu/courses/ib200", "graduate", ["Ecology", "Evolution"]),
            # Economics and Business
            ("Econ 115: Macroeconomic Policies", "Economics", "Various", "https://econ.berkeley.edu/courses/econ115", "undergraduate", ["Macroeconomics", "Public Policy"]),
            ("Econ 136: Financial Economics II", "Economics", "Various", "https://econ.berkeley.edu/courses/econ136-ii", "undergraduate", ["Finance", "Economics"]),
            ("Econ 140: Econometrics", "Economics", "Various", "https://econ.berkeley.edu/courses/econ140", "undergraduate", ["Econometrics", "Statistics"]),
            ("Econ 145: Economics of Technology", "Economics", "Various", "https://econ.berkeley.edu/courses/econ145", "undergraduate", ["Economics", "Technology"]),
            ("Econ 174: Decisions Under Uncertainty", "Economics", "Various", "https://econ.berkeley.edu/courses/econ174", "undergraduate", ["Economics", "Decision Theory"]),
            ("Econ 210A: Microeconomic Theory", "Economics", "Various", "https://econ.berkeley.edu/courses/econ210a", "graduate", ["Microeconomics", "Economics"]),
            ("Econ 270D: Political Economy", "Economics", "Various", "https://econ.berkeley.edu/courses/econ270d", "graduate", ["Political Economy", "Economics"]),
            # Health and Medicine
            ("Public Health 111: Epidemiology of Chronic Diseases", "Public Health", "Various", "https://sph.berkeley.edu/courses/ph111", "undergraduate", ["Epidemiology", "Public Health"]),
            ("Public Health 112: Introduction to Biostatistics", "Public Health", "Various", "https://sph.berkeley.edu/courses/ph112", "undergraduate", ["Biostatistics", "Statistics"]),
            ("Public Health 116: Disease Prevention and Control", "Public Health", "Various", "https://sph.berkeley.edu/courses/ph116", "undergraduate", ["Public Health", "Medicine"]),
            ("Public Health 217: Health and Social Behavior", "Public Health", "Various", "https://sph.berkeley.edu/courses/ph217", "graduate", ["Public Health", "Social Sciences"]),
            ("Public Health 250D: Genomics and Population Health", "Public Health", "Various", "https://sph.berkeley.edu/courses/ph250d", "graduate", ["Genomics", "Epidemiology"]),
        ]
    }
}

# ─── DB helpers ───────────────────────────────────────────────────────────────

def get_conn():
    return psycopg2.connect(**DB)


def upsert_university(cur, key: str, data: dict) -> str:
    cur.execute("SELECT id FROM universities WHERE source_key = %s", (key,))
    row = cur.fetchone()
    if row:
        return row[0]
    uid = str(uuid.uuid4())
    cur.execute(
        """INSERT INTO universities (id, name, slug, website, country, source_key, description)
           VALUES (%s, %s, %s, %s, %s, %s, %s)
           ON CONFLICT (slug) DO UPDATE SET name=EXCLUDED.name RETURNING id""",
        (uid, data["name"], data["slug"], data["website"], data["country"], key, data["description"])
    )
    row = cur.fetchone()
    return row[0] if row else uid


def upsert_subject(cur, name: str, cache: dict) -> str:
    if name in cache:
        return cache[name]
    slug = slugify(name)
    cur.execute("SELECT id FROM subjects WHERE slug=%s", (slug,))
    row = cur.fetchone()
    if row:
        cache[name] = row[0]
        return row[0]
    sid = str(uuid.uuid4())
    cur.execute(
        "INSERT INTO subjects (id, name, slug) VALUES (%s,%s,%s) ON CONFLICT (slug) DO UPDATE SET name=EXCLUDED.name RETURNING id",
        (sid, name, slug)
    )
    row = cur.fetchone()
    cache[name] = row[0] if row else sid
    return cache[name]


def make_slug(title: str, uni_slug: str, seen: set) -> str:
    base = slugify(f"{title} {uni_slug}")
    slug = base
    i = 2
    while slug in seen:
        slug = f"{base}-{i}"
        i += 1
    seen.add(slug)
    return slug


def load_all():
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("SELECT slug FROM courses")
    seen_slugs: set = {r[0] for r in cur.fetchall()}
    cur.execute("SELECT source_url FROM courses")
    seen_urls: set = {r[0] for r in cur.fetchall()}

    subject_cache: dict = {}
    total_created = 0
    total_skipped = 0

    for uni_key, uni_data in CATALOGUE.items():
        print(f"\n→ {uni_data['name']}", flush=True)
        uni_id = upsert_university(cur, uni_key, uni_data)
        conn.commit()

        created = skipped = 0
        for (title, dept, instructor, source_url, level, subjects) in uni_data["courses"]:
            if source_url in seen_urls:
                skipped += 1
                continue

            slug = make_slug(title, uni_data["slug"], seen_slugs)
            course_id = str(uuid.uuid4())
            description = f"{title}. Offered by {uni_data['name']}."
            if dept:
                description += f" Department: {dept}."
            if instructor and instructor != "Various":
                description += f" Instructor: {instructor}."

            try:
                cur.execute(
                    """INSERT INTO courses (
                        id, university_id, title, slug, source_key, source_url,
                        description, level, instructor, has_video_lectures
                    ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                    ON CONFLICT (slug) DO NOTHING""",
                    (course_id, uni_id, title, slug, uni_key, source_url,
                     description, level, instructor if instructor != "Various" else None, True)
                )

                for subj_name in subjects[:3]:
                    if subj_name:
                        subj_id = upsert_subject(cur, subj_name, subject_cache)
                        cur.execute(
                            "INSERT INTO course_subjects (id, course_id, subject_id) VALUES (%s,%s,%s) ON CONFLICT DO NOTHING",
                            (str(uuid.uuid4()), course_id, subj_id)
                        )

                seen_urls.add(source_url)
                created += 1
            except Exception as e:
                conn.rollback()
                print(f"  Error: {title!r}: {e}", flush=True)
                continue

        conn.commit()
        print(f"  Created: {created}, Skipped: {skipped}", flush=True)
        total_created += created
        total_skipped += skipped

    cur.close()
    conn.close()
    print(f"\nTotal — Created: {total_created}, Skipped: {total_skipped}")


if __name__ == "__main__":
    load_all()
