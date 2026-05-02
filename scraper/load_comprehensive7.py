#!/usr/bin/env python
"""load_comprehensive7.py — UWashington, Rice, UT Austin, Vanderbilt, UF, Purdue"""
from __future__ import annotations
import uuid
import psycopg2
from slugify import slugify

DB = dict(host="127.0.0.1", port=5432, dbname="opencourseware", user="ocw", password="ocwpassword")

CATALOGUE = {
    "uwashington": {
        "name": "University of Washington", "slug": "uwashington",
        "website": "https://www.washington.edu", "country": "US",
        "description": "University of Washington open courses available via Coursera and edX.",
        "courses": [
            ("Programming Foundations with Python", "Computer Science", "Various", "https://www.coursera.org/learn/python-programming-uw", "undergraduate", ["Computer Science", "Python"]),
            ("Python for Data Science", "Computer Science", "Various", "https://www.edx.org/course/python-for-data-science-uw", "undergraduate", ["Data Science", "Python"]),
            ("Machine Learning Foundations", "Computer Science", "Emily Fox", "https://www.coursera.org/learn/ml-foundations", "undergraduate", ["Machine Learning"]),
            ("Machine Learning: Regression", "Computer Science", "Various", "https://www.coursera.org/learn/ml-regression", "undergraduate", ["Machine Learning", "Statistics"]),
            ("Machine Learning: Classification", "Computer Science", "Various", "https://www.coursera.org/learn/ml-classification", "undergraduate", ["Machine Learning"]),
            ("Machine Learning: Clustering & Retrieval", "Computer Science", "Various", "https://www.coursera.org/learn/ml-clustering-and-retrieval", "undergraduate", ["Machine Learning"]),
            ("Programming Languages, Part A", "Computer Science", "Dan Grossman", "https://www.coursera.org/learn/programming-languages", "undergraduate", ["Computer Science", "Programming Languages"]),
            ("Programming Languages, Part B", "Computer Science", "Dan Grossman", "https://www.coursera.org/learn/programming-languages-part-b", "undergraduate", ["Computer Science", "Programming Languages"]),
            ("Programming Languages, Part C", "Computer Science", "Dan Grossman", "https://www.coursera.org/learn/programming-languages-part-c", "undergraduate", ["Computer Science", "Programming Languages"]),
            ("Introduction to Data Science", "Data Science", "Various", "https://www.coursera.org/learn/data-manipulation", "undergraduate", ["Data Science"]),
            ("Communicating Data Science Results", "Data Science", "Various", "https://www.coursera.org/learn/data-results", "undergraduate", ["Data Science", "Communication"]),
            ("Astrobiology and the Search for Extraterrestrial Life", "Astronomy", "Charles Cockell", "https://www.coursera.org/learn/astrobiology", "undergraduate", ["Astronomy", "Biology"]),
            ("Global Health at the Human-Animal-Ecosystem Interface", "Public Health", "Various", "https://www.coursera.org/learn/global-health-uw", "graduate", ["Public Health", "Global Health"]),
            ("Human Trafficking", "Law", "Various", "https://www.coursera.org/learn/human-trafficking", "professional", ["Law", "Social Science"]),
            ("Introduction to Systematic Review and Meta-Analysis", "Medicine", "Various", "https://www.coursera.org/learn/systematic-review", "graduate", ["Medicine", "Research Methods"]),
            ("Designing, Running, and Analyzing Experiments", "Statistics", "Various", "https://www.coursera.org/learn/designexperiments", "graduate", ["Statistics", "Research Methods"]),
            ("Introduction to Financial Accounting", "Business", "Various", "https://www.edx.org/course/financial-accounting-uw", "undergraduate", ["Business", "Accounting"]),
            ("Disability Inclusion in Education", "Education", "Various", "https://www.coursera.org/learn/disability-inclusion", "professional", ["Education"]),
            ("Introduction to Kubernetes", "Computer Science", "Various", "https://www.edx.org/course/introduction-to-kubernetes", "professional", ["Computer Science", "DevOps"]),
            ("Introduction to Cloud Infrastructure Technologies", "Computer Science", "Various", "https://www.edx.org/course/introduction-to-cloud-infrastructure-technologies", "professional", ["Computer Science", "Cloud Computing"]),
        ]
    },
    "rice": {
        "name": "Rice University", "slug": "rice",
        "website": "https://www.rice.edu", "country": "US",
        "description": "Rice University open courses via Coursera and OpenStax.",
        "courses": [
            ("An Introduction to Interactive Programming in Python I", "Computer Science", "Joe Warren", "https://www.coursera.org/learn/interactive-python-1", "undergraduate", ["Computer Science", "Python"]),
            ("An Introduction to Interactive Programming in Python II", "Computer Science", "Joe Warren", "https://www.coursera.org/learn/interactive-python-2", "undergraduate", ["Computer Science", "Python"]),
            ("Principles of Computing I", "Computer Science", "Various", "https://www.coursera.org/learn/principles-of-computing-1", "undergraduate", ["Computer Science", "Algorithms"]),
            ("Principles of Computing II", "Computer Science", "Various", "https://www.coursera.org/learn/principles-of-computing-2", "undergraduate", ["Computer Science", "Algorithms"]),
            ("Algorithmic Thinking I", "Computer Science", "Various", "https://www.coursera.org/learn/algorithmic-thinking-1", "undergraduate", ["Computer Science", "Algorithms"]),
            ("Algorithmic Thinking II", "Computer Science", "Various", "https://www.coursera.org/learn/algorithmic-thinking-2", "undergraduate", ["Computer Science", "Algorithms"]),
            ("The Fundamentals of Music Theory", "Music", "Various", "https://www.coursera.org/learn/music-theory", "undergraduate", ["Music"]),
            ("Introduction to Classical Music", "Music", "Craig Wright", "https://www.coursera.org/learn/introclassicalmusic-rice", "undergraduate", ["Music", "History"]),
            ("Introduction to Psychology as a Science", "Psychology", "Various", "https://www.coursera.org/learn/psychology-rice", "undergraduate", ["Psychology"]),
            ("Nanotechnology and Nanosensors", "Engineering", "Various", "https://www.coursera.org/learn/nanotechnology1", "graduate", ["Engineering", "Chemistry"]),
            ("A Hands-on Introduction to Engineering Simulations", "Engineering", "Various", "https://www.edx.org/course/hands-on-intro-to-engineering-simulations-rice", "undergraduate", ["Engineering"]),
            ("Mechanics of Materials", "Engineering", "Various", "https://www.edx.org/course/mechanics-of-materials-i-fundamentals", "undergraduate", ["Engineering", "Mechanics"]),
            ("Introduction to Engineering Mechanics", "Engineering", "Various", "https://www.edx.org/course/introduction-to-engineering-mechanics-rice", "undergraduate", ["Engineering", "Mechanics"]),
            ("Introduction to Systematic Review", "Medicine", "Various", "https://www.coursera.org/learn/systematic-review-rice", "graduate", ["Medicine", "Research Methods"]),
            ("Bioinformatics Methods I", "Bioinformatics", "Various", "https://www.coursera.org/learn/bioinformatics-methods-1", "graduate", ["Bioinformatics", "Computer Science"]),
            ("Astronomy: Exploring Time and Space", "Astronomy", "Various", "https://www.coursera.org/learn/astronomy-rice", "undergraduate", ["Astronomy"]),
            ("Introduction to Finance and Accounting", "Finance", "Various", "https://www.coursera.org/learn/finance-accounting-rice", "undergraduate", ["Finance", "Business"]),
            ("Cryptography I", "Computer Science", "Dan Boneh", "https://www.coursera.org/learn/crypto-rice", "graduate", ["Cryptography", "Computer Science"]),
            ("Pre-Calculus", "Mathematics", "Various", "https://www.coursera.org/learn/precalculus-rice", "undergraduate", ["Mathematics"]),
            ("Linear Algebra", "Mathematics", "Various", "https://www.edx.org/course/linear-algebra-rice", "undergraduate", ["Mathematics", "Linear Algebra"]),
        ]
    },
    "ut_austin": {
        "name": "University of Texas at Austin", "slug": "ut-austin",
        "website": "https://www.utexas.edu", "country": "US",
        "description": "University of Texas at Austin open courses via edX and other platforms.",
        "courses": [
            ("Foundations of Data Analysis — Part 1: Statistics Using R", "Statistics", "Various", "https://www.edx.org/course/foundations-data-analysis-part-1-utaustinx-ut-7-10x", "undergraduate", ["Statistics", "Data Science"]),
            ("Foundations of Data Analysis — Part 2: Inferential Statistics", "Statistics", "Various", "https://www.edx.org/course/foundations-data-analysis-part-2-utaustinx-ut-7-20x", "undergraduate", ["Statistics", "Data Science"]),
            ("Linear Algebra — Foundations to Frontiers", "Mathematics", "Robert van de Geijn", "https://www.edx.org/course/linear-algebra-foundations-frontiers-utaustinx-ut-5-02x", "undergraduate", ["Mathematics", "Linear Algebra"]),
            ("Effective Thinking Through Mathematics", "Mathematics", "Various", "https://www.edx.org/course/effective-thinking-through-mathematics", "undergraduate", ["Mathematics"]),
            ("Introduction to Computer Science", "Computer Science", "Various", "https://www.edx.org/course/intro-computer-science-utaustinx-ut-cs1-1x", "undergraduate", ["Computer Science"]),
            ("Introduction to Programming Using Python", "Computer Science", "Various", "https://www.edx.org/course/introduction-programming-using-python-utaustinx-ut-py2-1x", "undergraduate", ["Computer Science", "Python"]),
            ("Introduction to Computer Science Using Java I", "Computer Science", "Various", "https://www.edx.org/course/introduction-to-java-programming", "undergraduate", ["Computer Science", "Java"]),
            ("Ethics in Technology", "Computer Science", "Various", "https://www.edx.org/course/ethics-technology-practice-utaustinx", "undergraduate", ["Ethics", "Technology"]),
            ("Civil Engineering Mechanics I", "Engineering", "Various", "https://www.edx.org/course/civil-engineering-mechanics", "undergraduate", ["Engineering", "Mechanics"]),
            ("Introduction to Environmental Economics", "Economics", "Various", "https://www.edx.org/course/environmental-economics-ut-austin", "undergraduate", ["Economics", "Environmental Science"]),
            ("Introduction to Mathematical Thinking", "Mathematics", "Various", "https://www.edx.org/course/mathematical-thinking-ut-austin", "undergraduate", ["Mathematics"]),
            ("Entrepreneurship I: Laying the Foundation", "Business", "Various", "https://www.edx.org/course/entrepreneurship-ut-austin", "professional", ["Business", "Entrepreneurship"]),
            ("UT.6.10x: Introductory Linear Algebra", "Mathematics", "Various", "https://www.edx.org/course/introductory-linear-algebra", "undergraduate", ["Mathematics", "Linear Algebra"]),
            ("The Science of Everyday Thinking", "Psychology", "Various", "https://www.edx.org/course/the-science-of-everyday-thinking", "undergraduate", ["Psychology"]),
            ("The Science of Nuclear Energy", "Physics", "Various", "https://www.edx.org/course/nuclear-energy-ut-austin", "undergraduate", ["Physics", "Environmental Science"]),
            ("eSports: From Fan to Pro", "Business", "Various", "https://www.edx.org/course/esports-ut-austin", "professional", ["Business"]),
            ("Accounting for Decision-Making", "Business", "Various", "https://www.edx.org/course/accounting-decision-making", "undergraduate", ["Business", "Accounting"]),
            ("Professional Responsibility", "Law", "Various", "https://www.edx.org/course/professional-responsibility-ut-austin", "professional", ["Law"]),
        ]
    },
    "vanderbilt": {
        "name": "Vanderbilt University", "slug": "vanderbilt",
        "website": "https://www.vanderbilt.edu", "country": "US",
        "description": "Vanderbilt University open courses via Coursera.",
        "courses": [
            ("Data Science Foundations Using R", "Data Science", "Various", "https://www.coursera.org/learn/data-scientists-tools", "undergraduate", ["Data Science", "R Programming"]),
            ("R Programming", "Computer Science", "Roger Peng", "https://www.coursera.org/learn/r-programming", "undergraduate", ["Computer Science", "Data Science"]),
            ("Getting and Cleaning Data", "Data Science", "Various", "https://www.coursera.org/learn/data-cleaning", "undergraduate", ["Data Science"]),
            ("Exploratory Data Analysis", "Data Science", "Roger Peng", "https://www.coursera.org/learn/exploratory-data-analysis", "undergraduate", ["Data Science", "Statistics"]),
            ("Reproducible Research", "Data Science", "Roger Peng", "https://www.coursera.org/learn/reproducible-research", "undergraduate", ["Data Science", "Research Methods"]),
            ("Statistical Inference", "Statistics", "Brian Caffo", "https://www.coursera.org/learn/statistical-inference", "undergraduate", ["Statistics"]),
            ("Regression Models", "Statistics", "Brian Caffo", "https://www.coursera.org/learn/regression-models", "undergraduate", ["Statistics", "Machine Learning"]),
            ("Practical Machine Learning", "Machine Learning", "Jeff Leek", "https://www.coursera.org/learn/practical-machine-learning", "undergraduate", ["Machine Learning", "Data Science"]),
            ("Developing Data Products", "Data Science", "Various", "https://www.coursera.org/learn/data-products", "undergraduate", ["Data Science"]),
            ("Introduction to Programming with MATLAB", "Computer Science", "Mike Fitzpatrick", "https://www.coursera.org/learn/matlab", "undergraduate", ["Computer Science", "Programming"]),
            ("Android App Development", "Computer Science", "Jules White", "https://www.coursera.org/learn/android-programming", "undergraduate", ["Computer Science", "Mobile Development"]),
            ("Server-side Development with NodeJS", "Computer Science", "Various", "https://www.coursera.org/learn/server-side-nodejs", "undergraduate", ["Computer Science", "Web Development"]),
            ("Front-End Web UI Frameworks and Tools: Bootstrap 4", "Computer Science", "Various", "https://www.coursera.org/learn/bootstrap-4", "undergraduate", ["Web Development"]),
            ("Front-End JavaScript Frameworks: Angular", "Computer Science", "Various", "https://www.coursera.org/learn/angular", "undergraduate", ["Web Development", "JavaScript"]),
            ("Multiplatform Mobile App Development with React Native", "Computer Science", "Various", "https://www.coursera.org/learn/react-native", "undergraduate", ["Web Development", "Mobile Development"]),
            ("Introduction to Homeland Security and Terrorism", "Political Science", "Various", "https://www.coursera.org/learn/homeland-security", "professional", ["Political Science", "Law"]),
            ("The Law of the European Union", "Law", "Various", "https://www.coursera.org/learn/eu-law", "professional", ["Law"]),
            ("Genetics and Society: A Course for Educators", "Biology", "Various", "https://www.coursera.org/learn/genetics-society", "professional", ["Biology", "Genetics"]),
            ("Principles of fMRI 1", "Neuroscience", "Martin Lindquist", "https://www.coursera.org/learn/functional-mri", "graduate", ["Neuroscience", "Medicine"]),
            ("The New Nordic Diet — from Gastronomy to Health", "Nutrition Science", "Various", "https://www.coursera.org/learn/new-nordic-diet", "professional", ["Nutrition", "Health"]),
        ]
    },
    "uf": {
        "name": "University of Florida", "slug": "uf",
        "website": "https://www.ufl.edu", "country": "US",
        "description": "University of Florida open courses via Coursera and other platforms.",
        "courses": [
            ("Introduction to UX Design", "Computer Science", "Various", "https://www.coursera.org/learn/ux-design-uf", "undergraduate", ["Design", "Computer Science"]),
            ("Java Programming", "Computer Science", "Various", "https://www.coursera.org/learn/java-programming-uf", "undergraduate", ["Computer Science", "Java"]),
            ("Databases and SQL for Data Science", "Computer Science", "Various", "https://www.coursera.org/learn/sql-databases-uf", "undergraduate", ["Computer Science", "Databases"]),
            ("Introduction to Statistics and Data Analysis", "Statistics", "Various", "https://www.coursera.org/learn/statistics-data-analysis-uf", "undergraduate", ["Statistics"]),
            ("Introduction to Social Media Marketing", "Business", "Various", "https://www.coursera.org/learn/social-media-marketing-uf", "professional", ["Business", "Marketing"]),
            ("Digital Marketing Analytics", "Business", "Various", "https://www.coursera.org/learn/digital-marketing-analytics-uf", "professional", ["Business", "Marketing"]),
            ("Sports and Society", "Sociology", "Various", "https://www.coursera.org/learn/sports-society-uf", "undergraduate", ["Sociology", "Sports Science"]),
            ("Journalism, the future, and you!", "Journalism", "Various", "https://www.coursera.org/learn/journalism-uf", "undergraduate", ["Journalism", "Communication"]),
            ("Inspiring and Motivating Individuals", "Business", "Various", "https://www.coursera.org/learn/motivating-individuals", "professional", ["Business", "Leadership"]),
            ("Leading Teams", "Business", "Various", "https://www.coursera.org/learn/leading-teams-uf", "professional", ["Business", "Leadership"]),
            ("Building Your Leadership Skills", "Business", "Various", "https://www.coursera.org/learn/leadership-skills-uf", "professional", ["Business", "Leadership"]),
            ("Introduction to Food and Our Environment", "Nutrition Science", "Various", "https://www.coursera.org/learn/food-environment-uf", "undergraduate", ["Nutrition", "Environmental Science"]),
            ("Everyday Excel Part 1", "Computer Science", "Various", "https://www.coursera.org/learn/everyday-excel-uf", "undergraduate", ["Computer Science"]),
            ("E-Learning Ecologies: Innovative Approaches to Teaching and Learning", "Education", "Various", "https://www.coursera.org/learn/e-learning-ecologies", "professional", ["Education"]),
            ("Florida Water Management", "Environmental Science", "Various", "https://www.coursera.org/learn/florida-water-management", "undergraduate", ["Environmental Science", "Water Resources"]),
            ("Cybersecurity Fundamentals", "Computer Science", "Various", "https://www.coursera.org/learn/cybersecurity-fundamentals-uf", "undergraduate", ["Cybersecurity"]),
            ("Introduction to Healthcare", "Medicine", "Various", "https://www.coursera.org/learn/intro-healthcare-uf", "professional", ["Medicine", "Public Health"]),
            ("Managing the Organization", "Business", "Various", "https://www.coursera.org/learn/managing-organization-uf", "professional", ["Business", "Management"]),
        ]
    },
    "purdue": {
        "name": "Purdue University", "slug": "purdue",
        "website": "https://www.purdue.edu", "country": "US",
        "description": "Purdue University open courses via edX and Coursera.",
        "courses": [
            ("Introduction to Engineering Design", "Engineering", "Various", "https://www.edx.org/course/introduction-engineering-design-purduex-engr0100x", "undergraduate", ["Engineering"]),
            ("Technical Communication", "Engineering", "Various", "https://www.edx.org/course/technical-communication-purdue", "undergraduate", ["Communication", "Engineering"]),
            ("Agriculture and the World We Live In", "Agriculture", "Various", "https://www.edx.org/course/agriculture-world-purduex-ansc1002x", "undergraduate", ["Agriculture"]),
            ("Introduction to Statistics", "Mathematics", "Various", "https://www.edx.org/course/statistics-purdue", "undergraduate", ["Statistics"]),
            ("Accounting Analysis I: The Role of Accounting as an Information System", "Business", "Various", "https://www.edx.org/course/accounting-analysis-i-purdue", "undergraduate", ["Business", "Accounting"]),
            ("Supply Chain and Logistics Fundamentals", "Business", "Various", "https://www.edx.org/course/supply-chain-logistics-purdue", "professional", ["Business", "Logistics"]),
            ("Introduction to Project Management", "Business", "Various", "https://www.edx.org/course/project-management-purdue", "professional", ["Business", "Management"]),
            ("Nanotechnology: A Maker's Course", "Engineering", "Various", "https://www.coursera.org/learn/nanotechnology-purdue", "undergraduate", ["Engineering", "Chemistry"]),
            ("Introduction to Cybersecurity", "Computer Science", "Various", "https://www.edx.org/course/intro-cybersecurity-purdue", "undergraduate", ["Cybersecurity"]),
            ("Global Leadership and Public Policy for the 21st Century", "Political Science", "Various", "https://www.edx.org/course/global-leadership-purdue", "professional", ["Political Science", "Leadership"]),
            ("Data Analysis: Essential Skills", "Data Science", "Various", "https://www.edx.org/course/data-analysis-purdue", "undergraduate", ["Data Science"]),
            ("Introduction to Python for Data Science", "Computer Science", "Various", "https://www.edx.org/course/python-data-science-purdue", "undergraduate", ["Computer Science", "Python"]),
            ("Six Sigma and the Organization: Advanced", "Business", "Various", "https://www.coursera.org/learn/six-sigma-organization-advanced", "professional", ["Business", "Management"]),
            ("Everyday Excel: Part 1", "Computer Science", "Various", "https://www.coursera.org/learn/everyday-excel-purdue", "undergraduate", ["Computer Science"]),
            ("Introduction to Mechanics", "Physics", "Various", "https://www.edx.org/course/introduction-mechanics-purdue", "undergraduate", ["Physics", "Mechanics"]),
            ("Introduction to Thermodynamics", "Engineering", "Various", "https://www.edx.org/course/thermodynamics-purdue", "undergraduate", ["Engineering", "Physics"]),
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
