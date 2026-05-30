"""
load_roadmaps.py
Populates the roadmaps and roadmap_entries tables with real degree program
course sequences from the universities in our DB.
"""
from __future__ import annotations

import os
import sys
import uuid

import psycopg2
import psycopg2.extras

DB_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://ocw:ocwpass@127.0.0.1:5432/opencourseware",
)

# ─────────────────────────────────────────────────────────────────────────────
# ROADMAP DATA
# Each entry: {
#   "university_slug": str,
#   "slug": str,               unique roadmap slug
#   "title": str,              e.g. "B.S. Computer Science"
#   "degree_type": str,        "Bachelor of Science", "Master of Science", etc.
#   "major": str,
#   "department": str,
#   "description": str,
#   "estimated_years": int,
#   "website_url": str,
#   "courses": [
#     {
#       "position": int,
#       "course_number": str,   e.g. "18.01"
#       "course_title": str,
#       "category": str,        "Core", "Math", "Science", "Elective", "Lab"
#       "semester": str,        "Year 1, Fall"
#       "year_in_program": int,
#       "is_required": bool,
#       "units": int,
#       "notes": str,
#     }
#   ]
# }
# ─────────────────────────────────────────────────────────────────────────────

ROADMAPS = [

    # ──────────────────────────────────────────────────────
    # MIT – Computer Science (Course 6-3)
    # ──────────────────────────────────────────────────────
    {
        "university_slug": "mit",
        "slug": "mit-bs-computer-science",
        "title": "B.S. Computer Science (Course 6-3)",
        "degree_type": "Bachelor of Science",
        "major": "Computer Science",
        "department": "Electrical Engineering & Computer Science",
        "description": (
            "MIT's Course 6-3 Computer Science program emphasizes algorithms, "
            "systems, theory, and AI. Students complete a rigorous math & science "
            "foundation alongside CS core subjects."
        ),
        "estimated_years": 4,
        "website_url": "https://www.eecs.mit.edu/academics/undergraduate-programs/curriculum/6-3-computer-science/",
        "courses": [
            # Year 1
            {"position": 1,  "course_number": "18.01",   "course_title": "Single Variable Calculus",          "category": "Math",   "semester": "Year 1, Fall",   "year_in_program": 1, "is_required": True,  "units": 12},
            {"position": 2,  "course_number": "8.01",    "course_title": "Physics I – Classical Mechanics",   "category": "Science","semester": "Year 1, Fall",   "year_in_program": 1, "is_required": True,  "units": 12},
            {"position": 3,  "course_number": "6.009",   "course_title": "Fundamentals of Programming",       "category": "Core",   "semester": "Year 1, Fall",   "year_in_program": 1, "is_required": True,  "units": 12},
            {"position": 4,  "course_number": "18.02",   "course_title": "Multivariable Calculus",            "category": "Math",   "semester": "Year 1, Spring", "year_in_program": 1, "is_required": True,  "units": 12},
            {"position": 5,  "course_number": "8.02",    "course_title": "Physics II – Electricity & Magnetism","category": "Science","semester": "Year 1, Spring","year_in_program": 1, "is_required": True,  "units": 12},
            {"position": 6,  "course_number": "6.042J",  "course_title": "Mathematics for Computer Science",  "category": "Math",   "semester": "Year 1, Spring", "year_in_program": 1, "is_required": True,  "units": 12},
            # Year 2
            {"position": 7,  "course_number": "6.004",   "course_title": "Computation Structures",            "category": "Core",   "semester": "Year 2, Fall",   "year_in_program": 2, "is_required": True,  "units": 12},
            {"position": 8,  "course_number": "6.006",   "course_title": "Introduction to Algorithms",        "category": "Core",   "semester": "Year 2, Fall",   "year_in_program": 2, "is_required": True,  "units": 12},
            {"position": 9,  "course_number": "18.06",   "course_title": "Linear Algebra",                    "category": "Math",   "semester": "Year 2, Fall",   "year_in_program": 2, "is_required": True,  "units": 12},
            {"position": 10, "course_number": "6.031",   "course_title": "Elements of Software Construction", "category": "Core",   "semester": "Year 2, Spring", "year_in_program": 2, "is_required": True,  "units": 15},
            {"position": 11, "course_number": "6.046J",  "course_title": "Design and Analysis of Algorithms", "category": "Core",   "semester": "Year 2, Spring", "year_in_program": 2, "is_required": True,  "units": 12},
            {"position": 12, "course_number": "6.041",   "course_title": "Probabilistic Systems Analysis",    "category": "Core",   "semester": "Year 2, Spring", "year_in_program": 2, "is_required": True,  "units": 12},
            # Year 3
            {"position": 13, "course_number": "6.033",   "course_title": "Computer System Engineering",       "category": "Core",   "semester": "Year 3, Fall",   "year_in_program": 3, "is_required": True,  "units": 12},
            {"position": 14, "course_number": "6.034",   "course_title": "Artificial Intelligence",           "category": "Core",   "semester": "Year 3, Fall",   "year_in_program": 3, "is_required": True,  "units": 12},
            {"position": 15, "course_number": "6.854J",  "course_title": "Advanced Algorithms",               "category": "Core",   "semester": "Year 3, Fall",   "year_in_program": 3, "is_required": False, "units": 12},
            {"position": 16, "course_number": "6.172",   "course_title": "Performance Engineering of Software Systems","category": "Advanced","semester": "Year 3, Spring","year_in_program": 3, "is_required": False, "units": 18},
            {"position": 17, "course_number": "6.824",   "course_title": "Distributed Systems",               "category": "Advanced","semester": "Year 3, Spring","year_in_program": 3, "is_required": False, "units": 12},
            {"position": 18, "course_number": "6.858",   "course_title": "Computer Systems Security",         "category": "Advanced","semester": "Year 3, Spring","year_in_program": 3, "is_required": False, "units": 12},
            # Year 4
            {"position": 19, "course_number": "6.864",   "course_title": "Advanced Natural Language Processing","category": "Advanced","semester": "Year 4, Fall", "year_in_program": 4, "is_required": False, "units": 12},
            {"position": 20, "course_number": "6.867",   "course_title": "Machine Learning",                  "category": "Advanced","semester": "Year 4, Fall", "year_in_program": 4, "is_required": False, "units": 12},
            {"position": 21, "course_number": "6.S191",  "course_title": "Introduction to Deep Learning",     "category": "Advanced","semester": "Year 4, Spring","year_in_program": 4, "is_required": False, "units": 6},
            {"position": 22, "course_number": "6.UAT",   "course_title": "Undergraduate Advanced Project",    "category": "Capstone","semester": "Year 4, Spring","year_in_program": 4, "is_required": True,  "units": 9},
        ],
    },

    # ──────────────────────────────────────────────────────
    # MIT – Physics (Course 8)
    # ──────────────────────────────────────────────────────
    {
        "university_slug": "mit",
        "slug": "mit-bs-physics",
        "title": "B.S. Physics (Course 8)",
        "degree_type": "Bachelor of Science",
        "major": "Physics",
        "department": "Physics",
        "description": (
            "MIT's Physics program (Course 8) provides a rigorous training in classical "
            "mechanics, electromagnetism, quantum mechanics, and statistical mechanics, "
            "culminating in advanced topics like particle physics and cosmology."
        ),
        "estimated_years": 4,
        "website_url": "https://physics.mit.edu/academic-programs/undergraduate-programs/",
        "courses": [
            {"position": 1,  "course_number": "8.01",   "course_title": "Classical Mechanics",               "category": "Core",   "semester": "Year 1, Fall",   "year_in_program": 1, "is_required": True,  "units": 12},
            {"position": 2,  "course_number": "18.01",  "course_title": "Single Variable Calculus",          "category": "Math",   "semester": "Year 1, Fall",   "year_in_program": 1, "is_required": True,  "units": 12},
            {"position": 3,  "course_number": "8.02",   "course_title": "Electricity and Magnetism",         "category": "Core",   "semester": "Year 1, Spring", "year_in_program": 1, "is_required": True,  "units": 12},
            {"position": 4,  "course_number": "18.02",  "course_title": "Multivariable Calculus",            "category": "Math",   "semester": "Year 1, Spring", "year_in_program": 1, "is_required": True,  "units": 12},
            {"position": 5,  "course_number": "8.03",   "course_title": "Vibrations and Waves",              "category": "Core",   "semester": "Year 2, Fall",   "year_in_program": 2, "is_required": True,  "units": 12},
            {"position": 6,  "course_number": "18.03",  "course_title": "Differential Equations",            "category": "Math",   "semester": "Year 2, Fall",   "year_in_program": 2, "is_required": True,  "units": 12},
            {"position": 7,  "course_number": "8.04",   "course_title": "Quantum Physics I",                 "category": "Core",   "semester": "Year 2, Spring", "year_in_program": 2, "is_required": True,  "units": 12},
            {"position": 8,  "course_number": "18.06",  "course_title": "Linear Algebra",                    "category": "Math",   "semester": "Year 2, Spring", "year_in_program": 2, "is_required": True,  "units": 12},
            {"position": 9,  "course_number": "8.05",   "course_title": "Quantum Physics II",                "category": "Core",   "semester": "Year 3, Fall",   "year_in_program": 3, "is_required": True,  "units": 12},
            {"position": 10, "course_number": "8.044",  "course_title": "Statistical Physics I",             "category": "Core",   "semester": "Year 3, Fall",   "year_in_program": 3, "is_required": True,  "units": 12},
            {"position": 11, "course_number": "8.06",   "course_title": "Quantum Physics III",               "category": "Core",   "semester": "Year 3, Spring", "year_in_program": 3, "is_required": True,  "units": 12},
            {"position": 12, "course_number": "8.07",   "course_title": "Electromagnetism II",               "category": "Core",   "semester": "Year 3, Spring", "year_in_program": 3, "is_required": True,  "units": 12},
            {"position": 13, "course_number": "8.033",  "course_title": "Relativity",                        "category": "Advanced","semester": "Year 4, Fall",  "year_in_program": 4, "is_required": False, "units": 12},
            {"position": 14, "course_number": "8.108",  "course_title": "Advanced Experimental Physics",    "category": "Lab",    "semester": "Year 4, Fall",   "year_in_program": 4, "is_required": True,  "units": 12},
            {"position": 15, "course_number": "8.09",   "course_title": "Classical Mechanics III",           "category": "Advanced","semester": "Year 4, Fall",  "year_in_program": 4, "is_required": False, "units": 12},
            {"position": 16, "course_number": "8.14",   "course_title": "Experimental Physics II",           "category": "Lab",    "semester": "Year 4, Spring", "year_in_program": 4, "is_required": True,  "units": 12},
        ],
    },

    # ──────────────────────────────────────────────────────
    # MIT – Mathematics (Course 18)
    # ──────────────────────────────────────────────────────
    {
        "university_slug": "mit",
        "slug": "mit-bs-mathematics",
        "title": "B.S. Mathematics (Course 18)",
        "degree_type": "Bachelor of Science",
        "major": "Mathematics",
        "department": "Mathematics",
        "description": (
            "MIT's mathematics curriculum trains students in rigorous proof-based "
            "mathematics across analysis, algebra, and topology, with options to "
            "specialize in pure or applied directions."
        ),
        "estimated_years": 4,
        "website_url": "https://math.mit.edu/academics/undergrad/",
        "courses": [
            {"position": 1,  "course_number": "18.01",  "course_title": "Single Variable Calculus",            "category": "Core", "semester": "Year 1, Fall",   "year_in_program": 1, "is_required": True, "units": 12},
            {"position": 2,  "course_number": "18.02",  "course_title": "Multivariable Calculus",              "category": "Core", "semester": "Year 1, Spring", "year_in_program": 1, "is_required": True, "units": 12},
            {"position": 3,  "course_number": "18.03",  "course_title": "Differential Equations",              "category": "Core", "semester": "Year 2, Fall",   "year_in_program": 2, "is_required": True, "units": 12},
            {"position": 4,  "course_number": "18.06",  "course_title": "Linear Algebra",                      "category": "Core", "semester": "Year 2, Fall",   "year_in_program": 2, "is_required": True, "units": 12},
            {"position": 5,  "course_number": "18.100", "course_title": "Real Analysis",                       "category": "Core", "semester": "Year 2, Spring", "year_in_program": 2, "is_required": True, "units": 12},
            {"position": 6,  "course_number": "18.200", "course_title": "Principles of Discrete Applied Mathematics","category": "Core", "semester": "Year 2, Spring", "year_in_program": 2, "is_required": False, "units": 12},
            {"position": 7,  "course_number": "18.701", "course_title": "Algebra I",                           "category": "Core", "semester": "Year 3, Fall",   "year_in_program": 3, "is_required": True, "units": 12},
            {"position": 8,  "course_number": "18.702", "course_title": "Algebra II",                          "category": "Core", "semester": "Year 3, Spring", "year_in_program": 3, "is_required": True, "units": 12},
            {"position": 9,  "course_number": "18.101", "course_title": "Analysis II",                         "category": "Core", "semester": "Year 3, Fall",   "year_in_program": 3, "is_required": False, "units": 12},
            {"position": 10, "course_number": "18.104", "course_title": "Seminar in Analysis",                 "category": "Core", "semester": "Year 3, Spring", "year_in_program": 3, "is_required": False, "units": 12},
            {"position": 11, "course_number": "18.211", "course_title": "Combinatorial Analysis",              "category": "Advanced","semester": "Year 4, Fall","year_in_program": 4, "is_required": False, "units": 12},
            {"position": 12, "course_number": "18.065", "course_title": "Matrix Methods in Data Analysis & ML","category": "Advanced","semester": "Year 4, Fall","year_in_program": 4, "is_required": False, "units": 12},
            {"position": 13, "course_number": "18.950", "course_title": "Differential Geometry",               "category": "Advanced","semester": "Year 4, Spring","year_in_program": 4, "is_required": False, "units": 12},
            {"position": 14, "course_number": "18.901", "course_title": "Introduction to Topology",            "category": "Advanced","semester": "Year 4, Spring","year_in_program": 4, "is_required": False, "units": 12},
        ],
    },

    # ──────────────────────────────────────────────────────
    # MIT – Electrical Engineering & Computer Science (6-2)
    # ──────────────────────────────────────────────────────
    {
        "university_slug": "mit",
        "slug": "mit-bs-eecs",
        "title": "B.S. Electrical Engineering & Computer Science (Course 6-2)",
        "degree_type": "Bachelor of Science",
        "major": "Electrical Engineering and Computer Science",
        "department": "Electrical Engineering & Computer Science",
        "description": (
            "MIT's Course 6-2 spans both electrical engineering and computer science. "
            "Students build a foundation in circuits, signals, and systems alongside "
            "software, algorithms, and computer architecture."
        ),
        "estimated_years": 4,
        "website_url": "https://www.eecs.mit.edu/academics/undergraduate-programs/curriculum/6-2-eecs/",
        "courses": [
            {"position": 1,  "course_number": "18.01",   "course_title": "Single Variable Calculus",             "category": "Math",   "semester": "Year 1, Fall",   "year_in_program": 1, "is_required": True,  "units": 12},
            {"position": 2,  "course_number": "8.01",    "course_title": "Classical Mechanics",                  "category": "Science","semester": "Year 1, Fall",   "year_in_program": 1, "is_required": True,  "units": 12},
            {"position": 3,  "course_number": "6.009",   "course_title": "Fundamentals of Programming",          "category": "Core",   "semester": "Year 1, Fall",   "year_in_program": 1, "is_required": True,  "units": 12},
            {"position": 4,  "course_number": "18.02",   "course_title": "Multivariable Calculus",               "category": "Math",   "semester": "Year 1, Spring", "year_in_program": 1, "is_required": True,  "units": 12},
            {"position": 5,  "course_number": "8.02",    "course_title": "Electricity and Magnetism",            "category": "Science","semester": "Year 1, Spring", "year_in_program": 1, "is_required": True,  "units": 12},
            {"position": 6,  "course_number": "6.002",   "course_title": "Circuits and Electronics",             "category": "Core",   "semester": "Year 2, Fall",   "year_in_program": 2, "is_required": True,  "units": 12},
            {"position": 7,  "course_number": "6.003",   "course_title": "Signals and Systems",                  "category": "Core",   "semester": "Year 2, Fall",   "year_in_program": 2, "is_required": True,  "units": 12},
            {"position": 8,  "course_number": "6.004",   "course_title": "Computation Structures",               "category": "Core",   "semester": "Year 2, Spring", "year_in_program": 2, "is_required": True,  "units": 12},
            {"position": 9,  "course_number": "6.006",   "course_title": "Introduction to Algorithms",           "category": "Core",   "semester": "Year 2, Spring", "year_in_program": 2, "is_required": True,  "units": 12},
            {"position": 10, "course_number": "6.042J",  "course_title": "Mathematics for Computer Science",     "category": "Math",   "semester": "Year 2, Spring", "year_in_program": 2, "is_required": True,  "units": 12},
            {"position": 11, "course_number": "6.011",   "course_title": "Intro to Communication, Control & Signal Processing","category": "Core","semester": "Year 3, Fall","year_in_program": 3, "is_required": True, "units": 12},
            {"position": 12, "course_number": "6.033",   "course_title": "Computer System Engineering",          "category": "Core",   "semester": "Year 3, Fall",   "year_in_program": 3, "is_required": True,  "units": 12},
            {"position": 13, "course_number": "6.046J",  "course_title": "Design and Analysis of Algorithms",   "category": "Core",   "semester": "Year 3, Spring", "year_in_program": 3, "is_required": True,  "units": 12},
            {"position": 14, "course_number": "6.041",   "course_title": "Probabilistic Systems Analysis",       "category": "Core",   "semester": "Year 3, Spring", "year_in_program": 3, "is_required": True,  "units": 12},
            {"position": 15, "course_number": "6.UAR",   "course_title": "Undergraduate Advanced Research",      "category": "Capstone","semester": "Year 4, Fall",  "year_in_program": 4, "is_required": True,  "units": 9},
            {"position": 16, "course_number": "6.UAT",   "course_title": "Undergraduate Advanced Project",       "category": "Capstone","semester": "Year 4, Spring","year_in_program": 4, "is_required": True,  "units": 9},
        ],
    },

    # ──────────────────────────────────────────────────────
    # Stanford – B.S. Computer Science
    # ──────────────────────────────────────────────────────
    {
        "university_slug": "stanford",
        "slug": "stanford-bs-computer-science",
        "title": "B.S. Computer Science",
        "degree_type": "Bachelor of Science",
        "major": "Computer Science",
        "department": "Computer Science",
        "description": (
            "Stanford's CS undergraduate program provides a broad foundation "
            "before allowing specialization in one of seven tracks: AI, Biocomputation, "
            "Computer Engineering, Graphics, Human-Computer Interaction, Systems, or Theory."
        ),
        "estimated_years": 4,
        "website_url": "https://cs.stanford.edu/degrees/undergrad/",
        "courses": [
            # Core Programming
            {"position": 1,  "course_number": "CS106A",  "course_title": "Programming Methodology",              "category": "Core",   "semester": "Year 1, Fall",   "year_in_program": 1, "is_required": True,  "units": 5},
            {"position": 2,  "course_number": "CS106B",  "course_title": "Programming Abstractions",             "category": "Core",   "semester": "Year 1, Spring", "year_in_program": 1, "is_required": True,  "units": 5},
            {"position": 3,  "course_number": "CS107",   "course_title": "Computer Organization and Systems",    "category": "Core",   "semester": "Year 2, Fall",   "year_in_program": 2, "is_required": True,  "units": 5},
            {"position": 4,  "course_number": "CS111",   "course_title": "Operating Systems Principles",         "category": "Core",   "semester": "Year 2, Spring", "year_in_program": 2, "is_required": True,  "units": 5},
            # Math
            {"position": 5,  "course_number": "MATH19",  "course_title": "Calculus",                             "category": "Math",   "semester": "Year 1, Fall",   "year_in_program": 1, "is_required": True,  "units": 5},
            {"position": 6,  "course_number": "CS103",   "course_title": "Mathematical Foundations of Computing","category": "Math",   "semester": "Year 1, Spring", "year_in_program": 1, "is_required": True,  "units": 5},
            {"position": 7,  "course_number": "CS109",   "course_title": "Probability for Computer Scientists",  "category": "Math",   "semester": "Year 2, Fall",   "year_in_program": 2, "is_required": True,  "units": 5},
            # Systems & Theory
            {"position": 8,  "course_number": "CS143",   "course_title": "Compilers",                            "category": "Systems","semester": "Year 3, Fall",   "year_in_program": 3, "is_required": False, "units": 4},
            {"position": 9,  "course_number": "CS154",   "course_title": "Introduction to the Theory of Computation","category": "Theory","semester": "Year 3, Fall","year_in_program": 3, "is_required": False, "units": 5},
            {"position": 10, "course_number": "CS161",   "course_title": "Design and Analysis of Algorithms",   "category": "Core",   "semester": "Year 3, Fall",   "year_in_program": 3, "is_required": True,  "units": 5},
            {"position": 11, "course_number": "CS145",   "course_title": "Introduction to Databases",            "category": "Systems","semester": "Year 3, Spring", "year_in_program": 3, "is_required": False, "units": 4},
            {"position": 12, "course_number": "CS246",   "course_title": "Mining Massive Datasets",              "category": "Advanced","semester": "Year 3, Spring","year_in_program": 3, "is_required": False, "units": 4},
            # AI Track (optional track)
            {"position": 13, "course_number": "CS221",   "course_title": "Artificial Intelligence: Principles & Techniques","category": "AI Track","semester": "Year 4, Fall","year_in_program": 4, "is_required": False, "units": 4},
            {"position": 14, "course_number": "CS229",   "course_title": "Machine Learning",                     "category": "AI Track","semester": "Year 4, Fall",  "year_in_program": 4, "is_required": False, "units": 4},
            {"position": 15, "course_number": "CS231N",  "course_title": "Deep Learning for Computer Vision",    "category": "AI Track","semester": "Year 4, Spring","year_in_program": 4, "is_required": False, "units": 4},
            {"position": 16, "course_number": "CS224N",  "course_title": "Natural Language Processing with Deep Learning","category": "AI Track","semester": "Year 4, Spring","year_in_program": 4, "is_required": False, "units": 4},
        ],
    },

    # ──────────────────────────────────────────────────────
    # Stanford – B.S. Electrical Engineering
    # ──────────────────────────────────────────────────────
    {
        "university_slug": "stanford",
        "slug": "stanford-bs-electrical-engineering",
        "title": "B.S. Electrical Engineering",
        "degree_type": "Bachelor of Science",
        "major": "Electrical Engineering",
        "department": "Electrical Engineering",
        "description": (
            "Stanford EE covers circuits, signals, electromagnetics, and "
            "systems. Students choose a track: circuits, physical electronics, "
            "signal processing, or communications."
        ),
        "estimated_years": 4,
        "website_url": "https://ee.stanford.edu/academics/undergrad",
        "courses": [
            {"position": 1,  "course_number": "MATH19",   "course_title": "Calculus",                              "category": "Math",    "semester": "Year 1, Fall",   "year_in_program": 1, "is_required": True, "units": 5},
            {"position": 2,  "course_number": "PHYS41",   "course_title": "Mechanics",                             "category": "Science", "semester": "Year 1, Fall",   "year_in_program": 1, "is_required": True, "units": 4},
            {"position": 3,  "course_number": "PHYS43",   "course_title": "Electricity and Magnetism",             "category": "Science", "semester": "Year 1, Spring", "year_in_program": 1, "is_required": True, "units": 4},
            {"position": 4,  "course_number": "CS106A",   "course_title": "Programming Methodology",               "category": "Core",    "semester": "Year 1, Spring", "year_in_program": 1, "is_required": True, "units": 5},
            {"position": 5,  "course_number": "EE101A",   "course_title": "Circuits I",                            "category": "Core",    "semester": "Year 2, Fall",   "year_in_program": 2, "is_required": True, "units": 5},
            {"position": 6,  "course_number": "EE101B",   "course_title": "Circuits II",                           "category": "Core",    "semester": "Year 2, Spring", "year_in_program": 2, "is_required": True, "units": 5},
            {"position": 7,  "course_number": "EE102A",   "course_title": "Signal Processing and Linear Systems",  "category": "Core",    "semester": "Year 2, Spring", "year_in_program": 2, "is_required": True, "units": 5},
            {"position": 8,  "course_number": "EE161",    "course_title": "Electromagnetic Engineering",           "category": "Core",    "semester": "Year 3, Fall",   "year_in_program": 3, "is_required": True, "units": 5},
            {"position": 9,  "course_number": "EE108",    "course_title": "Digital Systems",                       "category": "Core",    "semester": "Year 3, Fall",   "year_in_program": 3, "is_required": True, "units": 5},
            {"position": 10, "course_number": "EE216",    "course_title": "Principles and Models of Semiconductor Devices","category": "Advanced","semester": "Year 3, Spring","year_in_program": 3, "is_required": False, "units": 4},
            {"position": 11, "course_number": "EE364A",   "course_title": "Convex Optimization I",                 "category": "Advanced","semester": "Year 4, Fall",  "year_in_program": 4, "is_required": False, "units": 4},
            {"position": 12, "course_number": "EE261",    "course_title": "The Fourier Transform and Its Applications","category": "Advanced","semester": "Year 4, Fall","year_in_program": 4, "is_required": False, "units": 4},
        ],
    },

    # ──────────────────────────────────────────────────────
    # UC Berkeley – B.S. EECS
    # ──────────────────────────────────────────────────────
    {
        "university_slug": "berkeley",
        "slug": "berkeley-bs-eecs",
        "title": "B.S. Electrical Engineering & Computer Sciences (EECS)",
        "degree_type": "Bachelor of Science",
        "major": "Electrical Engineering and Computer Sciences",
        "department": "Electrical Engineering & Computer Sciences",
        "description": (
            "Berkeley's EECS program is one of the most rigorous undergraduate "
            "CS programs in the world. Students take a demanding core sequence "
            "in programming, algorithms, systems, and EE before specializing."
        ),
        "estimated_years": 4,
        "website_url": "https://eecs.berkeley.edu/academics/undergraduate/eecs-bs",
        "courses": [
            {"position": 1,  "course_number": "CS61A",   "course_title": "Structure and Interpretation of Computer Programs","category": "Core","semester": "Year 1, Fall","year_in_program": 1, "is_required": True, "units": 4},
            {"position": 2,  "course_number": "CS61B",   "course_title": "Data Structures",                       "category": "Core","semester": "Year 1, Spring","year_in_program": 1, "is_required": True, "units": 4},
            {"position": 3,  "course_number": "CS61C",   "course_title": "Great Ideas in Computer Architecture",  "category": "Core","semester": "Year 2, Fall","year_in_program": 2, "is_required": True, "units": 4},
            {"position": 4,  "course_number": "CS70",    "course_title": "Discrete Mathematics and Probability",  "category": "Math","semester": "Year 2, Fall","year_in_program": 2, "is_required": True, "units": 4},
            {"position": 5,  "course_number": "EE16A",   "course_title": "Designing Information Devices & Systems I","category": "EE Core","semester": "Year 1, Spring","year_in_program": 1, "is_required": True, "units": 4},
            {"position": 6,  "course_number": "EE16B",   "course_title": "Designing Information Devices & Systems II","category": "EE Core","semester": "Year 2, Fall","year_in_program": 2, "is_required": True, "units": 4},
            {"position": 7,  "course_number": "MATH53",  "course_title": "Multivariable Calculus",               "category": "Math","semester": "Year 1, Fall","year_in_program": 1, "is_required": True, "units": 4},
            {"position": 8,  "course_number": "MATH54",  "course_title": "Linear Algebra and Differential Equations","category": "Math","semester": "Year 1, Spring","year_in_program": 1, "is_required": True, "units": 4},
            {"position": 9,  "course_number": "CS162",   "course_title": "Operating Systems and System Programming","category": "Systems","semester": "Year 3, Fall","year_in_program": 3, "is_required": True, "units": 4},
            {"position": 10, "course_number": "CS170",   "course_title": "Efficient Algorithms and Intractable Problems","category": "Core","semester": "Year 3, Fall","year_in_program": 3, "is_required": True, "units": 4},
            {"position": 11, "course_number": "CS186",   "course_title": "Introduction to Database Systems",     "category": "Systems","semester": "Year 3, Spring","year_in_program": 3, "is_required": True, "units": 4},
            {"position": 12, "course_number": "CS188",   "course_title": "Introduction to Artificial Intelligence","category": "AI","semester": "Year 3, Spring","year_in_program": 3, "is_required": True, "units": 4},
            {"position": 13, "course_number": "CS285",   "course_title": "Deep Reinforcement Learning",          "category": "Advanced","semester": "Year 4, Fall","year_in_program": 4, "is_required": False, "units": 3},
            {"position": 14, "course_number": "CS189",   "course_title": "Introduction to Machine Learning",     "category": "Advanced","semester": "Year 4, Fall","year_in_program": 4, "is_required": False, "units": 4},
            {"position": 15, "course_number": "CS194",   "course_title": "Special Topics in EECS (Senior Design)","category": "Capstone","semester": "Year 4, Spring","year_in_program": 4, "is_required": True, "units": 4},
        ],
    },

    # ──────────────────────────────────────────────────────
    # UC Berkeley – B.A. Data Science
    # ──────────────────────────────────────────────────────
    {
        "university_slug": "berkeley",
        "slug": "berkeley-ba-data-science",
        "title": "B.A. Data Science",
        "degree_type": "Bachelor of Arts",
        "major": "Data Science",
        "department": "Data Science",
        "description": (
            "Berkeley's Data Science major teaches students to extract "
            "insights from data using statistics, computing, and domain expertise. "
            "It combines CS, statistics, and mathematics."
        ),
        "estimated_years": 4,
        "website_url": "https://data.berkeley.edu/degrees/data-science-ba",
        "courses": [
            {"position": 1,  "course_number": "DATA8",    "course_title": "Foundations of Data Science",           "category": "Core","semester": "Year 1, Fall","year_in_program": 1, "is_required": True, "units": 4},
            {"position": 2,  "course_number": "CS61A",    "course_title": "Structure and Interpretation of Computer Programs","category": "Core","semester": "Year 1, Spring","year_in_program": 1, "is_required": True, "units": 4},
            {"position": 3,  "course_number": "MATH10A",  "course_title": "Methods of Mathematics: Calculus & Statistics","category": "Math","semester": "Year 1, Fall","year_in_program": 1, "is_required": True, "units": 4},
            {"position": 4,  "course_number": "CS61B",    "course_title": "Data Structures",                       "category": "Core","semester": "Year 2, Fall","year_in_program": 2, "is_required": True, "units": 4},
            {"position": 5,  "course_number": "DATA100",  "course_title": "Principles and Techniques of Data Science","category": "Core","semester": "Year 2, Fall","year_in_program": 2, "is_required": True, "units": 4},
            {"position": 6,  "course_number": "STAT134",  "course_title": "Concepts of Probability",               "category": "Math","semester": "Year 2, Spring","year_in_program": 2, "is_required": True, "units": 4},
            {"position": 7,  "course_number": "STAT135",  "course_title": "Concepts of Statistics",                "category": "Math","semester": "Year 3, Fall","year_in_program": 3, "is_required": True, "units": 4},
            {"position": 8,  "course_number": "CS189",    "course_title": "Introduction to Machine Learning",      "category": "Advanced","semester": "Year 3, Spring","year_in_program": 3, "is_required": True, "units": 4},
            {"position": 9,  "course_number": "DATA102",  "course_title": "Data, Inference, and Decisions",        "category": "Core","semester": "Year 4, Fall","year_in_program": 4, "is_required": True, "units": 4},
            {"position": 10, "course_number": "DATA198",  "course_title": "Directed Group Studies for Advanced Undergraduates","category": "Capstone","semester": "Year 4, Spring","year_in_program": 4, "is_required": True, "units": 3},
        ],
    },

    # ──────────────────────────────────────────────────────
    # Harvard – A.B. Computer Science
    # ──────────────────────────────────────────────────────
    {
        "university_slug": "harvard",
        "slug": "harvard-ab-computer-science",
        "title": "A.B. Computer Science",
        "degree_type": "Bachelor of Arts",
        "major": "Computer Science",
        "department": "Computer Science",
        "description": (
            "Harvard's Computer Science concentration spans theory, systems, AI, "
            "and applications. Students complete a rigorous programming sequence "
            "and several breadth requirements."
        ),
        "estimated_years": 4,
        "website_url": "https://www.cs.harvard.edu/undergraduate/",
        "courses": [
            {"position": 1,  "course_number": "CS50",    "course_title": "Introduction to Computer Science",        "category": "Core","semester": "Year 1, Fall","year_in_program": 1, "is_required": True, "units": 4},
            {"position": 2,  "course_number": "CS51",    "course_title": "Abstraction and Design in Computation",    "category": "Core","semester": "Year 1, Spring","year_in_program": 1, "is_required": True, "units": 4},
            {"position": 3,  "course_number": "CS61",    "course_title": "Systems Programming and Machine Organization","category": "Core","semester": "Year 2, Fall","year_in_program": 2, "is_required": True, "units": 4},
            {"position": 4,  "course_number": "CS120",   "course_title": "Introduction to Algorithms and Their Limitations","category": "Core","semester": "Year 2, Spring","year_in_program": 2, "is_required": True, "units": 4},
            {"position": 5,  "course_number": "MATH21a", "course_title": "Multivariable Calculus",                   "category": "Math","semester": "Year 1, Fall","year_in_program": 1, "is_required": True, "units": 4},
            {"position": 6,  "course_number": "MATH21b", "course_title": "Linear Algebra and Differential Equations","category": "Math","semester": "Year 1, Spring","year_in_program": 1, "is_required": True, "units": 4},
            {"position": 7,  "course_number": "STAT110",  "course_title": "Probability",                             "category": "Math","semester": "Year 2, Fall","year_in_program": 2, "is_required": True, "units": 4},
            {"position": 8,  "course_number": "CS121",   "course_title": "Introduction to Theoretical Computer Science","category": "Theory","semester": "Year 3, Fall","year_in_program": 3, "is_required": True, "units": 4},
            {"position": 9,  "course_number": "CS124",   "course_title": "Data Structures and Algorithms",           "category": "Core","semester": "Year 3, Fall","year_in_program": 3, "is_required": True, "units": 4},
            {"position": 10, "course_number": "CS136",   "course_title": "Advanced Topics in Programming Languages", "category": "Advanced","semester": "Year 3, Spring","year_in_program": 3, "is_required": False, "units": 4},
            {"position": 11, "course_number": "CS161",   "course_title": "Operating Systems",                        "category": "Systems","semester": "Year 3, Spring","year_in_program": 3, "is_required": False, "units": 4},
            {"position": 12, "course_number": "CS181",   "course_title": "Introduction to Machine Learning",         "category": "AI","semester": "Year 4, Fall","year_in_program": 4, "is_required": False, "units": 4},
            {"position": 13, "course_number": "CS165",   "course_title": "Data Systems",                             "category": "Systems","semester": "Year 4, Fall","year_in_program": 4, "is_required": False, "units": 4},
            {"position": 14, "course_number": "CS91r",   "course_title": "Supervised Research",                      "category": "Capstone","semester": "Year 4, Spring","year_in_program": 4, "is_required": False, "units": 4},
        ],
    },

    # ──────────────────────────────────────────────────────
    # Harvard – A.B. Mathematics
    # ──────────────────────────────────────────────────────
    {
        "university_slug": "harvard",
        "slug": "harvard-ab-mathematics",
        "title": "A.B. Mathematics",
        "degree_type": "Bachelor of Arts",
        "major": "Mathematics",
        "department": "Mathematics",
        "description": (
            "Harvard's Mathematics concentration offers tracks in pure and "
            "applied mathematics. Students work through calculus, analysis, "
            "algebra, and topology with flexibility to specialize."
        ),
        "estimated_years": 4,
        "website_url": "https://math.harvard.edu/undergraduate",
        "courses": [
            {"position": 1,  "course_number": "MATH21a",  "course_title": "Multivariable Calculus",                  "category": "Core","semester": "Year 1, Fall","year_in_program": 1, "is_required": True, "units": 4},
            {"position": 2,  "course_number": "MATH21b",  "course_title": "Linear Algebra and Differential Equations","category": "Core","semester": "Year 1, Spring","year_in_program": 1, "is_required": True, "units": 4},
            {"position": 3,  "course_number": "MATH101",  "course_title": "Sets, Groups and Topology",               "category": "Core","semester": "Year 2, Fall","year_in_program": 2, "is_required": True, "units": 4},
            {"position": 4,  "course_number": "MATH112",  "course_title": "Introductory Real Analysis",              "category": "Core","semester": "Year 2, Spring","year_in_program": 2, "is_required": True, "units": 4},
            {"position": 5,  "course_number": "MATH122",  "course_title": "Algebra I: Theory of Groups and Vector Spaces","category": "Core","semester": "Year 2, Spring","year_in_program": 2, "is_required": True, "units": 4},
            {"position": 6,  "course_number": "MATH113",  "course_title": "Analysis I: Complex Function Theory",     "category": "Advanced","semester": "Year 3, Fall","year_in_program": 3, "is_required": False, "units": 4},
            {"position": 7,  "course_number": "MATH123",  "course_title": "Algebra II: Theory of Rings and Fields",  "category": "Advanced","semester": "Year 3, Fall","year_in_program": 3, "is_required": False, "units": 4},
            {"position": 8,  "course_number": "MATH131",  "course_title": "Topology I: Topological Spaces",          "category": "Advanced","semester": "Year 3, Spring","year_in_program": 3, "is_required": False, "units": 4},
            {"position": 9,  "course_number": "STAT110",  "course_title": "Probability",                             "category": "Applied","semester": "Year 3, Fall","year_in_program": 3, "is_required": False, "units": 4},
            {"position": 10, "course_number": "MATH141",  "course_title": "Introduction to Mathematical Logic",      "category": "Advanced","semester": "Year 4, Fall","year_in_program": 4, "is_required": False, "units": 4},
            {"position": 11, "course_number": "MATH99r",  "course_title": "Senior Thesis",                           "category": "Capstone","semester": "Year 4, Spring","year_in_program": 4, "is_required": False, "units": 8},
        ],
    },

    # ──────────────────────────────────────────────────────
    # Princeton – A.B. / B.S.E. Computer Science
    # ──────────────────────────────────────────────────────
    {
        "university_slug": "princeton",
        "slug": "princeton-bse-computer-science",
        "title": "B.S.E. Computer Science",
        "degree_type": "Bachelor of Science in Engineering",
        "major": "Computer Science",
        "department": "Computer Science",
        "description": (
            "Princeton's CS B.S.E. program covers algorithms, systems, programming "
            "languages, and applications. Students complete a senior thesis representing "
            "independent research."
        ),
        "estimated_years": 4,
        "website_url": "https://www.cs.princeton.edu/ugrad/",
        "courses": [
            {"position": 1,  "course_number": "COS126",  "course_title": "Computer Science: An Interdisciplinary Approach","category": "Core","semester": "Year 1, Fall","year_in_program": 1, "is_required": True, "units": 4},
            {"position": 2,  "course_number": "COS226",  "course_title": "Algorithms and Data Structures",         "category": "Core","semester": "Year 1, Spring","year_in_program": 1, "is_required": True, "units": 4},
            {"position": 3,  "course_number": "COS217",  "course_title": "Introduction to Programming Systems",    "category": "Core","semester": "Year 2, Fall","year_in_program": 2, "is_required": True, "units": 4},
            {"position": 4,  "course_number": "COS240",  "course_title": "Reasoning About Computation",           "category": "Theory","semester": "Year 2, Fall","year_in_program": 2, "is_required": True, "units": 4},
            {"position": 5,  "course_number": "MAT201",  "course_title": "Multivariable Calculus",                "category": "Math","semester": "Year 1, Fall","year_in_program": 1, "is_required": True, "units": 4},
            {"position": 6,  "course_number": "MAT202",  "course_title": "Linear Algebra with Applications",      "category": "Math","semester": "Year 1, Spring","year_in_program": 1, "is_required": True, "units": 4},
            {"position": 7,  "course_number": "COS318",  "course_title": "Operating Systems",                     "category": "Systems","semester": "Year 3, Fall","year_in_program": 3, "is_required": False, "units": 4},
            {"position": 8,  "course_number": "COS333",  "course_title": "Advanced Programming Techniques",       "category": "Core","semester": "Year 3, Spring","year_in_program": 3, "is_required": True, "units": 4},
            {"position": 9,  "course_number": "COS423",  "course_title": "Theory of Algorithms",                  "category": "Theory","semester": "Year 3, Spring","year_in_program": 3, "is_required": True, "units": 4},
            {"position": 10, "course_number": "COS418",  "course_title": "Distributed Systems",                   "category": "Systems","semester": "Year 4, Fall","year_in_program": 4, "is_required": False, "units": 4},
            {"position": 11, "course_number": "COS401",  "course_title": "Introduction to Machine Translation",   "category": "Advanced","semester": "Year 4, Fall","year_in_program": 4, "is_required": False, "units": 4},
            {"position": 12, "course_number": "COS IW",  "course_title": "Junior Independent Work",               "category": "Capstone","semester": "Year 3, Spring","year_in_program": 3, "is_required": True, "units": 4},
            {"position": 13, "course_number": "COS Thesis","course_title": "Senior Thesis",                       "category": "Capstone","semester": "Year 4, Fall/Spring","year_in_program": 4, "is_required": True, "units": 8},
        ],
    },

    # ──────────────────────────────────────────────────────
    # Carnegie Mellon – B.S. Computer Science
    # ──────────────────────────────────────────────────────
    {
        "university_slug": "carnegie-mellon",
        "slug": "cmu-bs-computer-science",
        "title": "B.S. Computer Science",
        "degree_type": "Bachelor of Science",
        "major": "Computer Science",
        "department": "School of Computer Science",
        "description": (
            "CMU's CS program is one of the top-ranked in the world. "
            "Students complete a rigorous sequence in algorithms, systems, "
            "theory, and software engineering, with multiple technical areas."
        ),
        "estimated_years": 4,
        "website_url": "https://www.cs.cmu.edu/academics/undergraduate",
        "courses": [
            {"position": 1,  "course_number": "15-112",  "course_title": "Fundamentals of Programming and Computer Science","category": "Core","semester": "Year 1, Fall","year_in_program": 1, "is_required": True, "units": 12},
            {"position": 2,  "course_number": "21-127",  "course_title": "Concepts of Mathematics",               "category": "Math","semester": "Year 1, Fall","year_in_program": 1, "is_required": True, "units": 10},
            {"position": 3,  "course_number": "15-122",  "course_title": "Principles of Imperative Computation", "category": "Core","semester": "Year 1, Spring","year_in_program": 1, "is_required": True, "units": 10},
            {"position": 4,  "course_number": "21-259",  "course_title": "Calculus in Three Dimensions",          "category": "Math","semester": "Year 1, Spring","year_in_program": 1, "is_required": True, "units": 10},
            {"position": 5,  "course_number": "15-150",  "course_title": "Principles of Functional Programming", "category": "Core","semester": "Year 2, Fall","year_in_program": 2, "is_required": True, "units": 10},
            {"position": 6,  "course_number": "15-251",  "course_title": "Great Theoretical Ideas in Computer Science","category": "Theory","semester": "Year 2, Fall","year_in_program": 2, "is_required": True, "units": 12},
            {"position": 7,  "course_number": "21-241",  "course_title": "Matrices and Linear Transformations",   "category": "Math","semester": "Year 2, Fall","year_in_program": 2, "is_required": True, "units": 10},
            {"position": 8,  "course_number": "15-213",  "course_title": "Introduction to Computer Systems",      "category": "Systems","semester": "Year 2, Spring","year_in_program": 2, "is_required": True, "units": 12},
            {"position": 9,  "course_number": "36-226",  "course_title": "Introduction to Statistical Inference", "category": "Math","semester": "Year 2, Spring","year_in_program": 2, "is_required": True, "units": 9},
            {"position": 10, "course_number": "15-410",  "course_title": "Operating System Design and Implementation","category": "Systems","semester": "Year 3, Fall","year_in_program": 3, "is_required": True, "units": 15},
            {"position": 11, "course_number": "15-451",  "course_title": "Algorithm Design and Analysis",         "category": "Theory","semester": "Year 3, Fall","year_in_program": 3, "is_required": True, "units": 12},
            {"position": 12, "course_number": "15-445",  "course_title": "Database Systems",                      "category": "Systems","semester": "Year 3, Spring","year_in_program": 3, "is_required": False, "units": 12},
            {"position": 13, "course_number": "15-441",  "course_title": "Computer Networks",                     "category": "Systems","semester": "Year 3, Spring","year_in_program": 3, "is_required": False, "units": 12},
            {"position": 14, "course_number": "15-462",  "course_title": "Computer Graphics",                     "category": "Advanced","semester": "Year 4, Fall","year_in_program": 4, "is_required": False, "units": 12},
            {"position": 15, "course_number": "10-601",  "course_title": "Introduction to Machine Learning",      "category": "Advanced","semester": "Year 4, Fall","year_in_program": 4, "is_required": False, "units": 12},
            {"position": 16, "course_number": "15-414",  "course_title": "Bug Catching: Automated Program Verification and Testing","category": "Advanced","semester": "Year 4, Spring","year_in_program": 4, "is_required": False, "units": 12},
        ],
    },

    # ──────────────────────────────────────────────────────
    # Yale – B.S. Computer Science
    # ──────────────────────────────────────────────────────
    {
        "university_slug": "yale",
        "slug": "yale-bs-computer-science",
        "title": "B.S. Computer Science",
        "degree_type": "Bachelor of Science",
        "major": "Computer Science",
        "department": "Computer Science",
        "description": (
            "Yale's CS major blends theory, systems, and applications, "
            "allowing students to develop core foundations while pursuing "
            "elective depth in AI, systems, or theory."
        ),
        "estimated_years": 4,
        "website_url": "https://cpsc.yale.edu/academics/undergraduate-program",
        "courses": [
            {"position": 1,  "course_number": "CPSC112",  "course_title": "Introduction to Programming",             "category": "Core","semester": "Year 1, Fall","year_in_program": 1, "is_required": True, "units": 4},
            {"position": 2,  "course_number": "CPSC201",  "course_title": "Introduction to Computer Science",        "category": "Core","semester": "Year 1, Spring","year_in_program": 1, "is_required": True, "units": 4},
            {"position": 3,  "course_number": "CPSC202",  "course_title": "Mathematical Tools for Computer Science", "category": "Math","semester": "Year 2, Fall","year_in_program": 2, "is_required": True, "units": 4},
            {"position": 4,  "course_number": "CPSC223",  "course_title": "Data Structures and Programming Techniques","category": "Core","semester": "Year 2, Fall","year_in_program": 2, "is_required": True, "units": 4},
            {"position": 5,  "course_number": "CPSC323",  "course_title": "Introduction to Systems Programming",    "category": "Systems","semester": "Year 2, Spring","year_in_program": 2, "is_required": True, "units": 4},
            {"position": 6,  "course_number": "CPSC366",  "course_title": "Intensive Algorithms",                   "category": "Theory","semester": "Year 3, Fall","year_in_program": 3, "is_required": True, "units": 4},
            {"position": 7,  "course_number": "CPSC365",  "course_title": "Design and Analysis of Algorithms",      "category": "Theory","semester": "Year 3, Fall","year_in_program": 3, "is_required": True, "units": 4},
            {"position": 8,  "course_number": "CPSC426",  "course_title": "Building Distributed Systems",           "category": "Systems","semester": "Year 3, Spring","year_in_program": 3, "is_required": False, "units": 4},
            {"position": 9,  "course_number": "CPSC435",  "course_title": "Introduction to Database Systems",       "category": "Systems","semester": "Year 3, Spring","year_in_program": 3, "is_required": False, "units": 4},
            {"position": 10, "course_number": "CPSC475",  "course_title": "Computational Vision and Biological Perception","category": "Advanced","semester": "Year 4, Fall","year_in_program": 4, "is_required": False, "units": 4},
            {"position": 11, "course_number": "CPSC470",  "course_title": "Artificial Intelligence",                "category": "AI","semester": "Year 4, Fall","year_in_program": 4, "is_required": False, "units": 4},
        ],
    },

    # ──────────────────────────────────────────────────────
    # Georgia Tech – B.S. Computer Science (Systems & Architecture Thread)
    # ──────────────────────────────────────────────────────
    {
        "university_slug": "georgia-tech",
        "slug": "gatech-bs-computer-science-systems",
        "title": "B.S. Computer Science (Systems & Architecture Thread)",
        "degree_type": "Bachelor of Science",
        "major": "Computer Science",
        "department": "School of Computer Science",
        "description": (
            "Georgia Tech's CS program uses a 'threads' model where students "
            "pick two of nine specialization areas. This roadmap follows the "
            "Systems & Architecture thread, emphasizing OS, networks, and architecture."
        ),
        "estimated_years": 4,
        "website_url": "https://www.cc.gatech.edu/programs/bs-computer-science",
        "courses": [
            {"position": 1,  "course_number": "CS1301",   "course_title": "Introduction to Computing",              "category": "Core","semester": "Year 1, Fall","year_in_program": 1, "is_required": True, "units": 3},
            {"position": 2,  "course_number": "CS1331",   "course_title": "Introduction to Object-Oriented Programming","category": "Core","semester": "Year 1, Spring","year_in_program": 1, "is_required": True, "units": 3},
            {"position": 3,  "course_number": "MATH1551", "course_title": "Differential Calculus",                  "category": "Math","semester": "Year 1, Fall","year_in_program": 1, "is_required": True, "units": 2},
            {"position": 4,  "course_number": "MATH1552", "course_title": "Integral Calculus",                      "category": "Math","semester": "Year 1, Spring","year_in_program": 1, "is_required": True, "units": 4},
            {"position": 5,  "course_number": "CS1332",   "course_title": "Data Structures and Algorithms",         "category": "Core","semester": "Year 2, Fall","year_in_program": 2, "is_required": True, "units": 3},
            {"position": 6,  "course_number": "CS2110",   "course_title": "Computer Organization and Programming",  "category": "Core","semester": "Year 2, Fall","year_in_program": 2, "is_required": True, "units": 4},
            {"position": 7,  "course_number": "MATH2605", "course_title": "Calculus III for Computer Scientists",   "category": "Math","semester": "Year 2, Fall","year_in_program": 2, "is_required": True, "units": 2},
            {"position": 8,  "course_number": "CS2200",   "course_title": "Computer Systems and Networks",          "category": "Systems","semester": "Year 2, Spring","year_in_program": 2, "is_required": True, "units": 4},
            {"position": 9,  "course_number": "CS3510",   "course_title": "Design and Analysis of Algorithms",      "category": "Theory","semester": "Year 3, Fall","year_in_program": 3, "is_required": True, "units": 3},
            {"position": 10, "course_number": "CS3220",   "course_title": "Introduction to Computing Organization", "category": "Systems","semester": "Year 3, Fall","year_in_program": 3, "is_required": True, "units": 3},
            {"position": 11, "course_number": "CS4400",   "course_title": "Introduction to Database Systems",       "category": "Systems","semester": "Year 3, Spring","year_in_program": 3, "is_required": False, "units": 3},
            {"position": 12, "course_number": "CS4210",   "course_title": "Advanced Operating Systems",             "category": "Systems","semester": "Year 4, Fall","year_in_program": 4, "is_required": True, "units": 3},
            {"position": 13, "course_number": "CS4251",   "course_title": "Computer Networks I",                    "category": "Systems","semester": "Year 4, Fall","year_in_program": 4, "is_required": False, "units": 3},
            {"position": 14, "course_number": "CS4270",   "course_title": "Digital System Design",                  "category": "Advanced","semester": "Year 4, Spring","year_in_program": 4, "is_required": False, "units": 3},
            {"position": 15, "course_number": "CS4901",   "course_title": "Senior Design Project",                  "category": "Capstone","semester": "Year 4, Spring","year_in_program": 4, "is_required": True, "units": 3},
        ],
    },

    # ──────────────────────────────────────────────────────
    # Georgia Tech – B.S. Computer Science (Intelligence Thread)
    # ──────────────────────────────────────────────────────
    {
        "university_slug": "georgia-tech",
        "slug": "gatech-bs-computer-science-intelligence",
        "title": "B.S. Computer Science (Intelligence Thread)",
        "degree_type": "Bachelor of Science",
        "major": "Computer Science",
        "department": "School of Computer Science",
        "description": (
            "Georgia Tech's Intelligence thread focuses on AI, machine learning, "
            "and robotics. Combined with a second thread, students gain both "
            "depth in AI and breadth across CS."
        ),
        "estimated_years": 4,
        "website_url": "https://www.cc.gatech.edu/programs/bs-computer-science",
        "courses": [
            {"position": 1,  "course_number": "CS1301",   "course_title": "Introduction to Computing",              "category": "Core","semester": "Year 1, Fall","year_in_program": 1, "is_required": True, "units": 3},
            {"position": 2,  "course_number": "CS1331",   "course_title": "Introduction to Object-Oriented Programming","category": "Core","semester": "Year 1, Spring","year_in_program": 1, "is_required": True, "units": 3},
            {"position": 3,  "course_number": "CS1332",   "course_title": "Data Structures and Algorithms",         "category": "Core","semester": "Year 2, Fall","year_in_program": 2, "is_required": True, "units": 3},
            {"position": 4,  "course_number": "CS3600",   "course_title": "Introduction to Artificial Intelligence","category": "Core","semester": "Year 2, Spring","year_in_program": 2, "is_required": True, "units": 3},
            {"position": 5,  "course_number": "CS4641",   "course_title": "Machine Learning",                       "category": "Core","semester": "Year 3, Fall","year_in_program": 3, "is_required": True, "units": 3},
            {"position": 6,  "course_number": "CS4649",   "course_title": "Robot Intelligence: Planning",           "category": "AI","semester": "Year 3, Fall","year_in_program": 3, "is_required": False, "units": 3},
            {"position": 7,  "course_number": "CS4650",   "course_title": "Natural Language Processing",            "category": "AI","semester": "Year 3, Spring","year_in_program": 3, "is_required": False, "units": 3},
            {"position": 8,  "course_number": "CS4476",   "course_title": "Computer Vision",                        "category": "AI","semester": "Year 3, Spring","year_in_program": 3, "is_required": False, "units": 3},
            {"position": 9,  "course_number": "CS7641",   "course_title": "Machine Learning (Graduate)",            "category": "Advanced","semester": "Year 4, Fall","year_in_program": 4, "is_required": False, "units": 3, "notes": "Undergrads may enroll"},
            {"position": 10, "course_number": "CS4731",   "course_title": "Game Artificial Intelligence",           "category": "AI","semester": "Year 4, Spring","year_in_program": 4, "is_required": False, "units": 3},
            {"position": 11, "course_number": "CS4901",   "course_title": "Senior Design Project",                  "category": "Capstone","semester": "Year 4, Spring","year_in_program": 4, "is_required": True, "units": 3},
        ],
    },

    # ──────────────────────────────────────────────────────
    # University of Oxford – Computer Science (MEng)
    # ──────────────────────────────────────────────────────
    {
        "university_slug": "oxford",
        "slug": "oxford-meng-computer-science",
        "title": "M.Eng. Computer Science",
        "degree_type": "Master of Engineering",
        "major": "Computer Science",
        "department": "Department of Computer Science",
        "description": (
            "Oxford's four-year integrated MEng in Computer Science combines rigorous "
            "mathematical foundations with programming, logic, algorithms, and "
            "advanced topics in year 3-4 specialization."
        ),
        "estimated_years": 4,
        "website_url": "https://www.cs.ox.ac.uk/admissions/undergraduate/",
        "courses": [
            # Year 1 – Part A
            {"position": 1,  "course_number": "CS1P1",    "course_title": "Functional Programming",                "category": "Core","semester": "Year 1, Michaelmas","year_in_program": 1, "is_required": True},
            {"position": 2,  "course_number": "CS1P2",    "course_title": "Design and Analysis of Algorithms",    "category": "Core","semester": "Year 1, Michaelmas","year_in_program": 1, "is_required": True},
            {"position": 3,  "course_number": "CS1P3",    "course_title": "Discrete Mathematics",                 "category": "Math","semester": "Year 1, Michaelmas","year_in_program": 1, "is_required": True},
            {"position": 4,  "course_number": "CS1P4",    "course_title": "Introduction to Formal Proof",         "category": "Math","semester": "Year 1, Hilary","year_in_program": 1, "is_required": True},
            {"position": 5,  "course_number": "CS1P5",    "course_title": "Linear Algebra",                       "category": "Math","semester": "Year 1, Hilary","year_in_program": 1, "is_required": True},
            {"position": 6,  "course_number": "CS1P6",    "course_title": "Continuous Mathematics",               "category": "Math","semester": "Year 1, Trinity","year_in_program": 1, "is_required": True},
            # Year 2 – Part A
            {"position": 7,  "course_number": "CS2P1",    "course_title": "Imperative Programming",               "category": "Core","semester": "Year 2, Michaelmas","year_in_program": 2, "is_required": True},
            {"position": 8,  "course_number": "CS2P2",    "course_title": "Models of Computation",                "category": "Theory","semester": "Year 2, Michaelmas","year_in_program": 2, "is_required": True},
            {"position": 9,  "course_number": "CS2P3",    "course_title": "Probability",                          "category": "Math","semester": "Year 2, Hilary","year_in_program": 2, "is_required": True},
            {"position": 10, "course_number": "CS2P4",    "course_title": "Computer Architecture",                "category": "Systems","semester": "Year 2, Hilary","year_in_program": 2, "is_required": True},
            {"position": 11, "course_number": "CS2P5",    "course_title": "Databases",                            "category": "Systems","semester": "Year 2, Trinity","year_in_program": 2, "is_required": True},
            {"position": 12, "course_number": "CS2P6",    "course_title": "Logic and Proof",                      "category": "Theory","semester": "Year 2, Trinity","year_in_program": 2, "is_required": True},
            # Year 3 – Part B
            {"position": 13, "course_number": "CS3opt",   "course_title": "Machine Learning",                     "category": "Advanced","semester": "Year 3","year_in_program": 3, "is_required": False},
            {"position": 14, "course_number": "CS3opt2",  "course_title": "Computer Networks",                    "category": "Advanced","semester": "Year 3","year_in_program": 3, "is_required": False},
            {"position": 15, "course_number": "CS3opt3",  "course_title": "Concurrent Algorithms and Data Structures","category": "Advanced","semester": "Year 3","year_in_program": 3, "is_required": False},
            {"position": 16, "course_number": "CS3opt4",  "course_title": "Programming Languages",                "category": "Advanced","semester": "Year 3","year_in_program": 3, "is_required": False},
            # Year 4 – Part C
            {"position": 17, "course_number": "CS4opt1",  "course_title": "Computational Learning Theory",        "category": "Advanced","semester": "Year 4","year_in_program": 4, "is_required": False},
            {"position": 18, "course_number": "CS4opt2",  "course_title": "Information Theory",                   "category": "Advanced","semester": "Year 4","year_in_program": 4, "is_required": False},
            {"position": 19, "course_number": "CS4P",     "course_title": "Project",                              "category": "Capstone","semester": "Year 4","year_in_program": 4, "is_required": True},
        ],
    },

    # ──────────────────────────────────────────────────────
    # University of Cambridge – Computer Science (Tripos)
    # ──────────────────────────────────────────────────────
    {
        "university_slug": "cambridge",
        "slug": "cambridge-ba-computer-science",
        "title": "B.A. / M.Eng. Computer Science (Computer Science Tripos)",
        "degree_type": "Bachelor of Arts / Master of Engineering",
        "major": "Computer Science",
        "department": "Department of Computer Science and Technology",
        "description": (
            "Cambridge's Computer Science Tripos spans three years (BA) or four "
            "years (MEng). It covers theory, algorithms, programming, and systems, "
            "with significant mathematical foundations."
        ),
        "estimated_years": 4,
        "website_url": "https://www.cst.cam.ac.uk/admissions/undergraduate",
        "courses": [
            # Part 1A
            {"position": 1,  "course_number": "1A-P1",   "course_title": "Foundations of Computer Science",       "category": "Core","semester": "Year 1, Michaelmas","year_in_program": 1, "is_required": True},
            {"position": 2,  "course_number": "1A-P2",   "course_title": "Object-Oriented Programming",           "category": "Core","semester": "Year 1, Lent","year_in_program": 1, "is_required": True},
            {"position": 3,  "course_number": "1A-P3",   "course_title": "Introduction to Graphics",              "category": "Core","semester": "Year 1, Easter","year_in_program": 1, "is_required": True},
            {"position": 4,  "course_number": "1A-P4",   "course_title": "Digital Electronics",                   "category": "Core","semester": "Year 1, Michaelmas","year_in_program": 1, "is_required": True},
            {"position": 5,  "course_number": "1A-P5",   "course_title": "Algorithms",                            "category": "Theory","semester": "Year 1, Lent","year_in_program": 1, "is_required": True},
            {"position": 6,  "course_number": "1A-P6",   "course_title": "Discrete Mathematics",                  "category": "Math","semester": "Year 1, Michaelmas","year_in_program": 1, "is_required": True},
            # Part 1B
            {"position": 7,  "course_number": "1B-P1",   "course_title": "Compiler Construction",                 "category": "Core","semester": "Year 2, Michaelmas","year_in_program": 2, "is_required": True},
            {"position": 8,  "course_number": "1B-P2",   "course_title": "Computer Design",                       "category": "Systems","semester": "Year 2, Lent","year_in_program": 2, "is_required": True},
            {"position": 9,  "course_number": "1B-P3",   "course_title": "Artificial Intelligence I",             "category": "AI","semester": "Year 2, Michaelmas","year_in_program": 2, "is_required": True},
            {"position": 10, "course_number": "1B-P4",   "course_title": "Complexity Theory",                     "category": "Theory","semester": "Year 2, Lent","year_in_program": 2, "is_required": True},
            {"position": 11, "course_number": "1B-P5",   "course_title": "Operating Systems",                     "category": "Systems","semester": "Year 2, Easter","year_in_program": 2, "is_required": True},
            # Part II
            {"position": 12, "course_number": "2-opt1",  "course_title": "Machine Learning and Bayesian Inference","category": "Advanced","semester": "Year 3","year_in_program": 3, "is_required": False},
            {"position": 13, "course_number": "2-opt2",  "course_title": "Distributed Systems",                   "category": "Advanced","semester": "Year 3","year_in_program": 3, "is_required": False},
            {"position": 14, "course_number": "2-opt3",  "course_title": "Computer Graphics and Image Processing","category": "Advanced","semester": "Year 3","year_in_program": 3, "is_required": False},
            {"position": 15, "course_number": "2-opt4",  "course_title": "Information Theory",                    "category": "Advanced","semester": "Year 3","year_in_program": 3, "is_required": False},
            {"position": 16, "course_number": "2-proj",  "course_title": "Dissertation",                          "category": "Capstone","semester": "Year 3","year_in_program": 3, "is_required": True},
            # Part III (MEng only)
            {"position": 17, "course_number": "3-opt1",  "course_title": "Advanced Machine Learning",             "category": "Advanced","semester": "Year 4","year_in_program": 4, "is_required": False},
            {"position": 18, "course_number": "3-opt2",  "course_title": "Security",                              "category": "Advanced","semester": "Year 4","year_in_program": 4, "is_required": False},
            {"position": 19, "course_number": "3-proj",  "course_title": "Research Project",                      "category": "Capstone","semester": "Year 4","year_in_program": 4, "is_required": True},
        ],
    },

    # ──────────────────────────────────────────────────────
    # MIT – MEng Electrical Engineering & Computer Science
    # ──────────────────────────────────────────────────────
    {
        "university_slug": "mit",
        "slug": "mit-meng-eecs",
        "title": "M.Eng. Electrical Engineering & Computer Science (Course VI)",
        "degree_type": "Master of Engineering",
        "major": "Electrical Engineering and Computer Science",
        "department": "Electrical Engineering & Computer Science",
        "description": (
            "MIT's MEng is a fifth-year program for Course 6 undergrads. "
            "Students take advanced graduate subjects and complete an independent "
            "research thesis in their area of specialization."
        ),
        "estimated_years": 1,
        "website_url": "https://www.eecs.mit.edu/academics/graduate-programs/meng/",
        "courses": [
            {"position": 1,  "course_number": "6.854J",  "course_title": "Advanced Algorithms",                    "category": "Theory","semester": "Year 1, Fall","year_in_program": 1, "is_required": False, "units": 12},
            {"position": 2,  "course_number": "6.867",   "course_title": "Machine Learning",                       "category": "AI","semester": "Year 1, Fall","year_in_program": 1, "is_required": False, "units": 12},
            {"position": 3,  "course_number": "6.858",   "course_title": "Computer Systems Security",              "category": "Systems","semester": "Year 1, Fall","year_in_program": 1, "is_required": False, "units": 12},
            {"position": 4,  "course_number": "6.824",   "course_title": "Distributed Systems",                    "category": "Systems","semester": "Year 1, Spring","year_in_program": 1, "is_required": False, "units": 12},
            {"position": 5,  "course_number": "6.864",   "course_title": "Advanced Natural Language Processing",   "category": "AI","semester": "Year 1, Spring","year_in_program": 1, "is_required": False, "units": 12},
            {"position": 6,  "course_number": "6.THM",   "course_title": "MEng Thesis",                            "category": "Capstone","semester": "Year 1, Fall/Spring","year_in_program": 1, "is_required": True, "units": 18},
        ],
    },

    # ──────────────────────────────────────────────────────
    # Khan Academy – Self-paced Mathematics Pathway
    # ──────────────────────────────────────────────────────
    {
        "university_slug": "khan-academy",
        "slug": "khan-math-pathway",
        "title": "Mathematics Pathway (Pre-Algebra through Calculus)",
        "degree_type": "Self-paced",
        "major": "Mathematics",
        "department": "Mathematics",
        "description": (
            "Khan Academy's complete mathematics pathway takes learners from "
            "pre-algebra through AP Calculus and Statistics. Designed for "
            "self-paced mastery learning."
        ),
        "estimated_years": 4,
        "website_url": "https://www.khanacademy.org/math",
        "courses": [
            {"position": 1,  "course_number": None,  "course_title": "Pre-algebra",                        "category": "Foundations","semester": "Stage 1","year_in_program": 1, "is_required": True},
            {"position": 2,  "course_number": None,  "course_title": "Algebra 1",                          "category": "Foundations","semester": "Stage 2","year_in_program": 1, "is_required": True},
            {"position": 3,  "course_number": None,  "course_title": "Geometry",                           "category": "Foundations","semester": "Stage 3","year_in_program": 2, "is_required": True},
            {"position": 4,  "course_number": None,  "course_title": "Algebra 2",                          "category": "Foundations","semester": "Stage 4","year_in_program": 2, "is_required": True},
            {"position": 5,  "course_number": None,  "course_title": "Trigonometry",                       "category": "Intermediate","semester": "Stage 5","year_in_program": 3, "is_required": True},
            {"position": 6,  "course_number": None,  "course_title": "Precalculus",                        "category": "Intermediate","semester": "Stage 6","year_in_program": 3, "is_required": True},
            {"position": 7,  "course_number": "AP",  "course_title": "AP Calculus AB",                     "category": "Advanced","semester": "Stage 7","year_in_program": 4, "is_required": True},
            {"position": 8,  "course_number": "AP",  "course_title": "AP Calculus BC",                     "category": "Advanced","semester": "Stage 8","year_in_program": 4, "is_required": False},
            {"position": 9,  "course_number": "AP",  "course_title": "AP Statistics",                      "category": "Advanced","semester": "Stage 8","year_in_program": 4, "is_required": False},
            {"position": 10, "course_number": None,  "course_title": "Multivariable Calculus",             "category": "Advanced","semester": "Stage 9","year_in_program": 4, "is_required": False},
            {"position": 11, "course_number": None,  "course_title": "Linear Algebra",                     "category": "Advanced","semester": "Stage 10","year_in_program": 4, "is_required": False},
            {"position": 12, "course_number": None,  "course_title": "Differential Equations",             "category": "Advanced","semester": "Stage 11","year_in_program": 4, "is_required": False},
        ],
    },

    # ──────────────────────────────────────────────────────
    # freeCodeCamp – Full-Stack Web Development Pathway
    # ──────────────────────────────────────────────────────
    {
        "university_slug": "freecodecamp",
        "slug": "freecodecamp-fullstack-web-dev",
        "title": "Full-Stack Web Development Curriculum",
        "degree_type": "Self-paced Certification",
        "major": "Web Development",
        "department": "Software Engineering",
        "description": (
            "freeCodeCamp's full-stack certification pathway covers HTML/CSS, "
            "JavaScript, front-end frameworks, APIs, databases, and deployment "
            "— approximately 3,000 hours of content."
        ),
        "estimated_years": 2,
        "website_url": "https://www.freecodecamp.org/learn",
        "courses": [
            {"position": 1,  "course_number": None, "course_title": "Responsive Web Design",                  "category": "Core","semester": "Phase 1","year_in_program": 1, "is_required": True},
            {"position": 2,  "course_number": None, "course_title": "JavaScript Algorithms and Data Structures","category": "Core","semester": "Phase 2","year_in_program": 1, "is_required": True},
            {"position": 3,  "course_number": None, "course_title": "Front End Libraries (React)",            "category": "Core","semester": "Phase 3","year_in_program": 1, "is_required": True},
            {"position": 4,  "course_number": None, "course_title": "Data Visualization",                    "category": "Core","semester": "Phase 4","year_in_program": 1, "is_required": True},
            {"position": 5,  "course_number": None, "course_title": "Relational Database (SQL & PostgreSQL)", "category": "Core","semester": "Phase 5","year_in_program": 2, "is_required": True},
            {"position": 6,  "course_number": None, "course_title": "Back End Development and APIs (Node.js)","category": "Core","semester": "Phase 6","year_in_program": 2, "is_required": True},
            {"position": 7,  "course_number": None, "course_title": "Quality Assurance",                     "category": "Core","semester": "Phase 7","year_in_program": 2, "is_required": True},
            {"position": 8,  "course_number": None, "course_title": "Scientific Computing with Python",      "category": "Core","semester": "Phase 8","year_in_program": 2, "is_required": True},
            {"position": 9,  "course_number": None, "course_title": "Data Analysis with Python",             "category": "Advanced","semester": "Phase 9","year_in_program": 2, "is_required": False},
            {"position": 10, "course_number": None, "course_title": "Information Security",                  "category": "Advanced","semester": "Phase 10","year_in_program": 2, "is_required": False},
            {"position": 11, "course_number": None, "course_title": "Machine Learning with Python",          "category": "Advanced","semester": "Phase 11","year_in_program": 2, "is_required": False},
        ],
    },

    # ──────────────────────────────────────────────────────
    # MIT – Mathematics (Course 18)
    # ──────────────────────────────────────────────────────
    {
        "university_slug": "mit",
        "slug": "mit-bs-mathematics",
        "title": "B.S. Mathematics (Course 18)",
        "degree_type": "Bachelor of Science",
        "major": "Mathematics",
        "department": "Mathematics",
        "description": (
            "MIT's Mathematics program (Course 18) offers rigorous training in analysis, "
            "algebra, geometry, and topology, preparing students for research, graduate "
            "school, finance, and technology careers."
        ),
        "estimated_years": 4,
        "website_url": "https://math.mit.edu/academics/undergrad/major/",
        "courses": [
            {"position": 1,  "course_number": "18.01",  "course_title": "Single Variable Calculus",           "category": "Core",    "semester": "Year 1, Fall",   "year_in_program": 1, "is_required": True,  "units": 12},
            {"position": 2,  "course_number": "18.02",  "course_title": "Multivariable Calculus",             "category": "Core",    "semester": "Year 1, Spring", "year_in_program": 1, "is_required": True,  "units": 12},
            {"position": 3,  "course_number": "18.03",  "course_title": "Differential Equations",             "category": "Core",    "semester": "Year 2, Fall",   "year_in_program": 2, "is_required": True,  "units": 12},
            {"position": 4,  "course_number": "18.06",  "course_title": "Linear Algebra",                     "category": "Core",    "semester": "Year 2, Fall",   "year_in_program": 2, "is_required": True,  "units": 12},
            {"position": 5,  "course_number": "18.100A","course_title": "Real Analysis",                      "category": "Core",    "semester": "Year 2, Spring", "year_in_program": 2, "is_required": True,  "units": 12},
            {"position": 6,  "course_number": "18.701", "course_title": "Algebra I",                          "category": "Core",    "semester": "Year 3, Fall",   "year_in_program": 3, "is_required": True,  "units": 12},
            {"position": 7,  "course_number": "18.702", "course_title": "Algebra II",                         "category": "Core",    "semester": "Year 3, Spring", "year_in_program": 3, "is_required": True,  "units": 12},
            {"position": 8,  "course_number": "18.901", "course_title": "Introduction to Topology",           "category": "Advanced","semester": "Year 3, Fall",   "year_in_program": 3, "is_required": False, "units": 12},
            {"position": 9,  "course_number": "18.101", "course_title": "Analysis II",                        "category": "Advanced","semester": "Year 3, Spring", "year_in_program": 3, "is_required": False, "units": 12},
            {"position": 10, "course_number": "18.112", "course_title": "Complex Analysis",                   "category": "Advanced","semester": "Year 4, Fall",   "year_in_program": 4, "is_required": False, "units": 12},
            {"position": 11, "course_number": "18.781", "course_title": "Theory of Numbers",                  "category": "Advanced","semester": "Year 4, Fall",   "year_in_program": 4, "is_required": False, "units": 12},
            {"position": 12, "course_number": "18.994", "course_title": "Seminar in Mathematics (Thesis)",    "category": "Capstone","semester": "Year 4, Spring", "year_in_program": 4, "is_required": True,  "units": 12},
        ],
    },

    # ──────────────────────────────────────────────────────
    # Princeton – A.B. Mathematics
    # ──────────────────────────────────────────────────────
    {
        "university_slug": "princeton",
        "slug": "princeton-ab-mathematics",
        "title": "A.B. Mathematics",
        "degree_type": "Bachelor of Arts",
        "major": "Mathematics",
        "department": "Mathematics",
        "description": (
            "Princeton's mathematics A.B. focuses on pure mathematics — analysis, algebra, "
            "topology, and geometry — with a strong emphasis on proof writing and a "
            "senior independent work (thesis) requirement."
        ),
        "estimated_years": 4,
        "website_url": "https://www.math.princeton.edu/undergraduate",
        "courses": [
            {"position": 1,  "course_number": "MAT201", "course_title": "Multivariable Calculus",             "category": "Core",    "semester": "Year 1, Fall",   "year_in_program": 1, "is_required": True,  "units": 4},
            {"position": 2,  "course_number": "MAT202", "course_title": "Linear Algebra with Applications",   "category": "Core",    "semester": "Year 1, Spring", "year_in_program": 1, "is_required": True,  "units": 4},
            {"position": 3,  "course_number": "MAT215", "course_title": "Single Variable Analysis",           "category": "Core",    "semester": "Year 2, Fall",   "year_in_program": 2, "is_required": True,  "units": 4},
            {"position": 4,  "course_number": "MAT217", "course_title": "Honors Linear Algebra",              "category": "Core",    "semester": "Year 2, Fall",   "year_in_program": 2, "is_required": True,  "units": 4},
            {"position": 5,  "course_number": "MAT218", "course_title": "Analysis II",                        "category": "Core",    "semester": "Year 2, Spring", "year_in_program": 2, "is_required": True,  "units": 4},
            {"position": 6,  "course_number": "MAT345", "course_title": "Algebra I",                          "category": "Core",    "semester": "Year 3, Fall",   "year_in_program": 3, "is_required": True,  "units": 4},
            {"position": 7,  "course_number": "MAT346", "course_title": "Algebra II",                         "category": "Core",    "semester": "Year 3, Spring", "year_in_program": 3, "is_required": True,  "units": 4},
            {"position": 8,  "course_number": "MAT365", "course_title": "Topology",                           "category": "Advanced","semester": "Year 3, Spring", "year_in_program": 3, "is_required": False, "units": 4},
            {"position": 9,  "course_number": "MAT449", "course_title": "Topics in Geometry",                 "category": "Advanced","semester": "Year 4, Fall",   "year_in_program": 4, "is_required": False, "units": 4},
            {"position": 10, "course_number": "MAT419", "course_title": "Topics in Number Theory",            "category": "Advanced","semester": "Year 4, Fall",   "year_in_program": 4, "is_required": False, "units": 4},
            {"position": 11, "course_number": "MAT498", "course_title": "Senior Thesis",                      "category": "Capstone","semester": "Year 4, Spring", "year_in_program": 4, "is_required": True,  "units": 4},
        ],
    },

    # ──────────────────────────────────────────────────────
    # Stanford – B.S. Mathematics
    # ──────────────────────────────────────────────────────
    {
        "university_slug": "stanford",
        "slug": "stanford-bs-mathematics",
        "title": "B.S. Mathematics",
        "degree_type": "Bachelor of Science",
        "major": "Mathematics",
        "department": "Mathematics",
        "description": (
            "Stanford's B.S. in Mathematics provides broad training in real and complex "
            "analysis, abstract algebra, and topology, with flexibility for applied tracks "
            "including probability, numerical analysis, and mathematical physics."
        ),
        "estimated_years": 4,
        "website_url": "https://mathematics.stanford.edu/academics/undergraduate",
        "courses": [
            {"position": 1,  "course_number": "MATH41",  "course_title": "Calculus",                         "category": "Core",    "semester": "Year 1, Fall",   "year_in_program": 1, "is_required": True,  "units": 5},
            {"position": 2,  "course_number": "MATH42",  "course_title": "Calculus II",                      "category": "Core",    "semester": "Year 1, Spring", "year_in_program": 1, "is_required": True,  "units": 5},
            {"position": 3,  "course_number": "MATH51",  "course_title": "Linear Algebra and Differential Calculus","category": "Core", "semester": "Year 2, Fall",  "year_in_program": 2, "is_required": True,  "units": 5},
            {"position": 4,  "course_number": "MATH52",  "course_title": "Integral Calculus of Several Variables","category": "Core","semester": "Year 2, Spring","year_in_program": 2, "is_required": True,  "units": 5},
            {"position": 5,  "course_number": "MATH115", "course_title": "Functions of a Real Variable",     "category": "Core",    "semester": "Year 3, Fall",   "year_in_program": 3, "is_required": True,  "units": 5},
            {"position": 6,  "course_number": "MATH120", "course_title": "Groups and Rings",                  "category": "Core",    "semester": "Year 3, Fall",   "year_in_program": 3, "is_required": True,  "units": 5},
            {"position": 7,  "course_number": "MATH116", "course_title": "Complex Analysis",                  "category": "Core",    "semester": "Year 3, Spring", "year_in_program": 3, "is_required": True,  "units": 5},
            {"position": 8,  "course_number": "MATH121", "course_title": "Galois Theory",                     "category": "Advanced","semester": "Year 3, Spring", "year_in_program": 3, "is_required": False, "units": 5},
            {"position": 9,  "course_number": "MATH171", "course_title": "Fundamental Concepts of Analysis", "category": "Advanced","semester": "Year 4, Fall",   "year_in_program": 4, "is_required": False, "units": 5},
            {"position": 10, "course_number": "MATH215", "course_title": "Algebraic Topology",               "category": "Advanced","semester": "Year 4, Spring", "year_in_program": 4, "is_required": False, "units": 5},
        ],
    },

    # ──────────────────────────────────────────────────────
    # MIT – Biology (Course 7)
    # ──────────────────────────────────────────────────────
    {
        "university_slug": "mit",
        "slug": "mit-bs-biology",
        "title": "B.S. Biology (Course 7)",
        "degree_type": "Bachelor of Science",
        "major": "Biology",
        "department": "Biology",
        "description": (
            "MIT's Biology program (Course 7) covers molecular and cell biology, genetics, "
            "biochemistry, and developmental biology. Students gain deep experimental skills "
            "through required lab courses and a supervised research thesis."
        ),
        "estimated_years": 4,
        "website_url": "https://biology.mit.edu/undergraduate/major/",
        "courses": [
            {"position": 1,  "course_number": "7.012",  "course_title": "Introductory Biology",              "category": "Core",    "semester": "Year 1, Fall",   "year_in_program": 1, "is_required": True,  "units": 12},
            {"position": 2,  "course_number": "5.111",  "course_title": "Principles of Chemical Science",    "category": "Science", "semester": "Year 1, Fall",   "year_in_program": 1, "is_required": True,  "units": 12},
            {"position": 3,  "course_number": "18.01",  "course_title": "Single Variable Calculus",          "category": "Math",    "semester": "Year 1, Fall",   "year_in_program": 1, "is_required": True,  "units": 12},
            {"position": 4,  "course_number": "5.112",  "course_title": "Principles of Chemical Science II", "category": "Science", "semester": "Year 1, Spring", "year_in_program": 1, "is_required": True,  "units": 12},
            {"position": 5,  "course_number": "18.02",  "course_title": "Multivariable Calculus",            "category": "Math",    "semester": "Year 1, Spring", "year_in_program": 1, "is_required": True,  "units": 12},
            {"position": 6,  "course_number": "7.02",   "course_title": "Introduction to Experimental Biology and Communication","category": "Lab","semester": "Year 2, Fall", "year_in_program": 2, "is_required": True,  "units": 15},
            {"position": 7,  "course_number": "7.03",   "course_title": "Genetics",                          "category": "Core",    "semester": "Year 2, Fall",   "year_in_program": 2, "is_required": True,  "units": 12},
            {"position": 8,  "course_number": "5.07",   "course_title": "Biological Chemistry I",            "category": "Core",    "semester": "Year 2, Spring", "year_in_program": 2, "is_required": True,  "units": 12},
            {"position": 9,  "course_number": "7.05",   "course_title": "General Biochemistry",              "category": "Core",    "semester": "Year 2, Spring", "year_in_program": 2, "is_required": True,  "units": 12},
            {"position": 10, "course_number": "7.06",   "course_title": "Cell Biology",                      "category": "Core",    "semester": "Year 3, Fall",   "year_in_program": 3, "is_required": True,  "units": 12},
            {"position": 11, "course_number": "7.28",   "course_title": "Molecular Biology",                 "category": "Core",    "semester": "Year 3, Fall",   "year_in_program": 3, "is_required": True,  "units": 12},
            {"position": 12, "course_number": "7.29J",  "course_title": "Cellular Neurobiology",             "category": "Advanced","semester": "Year 3, Spring", "year_in_program": 3, "is_required": False, "units": 12},
            {"position": 13, "course_number": "7.32",   "course_title": "Systems Biology",                   "category": "Advanced","semester": "Year 3, Spring", "year_in_program": 3, "is_required": False, "units": 12},
            {"position": 14, "course_number": "7.089",  "course_title": "Biology Research Seminar",          "category": "Capstone","semester": "Year 4, Fall",   "year_in_program": 4, "is_required": True,  "units": 6},
            {"position": 15, "course_number": "7.THU",  "course_title": "Undergraduate Research – Thesis",   "category": "Capstone","semester": "Year 4, Spring", "year_in_program": 4, "is_required": True,  "units": 12},
        ],
    },

    # ──────────────────────────────────────────────────────
    # Stanford – B.S. Biology
    # ──────────────────────────────────────────────────────
    {
        "university_slug": "stanford",
        "slug": "stanford-bs-biology",
        "title": "B.S. Biology",
        "degree_type": "Bachelor of Science",
        "major": "Biology",
        "department": "Biology",
        "description": (
            "Stanford's Biology B.S. encompasses molecular, cellular, developmental, and "
            "evolutionary biology. Students complete laboratory rotations and a senior "
            "research project or capstone, with flexibility across life science tracks."
        ),
        "estimated_years": 4,
        "website_url": "https://biology.stanford.edu/academics/undergraduate-program",
        "courses": [
            {"position": 1,  "course_number": "BIO81",   "course_title": "Biochemistry",                     "category": "Core",    "semester": "Year 1, Fall",   "year_in_program": 1, "is_required": True,  "units": 4},
            {"position": 2,  "course_number": "CHEM31A",  "course_title": "Chemical Principles I",           "category": "Science", "semester": "Year 1, Fall",   "year_in_program": 1, "is_required": True,  "units": 5},
            {"position": 3,  "course_number": "MATH19",   "course_title": "Calculus",                        "category": "Math",    "semester": "Year 1, Fall",   "year_in_program": 1, "is_required": True,  "units": 3},
            {"position": 4,  "course_number": "BIO82",   "course_title": "Cell Biology",                     "category": "Core",    "semester": "Year 1, Spring", "year_in_program": 1, "is_required": True,  "units": 4},
            {"position": 5,  "course_number": "CHEM31B",  "course_title": "Chemical Principles II",          "category": "Science", "semester": "Year 1, Spring", "year_in_program": 1, "is_required": True,  "units": 5},
            {"position": 6,  "course_number": "BIO83",   "course_title": "Genetics",                         "category": "Core",    "semester": "Year 2, Fall",   "year_in_program": 2, "is_required": True,  "units": 4},
            {"position": 7,  "course_number": "BIOC218", "course_title": "Molecular Biology Laboratory",     "category": "Lab",     "semester": "Year 2, Fall",   "year_in_program": 2, "is_required": True,  "units": 4},
            {"position": 8,  "course_number": "BIO84",   "course_title": "Developmental Biology",            "category": "Core",    "semester": "Year 2, Spring", "year_in_program": 2, "is_required": True,  "units": 4},
            {"position": 9,  "course_number": "STATS141", "course_title": "Statistics for Biologists",       "category": "Math",    "semester": "Year 2, Spring", "year_in_program": 2, "is_required": True,  "units": 4},
            {"position": 10, "course_number": "BIO150",  "course_title": "Evolutionary Biology",             "category": "Core",    "semester": "Year 3, Fall",   "year_in_program": 3, "is_required": True,  "units": 4},
            {"position": 11, "course_number": "BIO201",  "course_title": "Molecular Biology: Advanced Topics","category": "Advanced","semester": "Year 3, Spring","year_in_program": 3, "is_required": False, "units": 4},
            {"position": 12, "course_number": "BIOE", "course_title": "Senior Research Project",             "category": "Capstone","semester": "Year 4, Spring", "year_in_program": 4, "is_required": True,  "units": 5},
        ],
    },

    # ──────────────────────────────────────────────────────
    # MIT – Mechanical Engineering (Course 2)
    # ──────────────────────────────────────────────────────
    {
        "university_slug": "mit",
        "slug": "mit-bs-mechanical-engineering",
        "title": "B.S. Mechanical Engineering (Course 2)",
        "degree_type": "Bachelor of Science",
        "major": "Mechanical Engineering",
        "department": "Mechanical Engineering",
        "description": (
            "MIT's Mechanical Engineering program (Course 2) trains students in the "
            "design and analysis of mechanical systems, covering thermodynamics, fluid "
            "mechanics, solid mechanics, dynamics, and controls with hands-on lab projects."
        ),
        "estimated_years": 4,
        "website_url": "https://meche.mit.edu/academics/undergraduate/program",
        "courses": [
            {"position": 1,  "course_number": "2.001",  "course_title": "Mechanics & Materials I",           "category": "Core",    "semester": "Year 1, Fall",   "year_in_program": 1, "is_required": True,  "units": 12},
            {"position": 2,  "course_number": "18.01",  "course_title": "Single Variable Calculus",          "category": "Math",    "semester": "Year 1, Fall",   "year_in_program": 1, "is_required": True,  "units": 12},
            {"position": 3,  "course_number": "8.01",   "course_title": "Classical Mechanics",               "category": "Science", "semester": "Year 1, Fall",   "year_in_program": 1, "is_required": True,  "units": 12},
            {"position": 4,  "course_number": "2.002",  "course_title": "Mechanics & Materials II",          "category": "Core",    "semester": "Year 1, Spring", "year_in_program": 1, "is_required": True,  "units": 12},
            {"position": 5,  "course_number": "18.02",  "course_title": "Multivariable Calculus",            "category": "Math",    "semester": "Year 1, Spring", "year_in_program": 1, "is_required": True,  "units": 12},
            {"position": 6,  "course_number": "8.02",   "course_title": "Electricity and Magnetism",         "category": "Science", "semester": "Year 1, Spring", "year_in_program": 1, "is_required": True,  "units": 12},
            {"position": 7,  "course_number": "2.003J", "course_title": "Dynamics and Vibration",            "category": "Core",    "semester": "Year 2, Fall",   "year_in_program": 2, "is_required": True,  "units": 12},
            {"position": 8,  "course_number": "2.005",  "course_title": "Thermal-Fluids Engineering I",      "category": "Core",    "semester": "Year 2, Fall",   "year_in_program": 2, "is_required": True,  "units": 12},
            {"position": 9,  "course_number": "18.03",  "course_title": "Differential Equations",            "category": "Math",    "semester": "Year 2, Fall",   "year_in_program": 2, "is_required": True,  "units": 12},
            {"position": 10, "course_number": "2.006",  "course_title": "Thermal-Fluids Engineering II",     "category": "Core",    "semester": "Year 2, Spring", "year_in_program": 2, "is_required": True,  "units": 12},
            {"position": 11, "course_number": "2.007",  "course_title": "Design and Manufacturing I",        "category": "Lab",     "semester": "Year 2, Spring", "year_in_program": 2, "is_required": True,  "units": 12},
            {"position": 12, "course_number": "2.008",  "course_title": "Design and Manufacturing II",       "category": "Lab",     "semester": "Year 3, Fall",   "year_in_program": 3, "is_required": True,  "units": 12},
            {"position": 13, "course_number": "2.004",  "course_title": "Dynamics and Control II",           "category": "Core",    "semester": "Year 3, Fall",   "year_in_program": 3, "is_required": True,  "units": 12},
            {"position": 14, "course_number": "2.014",  "course_title": "Engineering Systems Development",   "category": "Core",    "semester": "Year 3, Spring", "year_in_program": 3, "is_required": True,  "units": 12},
            {"position": 15, "course_number": "2.019",  "course_title": "Design of Ocean Systems",           "category": "Advanced","semester": "Year 4, Fall",   "year_in_program": 4, "is_required": False, "units": 12},
            {"position": 16, "course_number": "2.THU",  "course_title": "Undergraduate Thesis",              "category": "Capstone","semester": "Year 4, Spring", "year_in_program": 4, "is_required": True,  "units": 12},
        ],
    },

    # ──────────────────────────────────────────────────────
    # Georgia Tech – B.S. Mechanical Engineering
    # ──────────────────────────────────────────────────────
    {
        "university_slug": "georgia-tech",
        "slug": "gatech-bs-mechanical-engineering",
        "title": "B.S. Mechanical Engineering",
        "degree_type": "Bachelor of Science",
        "major": "Mechanical Engineering",
        "department": "George W. Woodruff School of Mechanical Engineering",
        "description": (
            "Georgia Tech's Mechanical Engineering program is consistently ranked among "
            "the nation's best. Students study thermodynamics, fluid mechanics, dynamics, "
            "and design, with required labs and a capstone senior design project."
        ),
        "estimated_years": 4,
        "website_url": "https://me.gatech.edu/undergraduate-studies",
        "courses": [
            {"position": 1,  "course_number": "PHYS2211","course_title": "Intro Physics I",                  "category": "Science", "semester": "Year 1, Fall",   "year_in_program": 1, "is_required": True,  "units": 4},
            {"position": 2,  "course_number": "MATH1551","course_title": "Differential Calculus",            "category": "Math",    "semester": "Year 1, Fall",   "year_in_program": 1, "is_required": True,  "units": 2},
            {"position": 3,  "course_number": "CHEM1310","course_title": "General Chemistry",                "category": "Science", "semester": "Year 1, Fall",   "year_in_program": 1, "is_required": True,  "units": 3},
            {"position": 4,  "course_number": "ME1770", "course_title": "Intro to Mechanical Engineering",   "category": "Core",    "semester": "Year 1, Fall",   "year_in_program": 1, "is_required": True,  "units": 3},
            {"position": 5,  "course_number": "PHYS2212","course_title": "Intro Physics II",                 "category": "Science", "semester": "Year 1, Spring", "year_in_program": 1, "is_required": True,  "units": 4},
            {"position": 6,  "course_number": "MATH1552","course_title": "Integral Calculus",                "category": "Math",    "semester": "Year 1, Spring", "year_in_program": 1, "is_required": True,  "units": 4},
            {"position": 7,  "course_number": "ME2110", "course_title": "Creative Decisions and Design",     "category": "Core",    "semester": "Year 2, Fall",   "year_in_program": 2, "is_required": True,  "units": 3},
            {"position": 8,  "course_number": "ME2202", "course_title": "Dynamics of Rigid Bodies",          "category": "Core",    "semester": "Year 2, Fall",   "year_in_program": 2, "is_required": True,  "units": 3},
            {"position": 9,  "course_number": "MATH2552","course_title": "Differential Equations",           "category": "Math",    "semester": "Year 2, Fall",   "year_in_program": 2, "is_required": True,  "units": 4},
            {"position": 10, "course_number": "ME3322", "course_title": "Thermodynamics",                    "category": "Core",    "semester": "Year 2, Spring", "year_in_program": 2, "is_required": True,  "units": 3},
            {"position": 11, "course_number": "ME3340", "course_title": "Fluid Mechanics",                   "category": "Core",    "semester": "Year 3, Fall",   "year_in_program": 3, "is_required": True,  "units": 3},
            {"position": 12, "course_number": "ME4315", "course_title": "Automatic Controls",                "category": "Core",    "semester": "Year 3, Spring", "year_in_program": 3, "is_required": True,  "units": 3},
            {"position": 13, "course_number": "ME4182", "course_title": "Heat Transfer",                     "category": "Core",    "semester": "Year 3, Spring", "year_in_program": 3, "is_required": True,  "units": 3},
            {"position": 14, "course_number": "ME4723", "course_title": "Senior Design – Capstone I",        "category": "Capstone","semester": "Year 4, Fall",   "year_in_program": 4, "is_required": True,  "units": 3},
            {"position": 15, "course_number": "ME4725", "course_title": "Senior Design – Capstone II",       "category": "Capstone","semester": "Year 4, Spring", "year_in_program": 4, "is_required": True,  "units": 3},
        ],
    },

    # ──────────────────────────────────────────────────────
    # Harvard – A.B. Economics
    # ──────────────────────────────────────────────────────
    {
        "university_slug": "harvard",
        "slug": "harvard-ab-economics",
        "title": "A.B. Economics",
        "degree_type": "Bachelor of Arts",
        "major": "Economics",
        "department": "Economics",
        "description": (
            "Harvard's Economics A.B. trains students in micro and macroeconomic theory, "
            "econometrics, and a breadth of applied fields including labor, public, and "
            "international economics. A required senior thesis develops original research skills."
        ),
        "estimated_years": 4,
        "website_url": "https://economics.harvard.edu/undergraduate",
        "courses": [
            {"position": 1,  "course_number": "ECON10A","course_title": "Principles of Economics",           "category": "Core",    "semester": "Year 1, Fall",   "year_in_program": 1, "is_required": True,  "units": 4},
            {"position": 2,  "course_number": "MATH21A","course_title": "Multivariable Calculus",             "category": "Math",    "semester": "Year 1, Fall",   "year_in_program": 1, "is_required": True,  "units": 4},
            {"position": 3,  "course_number": "ECON10B","course_title": "Principles of Economics II",         "category": "Core",    "semester": "Year 1, Spring", "year_in_program": 1, "is_required": True,  "units": 4},
            {"position": 4,  "course_number": "MATH21B","course_title": "Linear Algebra and Differential Equations","category": "Math","semester": "Year 1, Spring","year_in_program": 1, "is_required": True,  "units": 4},
            {"position": 5,  "course_number": "ECON1010A","course_title": "Microeconomic Theory",            "category": "Core",    "semester": "Year 2, Fall",   "year_in_program": 2, "is_required": True,  "units": 4},
            {"position": 6,  "course_number": "ECON1011A","course_title": "Macroeconomic Theory",            "category": "Core",    "semester": "Year 2, Spring", "year_in_program": 2, "is_required": True,  "units": 4},
            {"position": 7,  "course_number": "ECON1123", "course_title": "Introduction to Econometrics",    "category": "Core",    "semester": "Year 2, Spring", "year_in_program": 2, "is_required": True,  "units": 4},
            {"position": 8,  "course_number": "ECON1400", "course_title": "Economic History",                "category": "Elective","semester": "Year 3, Fall",   "year_in_program": 3, "is_required": False, "units": 4},
            {"position": 9,  "course_number": "ECON1450", "course_title": "Finance and Financial Markets",   "category": "Elective","semester": "Year 3, Fall",   "year_in_program": 3, "is_required": False, "units": 4},
            {"position": 10, "course_number": "ECON1530", "course_title": "Public Economics",               "category": "Elective","semester": "Year 3, Spring", "year_in_program": 3, "is_required": False, "units": 4},
            {"position": 11, "course_number": "ECON1660", "course_title": "International Trade",             "category": "Elective","semester": "Year 3, Spring", "year_in_program": 3, "is_required": False, "units": 4},
            {"position": 12, "course_number": "ECON985",  "course_title": "Senior Thesis",                   "category": "Capstone","semester": "Year 4",         "year_in_program": 4, "is_required": True,  "units": 8},
        ],
    },

    # ──────────────────────────────────────────────────────
    # MIT – Economics (Course 14)
    # ──────────────────────────────────────────────────────
    {
        "university_slug": "mit",
        "slug": "mit-bs-economics",
        "title": "B.S. Economics (Course 14)",
        "degree_type": "Bachelor of Science",
        "major": "Economics",
        "department": "Economics",
        "description": (
            "MIT's Economics B.S. (Course 14) combines rigorous economic theory with "
            "strong quantitative and mathematical training. Students study micro and macro "
            "theory, econometrics, and a variety of applied fields."
        ),
        "estimated_years": 4,
        "website_url": "https://economics.mit.edu/academic-programs/undergraduate-program",
        "courses": [
            {"position": 1,  "course_number": "14.01",  "course_title": "Principles of Microeconomics",      "category": "Core",    "semester": "Year 1, Fall",   "year_in_program": 1, "is_required": True,  "units": 12},
            {"position": 2,  "course_number": "14.02",  "course_title": "Principles of Macroeconomics",      "category": "Core",    "semester": "Year 1, Spring", "year_in_program": 1, "is_required": True,  "units": 12},
            {"position": 3,  "course_number": "18.01",  "course_title": "Single Variable Calculus",          "category": "Math",    "semester": "Year 1, Fall",   "year_in_program": 1, "is_required": True,  "units": 12},
            {"position": 4,  "course_number": "18.02",  "course_title": "Multivariable Calculus",            "category": "Math",    "semester": "Year 1, Spring", "year_in_program": 1, "is_required": True,  "units": 12},
            {"position": 5,  "course_number": "14.04",  "course_title": "Intermediate Microeconomic Theory", "category": "Core",    "semester": "Year 2, Fall",   "year_in_program": 2, "is_required": True,  "units": 12},
            {"position": 6,  "course_number": "14.05",  "course_title": "Intermediate Macroeconomics",       "category": "Core",    "semester": "Year 2, Spring", "year_in_program": 2, "is_required": True,  "units": 12},
            {"position": 7,  "course_number": "14.32",  "course_title": "Econometrics",                      "category": "Core",    "semester": "Year 2, Spring", "year_in_program": 2, "is_required": True,  "units": 12},
            {"position": 8,  "course_number": "14.41",  "course_title": "Public Finance and Public Policy",  "category": "Elective","semester": "Year 3, Fall",   "year_in_program": 3, "is_required": False, "units": 12},
            {"position": 9,  "course_number": "14.451", "course_title": "Macroeconomic Theory I",            "category": "Advanced","semester": "Year 3, Fall",   "year_in_program": 3, "is_required": False, "units": 12},
            {"position": 10, "course_number": "14.462", "course_title": "Advanced Macroeconomics",           "category": "Advanced","semester": "Year 3, Spring", "year_in_program": 3, "is_required": False, "units": 12},
            {"position": 11, "course_number": "14.33",  "course_title": "Research and Communication in Economics","category": "Capstone","semester": "Year 4, Fall","year_in_program": 4, "is_required": True,  "units": 12},
            {"position": 12, "course_number": "14.THU", "course_title": "Undergraduate Thesis in Economics", "category": "Capstone","semester": "Year 4, Spring", "year_in_program": 4, "is_required": False, "units": 12},
        ],
    },

    # ──────────────────────────────────────────────────────
    # Stanford – B.S. Statistics
    # ──────────────────────────────────────────────────────
    {
        "university_slug": "stanford",
        "slug": "stanford-bs-statistics",
        "title": "B.S. Statistics",
        "degree_type": "Bachelor of Science",
        "major": "Statistics",
        "department": "Statistics",
        "description": (
            "Stanford's Statistics B.S. provides rigorous training in probability theory, "
            "statistical inference, data analysis, and machine learning, with applications "
            "across science, engineering, medicine, and social science."
        ),
        "estimated_years": 4,
        "website_url": "https://statistics.stanford.edu/academics/undergraduate-program",
        "courses": [
            {"position": 1,  "course_number": "MATH19",  "course_title": "Calculus",                         "category": "Math",    "semester": "Year 1, Fall",   "year_in_program": 1, "is_required": True,  "units": 3},
            {"position": 2,  "course_number": "MATH20",  "course_title": "Calculus II",                      "category": "Math",    "semester": "Year 1, Spring", "year_in_program": 1, "is_required": True,  "units": 3},
            {"position": 3,  "course_number": "MATH51",  "course_title": "Linear Algebra",                   "category": "Math",    "semester": "Year 2, Fall",   "year_in_program": 2, "is_required": True,  "units": 5},
            {"position": 4,  "course_number": "CS106A",  "course_title": "Programming Methodology",          "category": "Core",    "semester": "Year 1, Spring", "year_in_program": 1, "is_required": True,  "units": 5},
            {"position": 5,  "course_number": "STATS116","course_title": "Theory of Probability",            "category": "Core",    "semester": "Year 2, Fall",   "year_in_program": 2, "is_required": True,  "units": 4},
            {"position": 6,  "course_number": "STATS200","course_title": "Introduction to Statistical Inference","category": "Core","semester": "Year 2, Spring","year_in_program": 2, "is_required": True,  "units": 4},
            {"position": 7,  "course_number": "STATS202","course_title": "Data Mining and Analysis",         "category": "Core",    "semester": "Year 3, Fall",   "year_in_program": 3, "is_required": True,  "units": 3},
            {"position": 8,  "course_number": "STATS203","course_title": "Linear Models, Generalized Linear Models","category": "Core","semester": "Year 3, Fall","year_in_program": 3, "is_required": True,  "units": 3},
            {"position": 9,  "course_number": "STATS205","course_title": "Nonparametric Statistics",         "category": "Advanced","semester": "Year 3, Spring", "year_in_program": 3, "is_required": False, "units": 3},
            {"position": 10, "course_number": "STATS217","course_title": "Introduction to Stochastic Processes","category": "Advanced","semester": "Year 3, Spring","year_in_program": 3, "is_required": False, "units": 3},
            {"position": 11, "course_number": "CS229",   "course_title": "Machine Learning",                 "category": "Advanced","semester": "Year 4, Fall",   "year_in_program": 4, "is_required": False, "units": 3},
            {"position": 12, "course_number": "STATS390","course_title": "Undergraduate Research",           "category": "Capstone","semester": "Year 4, Spring", "year_in_program": 4, "is_required": True,  "units": 4},
        ],
    },

    # ──────────────────────────────────────────────────────
    # Berkeley – B.A. Statistics
    # ──────────────────────────────────────────────────────
    {
        "university_slug": "berkeley",
        "slug": "berkeley-ba-statistics",
        "title": "B.A. Statistics",
        "degree_type": "Bachelor of Arts",
        "major": "Statistics",
        "department": "Statistics",
        "description": (
            "UC Berkeley's Statistics B.A. offers foundational training in probability, "
            "inference, regression, and data science. It emphasizes both theory and "
            "applied data analysis in R and Python across diverse disciplines."
        ),
        "estimated_years": 4,
        "website_url": "https://statistics.berkeley.edu/academics/undergraduate",
        "courses": [
            {"position": 1,  "course_number": "MATH1A", "course_title": "Calculus",                          "category": "Math",    "semester": "Year 1, Fall",   "year_in_program": 1, "is_required": True,  "units": 4},
            {"position": 2,  "course_number": "MATH1B", "course_title": "Calculus II",                       "category": "Math",    "semester": "Year 1, Spring", "year_in_program": 1, "is_required": True,  "units": 4},
            {"position": 3,  "course_number": "STAT20", "course_title": "Introductory Statistics",           "category": "Core",    "semester": "Year 1, Spring", "year_in_program": 1, "is_required": True,  "units": 4},
            {"position": 4,  "course_number": "MATH54", "course_title": "Linear Algebra and Differential Equations","category": "Math","semester": "Year 2, Fall","year_in_program": 2, "is_required": True,  "units": 4},
            {"position": 5,  "course_number": "STAT134","course_title": "Concepts of Probability",           "category": "Core",    "semester": "Year 2, Fall",   "year_in_program": 2, "is_required": True,  "units": 4},
            {"position": 6,  "course_number": "STAT135","course_title": "Concepts of Statistics",            "category": "Core",    "semester": "Year 2, Spring", "year_in_program": 2, "is_required": True,  "units": 4},
            {"position": 7,  "course_number": "STAT150","course_title": "Stochastic Processes",              "category": "Core",    "semester": "Year 3, Fall",   "year_in_program": 3, "is_required": True,  "units": 4},
            {"position": 8,  "course_number": "STAT151A","course_title": "Linear Modelling: Theory and Applications","category": "Core","semester": "Year 3, Spring","year_in_program": 3, "is_required": True,  "units": 4},
            {"position": 9,  "course_number": "STAT153","course_title": "Introduction to Time Series",        "category": "Advanced","semester": "Year 3, Spring", "year_in_program": 3, "is_required": False, "units": 4},
            {"position": 10, "course_number": "STAT154","course_title": "Modern Statistical Prediction and Machine Learning","category": "Advanced","semester": "Year 4, Fall","year_in_program": 4, "is_required": False, "units": 4},
            {"position": 11, "course_number": "STAT215A","course_title": "Statistical Models: Theory and Application","category": "Advanced","semester": "Year 4, Fall","year_in_program": 4, "is_required": False, "units": 4},
        ],
    },

    # ──────────────────────────────────────────────────────
    # MIT – Chemistry (Course 5)
    # ──────────────────────────────────────────────────────
    {
        "university_slug": "mit",
        "slug": "mit-bs-chemistry",
        "title": "B.S. Chemistry (Course 5)",
        "degree_type": "Bachelor of Science",
        "major": "Chemistry",
        "department": "Chemistry",
        "description": (
            "MIT's Chemistry program (Course 5) provides rigorous training in physical, "
            "organic, and inorganic chemistry, with a required laboratory curriculum. "
            "Students conduct undergraduate research with faculty for senior thesis credit."
        ),
        "estimated_years": 4,
        "website_url": "https://chemistry.mit.edu/academic-programs/undergraduate-programs/",
        "courses": [
            {"position": 1,  "course_number": "5.111",  "course_title": "Principles of Chemical Science",    "category": "Core",    "semester": "Year 1, Fall",   "year_in_program": 1, "is_required": True,  "units": 12},
            {"position": 2,  "course_number": "18.01",  "course_title": "Single Variable Calculus",          "category": "Math",    "semester": "Year 1, Fall",   "year_in_program": 1, "is_required": True,  "units": 12},
            {"position": 3,  "course_number": "5.112",  "course_title": "Principles of Chemical Science II", "category": "Core",    "semester": "Year 1, Spring", "year_in_program": 1, "is_required": True,  "units": 12},
            {"position": 4,  "course_number": "18.02",  "course_title": "Multivariable Calculus",            "category": "Math",    "semester": "Year 1, Spring", "year_in_program": 1, "is_required": True,  "units": 12},
            {"position": 5,  "course_number": "5.12",   "course_title": "Organic Chemistry I",               "category": "Core",    "semester": "Year 2, Fall",   "year_in_program": 2, "is_required": True,  "units": 12},
            {"position": 6,  "course_number": "5.61",   "course_title": "Physical Chemistry I",              "category": "Core",    "semester": "Year 2, Fall",   "year_in_program": 2, "is_required": True,  "units": 12},
            {"position": 7,  "course_number": "5.13",   "course_title": "Organic Chemistry II",              "category": "Core",    "semester": "Year 2, Spring", "year_in_program": 2, "is_required": True,  "units": 12},
            {"position": 8,  "course_number": "5.62",   "course_title": "Physical Chemistry II",             "category": "Core",    "semester": "Year 2, Spring", "year_in_program": 2, "is_required": True,  "units": 12},
            {"position": 9,  "course_number": "5.03",   "course_title": "Principles of Inorganic Chemistry I","category": "Core",   "semester": "Year 3, Fall",   "year_in_program": 3, "is_required": True,  "units": 12},
            {"position": 10, "course_number": "5.310",  "course_title": "Laboratory Chemistry",              "category": "Lab",     "semester": "Year 3, Fall",   "year_in_program": 3, "is_required": True,  "units": 12},
            {"position": 11, "course_number": "5.04",   "course_title": "Principles of Inorganic Chemistry II","category": "Core",  "semester": "Year 3, Spring", "year_in_program": 3, "is_required": True,  "units": 12},
            {"position": 12, "course_number": "5.311",  "course_title": "Laboratory Chemistry II",           "category": "Lab",     "semester": "Year 3, Spring", "year_in_program": 3, "is_required": True,  "units": 12},
            {"position": 13, "course_number": "5.THU",  "course_title": "Undergraduate Research – Thesis",   "category": "Capstone","semester": "Year 4",         "year_in_program": 4, "is_required": True,  "units": 12},
        ],
    },

    # ──────────────────────────────────────────────────────
    # Harvard – B.S. Applied Mathematics
    # ──────────────────────────────────────────────────────
    {
        "university_slug": "harvard",
        "slug": "harvard-ab-applied-mathematics",
        "title": "A.B. Applied Mathematics",
        "degree_type": "Bachelor of Arts",
        "major": "Applied Mathematics",
        "department": "Applied Mathematics (John A. Paulson School of Engineering)",
        "description": (
            "Harvard's Applied Mathematics A.B. bridges pure mathematics with "
            "applications in physics, biology, economics, and computation. Students "
            "develop strong analytical skills and choose a field of application for depth."
        ),
        "estimated_years": 4,
        "website_url": "https://appliedmath.harvard.edu/undergraduate",
        "courses": [
            {"position": 1,  "course_number": "MATH21A","course_title": "Multivariable Calculus",             "category": "Core",    "semester": "Year 1, Fall",   "year_in_program": 1, "is_required": True,  "units": 4},
            {"position": 2,  "course_number": "MATH21B","course_title": "Linear Algebra and Differential Equations","category": "Core","semester": "Year 1, Spring","year_in_program": 1, "is_required": True,  "units": 4},
            {"position": 3,  "course_number": "APPM050","course_title": "Mathematics Concepts for Applied Sciences","category": "Core","semester": "Year 1, Spring","year_in_program": 1, "is_required": True,  "units": 4},
            {"position": 4,  "course_number": "MATH23A","course_title": "Linear Algebra and Real Analysis I", "category": "Core",    "semester": "Year 2, Fall",   "year_in_program": 2, "is_required": True,  "units": 4},
            {"position": 5,  "course_number": "MATH23B","course_title": "Linear Algebra and Real Analysis II","category": "Core",    "semester": "Year 2, Spring", "year_in_program": 2, "is_required": True,  "units": 4},
            {"position": 6,  "course_number": "APMTH106","course_title": "Applied Algebra",                  "category": "Core",    "semester": "Year 2, Fall",   "year_in_program": 2, "is_required": True,  "units": 4},
            {"position": 7,  "course_number": "APMTH104","course_title": "Real and Functional Analysis",     "category": "Core",    "semester": "Year 3, Fall",   "year_in_program": 3, "is_required": True,  "units": 4},
            {"position": 8,  "course_number": "APMTH105","course_title": "Applied Complex Analysis",         "category": "Core",    "semester": "Year 3, Spring", "year_in_program": 3, "is_required": True,  "units": 4},
            {"position": 9,  "course_number": "STAT110", "course_title": "Probability",                      "category": "Core",    "semester": "Year 2, Spring", "year_in_program": 2, "is_required": True,  "units": 4},
            {"position": 10, "course_number": "APMTH115","course_title": "Asymptotic and Perturbation Methods","category": "Advanced","semester": "Year 3, Fall",  "year_in_program": 3, "is_required": False, "units": 4},
            {"position": 11, "course_number": "APMTH203","course_title": "Stochastic Methods for Data Analysis","category": "Advanced","semester": "Year 4, Fall", "year_in_program": 4, "is_required": False, "units": 4},
            {"position": 12, "course_number": "APMTH499","course_title": "Senior Thesis in Applied Mathematics","category": "Capstone","semester": "Year 4, Spring","year_in_program": 4, "is_required": True,  "units": 4},
        ],
    },

    # ──────────────────────────────────────────────────────
    # Stanford – B.S. Electrical Engineering
    # (data already exists for this school/slug — this adds
    #  a second track: Computer Systems Engineering)
    # ──────────────────────────────────────────────────────
    {
        "university_slug": "stanford",
        "slug": "stanford-bs-ee-systems",
        "title": "B.S. Electrical Engineering (Systems Track)",
        "degree_type": "Bachelor of Science",
        "major": "Electrical Engineering",
        "department": "Electrical Engineering",
        "description": (
            "Stanford's EE Systems track covers signal processing, communications, "
            "control theory, and embedded systems. Students gain both theory and hands-on "
            "lab experience in circuits, signals, and hardware design."
        ),
        "estimated_years": 4,
        "website_url": "https://ee.stanford.edu/academics/undergraduate",
        "courses": [
            {"position": 1,  "course_number": "MATH19",  "course_title": "Calculus",                         "category": "Math",    "semester": "Year 1, Fall",   "year_in_program": 1, "is_required": True,  "units": 3},
            {"position": 2,  "course_number": "PHYS41",  "course_title": "Mechanics",                        "category": "Science", "semester": "Year 1, Fall",   "year_in_program": 1, "is_required": True,  "units": 4},
            {"position": 3,  "course_number": "EE101A",  "course_title": "Circuit Analysis",                 "category": "Core",    "semester": "Year 2, Fall",   "year_in_program": 2, "is_required": True,  "units": 5},
            {"position": 4,  "course_number": "EE101B",  "course_title": "Circuit Analysis II",              "category": "Core",    "semester": "Year 2, Spring", "year_in_program": 2, "is_required": True,  "units": 5},
            {"position": 5,  "course_number": "EE102A",  "course_title": "Signal Processing and Linear Systems","category": "Core", "semester": "Year 2, Spring", "year_in_program": 2, "is_required": True,  "units": 5},
            {"position": 6,  "course_number": "EE108",   "course_title": "Digital Systems I",                "category": "Core",    "semester": "Year 3, Fall",   "year_in_program": 3, "is_required": True,  "units": 5},
            {"position": 7,  "course_number": "EE109",   "course_title": "Introduction to Embedded Systems", "category": "Core",    "semester": "Year 3, Fall",   "year_in_program": 3, "is_required": True,  "units": 5},
            {"position": 8,  "course_number": "EE179",   "course_title": "Analog and Digital Communication Systems","category": "Core","semester": "Year 3, Spring","year_in_program": 3, "is_required": True,  "units": 5},
            {"position": 9,  "course_number": "EE263",   "course_title": "Introduction to Linear Dynamical Systems","category": "Advanced","semester": "Year 4, Fall","year_in_program": 4, "is_required": False, "units": 3},
            {"position": 10, "course_number": "EE364A",  "course_title": "Convex Optimization I",            "category": "Advanced","semester": "Year 4, Fall",   "year_in_program": 4, "is_required": False, "units": 3},
            {"position": 11, "course_number": "EE191",   "course_title": "Senior Project",                   "category": "Capstone","semester": "Year 4, Spring", "year_in_program": 4, "is_required": True,  "units": 4},
        ],
    },

    # ──────────────────────────────────────────────────────
    # Yale – B.A. Economics
    # ──────────────────────────────────────────────────────
    {
        "university_slug": "yale",
        "slug": "yale-ba-economics",
        "title": "B.A. Economics",
        "degree_type": "Bachelor of Arts",
        "major": "Economics",
        "department": "Economics",
        "description": (
            "Yale's Economics B.A. develops quantitative reasoning and economic analysis "
            "across micro and macro theory, econometrics, and applied fields. Students "
            "complete a senior essay demonstrating original research."
        ),
        "estimated_years": 4,
        "website_url": "https://economics.yale.edu/undergraduate",
        "courses": [
            {"position": 1,  "course_number": "ECON115","course_title": "Introductory Microeconomics",       "category": "Core",    "semester": "Year 1, Fall",   "year_in_program": 1, "is_required": True,  "units": 4},
            {"position": 2,  "course_number": "ECON116","course_title": "Introductory Macroeconomics",       "category": "Core",    "semester": "Year 1, Spring", "year_in_program": 1, "is_required": True,  "units": 4},
            {"position": 3,  "course_number": "MATH112","course_title": "Calculus of Functions of One Variable","category": "Math", "semester": "Year 1, Fall",   "year_in_program": 1, "is_required": True,  "units": 4},
            {"position": 4,  "course_number": "ECON300","course_title": "Microeconomic Theory",              "category": "Core",    "semester": "Year 2, Fall",   "year_in_program": 2, "is_required": True,  "units": 4},
            {"position": 5,  "course_number": "ECON301","course_title": "Macroeconomic Theory",              "category": "Core",    "semester": "Year 2, Spring", "year_in_program": 2, "is_required": True,  "units": 4},
            {"position": 6,  "course_number": "ECON131","course_title": "Econometrics",                      "category": "Core",    "semester": "Year 2, Spring", "year_in_program": 2, "is_required": True,  "units": 4},
            {"position": 7,  "course_number": "ECON361","course_title": "Industrial Organization",           "category": "Elective","semester": "Year 3, Fall",   "year_in_program": 3, "is_required": False, "units": 4},
            {"position": 8,  "course_number": "ECON437","course_title": "Behavioral Economics",              "category": "Elective","semester": "Year 3, Spring", "year_in_program": 3, "is_required": False, "units": 4},
            {"position": 9,  "course_number": "ECON441","course_title": "Economics of Inequality",           "category": "Elective","semester": "Year 3, Spring", "year_in_program": 3, "is_required": False, "units": 4},
            {"position": 10, "course_number": "ECON491","course_title": "Senior Essay in Economics",         "category": "Capstone","semester": "Year 4",         "year_in_program": 4, "is_required": True,  "units": 4},
        ],
    },

    # ──────────────────────────────────────────────────────
    # NPTEL – B.Tech Physics (Indian Institute pathway)
    # ──────────────────────────────────────────────────────
    {
        "university_slug": "nptel",
        "slug": "nptel-btech-physics",
        "title": "B.Tech Physics Electives Pathway",
        "degree_type": "Bachelor of Technology",
        "major": "Physics",
        "department": "Physics",
        "description": (
            "NPTEL provides free video lectures covering the full spectrum of undergraduate "
            "physics aligned with Indian IIT/NIT curricula: mechanics, electrodynamics, "
            "quantum mechanics, thermodynamics, and modern physics."
        ),
        "estimated_years": 4,
        "website_url": "https://nptel.ac.in/course.html",
        "courses": [
            {"position": 1,  "course_number": "PH101", "course_title": "Classical Mechanics",                "category": "Core",    "semester": "Year 1, Fall",   "year_in_program": 1, "is_required": True,  "units": 4},
            {"position": 2,  "course_number": "PH102", "course_title": "Electrodynamics",                    "category": "Core",    "semester": "Year 1, Spring", "year_in_program": 1, "is_required": True,  "units": 4},
            {"position": 3,  "course_number": "MA101", "course_title": "Mathematics I – Calculus",           "category": "Math",    "semester": "Year 1, Fall",   "year_in_program": 1, "is_required": True,  "units": 4},
            {"position": 4,  "course_number": "MA102", "course_title": "Mathematics II – Linear Algebra/ODE","category": "Math",    "semester": "Year 1, Spring", "year_in_program": 1, "is_required": True,  "units": 4},
            {"position": 5,  "course_number": "PH201", "course_title": "Quantum Mechanics I",                "category": "Core",    "semester": "Year 2, Fall",   "year_in_program": 2, "is_required": True,  "units": 4},
            {"position": 6,  "course_number": "PH202", "course_title": "Statistical Mechanics",              "category": "Core",    "semester": "Year 2, Spring", "year_in_program": 2, "is_required": True,  "units": 4},
            {"position": 7,  "course_number": "PH301", "course_title": "Quantum Mechanics II",               "category": "Core",    "semester": "Year 3, Fall",   "year_in_program": 3, "is_required": True,  "units": 4},
            {"position": 8,  "course_number": "PH302", "course_title": "Condensed Matter Physics",           "category": "Core",    "semester": "Year 3, Spring", "year_in_program": 3, "is_required": True,  "units": 4},
            {"position": 9,  "course_number": "PH401", "course_title": "Nuclear and Particle Physics",       "category": "Advanced","semester": "Year 4, Fall",   "year_in_program": 4, "is_required": False, "units": 4},
            {"position": 10, "course_number": "PH402", "course_title": "Astrophysics and Cosmology",         "category": "Advanced","semester": "Year 4, Spring", "year_in_program": 4, "is_required": False, "units": 4},
        ],
    },

    # ──────────────────────────────────────────────────────
    # Khan Academy – K–12 through Calculus Mathematics
    # ──────────────────────────────────────────────────────
    {
        "university_slug": "khan-academy",
        "slug": "khan-mathematics-k12-calculus",
        "title": "Mathematics: Foundations to Calculus",
        "degree_type": "Self-paced",
        "major": "Mathematics",
        "department": "Mathematics",
        "description": (
            "Khan Academy's complete mathematics pathway takes students from arithmetic "
            "through pre-algebra, algebra, geometry, trigonometry, pre-calculus, "
            "calculus, and linear algebra — all free and at your own pace."
        ),
        "estimated_years": 3,
        "website_url": "https://www.khanacademy.org/math",
        "courses": [
            {"position": 1,  "course_number": None, "course_title": "Pre-Algebra",                           "category": "Foundation","semester": "Phase 1",      "year_in_program": 1, "is_required": True,  "units": None},
            {"position": 2,  "course_number": None, "course_title": "Algebra 1",                             "category": "Foundation","semester": "Phase 1",      "year_in_program": 1, "is_required": True,  "units": None},
            {"position": 3,  "course_number": None, "course_title": "Geometry",                              "category": "Foundation","semester": "Phase 1",      "year_in_program": 1, "is_required": True,  "units": None},
            {"position": 4,  "course_number": None, "course_title": "Algebra 2",                             "category": "Foundation","semester": "Phase 2",      "year_in_program": 2, "is_required": True,  "units": None},
            {"position": 5,  "course_number": None, "course_title": "Trigonometry",                          "category": "Foundation","semester": "Phase 2",      "year_in_program": 2, "is_required": True,  "units": None},
            {"position": 6,  "course_number": None, "course_title": "Precalculus",                           "category": "Core",    "semester": "Phase 2",        "year_in_program": 2, "is_required": True,  "units": None},
            {"position": 7,  "course_number": None, "course_title": "Differential Calculus",                 "category": "Core",    "semester": "Phase 3",        "year_in_program": 3, "is_required": True,  "units": None},
            {"position": 8,  "course_number": None, "course_title": "Integral Calculus",                     "category": "Core",    "semester": "Phase 3",        "year_in_program": 3, "is_required": True,  "units": None},
            {"position": 9,  "course_number": None, "course_title": "Multivariable Calculus",                "category": "Advanced","semester": "Phase 3",        "year_in_program": 3, "is_required": False, "units": None},
            {"position": 10, "course_number": None, "course_title": "Linear Algebra",                        "category": "Advanced","semester": "Phase 3",        "year_in_program": 3, "is_required": False, "units": None},
            {"position": 11, "course_number": None, "course_title": "Statistics and Probability",            "category": "Advanced","semester": "Phase 3",        "year_in_program": 3, "is_required": False, "units": None},
        ],
    },

]  # ← end of ROADMAPS list

