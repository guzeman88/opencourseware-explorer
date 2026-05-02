#!/usr/bin/env python
"""load_comprehensive6.py — UPenn, Duke, UMich, UCSD"""
from __future__ import annotations
import uuid
import psycopg2
from slugify import slugify

DB = dict(host="127.0.0.1", port=5432, dbname="opencourseware", user="ocw", password="ocwpassword")

CATALOGUE = {
    "upenn": {
        "name": "University of Pennsylvania", "slug": "upenn",
        "website": "https://www.upenn.edu", "country": "US",
        "description": "University of Pennsylvania open courses available via Coursera and Penn OpenCourseWare.",
        "courses": [
            ("An Introduction to American Law", "Law", "Various", "https://www.coursera.org/learn/american-law", "undergraduate", ["Law"]),
            ("Constitutional Law", "Law", "Kermit Roosevelt", "https://www.coursera.org/learn/constitutional-law", "undergraduate", ["Law", "Political Science"]),
            ("Introduction to Marketing", "Business", "Various", "https://www.coursera.org/learn/wharton-marketing", "undergraduate", ["Business", "Marketing"]),
            ("Introduction to Financial Accounting", "Business", "Various", "https://www.coursera.org/learn/wharton-accounting", "undergraduate", ["Business", "Accounting"]),
            ("Introduction to Corporate Finance", "Finance", "Various", "https://www.coursera.org/learn/wharton-finance", "undergraduate", ["Finance", "Business"]),
            ("Introduction to Operations Management", "Business", "Various", "https://www.coursera.org/learn/wharton-operations", "undergraduate", ["Business", "Management"]),
            ("Foundations of Finance", "Finance", "Various", "https://www.coursera.org/learn/finance-fundamentals", "undergraduate", ["Finance"]),
            ("Business Analytics", "Business", "Various", "https://www.coursera.org/learn/wharton-customer-analytics", "undergraduate", ["Business", "Data Science"]),
            ("Calculus: Single Variable", "Mathematics", "Robert Ghrist", "https://www.coursera.org/learn/single-variable-calculus", "undergraduate", ["Mathematics", "Calculus"]),
            ("Calculus: Single Variable Part 2 — Differentiation", "Mathematics", "Robert Ghrist", "https://www.coursera.org/learn/differentiation-calculus", "undergraduate", ["Mathematics", "Calculus"]),
            ("Calculus: Single Variable Part 3 — Integration", "Mathematics", "Robert Ghrist", "https://www.coursera.org/learn/integration-calculus", "undergraduate", ["Mathematics", "Calculus"]),
            ("Calculus: Single Variable Part 4 — Applications", "Mathematics", "Robert Ghrist", "https://www.coursera.org/learn/applications-calculus", "undergraduate", ["Mathematics", "Calculus"]),
            ("Introduction to Genomic Technologies", "Biomedical Engineering", "Various", "https://www.coursera.org/learn/introduction-genomics", "undergraduate", ["Biology", "Genomics"]),
            ("Genomic Data Science and Clustering", "Biomedical Engineering", "Various", "https://www.coursera.org/learn/genomic-data", "graduate", ["Biology", "Data Science"]),
            ("A Crash Course in Data Science", "Statistics", "Various", "https://www.coursera.org/learn/data-science-crash-course", "undergraduate", ["Data Science"]),
            ("Python for Everybody", "Computer Science", "Various", "https://www.coursera.org/learn/python-programming-introduction", "undergraduate", ["Computer Science", "Python"]),
            ("Introduction to Psychology", "Psychology", "Paul Bloom", "https://www.coursera.org/learn/introduction-psych", "undergraduate", ["Psychology"]),
            ("Moralities of Everyday Life", "Psychology", "Paul Bloom", "https://www.coursera.org/learn/moralities", "undergraduate", ["Psychology", "Ethics"]),
            ("Social Norms, Social Change I", "Sociology", "Various", "https://www.coursera.org/learn/change", "undergraduate", ["Sociology", "Social Science"]),
            ("Healthcare Innovation and Entrepreneurship", "Medicine", "Various", "https://www.coursera.org/learn/healthcare-innovation", "professional", ["Medicine", "Business"]),
            ("Introduction to Intellectual Property", "Law", "Various", "https://www.coursera.org/learn/intellectual-property", "undergraduate", ["Law"]),
            ("Ancient Philosophy: Plato & His Predecessors", "Philosophy", "Various", "https://www.coursera.org/learn/plato", "undergraduate", ["Philosophy"]),
            ("Ancient Philosophy: Aristotle and His Successors", "Philosophy", "Various", "https://www.coursera.org/learn/aristotle", "undergraduate", ["Philosophy"]),
            ("A Brief History of Humankind", "History", "Various", "https://www.coursera.org/learn/human-history", "undergraduate", ["History"]),
            ("The Holocaust — An Introduction I: Nazi Germany", "History", "Various", "https://www.coursera.org/learn/holocaust-introduction-i", "undergraduate", ["History"]),
            ("Fiction of Relationship", "English", "Various", "https://www.coursera.org/learn/literary-analysis", "undergraduate", ["Literature", "English"]),
            ("Introduction to Architecture and Design Thinking", "Architecture", "Various", "https://www.coursera.org/learn/architecture-design-thinking", "undergraduate", ["Architecture", "Design"]),
            ("Fundamentals of Quantitative Modeling", "Statistics", "Various", "https://www.coursera.org/learn/wharton-quantitative-modeling", "undergraduate", ["Statistics", "Mathematics"]),
            ("Introduction to Spreadsheets and Models", "Business", "Various", "https://www.coursera.org/learn/wharton-introduction-spreadsheets-models", "undergraduate", ["Business", "Data Science"]),
            ("Epidemiology: The Basic Science of Public Health", "Public Health", "Various", "https://www.coursera.org/learn/epidemiology", "undergraduate", ["Epidemiology", "Public Health"]),
        ]
    },
    "duke": {
        "name": "Duke University", "slug": "duke",
        "website": "https://www.duke.edu", "country": "US",
        "description": "Duke University open courses available via Coursera and Duke online platforms.",
        "courses": [
            ("Data Science Math Skills", "Mathematics", "Various", "https://www.coursera.org/learn/datasciencemathskills", "undergraduate", ["Mathematics", "Data Science"]),
            ("Introduction to Probability and Data", "Statistics", "Mine Cetinkaya-Rundel", "https://www.coursera.org/learn/probability-intro", "undergraduate", ["Statistics", "Probability"]),
            ("Inferential Statistics", "Statistics", "Mine Cetinkaya-Rundel", "https://www.coursera.org/learn/inferential-statistics-intro", "undergraduate", ["Statistics"]),
            ("Linear Regression and Modeling", "Statistics", "Mine Cetinkaya-Rundel", "https://www.coursera.org/learn/linear-regression-model", "undergraduate", ["Statistics", "Machine Learning"]),
            ("Bayesian Statistics", "Statistics", "Various", "https://www.coursera.org/learn/bayesian", "undergraduate", ["Statistics", "Bayesian Statistics"]),
            ("Introduction to Logic and Critical Thinking", "Philosophy", "Walter Sinnott-Armstrong", "https://www.coursera.org/learn/think-again-how-to-reason-and-argue", "undergraduate", ["Philosophy", "Logic"]),
            ("Think Again I: How to Understand Arguments", "Philosophy", "Walter Sinnott-Armstrong", "https://www.coursera.org/learn/understanding-arguments", "undergraduate", ["Philosophy", "Logic"]),
            ("Introduction to Genetics and Evolution", "Biology", "Mohamed Noor", "https://www.coursera.org/learn/genetics-evolution", "undergraduate", ["Biology", "Genetics"]),
            ("Introduction to Biology: DNA to Organisms", "Biology", "Various", "https://www.coursera.org/learn/biology-dna", "undergraduate", ["Biology", "Molecular Biology"]),
            ("Genome Sequencing", "Biology", "Various", "https://www.coursera.org/learn/genome-sequencing", "graduate", ["Biology", "Genomics"]),
            ("Biology Meets Programming: Bioinformatics for Beginners", "Computer Science", "Various", "https://www.coursera.org/learn/bioinformatics", "undergraduate", ["Bioinformatics", "Computer Science"]),
            ("Python for Genomic Data Science", "Computer Science", "Various", "https://www.coursera.org/learn/python-genomics", "undergraduate", ["Computer Science", "Biology"]),
            ("Introduction to Python Programming", "Computer Science", "Various", "https://www.coursera.org/learn/python-programming-duke", "undergraduate", ["Computer Science", "Python"]),
            ("Java Programming: Solving Problems with Software", "Computer Science", "Various", "https://www.coursera.org/learn/java-programming", "undergraduate", ["Computer Science", "Java"]),
            ("Java Programming: Arrays, Lists, and Structured Data", "Computer Science", "Various", "https://www.coursera.org/learn/java-programming-arrays-lists-data", "undergraduate", ["Computer Science", "Java"]),
            ("Programming Foundations with JavaScript, HTML and CSS", "Computer Science", "Various", "https://www.coursera.org/learn/duke-programming-web", "undergraduate", ["Computer Science", "Web Development"]),
            ("Algorithms, Part I", "Computer Science", "Kevin Wayne", "https://www.coursera.org/learn/algorithms-part1-duke", "undergraduate", ["Computer Science", "Algorithms"]),
            ("Business Foundations", "Business", "Various", "https://www.coursera.org/learn/wharton-operations-duke", "undergraduate", ["Business"]),
            ("Healthcare Trends for Business Professionals", "Medicine", "Various", "https://www.coursera.org/learn/healthcare-trends", "professional", ["Medicine", "Business"]),
            ("English Composition I", "English", "Denise Comer", "https://www.coursera.org/learn/english-composition", "undergraduate", ["Writing", "English"]),
            ("Greek and Roman Mythology", "Classical Studies", "Peter Struck", "https://www.coursera.org/learn/mythology", "undergraduate", ["History", "Literature"]),
            ("History of Rock, Part One", "Music", "John Covach", "https://www.coursera.org/learn/history-of-rock", "undergraduate", ["Music", "History"]),
            ("Music Theory", "Music", "Various", "https://www.coursera.org/learn/musictheory-duke", "undergraduate", ["Music"]),
            ("Introduction to Finance: The Basics", "Finance", "Various", "https://www.coursera.org/learn/intro-finance-duke", "undergraduate", ["Finance"]),
            ("Financial Engineering and Risk Management I", "Finance", "Various", "https://www.coursera.org/learn/financial-engineering", "graduate", ["Finance", "Mathematics"]),
            ("Neuroscience and Neuroimaging", "Neuroscience", "Scott Huettel", "https://www.coursera.org/learn/neuroscience-neuroimaging", "graduate", ["Neuroscience", "Biology"]),
        ]
    },
    "umich": {
        "name": "University of Michigan", "slug": "umich",
        "website": "https://www.umich.edu", "country": "US",
        "description": "University of Michigan open courses and resources via Coursera and CAEN.",
        "courses": [
            ("Programming for Everybody (Getting Started with Python)", "Computer Science", "Charles Severance", "https://www.coursera.org/learn/python", "undergraduate", ["Computer Science", "Python"]),
            ("Python Data Structures", "Computer Science", "Charles Severance", "https://www.coursera.org/learn/python-data", "undergraduate", ["Computer Science", "Python"]),
            ("Using Python to Access Web Data", "Computer Science", "Charles Severance", "https://www.coursera.org/learn/python-network-data", "undergraduate", ["Computer Science", "Python"]),
            ("Using Databases with Python", "Computer Science", "Charles Severance", "https://www.coursera.org/learn/python-databases", "undergraduate", ["Computer Science", "Databases"]),
            ("Capstone: Retrieving, Processing, and Visualizing Data with Python", "Computer Science", "Charles Severance", "https://www.coursera.org/learn/python-data-visualization", "undergraduate", ["Computer Science", "Data Science"]),
            ("Introduction to Data Science in Python", "Data Science", "Christopher Brooks", "https://www.coursera.org/learn/python-data-analysis", "undergraduate", ["Data Science", "Python"]),
            ("Applied Plotting, Charting & Data Representation in Python", "Data Science", "Christopher Brooks", "https://www.coursera.org/learn/python-plotting", "undergraduate", ["Data Science", "Python"]),
            ("Applied Machine Learning in Python", "Machine Learning", "Kevyn Collins-Thompson", "https://www.coursera.org/learn/python-machine-learning", "undergraduate", ["Machine Learning", "Python"]),
            ("Applied Text Mining in Python", "Data Science", "V.G. Vinod Vydiswaran", "https://www.coursera.org/learn/python-text-mining", "undergraduate", ["Natural Language Processing", "Python"]),
            ("Applied Social Network Analysis in Python", "Data Science", "Daniel Romero", "https://www.coursera.org/learn/python-social-networks", "undergraduate", ["Data Science", "Python"]),
            ("Web Design for Everybody: Basics of Web Development & Coding", "Computer Science", "Colleen van Lent", "https://www.coursera.org/learn/html", "undergraduate", ["Web Development", "Computer Science"]),
            ("Introduction to HTML5", "Computer Science", "Colleen van Lent", "https://www.coursera.org/learn/html-umich", "undergraduate", ["Web Development", "HTML"]),
            ("Introduction to CSS3", "Computer Science", "Colleen van Lent", "https://www.coursera.org/learn/introcss", "undergraduate", ["Web Development", "CSS"]),
            ("Interactivity with JavaScript", "Computer Science", "Colleen van Lent", "https://www.coursera.org/learn/javascript-umich", "undergraduate", ["Web Development", "JavaScript"]),
            ("Advanced Styling with Responsive Design", "Computer Science", "Colleen van Lent", "https://www.coursera.org/learn/responsivedesign", "undergraduate", ["Web Development", "CSS"]),
            ("Model Thinking", "Social Science", "Scott Page", "https://www.coursera.org/learn/model-thinking", "undergraduate", ["Social Science", "Mathematics"]),
            ("Introduction to Finance", "Finance", "Gautam Kaul", "https://www.coursera.org/learn/finance-umich", "undergraduate", ["Finance"]),
            ("Financial Accounting Fundamentals", "Business", "Various", "https://www.coursera.org/learn/financial-accounting-basics", "undergraduate", ["Business", "Accounting"]),
            ("Understanding Medical Research", "Medicine", "Various", "https://www.coursera.org/learn/understanding-medical-research", "professional", ["Medicine", "Research Methods"]),
            ("Drug Discovery", "Pharmacy", "Various", "https://www.coursera.org/learn/drug-discovery", "graduate", ["Medicine", "Chemistry"]),
            ("Introduction to Genetics and Evolution", "Biology", "Various", "https://www.coursera.org/learn/genetics-evolution-umich", "undergraduate", ["Biology", "Genetics"]),
            ("Introduction to Psychology as a Science", "Psychology", "Various", "https://www.coursera.org/learn/psychology-science", "undergraduate", ["Psychology"]),
            ("De-Mystifying Mindfulness", "Psychology", "Various", "https://www.coursera.org/learn/mindfulness", "undergraduate", ["Psychology", "Health"]),
            ("The Science of Well-Being", "Psychology", "Laurie Santos", "https://www.coursera.org/learn/the-science-of-well-being-umich", "undergraduate", ["Psychology"]),
            ("Everyday Chinese Medicine", "Medicine", "Various", "https://www.coursera.org/learn/everyday-chinese-medicine", "professional", ["Medicine", "Health"]),
            ("Teach English Now! Foundational Principles", "Education", "Various", "https://www.coursera.org/learn/teach-english", "professional", ["Education"]),
            ("Surviving Disruptive Technologies", "Business", "Various", "https://www.coursera.org/learn/surviving-disruptive-technologies", "professional", ["Business", "Technology"]),
            ("Introduction to Classical Music", "Music", "Craig Wright", "https://www.coursera.org/learn/introclassicalmusic", "undergraduate", ["Music"]),
            ("Social Psychology", "Psychology", "Scott Plous", "https://www.coursera.org/learn/social-psychology-umich", "undergraduate", ["Psychology", "Social Science"]),
            ("Understanding Einstein: The Special Theory of Relativity", "Physics", "Larry Randles Lagerstrom", "https://www.coursera.org/learn/einstein-relativity-umich", "undergraduate", ["Physics", "Relativity"]),
            ("Introduction to Thermodynamics", "Engineering", "Various", "https://www.coursera.org/learn/thermodynamics-umich", "undergraduate", ["Engineering", "Physics"]),
            ("Algorithms, Part I", "Computer Science", "Various", "https://www.coursera.org/learn/algorithms-umich", "undergraduate", ["Computer Science", "Algorithms"]),
            ("Introduction to Human Language and Technology", "Linguistics", "Various", "https://www.coursera.org/learn/human-language-technology", "undergraduate", ["Linguistics", "Computer Science"]),
        ]
    },
    "ucsd": {
        "name": "University of California, San Diego", "slug": "ucsd",
        "website": "https://www.ucsd.edu", "country": "US",
        "description": "UC San Diego open courses available via Coursera and edX.",
        "courses": [
            ("Computational Neuroscience", "Cognitive Science", "Various", "https://www.coursera.org/learn/computational-neuroscience", "graduate", ["Neuroscience", "Computer Science"]),
            ("Bioinformatics Algorithms I", "Bioinformatics", "Pavel Pevzner", "https://www.coursera.org/learn/bioinformatics", "undergraduate", ["Bioinformatics", "Computer Science"]),
            ("Bioinformatics Algorithms II", "Bioinformatics", "Pavel Pevzner", "https://www.coursera.org/learn/bioinformatics-2", "undergraduate", ["Bioinformatics", "Computer Science"]),
            ("Learning How to Learn", "Psychology", "Barbara Oakley", "https://www.coursera.org/learn/learning-how-to-learn", "undergraduate", ["Psychology", "Education"]),
            ("Mindshift: Break Through Obstacles", "Psychology", "Barbara Oakley", "https://www.coursera.org/learn/mindshift", "undergraduate", ["Psychology", "Education"]),
            ("Algorithmic Toolbox", "Computer Science", "Various", "https://www.coursera.org/learn/algorithmic-toolbox", "undergraduate", ["Computer Science", "Algorithms"]),
            ("Data Structures", "Computer Science", "Various", "https://www.coursera.org/learn/data-structures-ucsd", "undergraduate", ["Computer Science", "Data Structures"]),
            ("Algorithms on Graphs", "Computer Science", "Various", "https://www.coursera.org/learn/algorithms-on-graphs", "undergraduate", ["Computer Science", "Algorithms"]),
            ("Algorithms on Strings", "Computer Science", "Various", "https://www.coursera.org/learn/algorithms-on-strings", "undergraduate", ["Computer Science", "Algorithms"]),
            ("Advanced Algorithms and Complexity", "Computer Science", "Various", "https://www.coursera.org/learn/advanced-algorithms-and-complexity", "graduate", ["Computer Science", "Algorithms"]),
            ("Object-Oriented Java Programming", "Computer Science", "Various", "https://www.coursera.org/learn/object-oriented-java", "undergraduate", ["Computer Science", "Java"]),
            ("Data Structures and Performance", "Computer Science", "Various", "https://www.coursera.org/learn/data-structures-optimizing-performance", "undergraduate", ["Computer Science", "Data Structures"]),
            ("Introduction to Machine Learning", "Computer Science", "Various", "https://www.coursera.org/learn/machine-learning-ucsd", "undergraduate", ["Machine Learning", "Computer Science"]),
            ("Big Data: Statistical Inference and Machine Learning", "Data Science", "Various", "https://www.coursera.org/learn/big-data-machine-learning", "graduate", ["Data Science", "Machine Learning"]),
            ("Ethical Hacking", "Computer Science", "Various", "https://www.coursera.org/learn/ethical-hacking-ucsd", "undergraduate", ["Cybersecurity", "Computer Science"]),
            ("Introduction to Statistics", "Mathematics", "Various", "https://www.coursera.org/learn/stanford-statistics-ucsd", "undergraduate", ["Statistics"]),
            ("Everyday Excel", "Computer Science", "Charlie Nuttelman", "https://www.coursera.org/learn/everyday-excel-part1", "undergraduate", ["Computer Science", "Data Science"]),
            ("Buddhism and Modern Psychology", "Psychology", "Robert Wright", "https://www.coursera.org/learn/science-of-meditation", "undergraduate", ["Psychology", "Religion"]),
            ("Healing with the Arts", "Medicine", "Various", "https://www.coursera.org/learn/healing-with-the-arts", "professional", ["Medicine", "Arts"]),
            ("Design Thinking for Innovation", "Engineering", "Various", "https://www.coursera.org/learn/design-thinking-innovation-ucsd", "professional", ["Engineering", "Design"]),
            ("Introduction to Astronomy", "Physics", "Various", "https://www.coursera.org/learn/intro-astronomy-ucsd", "undergraduate", ["Astronomy", "Physics"]),
            ("The Human Brain", "Neuroscience", "Various", "https://www.coursera.org/learn/human-brain", "undergraduate", ["Neuroscience", "Biology"]),
            ("Introduction to Linguistics", "Linguistics", "Various", "https://www.coursera.org/learn/linguistics-ucsd", "undergraduate", ["Linguistics"]),
            ("Global Warming I: The Science and Modeling", "Environmental Science", "Various", "https://www.coursera.org/learn/global-warming", "undergraduate", ["Environmental Science", "Climate Science"]),
            ("Microeconomics: The Power of Markets", "Economics", "Various", "https://www.coursera.org/learn/microeconomics-ucsd", "undergraduate", ["Economics"]),
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
