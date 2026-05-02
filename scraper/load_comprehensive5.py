#!/usr/bin/env python
"""load_comprehensive5.py — Saylor Academy, Caltech"""
from __future__ import annotations
import uuid
import psycopg2
from slugify import slugify

DB = dict(host="127.0.0.1", port=5432, dbname="opencourseware", user="ocw", password="ocwpassword")

CATALOGUE = {
    "saylor": {
        "name": "Saylor Academy", "slug": "saylor",
        "website": "https://learn.saylor.org", "country": "US",
        "description": "Saylor Academy offers free and open online courses leading to college credit.",
        "courses": [
            # Computer Science
            ("Introduction to Computer Science I", "Computer Science", "Various", "https://learn.saylor.org/course/cs101", "undergraduate", ["Computer Science", "Programming"]),
            ("Introduction to Computer Science II", "Computer Science", "Various", "https://learn.saylor.org/course/cs102", "undergraduate", ["Computer Science", "Programming"]),
            ("Introduction to Computer Science Using Python", "Computer Science", "Various", "https://learn.saylor.org/course/cs1", "undergraduate", ["Computer Science", "Python"]),
            ("Elementary Data Structures", "Computer Science", "Various", "https://learn.saylor.org/course/cs201", "undergraduate", ["Computer Science", "Data Structures"]),
            ("Data Structures", "Computer Science", "Various", "https://learn.saylor.org/course/cs202", "undergraduate", ["Computer Science", "Algorithms"]),
            ("Introduction to Algorithms", "Computer Science", "Various", "https://learn.saylor.org/course/cs301", "undergraduate", ["Computer Science", "Algorithms"]),
            ("Computability and Complexity", "Computer Science", "Various", "https://learn.saylor.org/course/cs302", "undergraduate", ["Computer Science", "Theory of Computing"]),
            ("Design of Algorithms", "Computer Science", "Various", "https://learn.saylor.org/course/cs303", "undergraduate", ["Computer Science", "Algorithms"]),
            ("Programming Languages", "Computer Science", "Various", "https://learn.saylor.org/course/cs304", "undergraduate", ["Computer Science", "Programming Languages"]),
            ("Object-Oriented Programming", "Computer Science", "Various", "https://learn.saylor.org/course/cs101b", "undergraduate", ["Computer Science", "Object-Oriented Programming"]),
            ("Software Engineering", "Computer Science", "Various", "https://learn.saylor.org/course/cs302b", "undergraduate", ["Software Engineering", "Computer Science"]),
            ("Databases", "Computer Science", "Various", "https://learn.saylor.org/course/cs403", "undergraduate", ["Computer Science", "Databases"]),
            ("Operating Systems", "Computer Science", "Various", "https://learn.saylor.org/course/cs401", "undergraduate", ["Computer Science", "Operating Systems"]),
            ("Computer Architecture", "Computer Science", "Various", "https://learn.saylor.org/course/cs302c", "undergraduate", ["Computer Science", "Computer Architecture"]),
            ("Computer Networks", "Computer Science", "Various", "https://learn.saylor.org/course/cs402", "undergraduate", ["Computer Science", "Networking"]),
            ("Artificial Intelligence", "Computer Science", "Various", "https://learn.saylor.org/course/cs405", "undergraduate", ["Artificial Intelligence", "Computer Science"]),
            ("Machine Learning", "Computer Science", "Various", "https://learn.saylor.org/course/cs404", "graduate", ["Machine Learning", "Computer Science"]),
            ("Introduction to Cryptography", "Computer Science", "Various", "https://learn.saylor.org/course/cs409", "undergraduate", ["Cryptography", "Computer Science"]),
            ("Computer Security", "Computer Science", "Various", "https://learn.saylor.org/course/cs406", "undergraduate", ["Cybersecurity", "Computer Science"]),
            ("Web Development", "Computer Science", "Various", "https://learn.saylor.org/course/cs412", "undergraduate", ["Web Development", "Computer Science"]),
            # Mathematics
            ("Pre-Calculus", "Mathematics", "Various", "https://learn.saylor.org/course/ma001", "high_school", ["Mathematics", "Pre-Calculus"]),
            ("Single-Variable Calculus I", "Mathematics", "Various", "https://learn.saylor.org/course/ma101", "undergraduate", ["Mathematics", "Calculus"]),
            ("Single-Variable Calculus II", "Mathematics", "Various", "https://learn.saylor.org/course/ma102", "undergraduate", ["Mathematics", "Calculus"]),
            ("Multivariable Calculus", "Mathematics", "Various", "https://learn.saylor.org/course/ma103", "undergraduate", ["Mathematics", "Calculus"]),
            ("Linear Algebra", "Mathematics", "Various", "https://learn.saylor.org/course/ma211", "undergraduate", ["Mathematics", "Linear Algebra"]),
            ("Differential Equations", "Mathematics", "Various", "https://learn.saylor.org/course/ma221", "undergraduate", ["Mathematics", "Differential Equations"]),
            ("Introduction to Statistics", "Mathematics", "Various", "https://learn.saylor.org/course/ma121", "undergraduate", ["Statistics", "Mathematics"]),
            ("Introduction to Probability", "Mathematics", "Various", "https://learn.saylor.org/course/ma201", "undergraduate", ["Mathematics", "Probability"]),
            ("Real Analysis", "Mathematics", "Various", "https://learn.saylor.org/course/ma241", "undergraduate", ["Mathematics"]),
            ("Abstract Algebra", "Mathematics", "Various", "https://learn.saylor.org/course/ma231", "undergraduate", ["Mathematics", "Algebra"]),
            ("Discrete Mathematics", "Mathematics", "Various", "https://learn.saylor.org/course/cs202b", "undergraduate", ["Mathematics", "Discrete Mathematics"]),
            ("Number Theory", "Mathematics", "Various", "https://learn.saylor.org/course/ma313", "undergraduate", ["Mathematics", "Number Theory"]),
            # Sciences
            ("Chemistry I: Atoms and Molecules", "Chemistry", "Various", "https://learn.saylor.org/course/chem101", "undergraduate", ["Chemistry"]),
            ("Chemistry II: Reactions and Thermodynamics", "Chemistry", "Various", "https://learn.saylor.org/course/chem102", "undergraduate", ["Chemistry"]),
            ("Organic Chemistry I", "Chemistry", "Various", "https://learn.saylor.org/course/chem103", "undergraduate", ["Chemistry", "Organic Chemistry"]),
            ("Organic Chemistry II", "Chemistry", "Various", "https://learn.saylor.org/course/chem104", "undergraduate", ["Chemistry", "Organic Chemistry"]),
            ("Biology I: Cells", "Biology", "Various", "https://learn.saylor.org/course/bio101", "undergraduate", ["Biology", "Cell Biology"]),
            ("Biology II: Genetics", "Biology", "Various", "https://learn.saylor.org/course/bio102", "undergraduate", ["Biology", "Genetics"]),
            ("Introduction to Molecular and Cellular Biology", "Biology", "Various", "https://learn.saylor.org/course/bio301", "undergraduate", ["Biology", "Molecular Biology"]),
            ("Introduction to Evolutionary Biology", "Biology", "Various", "https://learn.saylor.org/course/bio302", "undergraduate", ["Biology", "Evolution"]),
            ("Physics I", "Physics", "Various", "https://learn.saylor.org/course/phys101", "undergraduate", ["Physics", "Mechanics"]),
            ("Physics II", "Physics", "Various", "https://learn.saylor.org/course/phys102", "undergraduate", ["Physics", "Electromagnetism"]),
            # Economics
            ("Introduction to Microeconomics", "Economics", "Various", "https://learn.saylor.org/course/econ101", "undergraduate", ["Economics", "Microeconomics"]),
            ("Introduction to Macroeconomics", "Economics", "Various", "https://learn.saylor.org/course/econ102", "undergraduate", ["Economics", "Macroeconomics"]),
            ("Intermediate Microeconomics", "Economics", "Various", "https://learn.saylor.org/course/econ201", "undergraduate", ["Economics", "Microeconomics"]),
            ("Intermediate Macroeconomics", "Economics", "Various", "https://learn.saylor.org/course/econ202", "undergraduate", ["Economics", "Macroeconomics"]),
            ("Money and Banking", "Economics", "Various", "https://learn.saylor.org/course/econ302", "undergraduate", ["Economics", "Finance"]),
            ("International Economics", "Economics", "Various", "https://learn.saylor.org/course/econ303", "undergraduate", ["Economics", "International Relations"]),
            ("Development Economics", "Economics", "Various", "https://learn.saylor.org/course/econ304", "undergraduate", ["Economics"]),
            ("Game Theory", "Economics", "Various", "https://learn.saylor.org/course/econ204", "undergraduate", ["Economics", "Mathematics"]),
            # History
            ("World History I: Ancient to Pre-Modern", "History", "Various", "https://learn.saylor.org/course/hist101", "undergraduate", ["History"]),
            ("World History II: Modern", "History", "Various", "https://learn.saylor.org/course/hist102", "undergraduate", ["History"]),
            ("United States History I", "History", "Various", "https://learn.saylor.org/course/hist211", "undergraduate", ["History", "American History"]),
            ("United States History II", "History", "Various", "https://learn.saylor.org/course/hist212", "undergraduate", ["History", "American History"]),
            # Political Science
            ("Introduction to Political Science", "Political Science", "Various", "https://learn.saylor.org/course/polsc101", "undergraduate", ["Political Science"]),
            ("American Government", "Political Science", "Various", "https://learn.saylor.org/course/polsc231", "undergraduate", ["Political Science", "American History"]),
            ("International Relations", "Political Science", "Various", "https://learn.saylor.org/course/polsc211", "undergraduate", ["Political Science", "International Relations"]),
            ("Comparative Politics", "Political Science", "Various", "https://learn.saylor.org/course/polsc221", "undergraduate", ["Political Science"]),
            # English / Writing
            ("English Composition I", "English", "Various", "https://learn.saylor.org/course/engl001", "undergraduate", ["Writing", "English"]),
            ("English Composition II", "English", "Various", "https://learn.saylor.org/course/engl002", "undergraduate", ["Writing", "English"]),
            ("Introduction to Literary Studies", "English", "Various", "https://learn.saylor.org/course/engl101", "undergraduate", ["Literature", "English"]),
            # Business
            ("Introduction to Business", "Business", "Various", "https://learn.saylor.org/course/bus101", "undergraduate", ["Business"]),
            ("Business Ethics", "Business", "Various", "https://learn.saylor.org/course/bus206", "undergraduate", ["Business", "Ethics"]),
            ("Principles of Management", "Business", "Various", "https://learn.saylor.org/course/bus208", "undergraduate", ["Business", "Management"]),
            ("Marketing Principles", "Business", "Various", "https://learn.saylor.org/course/bus203", "undergraduate", ["Business", "Marketing"]),
            ("Accounting I", "Business", "Various", "https://learn.saylor.org/course/bus103", "undergraduate", ["Business", "Accounting"]),
            ("Accounting II", "Business", "Various", "https://learn.saylor.org/course/bus104", "undergraduate", ["Business", "Accounting"]),
            ("Introduction to Finance", "Business", "Various", "https://learn.saylor.org/course/bus202", "undergraduate", ["Finance", "Business"]),
            # Psychology
            ("Introduction to Psychology", "Psychology", "Various", "https://learn.saylor.org/course/psych101", "undergraduate", ["Psychology"]),
            ("Abnormal Psychology", "Psychology", "Various", "https://learn.saylor.org/course/psych205", "undergraduate", ["Psychology"]),
            ("Social Psychology", "Psychology", "Various", "https://learn.saylor.org/course/psych301", "undergraduate", ["Psychology", "Social Science"]),
            ("Developmental Psychology", "Psychology", "Various", "https://learn.saylor.org/course/psych302", "undergraduate", ["Psychology"]),
            # Sociology
            ("Introduction to Sociology", "Sociology", "Various", "https://learn.saylor.org/course/soc101", "undergraduate", ["Sociology"]),
            ("Social Problems", "Sociology", "Various", "https://learn.saylor.org/course/soc201", "undergraduate", ["Sociology", "Social Science"]),
            # Philosophy
            ("Introduction to Philosophy", "Philosophy", "Various", "https://learn.saylor.org/course/phil101", "undergraduate", ["Philosophy"]),
            ("Ethics", "Philosophy", "Various", "https://learn.saylor.org/course/phil102", "undergraduate", ["Philosophy", "Ethics"]),
            ("Logic", "Philosophy", "Various", "https://learn.saylor.org/course/phil103", "undergraduate", ["Philosophy", "Logic"]),
        ]
    },
    "caltech": {
        "name": "California Institute of Technology", "slug": "caltech",
        "website": "https://www.caltech.edu", "country": "US",
        "description": "Caltech courses and lectures available online through various open access platforms.",
        "courses": [
            ("Classical Mechanics", "Physics", "Sean Carroll", "https://www.youtube.com/playlist?list=PLB72416C707D85AB0", "undergraduate", ["Physics", "Classical Mechanics"]),
            ("Quantum Mechanics", "Physics", "Leonard Susskind", "https://www.youtube.com/playlist?list=PL701CD168D02FF56F", "undergraduate", ["Physics", "Quantum Mechanics"]),
            ("Special Relativity and Electrodynamics", "Physics", "Leonard Susskind", "https://www.youtube.com/playlist?list=PLD9DDFBDC338226CA", "undergraduate", ["Physics", "Relativity"]),
            ("General Relativity", "Physics", "Leonard Susskind", "https://www.youtube.com/playlist?list=PLpGHT1n4-mAsxuRxVPv7kj4-dQYoC3VVu", "graduate", ["Physics", "General Relativity"]),
            ("Statistical Mechanics", "Physics", "Leonard Susskind", "https://www.youtube.com/playlist?list=PLB3C8585E4C1D3A8E", "graduate", ["Physics", "Statistical Mechanics"]),
            ("Cosmology", "Physics", "Sean Carroll", "https://www.youtube.com/playlist?list=PLF363D9CBD9A5EFBE", "graduate", ["Physics", "Cosmology"]),
            ("Particle Physics", "Physics", "Leonard Susskind", "https://www.youtube.com/playlist?list=PLB3C8585E4C1D3A8E2", "graduate", ["Physics", "Particle Physics"]),
            ("Introduction to Quantum Entanglement", "Physics", "Leonard Susskind", "https://www.youtube.com/playlist?list=PL718E83E91AD09DBB", "graduate", ["Physics", "Quantum Mechanics"]),
            ("Ma 1abc: Calculus of One and Several Variables", "Mathematics", "Various", "https://www.math.caltech.edu/~2016-17/1term/ma001a/", "undergraduate", ["Mathematics", "Calculus"]),
            ("Ma 2: Differential Equations", "Mathematics", "Various", "https://www.math.caltech.edu/courses/ma002/", "undergraduate", ["Mathematics", "Differential Equations"]),
            ("Ma 3: Introduction to Probability and Statistics", "Mathematics", "Various", "https://www.math.caltech.edu/courses/ma003/", "undergraduate", ["Mathematics", "Probability"]),
            ("Linear Algebra and Differential Equations", "Mathematics", "Various", "https://www.math.caltech.edu/courses/ma108a/", "undergraduate", ["Mathematics", "Linear Algebra"]),
            ("Introduction to Algorithms", "Computer Science", "Various", "https://www.cms.caltech.edu/academics/courses/cs38", "undergraduate", ["Computer Science", "Algorithms"]),
            ("Introduction to Machine Learning", "Computer Science", "Yisong Yue", "https://www.cms.caltech.edu/academics/courses/cs156a", "undergraduate", ["Machine Learning", "Computer Science"]),
            ("Learning Systems", "Computer Science", "Yisong Yue", "https://www.cms.caltech.edu/academics/courses/cs155", "graduate", ["Machine Learning", "Computer Science"]),
            ("Deep Learning", "Computer Science", "Katie Bouman", "https://www.cms.caltech.edu/academics/courses/cs101", "graduate", ["Deep Learning", "Computer Science"]),
            ("Networks", "Computer Science", "Various", "https://www.cms.caltech.edu/academics/courses/cs144", "undergraduate", ["Computer Science", "Networking"]),
            ("Computational Complexity", "Computer Science", "Chris Umans", "https://www.cms.caltech.edu/academics/courses/cs151", "graduate", ["Computer Science", "Theory of Computing"]),
            ("Information Theory", "Electrical Engineering", "Various", "https://ee.caltech.edu/courses/ee126", "graduate", ["Electrical Engineering", "Information Theory"]),
            ("Control and Dynamical Systems", "Mechanical Engineering", "Various", "https://www.cms.caltech.edu/academics/courses/cds110", "graduate", ["Engineering", "Control Theory"]),
            ("Introduction to Astrophysics", "Physics, Mathematics and Astronomy", "Various", "https://pma.caltech.edu/courses/ay1", "undergraduate", ["Physics", "Astronomy"]),
            ("Introduction to Chemical Engineering", "Chemical Engineering", "Various", "https://che.caltech.edu/courses/cheme10", "undergraduate", ["Chemical Engineering"]),
            ("Biochemistry", "Chemistry and Chemical Engineering", "Various", "https://che.caltech.edu/courses/ch4", "undergraduate", ["Biochemistry", "Chemistry"]),
            ("Organic Chemistry", "Chemistry and Chemical Engineering", "Various", "https://che.caltech.edu/courses/ch41", "undergraduate", ["Chemistry", "Organic Chemistry"]),
            ("Physical Chemistry", "Chemistry and Chemical Engineering", "Various", "https://che.caltech.edu/courses/ch21", "undergraduate", ["Chemistry", "Physical Chemistry"]),
            ("Introduction to Geology and Geophysics", "Geological and Planetary Sciences", "Various", "https://gps.caltech.edu/courses/ge1", "undergraduate", ["Earth Science", "Geology"]),
            ("Biology and Biological Engineering", "Biology", "Various", "https://www.bbe.caltech.edu/courses/bi1", "undergraduate", ["Biology"]),
            ("Molecular Biology", "Biology", "Various", "https://www.bbe.caltech.edu/courses/bi114", "undergraduate", ["Biology", "Molecular Biology"]),
        ]
    },
}


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