# ─────────────────────────────────────────────────────────────────────────────
# DB Insertion
# ─────────────────────────────────────────────────────────────────────────────

def slug_to_course_id(cur, slug_candidates: list[str]) -> uuid.UUID | None:
    """Try to find a course by slug pattern. Returns first match."""
    for s in slug_candidates:
        cur.execute("SELECT id FROM courses WHERE slug = %s LIMIT 1", (s,))
        row = cur.fetchone()
        if row:
            return row[0]
    return None


def build_slug_candidates(course_number: str | None, course_title: str) -> list[str]:
    """Build slug candidates to attempt matching against courses table."""
    if not course_number:
        return []
    # Normalise: "6.006" -> "6-006", "CS61A" -> "cs61a", etc.
    import re
    num = course_number.lower().replace(".", "-").replace(" ", "-")
    num = re.sub(r"[^a-z0-9\-]", "", num)
    return [num, f"mit-{num}", f"course-{num}"]


def main():
    psycopg2.extras.register_uuid()
    conn = psycopg2.connect(DB_URL)
    cur = conn.cursor()

    # Build university slug → id map
    cur.execute("SELECT slug, id FROM universities")
    uni_map = {row[0]: row[1] for row in cur.fetchall()}

    inserted_roadmaps = 0
    inserted_entries = 0
    skipped = 0

    for rm in ROADMAPS:
        uni_slug = rm["university_slug"]
        if uni_slug not in uni_map:
            print(f"  SKIP – university not found: {uni_slug}")
            skipped += 1
            continue

        uni_id = uni_map[uni_slug]

        # Upsert roadmap
        cur.execute(
            """
            INSERT INTO roadmaps
              (id, university_id, slug, title, degree_type, major, department,
               description, estimated_years, website_url)
            VALUES
              (gen_random_uuid(), %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (slug) DO UPDATE SET
              title          = EXCLUDED.title,
              degree_type    = EXCLUDED.degree_type,
              major          = EXCLUDED.major,
              department     = EXCLUDED.department,
              description    = EXCLUDED.description,
              estimated_years= EXCLUDED.estimated_years,
              website_url    = EXCLUDED.website_url,
              updated_at     = now()
            RETURNING id
            """,
            (
                uni_id,
                rm["slug"],
                rm["title"],
                rm.get("degree_type"),
                rm.get("major"),
                rm.get("department"),
                rm.get("description"),
                rm.get("estimated_years"),
                rm.get("website_url"),
            ),
        )
        roadmap_id = cur.fetchone()[0]
        inserted_roadmaps += 1

        # Delete existing entries and re-insert (idempotent)
        cur.execute("DELETE FROM roadmap_entries WHERE roadmap_id = %s", (roadmap_id,))

        for entry in rm.get("courses", []):
            # Try to link to a real course in the DB
            candidates = build_slug_candidates(entry.get("course_number"), entry["course_title"])
            course_id = slug_to_course_id(cur, candidates)

            cur.execute(
                """
                INSERT INTO roadmap_entries
                  (id, roadmap_id, course_id, position, course_number, course_title,
                   category, semester, year_in_program, is_required, units, notes)
                VALUES
                  (gen_random_uuid(), %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    roadmap_id,
                    course_id,
                    entry["position"],
                    entry.get("course_number"),
                    entry["course_title"],
                    entry.get("category"),
                    entry.get("semester"),
                    entry.get("year_in_program"),
                    entry.get("is_required", True),
                    entry.get("units"),
                    entry.get("notes"),
                ),
            )
            inserted_entries += 1

        print(f"  OK  {rm['title']} ({len(rm['courses'])} entries)")

    conn.commit()
    cur.close()
    conn.close()

    print(f"\nDone. {inserted_roadmaps} roadmaps, {inserted_entries} entries. Skipped: {skipped}")


if __name__ == "__main__":
    main()
