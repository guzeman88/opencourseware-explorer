#!/usr/bin/env python
"""load_comprehensive8.py — Open University UK, Edinburgh, Glasgow, UNSW, Melbourne, ANU"""
from __future__ import annotations
import uuid
import psycopg2
from slugify import slugify

DB = dict(host="127.0.0.1", port=5432, dbname="opencourseware", user="ocw", password="ocwpassword")

CATALOGUE = {
    "open_university_uk": {
        "name": "The Open University", "slug": "open-university-uk",
        "website": "https://www.open.edu/openlearn", "country": "UK",
        "description": "The Open University's OpenLearn platform offers free online courses and resources.",
        "courses": [
            ("Introduction to Cybersecurity", "Computing & IT", "Various", "https://www.open.edu/openlearn/digital-computing/introduction-cybersecurity", "professional", ["Cybersecurity", "Computer Science"]),
            ("Learn to Code for Data Analysis", "Computing & IT", "Various", "https://www.open.edu/openlearn/science-maths-technology/learn-code-data-analysis", "undergraduate", ["Data Science", "Python"]),
            ("Introduction to Artificial Intelligence", "Computing & IT", "Various", "https://www.open.edu/openlearn/digital-computing/introduction-artificial-intelligence", "undergraduate", ["Artificial Intelligence"]),
            ("Data, Design and Society", "Computing & IT", "Various", "https://www.open.edu/openlearn/society/data-design-and-society", "undergraduate", ["Data Science", "Sociology"]),
            ("Getting Started with Python", "Computing & IT", "Various", "https://www.open.edu/openlearn/digital-computing/getting-started-python", "undergraduate", ["Computer Science", "Python"]),
            ("Web Applications: An Introduction", "Computing & IT", "Various", "https://www.open.edu/openlearn/digital-computing/web-applications-introduction", "undergraduate", ["Web Development", "Computer Science"]),
            ("Software Engineering", "Computing & IT", "Various", "https://www.open.edu/openlearn/digital-computing/software-engineering", "undergraduate", ["Software Engineering", "Computer Science"]),
            ("Databases", "Computing & IT", "Various", "https://www.open.edu/openlearn/digital-computing/databases", "undergraduate", ["Computer Science", "Databases"]),
            ("Cryptography", "Computing & IT", "Various", "https://www.open.edu/openlearn/digital-computing/cryptography", "undergraduate", ["Cryptography", "Computer Science"]),
            ("Algorithms, Data Structures and Computability", "Computing & IT", "Various", "https://www.open.edu/openlearn/digital-computing/algorithms-data-structures-and-computability", "undergraduate", ["Computer Science", "Algorithms"]),
            ("Mathematics for Science and Technology", "Science, Maths & Technology", "Various", "https://www.open.edu/openlearn/science-maths-technology/mathematics-science-and-technology", "undergraduate", ["Mathematics"]),
            ("Introduction to Statistics", "Science, Maths & Technology", "Various", "https://www.open.edu/openlearn/science-maths-technology/introduction-statistics", "undergraduate", ["Statistics"]),
            ("Everyday Maths 1", "Science, Maths & Technology", "Various", "https://www.open.edu/openlearn/science-maths-technology/everyday-maths-1", "undergraduate", ["Mathematics"]),
            ("Everyday Maths 2", "Science, Maths & Technology", "Various", "https://www.open.edu/openlearn/science-maths-technology/everyday-maths-2", "undergraduate", ["Mathematics"]),
            ("Introduction to Calculus", "Science, Maths & Technology", "Various", "https://www.open.edu/openlearn/science-maths-technology/introduction-calculus", "undergraduate", ["Mathematics", "Calculus"]),
            ("Introduction to the Theory of Numbers", "Science, Maths & Technology", "Various", "https://www.open.edu/openlearn/science-maths-technology/introduction-theory-numbers", "undergraduate", ["Mathematics", "Number Theory"]),
            ("Discovering Chemistry", "Science, Maths & Technology", "Various", "https://www.open.edu/openlearn/science-maths-technology/discovering-chemistry", "undergraduate", ["Chemistry"]),
            ("Introduction to Biology", "Science, Maths & Technology", "Various", "https://www.open.edu/openlearn/science-maths-technology/introduction-biology", "undergraduate", ["Biology"]),
            ("Ecology and Conservation", "Science, Maths & Technology", "Various", "https://www.open.edu/openlearn/science-maths-technology/ecology-and-conservation", "undergraduate", ["Biology", "Ecology"]),
            ("Climate Change: From Learning to Action", "Science, Maths & Technology", "Various", "https://www.open.edu/openlearn/science-maths-technology/climate-change-learning-action", "undergraduate", ["Environmental Science", "Climate Science"]),
            ("Introduction to Astronomy", "Science, Maths & Technology", "Various", "https://www.open.edu/openlearn/science-maths-technology/introduction-astronomy", "undergraduate", ["Astronomy", "Physics"]),
            ("Introduction to Geology", "Science, Maths & Technology", "Various", "https://www.open.edu/openlearn/science-maths-technology/introduction-geology", "undergraduate", ["Earth Science", "Geology"]),
            ("Introduction to Psychology", "Psychology", "Various", "https://www.open.edu/openlearn/health-wellbeing/introduction-psychology", "undergraduate", ["Psychology"]),
            ("Developmental Psychology", "Psychology", "Various", "https://www.open.edu/openlearn/health-wellbeing/developmental-psychology", "undergraduate", ["Psychology"]),
            ("Introduction to Sociology", "Social Sciences", "Various", "https://www.open.edu/openlearn/society/introduction-sociology", "undergraduate", ["Sociology"]),
            ("Introduction to Economics", "Social Sciences", "Various", "https://www.open.edu/openlearn/society/introduction-economics", "undergraduate", ["Economics"]),
            ("Microeconomics", "Social Sciences", "Various", "https://www.open.edu/openlearn/society/microeconomics", "undergraduate", ["Economics", "Microeconomics"]),
            ("Macroeconomics", "Social Sciences", "Various", "https://www.open.edu/openlearn/society/macroeconomics", "undergraduate", ["Economics", "Macroeconomics"]),
            ("Introduction to Political Science", "Social Sciences", "Various", "https://www.open.edu/openlearn/society/introduction-political-science", "undergraduate", ["Political Science"]),
            ("Introduction to Law", "Law", "Various", "https://www.open.edu/openlearn/society/introduction-law", "undergraduate", ["Law"]),
            ("Introduction to Philosophy", "Humanities", "Various", "https://www.open.edu/openlearn/history-the-arts/introduction-philosophy", "undergraduate", ["Philosophy"]),
            ("Introduction to Ethics", "Humanities", "Various", "https://www.open.edu/openlearn/history-the-arts/introduction-ethics", "undergraduate", ["Philosophy", "Ethics"]),
            ("Introduction to World History", "Humanities", "Various", "https://www.open.edu/openlearn/history-the-arts/introduction-world-history", "undergraduate", ["History"]),
            ("Introduction to Education", "Education", "Various", "https://www.open.edu/openlearn/education-development/introduction-education", "professional", ["Education"]),
            ("Introduction to Business Management", "Business", "Various", "https://www.open.edu/openlearn/money-business/introduction-business-management", "undergraduate", ["Business", "Management"]),
            ("Introduction to Marketing", "Business", "Various", "https://www.open.edu/openlearn/money-business/introduction-marketing", "undergraduate", ["Business", "Marketing"]),
            ("Introduction to Finance", "Business", "Various", "https://www.open.edu/openlearn/money-business/introduction-finance", "undergraduate", ["Finance", "Business"]),
            ("Introduction to Accounting", "Business", "Various", "https://www.open.edu/openlearn/money-business/introduction-accounting", "undergraduate", ["Business", "Accounting"]),
            ("Introduction to Entrepreneurship", "Business", "Various", "https://www.open.edu/openlearn/money-business/introduction-entrepreneurship", "professional", ["Business", "Entrepreneurship"]),
            ("Introduction to Public Health", "Health", "Various", "https://www.open.edu/openlearn/health-wellbeing/introduction-public-health", "undergraduate", ["Public Health"]),
            ("Introduction to Nutrition and Health", "Health", "Various", "https://www.open.edu/openlearn/health-wellbeing/introduction-nutrition-and-health", "undergraduate", ["Nutrition", "Health"]),
            ("Exploring the Night Sky", "Science, Maths & Technology", "Various", "https://www.open.edu/openlearn/science-maths-technology/exploring-the-night-sky", "undergraduate", ["Astronomy"]),
            ("Introduction to Quantum Mechanics", "Science, Maths & Technology", "Various", "https://www.open.edu/openlearn/science-maths-technology/introduction-quantum-mechanics", "undergraduate", ["Physics", "Quantum Mechanics"]),
            ("Advanced Introduction to Machine Learning", "Computing & IT", "Various", "https://www.open.edu/openlearn/digital-computing/advanced-machine-learning", "graduate", ["Machine Learning", "Computer Science"]),
            ("Understanding Language: Learning and Teaching", "Humanities", "Various", "https://www.open.edu/openlearn/languages/understanding-language-learning-and-teaching", "professional", ["Linguistics", "Education"]),
        ]
    },
    "edinburgh": {
        "name": "University of Edinburgh", "slug": "edinburgh",
        "website": "https://www.ed.ac.uk", "country": "UK",
        "description": "University of Edinburgh open courses available via Coursera and FutureLearn.",
        "courses": [
            ("Introduction to Philosophy", "Philosophy", "Various", "https://www.coursera.org/learn/philosophy", "undergraduate", ["Philosophy"]),
            ("Philosophy and the Sciences: Introduction to the Philosophy of Physical Sciences", "Philosophy", "Various", "https://www.coursera.org/learn/philosophy-physical-sciences", "undergraduate", ["Philosophy", "Physics"]),
            ("Philosophy and the Sciences: Introduction to the Philosophy of Cognitive Sciences", "Philosophy", "Various", "https://www.coursera.org/learn/philosophy-cognitive-sciences", "undergraduate", ["Philosophy", "Cognitive Science"]),
            ("Critical Thinking in Global Challenges", "Social Sciences", "Various", "https://www.coursera.org/learn/critical-thinking-global-challenges", "undergraduate", ["Philosophy", "Social Science"]),
            ("Astrobiology and the Search for Extraterrestrial Life", "Astronomy", "Various", "https://www.coursera.org/learn/astrobiology-edinburgh", "undergraduate", ["Astronomy", "Biology"]),
            ("Introduction to Computational Thinking and Data Science", "Computer Science", "Various", "https://www.coursera.org/learn/computational-thinking-data-science-edinburgh", "undergraduate", ["Computer Science", "Data Science"]),
            ("Introduction to Machine Learning", "Computer Science", "Various", "https://www.coursera.org/learn/machine-learning-edinburgh", "undergraduate", ["Machine Learning"]),
            ("Practical Machine Learning on H2O", "Computer Science", "Various", "https://www.coursera.org/learn/machine-learning-h2o", "undergraduate", ["Machine Learning", "Data Science"]),
            ("Introduction to Natural Language Processing", "Computer Science", "Various", "https://www.coursera.org/learn/natural-language-processing-edinburgh", "graduate", ["Natural Language Processing", "Computer Science"]),
            ("Introduction to Systematic Review and Meta-Analysis", "Medicine", "Various", "https://www.coursera.org/learn/systematic-review-edinburgh", "graduate", ["Medicine", "Research Methods"]),
            ("Introduction to Genomic Technologies", "Biology", "Various", "https://www.coursera.org/learn/genomics-edinburgh", "undergraduate", ["Biology", "Genomics"]),
            ("Evolution: A Course for Educators", "Biology", "Various", "https://www.coursera.org/learn/evolution-edinburgh", "professional", ["Biology", "Evolution"]),
            ("Dino 101: Dinosaur Paleobiology", "Earth Sciences", "Various", "https://www.coursera.org/learn/dino101", "undergraduate", ["Earth Science", "Biology"]),
            ("Anatomy: Know Your Abdomen", "Medicine", "Various", "https://www.coursera.org/learn/anatomy-abdomen", "professional", ["Medicine", "Anatomy"]),
            ("Anatomy of the Upper Limb", "Medicine", "Various", "https://www.coursera.org/learn/anatomy-upper-limb", "professional", ["Medicine", "Anatomy"]),
            ("Practical Time Series Analysis", "Statistics", "Various", "https://www.coursera.org/learn/practical-time-series-analysis", "undergraduate", ["Statistics", "Data Science"]),
            ("Survey Data Collection and Analytics", "Statistics", "Various", "https://www.coursera.org/learn/data-collection-analytics-project", "graduate", ["Statistics", "Data Science"]),
            ("Data Science and Machine Learning Boot Camp with R", "Data Science", "Various", "https://www.coursera.org/learn/data-science-bootcamp-r", "undergraduate", ["Data Science", "R Programming"]),
            ("Agile Project Management", "Business", "Various", "https://www.coursera.org/learn/agile-project-management-edinburgh", "professional", ["Business", "Management"]),
            ("Introduction to Business Analytics", "Business", "Various", "https://www.coursera.org/learn/business-analytics-edinburgh", "undergraduate", ["Business", "Data Science"]),
            ("The Psychology of Criminal Justice", "Psychology", "Various", "https://www.futurelearn.com/courses/forensic-psychology-edinburgh", "undergraduate", ["Psychology", "Law"]),
            ("Social Research Methods", "Social Sciences", "Various", "https://www.coursera.org/learn/social-research-methods-edinburgh", "undergraduate", ["Social Science", "Research Methods"]),
            ("Introduction to Environmental Law and Policy", "Law", "Various", "https://www.coursera.org/learn/environmental-law-edinburgh", "undergraduate", ["Law", "Environmental Science"]),
            ("Animal Behaviour and Welfare", "Biology", "Various", "https://www.coursera.org/learn/animal-behaviour-welfare", "undergraduate", ["Biology", "Animal Science"]),
            ("Introduction to Infection Control", "Medicine", "Various", "https://www.futurelearn.com/courses/infection-control-edinburgh", "professional", ["Medicine", "Public Health"]),
            ("Understanding Dementia", "Medicine", "Various", "https://www.futurelearn.com/courses/understanding-dementia", "professional", ["Medicine", "Neuroscience"]),
            ("Sports and Exercise Medicine", "Medicine", "Various", "https://www.futurelearn.com/courses/sports-medicine-edinburgh", "professional", ["Medicine", "Sports Science"]),
            ("Introduction to Quantum Computing", "Computer Science", "Various", "https://www.coursera.org/learn/quantum-computing-edinburgh", "graduate", ["Quantum Computing", "Computer Science"]),
            ("Microwave Engineering and Antennas", "Engineering", "Various", "https://www.coursera.org/learn/microwave-engineering", "graduate", ["Electrical Engineering"]),
            ("Introduction to Machine Learning for Coders", "Computer Science", "Various", "https://www.futurelearn.com/courses/machine-learning-edinburgh", "undergraduate", ["Machine Learning", "Computer Science"]),
        ]
    },
    "glasgow": {
        "name": "University of Glasgow", "slug": "glasgow",
        "website": "https://www.gla.ac.uk", "country": "UK",
        "description": "University of Glasgow open courses via Coursera and FutureLearn.",
        "courses": [
            ("Introduction to the Piano", "Music", "Various", "https://www.coursera.org/learn/intro-piano", "undergraduate", ["Music"]),
            ("Advanced Piano Techniques", "Music", "Various", "https://www.coursera.org/learn/advanced-piano", "undergraduate", ["Music"]),
            ("Introduction to Classical Music", "Music", "Various", "https://www.coursera.org/learn/classical-music-glasgow", "undergraduate", ["Music", "History"]),
            ("Music as Biology", "Music", "Various", "https://www.coursera.org/learn/music-as-biology", "undergraduate", ["Music", "Biology"]),
            ("Introduction to Digital Tools for Social Science Research", "Social Sciences", "Various", "https://www.coursera.org/learn/digital-tools-social-science", "undergraduate", ["Social Science", "Data Science"]),
            ("Introduction to Human Behavioural Genetics", "Biology", "Various", "https://www.coursera.org/learn/behavioural-genetics", "undergraduate", ["Biology", "Genetics"]),
            ("Forensic Science: Witness to Your Own Murder", "Forensic Science", "Various", "https://www.coursera.org/learn/forensic-science", "undergraduate", ["Forensic Science", "Biology"]),
            ("Understanding the Brain: The Neurobiology of Everyday Life", "Neuroscience", "Various", "https://www.coursera.org/learn/neuroscience-glasgow", "undergraduate", ["Neuroscience", "Biology"]),
            ("Cancer Biology", "Medicine", "Various", "https://www.coursera.org/learn/cancer-biology-glasgow", "undergraduate", ["Medicine", "Biology"]),
            ("Liver Disease: Looking after Your Liver", "Medicine", "Various", "https://www.futurelearn.com/courses/liver-disease", "professional", ["Medicine", "Health"]),
            ("Introduction to Human Evolution", "Biology", "Various", "https://www.coursera.org/learn/human-evolution-glasgow", "undergraduate", ["Biology", "Anthropology"]),
            ("Introduction to the Music of the Beatles", "Music", "Various", "https://www.coursera.org/learn/music-beatles", "undergraduate", ["Music", "History"]),
            ("Scotland's Future", "Political Science", "Various", "https://www.coursera.org/learn/scotlands-future", "undergraduate", ["Political Science"]),
            ("Introduction to Renminbi", "Economics", "Various", "https://www.coursera.org/learn/renminbi", "professional", ["Economics", "Finance"]),
            ("Introduction to Immunology", "Medicine", "Various", "https://www.futurelearn.com/courses/immunology-glasgow", "undergraduate", ["Medicine", "Biology"]),
            ("Obesity: Causes and Consequences", "Medicine", "Various", "https://www.futurelearn.com/courses/obesity-causes-consequences", "professional", ["Medicine", "Nutrition"]),
            ("Introduction to Epidemiology", "Public Health", "Various", "https://www.coursera.org/learn/epidemiology-glasgow", "undergraduate", ["Epidemiology", "Public Health"]),
            ("The Art of the MOOC: Experiments in New Pedagogies", "Education", "Various", "https://www.coursera.org/learn/the-art-of-the-mooc", "professional", ["Education"]),
            ("Introduction to Veterinary Science", "Biology", "Various", "https://www.futurelearn.com/courses/veterinary-science-glasgow", "undergraduate", ["Biology", "Animal Science"]),
            ("Discovering Dentistry", "Medicine", "Various", "https://www.futurelearn.com/courses/discovering-dentistry", "professional", ["Medicine"]),
        ]
    },
    "unsw": {
        "name": "University of New South Wales", "slug": "unsw",
        "website": "https://www.unsw.edu.au", "country": "AU",
        "description": "UNSW open courses via edX and Coursera.",
        "courses": [
            ("Data Science for Decision Making", "Data Science", "Various", "https://www.edx.org/course/data-science-decision-making-unsw", "undergraduate", ["Data Science", "Business"]),
            ("Introduction to Machine Learning", "Computer Science", "Various", "https://www.edx.org/course/machine-learning-unsw", "undergraduate", ["Machine Learning"]),
            ("Algorithms Design and Analysis", "Computer Science", "Various", "https://www.edx.org/course/algorithms-unsw", "undergraduate", ["Computer Science", "Algorithms"]),
            ("Introduction to Python", "Computer Science", "Various", "https://www.edx.org/course/python-unsw", "undergraduate", ["Computer Science", "Python"]),
            ("Engineering Ethics", "Engineering", "Various", "https://www.edx.org/course/engineering-ethics-unsw", "undergraduate", ["Engineering", "Ethics"]),
            ("Introduction to Structural Analysis", "Engineering", "Various", "https://www.edx.org/course/structural-analysis-unsw", "undergraduate", ["Engineering", "Mechanics"]),
            ("Business Foundations", "Business", "Various", "https://www.edx.org/course/business-foundations-unsw", "undergraduate", ["Business"]),
            ("Entrepreneurship in Emerging Economies", "Business", "Various", "https://www.edx.org/course/entrepreneurship-unsw", "professional", ["Business", "Economics"]),
            ("Introduction to Logic", "Philosophy", "Various", "https://www.edx.org/course/logic-unsw", "undergraduate", ["Philosophy", "Logic"]),
            ("Extinction: Past and Present", "Biology", "Various", "https://www.edx.org/course/extinction-unsw", "undergraduate", ["Biology", "Earth Science"]),
            ("Tropical Coastal Ecosystems", "Environmental Science", "Various", "https://www.edx.org/course/tropical-coastal-ecosystems", "undergraduate", ["Environmental Science", "Biology"]),
            ("Introduction to Solar Cells", "Engineering", "Various", "https://www.edx.org/course/solar-cells-unsw", "undergraduate", ["Engineering", "Environmental Science"]),
            ("Developing Industrial Internet of Things", "Engineering", "Various", "https://www.edx.org/course/industrial-iot-unsw", "professional", ["Engineering", "Computer Science"]),
            ("Introduction to Psychology", "Psychology", "Various", "https://www.edx.org/course/psychology-unsw", "undergraduate", ["Psychology"]),
            ("Aboriginal and Torres Strait Islander Cultural Studies", "Social Sciences", "Various", "https://www.edx.org/course/indigenous-studies-unsw", "undergraduate", ["Social Science", "History"]),
            ("Preparation for University Study", "General", "Various", "https://www.edx.org/course/university-preparation-unsw", "undergraduate", ["Education"]),
            ("Excel Skills for Data Analytics and Visualization", "Computer Science", "Various", "https://www.coursera.org/learn/excel-skills-analytics-unsw", "undergraduate", ["Data Science", "Computer Science"]),
            ("Supply Chain Management A-Z", "Business", "Various", "https://www.coursera.org/learn/supply-chain-management-unsw", "professional", ["Business", "Management"]),
        ]
    },
    "umelbourne": {
        "name": "University of Melbourne", "slug": "umelbourne",
        "website": "https://www.unimelb.edu.au", "country": "AU",
        "description": "University of Melbourne open courses via Coursera and edX.",
        "courses": [
            ("Introduction to Discrete Mathematics for Computer Science", "Computer Science", "Various", "https://www.coursera.org/learn/discrete-mathematics", "undergraduate", ["Computer Science", "Mathematics"]),
            ("Introduction to Graph Theory", "Mathematics", "Various", "https://www.coursera.org/learn/graphs", "undergraduate", ["Mathematics", "Computer Science"]),
            ("Linear Algebra for Beginners", "Mathematics", "Various", "https://www.coursera.org/learn/linear-algebra-beginners-umelb", "undergraduate", ["Mathematics", "Linear Algebra"]),
            ("Good Brain, Bad Brain: Basics", "Neuroscience", "Various", "https://www.coursera.org/learn/good-brain-bad-brain-basics", "undergraduate", ["Neuroscience", "Biology"]),
            ("Good Brain, Bad Brain: Parkinson's Disease", "Neuroscience", "Various", "https://www.coursera.org/learn/good-brain-bad-brain-parkinsons", "undergraduate", ["Neuroscience", "Medicine"]),
            ("Introduction to Data Analytics for Business", "Data Science", "Various", "https://www.coursera.org/learn/data-analytics-business-umelb", "undergraduate", ["Data Science", "Business"]),
            ("Designing for the Anthropocene", "Design", "Various", "https://www.coursera.org/learn/anthropocene-design", "undergraduate", ["Design", "Environmental Science"]),
            ("Animal Behaviour", "Biology", "Various", "https://www.coursera.org/learn/animal-behaviour-umelb", "undergraduate", ["Biology"]),
            ("Mind Control: Managing Your Mental Health During COVID-19", "Psychology", "Various", "https://www.coursera.org/learn/managing-mental-health-covid-19", "professional", ["Psychology", "Health"]),
            ("Introduction to Philosophy of Psychology and the Neurosciences", "Philosophy", "Various", "https://www.coursera.org/learn/philosophy-psychology-neuroscience", "undergraduate", ["Philosophy", "Psychology"]),
            ("Society, Science, Survival: Lessons from AMC's The Walking Dead", "Social Sciences", "Various", "https://www.coursera.org/learn/walking-dead", "undergraduate", ["Sociology", "Science"]),
            ("Immunology: Immune Failures", "Medicine", "Various", "https://www.coursera.org/learn/immunology-failures", "undergraduate", ["Medicine", "Biology"]),
            ("Immunology: Immune Regulation", "Medicine", "Various", "https://www.coursera.org/learn/immunology-regulation", "undergraduate", ["Medicine", "Biology"]),
            ("Australian Indigenous Education", "Education", "Various", "https://www.coursera.org/learn/indigenous-education-australia", "professional", ["Education", "Social Science"]),
            ("The Art of Music Production", "Music", "Various", "https://www.coursera.org/learn/music-production-umelb", "undergraduate", ["Music"]),
            ("Urban Infrastructure Management", "Engineering", "Various", "https://www.edx.org/course/urban-infrastructure-umelb", "professional", ["Engineering"]),
            ("Philosophy, Science and Religion: Philosophy and Religion", "Philosophy", "Various", "https://www.coursera.org/learn/philosophy-religion-umelb", "undergraduate", ["Philosophy", "Religion"]),
            ("Philosophy, Science and Religion: Science and Philosophy", "Philosophy", "Various", "https://www.coursera.org/learn/science-philosophy-umelb", "undergraduate", ["Philosophy", "Science"]),
        ]
    },
    "anu": {
        "name": "Australian National University", "slug": "anu",
        "website": "https://www.anu.edu.au", "country": "AU",
        "description": "Australian National University open courses via edX.",
        "courses": [
            ("Introduction to Actuarial Studies", "Mathematics", "Various", "https://www.edx.org/course/actuarial-studies-anu", "undergraduate", ["Mathematics", "Finance"]),
            ("Introduction to Machine Learning", "Computer Science", "Various", "https://www.edx.org/course/machine-learning-anu", "undergraduate", ["Machine Learning"]),
            ("Introduction to Statistical Data Analysis", "Statistics", "Various", "https://www.edx.org/course/statistical-data-analysis-anu", "undergraduate", ["Statistics"]),
            ("Astrophysics: The Violent Universe", "Physics", "Various", "https://www.edx.org/course/astrophysics-violent-universe", "undergraduate", ["Physics", "Astronomy"]),
            ("Astrophysics: Exploring Exoplanets", "Physics", "Various", "https://www.edx.org/course/astrophysics-exoplanets", "undergraduate", ["Physics", "Astronomy"]),
            ("Astrophysics: The Cosmic Distance Scale", "Physics", "Various", "https://www.edx.org/course/astrophysics-cosmic-distance-scale", "undergraduate", ["Physics", "Astronomy"]),
            ("Climate Change: The Science", "Environmental Science", "Various", "https://www.edx.org/course/climate-change-science-anu", "undergraduate", ["Environmental Science", "Climate Science"]),
            ("Climate Change: Solutions", "Environmental Science", "Various", "https://www.edx.org/course/climate-change-solutions-anu", "undergraduate", ["Environmental Science", "Climate Science"]),
            ("Empirical Legal Research", "Law", "Various", "https://www.edx.org/course/empirical-legal-research-anu", "graduate", ["Law", "Research Methods"]),
            ("Public Policy Challenges of the 21st Century", "Political Science", "Various", "https://www.edx.org/course/public-policy-21st-century-anu", "undergraduate", ["Political Science"]),
            ("Introduction to Linguistics", "Linguistics", "Various", "https://www.edx.org/course/linguistics-anu", "undergraduate", ["Linguistics"]),
            ("Introduction to Aboriginal Culture", "Social Sciences", "Various", "https://www.edx.org/course/aboriginal-culture-anu", "undergraduate", ["Social Science", "History"]),
            ("China's Reemergence in the International Arena", "Political Science", "Various", "https://www.edx.org/course/china-international-arena-anu", "undergraduate", ["Political Science", "History"]),
            ("Introduction to Gravity", "Physics", "Brian Schmidt", "https://www.edx.org/course/introduction-gravity-anu", "undergraduate", ["Physics", "Astronomy"]),
            ("Quantum Mechanics for Everyone", "Physics", "Various", "https://www.edx.org/course/quantum-mechanics-anu", "undergraduate", ["Physics", "Quantum Mechanics"]),
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
