#!/usr/bin/env python
"""load_comprehensive4.py — Tufts, Utah State, UCI, JHSPH OCW"""
from __future__ import annotations
import uuid
import psycopg2
from slugify import slugify

DB = dict(host="127.0.0.1", port=5432, dbname="opencourseware", user="ocw", password="ocwpassword")

CATALOGUE = {
    "tufts": {
        "name": "Tufts University", "slug": "tufts",
        "website": "https://ocw.tufts.edu", "country": "US",
        "description": "Tufts OpenCourseWare provides freely available course materials from Tufts University.",
        "courses": [
            ("Biochemistry", "Biochemistry", "Various", "https://ocw.tufts.edu/courses/biochemistry/biochemistry/", "undergraduate", ["Biochemistry", "Biology"]),
            ("Organic Chemistry I", "Chemistry", "Various", "https://ocw.tufts.edu/courses/chemistry/organic-chemistry-i/", "undergraduate", ["Chemistry", "Organic Chemistry"]),
            ("Organic Chemistry II", "Chemistry", "Various", "https://ocw.tufts.edu/courses/chemistry/organic-chemistry-ii/", "undergraduate", ["Chemistry", "Organic Chemistry"]),
            ("General Chemistry I", "Chemistry", "Various", "https://ocw.tufts.edu/courses/chemistry/general-chemistry-i/", "undergraduate", ["Chemistry"]),
            ("General Chemistry II", "Chemistry", "Various", "https://ocw.tufts.edu/courses/chemistry/general-chemistry-ii/", "undergraduate", ["Chemistry"]),
            ("Calculus I", "Mathematics", "Various", "https://ocw.tufts.edu/courses/mathematics/calculus-i/", "undergraduate", ["Mathematics", "Calculus"]),
            ("Calculus II", "Mathematics", "Various", "https://ocw.tufts.edu/courses/mathematics/calculus-ii/", "undergraduate", ["Mathematics", "Calculus"]),
            ("Multivariable Calculus", "Mathematics", "Various", "https://ocw.tufts.edu/courses/mathematics/multivariable-calculus/", "undergraduate", ["Mathematics", "Calculus"]),
            ("Linear Algebra", "Mathematics", "Various", "https://ocw.tufts.edu/courses/mathematics/linear-algebra/", "undergraduate", ["Mathematics", "Linear Algebra"]),
            ("Differential Equations", "Mathematics", "Various", "https://ocw.tufts.edu/courses/mathematics/differential-equations/", "undergraduate", ["Mathematics"]),
            ("Physics I: Mechanics", "Physics", "Various", "https://ocw.tufts.edu/courses/physics/physics-i-mechanics/", "undergraduate", ["Physics", "Mechanics"]),
            ("Physics II: Electricity and Magnetism", "Physics", "Various", "https://ocw.tufts.edu/courses/physics/physics-ii-electricity-magnetism/", "undergraduate", ["Physics", "Electromagnetism"]),
            ("Genetics", "Biology", "Various", "https://ocw.tufts.edu/courses/biology/genetics/", "undergraduate", ["Biology", "Genetics"]),
            ("Cell Biology", "Biology", "Various", "https://ocw.tufts.edu/courses/biology/cell-biology/", "undergraduate", ["Biology", "Cell Biology"]),
            ("Microbiology", "Biology", "Various", "https://ocw.tufts.edu/courses/biology/microbiology/", "undergraduate", ["Biology", "Microbiology"]),
            ("Anatomy and Physiology I", "Biology", "Various", "https://ocw.tufts.edu/courses/biology/anatomy-physiology-i/", "undergraduate", ["Biology", "Anatomy"]),
            ("Anatomy and Physiology II", "Biology", "Various", "https://ocw.tufts.edu/courses/biology/anatomy-physiology-ii/", "undergraduate", ["Biology", "Physiology"]),
            ("Nutrition Science", "Nutrition Science", "Various", "https://ocw.tufts.edu/courses/nutrition/nutrition-science/", "undergraduate", ["Nutrition", "Health"]),
            ("Food Safety and Quality", "Nutrition Science", "Various", "https://ocw.tufts.edu/courses/nutrition/food-safety-quality/", "undergraduate", ["Nutrition", "Food Science"]),
            ("Introduction to Epidemiology", "Public Health", "Various", "https://ocw.tufts.edu/courses/public-health/intro-epidemiology/", "undergraduate", ["Public Health", "Epidemiology"]),
            ("Biostatistics", "Public Health", "Various", "https://ocw.tufts.edu/courses/public-health/biostatistics/", "undergraduate", ["Statistics", "Public Health"]),
            ("Clinical Nutrition", "Nutrition Science", "Various", "https://ocw.tufts.edu/courses/nutrition/clinical-nutrition/", "graduate", ["Nutrition", "Medicine"]),
            ("Environmental Health Sciences", "Public Health", "Various", "https://ocw.tufts.edu/courses/public-health/environmental-health-sciences/", "undergraduate", ["Environmental Science", "Public Health"]),
            ("Statics and Dynamics", "Engineering", "Various", "https://ocw.tufts.edu/courses/engineering/statics-dynamics/", "undergraduate", ["Engineering", "Mechanics"]),
            ("Thermodynamics", "Engineering", "Various", "https://ocw.tufts.edu/courses/engineering/thermodynamics/", "undergraduate", ["Engineering", "Physics"]),
            ("Fluid Mechanics", "Engineering", "Various", "https://ocw.tufts.edu/courses/engineering/fluid-mechanics/", "undergraduate", ["Engineering", "Physics"]),
            ("Materials Science and Engineering", "Engineering", "Various", "https://ocw.tufts.edu/courses/engineering/materials-science/", "undergraduate", ["Engineering", "Materials Science"]),
            ("Circuit Analysis", "Electrical Engineering", "Various", "https://ocw.tufts.edu/courses/engineering/circuit-analysis/", "undergraduate", ["Electrical Engineering"]),
            ("Signals and Systems", "Electrical Engineering", "Various", "https://ocw.tufts.edu/courses/engineering/signals-systems/", "undergraduate", ["Electrical Engineering", "Signal Processing"]),
            ("Introduction to Computer Science", "Computer Science", "Various", "https://ocw.tufts.edu/courses/computer-science/intro-cs/", "undergraduate", ["Computer Science"]),
            ("Data Structures", "Computer Science", "Various", "https://ocw.tufts.edu/courses/computer-science/data-structures/", "undergraduate", ["Computer Science", "Algorithms"]),
            ("Algorithms", "Computer Science", "Various", "https://ocw.tufts.edu/courses/computer-science/algorithms/", "undergraduate", ["Computer Science", "Algorithms"]),
            ("Operating Systems", "Computer Science", "Various", "https://ocw.tufts.edu/courses/computer-science/operating-systems/", "undergraduate", ["Computer Science", "Operating Systems"]),
            ("Developmental Psychology", "Psychology", "Various", "https://ocw.tufts.edu/courses/psychology/developmental-psychology/", "undergraduate", ["Psychology"]),
            ("Cognitive Psychology", "Psychology", "Various", "https://ocw.tufts.edu/courses/psychology/cognitive-psychology/", "undergraduate", ["Psychology", "Cognitive Science"]),
        ]
    },
    "utah_state": {
        "name": "Utah State University", "slug": "utah-state",
        "website": "https://ocw.usu.edu", "country": "US",
        "description": "Utah State University OpenCourseWare — free educational materials from USU.",
        "courses": [
            ("Principles of Irrigation Engineering", "Biological and Irrigation Engineering", "Various", "https://ocw.usu.edu/course/principles-irrigation-engineering/", "undergraduate", ["Engineering", "Agriculture"]),
            ("Introduction to Irrigation Engineering", "Biological and Irrigation Engineering", "Various", "https://ocw.usu.edu/course/intro-irrigation-engineering/", "undergraduate", ["Engineering", "Agriculture"]),
            ("Irrigation Water Management", "Biological and Irrigation Engineering", "Various", "https://ocw.usu.edu/course/irrigation-water-management/", "undergraduate", ["Agriculture", "Water Resources"]),
            ("Water Resources Engineering", "Civil and Environmental Engineering", "Various", "https://ocw.usu.edu/course/water-resources-engineering/", "undergraduate", ["Engineering", "Water Resources"]),
            ("Hydraulics", "Civil and Environmental Engineering", "Various", "https://ocw.usu.edu/course/hydraulics/", "undergraduate", ["Engineering", "Fluid Mechanics"]),
            ("Hydrology", "Civil and Environmental Engineering", "Various", "https://ocw.usu.edu/course/hydrology/", "undergraduate", ["Environmental Science", "Engineering"]),
            ("Introduction to Engineering", "Engineering", "Various", "https://ocw.usu.edu/course/intro-engineering/", "undergraduate", ["Engineering"]),
            ("Engineering Statics", "Mechanical and Aerospace Engineering", "Various", "https://ocw.usu.edu/course/engineering-statics/", "undergraduate", ["Engineering", "Mechanics"]),
            ("Engineering Dynamics", "Mechanical and Aerospace Engineering", "Various", "https://ocw.usu.edu/course/engineering-dynamics/", "undergraduate", ["Engineering", "Mechanics"]),
            ("Mechanics of Materials", "Civil and Environmental Engineering", "Various", "https://ocw.usu.edu/course/mechanics-of-materials/", "undergraduate", ["Engineering", "Materials Science"]),
            ("Thermodynamics", "Mechanical and Aerospace Engineering", "Various", "https://ocw.usu.edu/course/thermodynamics-usu/", "undergraduate", ["Engineering", "Physics"]),
            ("Heat Transfer", "Mechanical and Aerospace Engineering", "Various", "https://ocw.usu.edu/course/heat-transfer/", "undergraduate", ["Engineering", "Physics"]),
            ("Fluid Mechanics", "Mechanical and Aerospace Engineering", "Various", "https://ocw.usu.edu/course/fluid-mechanics-usu/", "undergraduate", ["Engineering", "Physics"]),
            ("Machine Design", "Mechanical and Aerospace Engineering", "Various", "https://ocw.usu.edu/course/machine-design/", "undergraduate", ["Engineering", "Mechanical Engineering"]),
            ("Control Systems", "Electrical and Computer Engineering", "Various", "https://ocw.usu.edu/course/control-systems/", "undergraduate", ["Engineering", "Control Theory"]),
            ("Circuit Theory", "Electrical and Computer Engineering", "Various", "https://ocw.usu.edu/course/circuit-theory/", "undergraduate", ["Electrical Engineering"]),
            ("Digital Systems", "Electrical and Computer Engineering", "Various", "https://ocw.usu.edu/course/digital-systems/", "undergraduate", ["Electrical Engineering", "Computer Science"]),
            ("Calculus I", "Mathematics and Statistics", "Various", "https://ocw.usu.edu/course/calculus-i-usu/", "undergraduate", ["Mathematics", "Calculus"]),
            ("Calculus II", "Mathematics and Statistics", "Various", "https://ocw.usu.edu/course/calculus-ii-usu/", "undergraduate", ["Mathematics", "Calculus"]),
            ("Calculus III", "Mathematics and Statistics", "Various", "https://ocw.usu.edu/course/calculus-iii-usu/", "undergraduate", ["Mathematics", "Calculus"]),
            ("Linear Algebra", "Mathematics and Statistics", "Various", "https://ocw.usu.edu/course/linear-algebra-usu/", "undergraduate", ["Mathematics", "Linear Algebra"]),
            ("Differential Equations", "Mathematics and Statistics", "Various", "https://ocw.usu.edu/course/differential-equations-usu/", "undergraduate", ["Mathematics"]),
            ("Statistics", "Mathematics and Statistics", "Various", "https://ocw.usu.edu/course/statistics-usu/", "undergraduate", ["Statistics", "Mathematics"]),
            ("General Chemistry I", "Chemistry and Biochemistry", "Various", "https://ocw.usu.edu/course/general-chemistry-i-usu/", "undergraduate", ["Chemistry"]),
            ("General Chemistry II", "Chemistry and Biochemistry", "Various", "https://ocw.usu.edu/course/general-chemistry-ii-usu/", "undergraduate", ["Chemistry"]),
            ("Organic Chemistry", "Chemistry and Biochemistry", "Various", "https://ocw.usu.edu/course/organic-chemistry-usu/", "undergraduate", ["Chemistry", "Organic Chemistry"]),
            ("Biochemistry", "Chemistry and Biochemistry", "Various", "https://ocw.usu.edu/course/biochemistry-usu/", "undergraduate", ["Biochemistry", "Chemistry"]),
            ("General Physics I", "Physics", "Various", "https://ocw.usu.edu/course/general-physics-i-usu/", "undergraduate", ["Physics"]),
            ("General Physics II", "Physics", "Various", "https://ocw.usu.edu/course/general-physics-ii-usu/", "undergraduate", ["Physics"]),
            ("Introduction to Biology", "Biology", "Various", "https://ocw.usu.edu/course/intro-biology-usu/", "undergraduate", ["Biology"]),
            ("Genetics", "Biology", "Various", "https://ocw.usu.edu/course/genetics-usu/", "undergraduate", ["Biology", "Genetics"]),
            ("Ecology", "Biology", "Various", "https://ocw.usu.edu/course/ecology-usu/", "undergraduate", ["Biology", "Ecology"]),
            ("Introduction to Soils", "Plants, Soils and Climate", "Various", "https://ocw.usu.edu/course/intro-soils/", "undergraduate", ["Agriculture", "Environmental Science"]),
            ("Crop Science", "Plants, Soils and Climate", "Various", "https://ocw.usu.edu/course/crop-science/", "undergraduate", ["Agriculture"]),
            ("Introduction to Animal Science", "Animal, Dairy and Veterinary Sciences", "Various", "https://ocw.usu.edu/course/intro-animal-science/", "undergraduate", ["Agriculture", "Animal Science"]),
            ("Introduction to Nutrition", "Nutrition, Dietetics and Food Sciences", "Various", "https://ocw.usu.edu/course/intro-nutrition-usu/", "undergraduate", ["Nutrition", "Health"]),
        ]
    },
    "uci": {
        "name": "University of California, Irvine", "slug": "uci",
        "website": "https://ocw.uci.edu", "country": "US",
        "description": "UC Irvine OpenCourseWare — free course materials from UC Irvine faculty.",
        "courses": [
            ("Introduction to Computer Science", "Computer Science", "Various", "https://ocw.uci.edu/courses/i2cs.html", "undergraduate", ["Computer Science"]),
            ("Data Structures", "Computer Science", "Various", "https://ocw.uci.edu/courses/data_structures.html", "undergraduate", ["Computer Science", "Algorithms"]),
            ("Algorithms", "Computer Science", "Various", "https://ocw.uci.edu/courses/algorithms_uci.html", "undergraduate", ["Computer Science", "Algorithms"]),
            ("Software Engineering", "Computer Science", "Various", "https://ocw.uci.edu/courses/software_engineering.html", "undergraduate", ["Software Engineering", "Computer Science"]),
            ("Compilers", "Computer Science", "Various", "https://ocw.uci.edu/courses/compilers.html", "undergraduate", ["Computer Science"]),
            ("Operating Systems", "Computer Science", "Various", "https://ocw.uci.edu/courses/operating_systems_uci.html", "undergraduate", ["Computer Science", "Operating Systems"]),
            ("Computer Networks", "Computer Science", "Various", "https://ocw.uci.edu/courses/computer_networks_uci.html", "undergraduate", ["Computer Science", "Networking"]),
            ("Introduction to Machine Learning", "Computer Science", "Various", "https://ocw.uci.edu/courses/intro_machine_learning.html", "graduate", ["Machine Learning", "Computer Science"]),
            ("Artificial Intelligence", "Computer Science", "Various", "https://ocw.uci.edu/courses/artificial_intelligence_uci.html", "undergraduate", ["Artificial Intelligence", "Computer Science"]),
            ("Database Management", "Computer Science", "Various", "https://ocw.uci.edu/courses/database_management.html", "undergraduate", ["Computer Science", "Databases"]),
            ("Calculus I", "Mathematics", "Various", "https://ocw.uci.edu/courses/calculus_1.html", "undergraduate", ["Mathematics", "Calculus"]),
            ("Calculus II", "Mathematics", "Various", "https://ocw.uci.edu/courses/calculus_2.html", "undergraduate", ["Mathematics", "Calculus"]),
            ("Linear Algebra", "Mathematics", "Various", "https://ocw.uci.edu/courses/linear_algebra_uci.html", "undergraduate", ["Mathematics", "Linear Algebra"]),
            ("Differential Equations", "Mathematics", "Various", "https://ocw.uci.edu/courses/differential_equations_uci.html", "undergraduate", ["Mathematics"]),
            ("Probability and Statistics", "Mathematics", "Various", "https://ocw.uci.edu/courses/probability_statistics.html", "undergraduate", ["Statistics", "Mathematics"]),
            ("General Chemistry I", "Chemistry", "Various", "https://ocw.uci.edu/courses/general_chemistry_1.html", "undergraduate", ["Chemistry"]),
            ("General Chemistry II", "Chemistry", "Various", "https://ocw.uci.edu/courses/general_chemistry_2.html", "undergraduate", ["Chemistry"]),
            ("Organic Chemistry I", "Chemistry", "Various", "https://ocw.uci.edu/courses/organic_chemistry_1.html", "undergraduate", ["Chemistry", "Organic Chemistry"]),
            ("Organic Chemistry II", "Chemistry", "Various", "https://ocw.uci.edu/courses/organic_chemistry_2.html", "undergraduate", ["Chemistry", "Organic Chemistry"]),
            ("Physics I: Classical Mechanics", "Physics and Astronomy", "Various", "https://ocw.uci.edu/courses/physics_1_mechanics.html", "undergraduate", ["Physics", "Mechanics"]),
            ("Physics II: Electromagnetism", "Physics and Astronomy", "Various", "https://ocw.uci.edu/courses/physics_2_electromagnetism.html", "undergraduate", ["Physics", "Electromagnetism"]),
            ("Physics III: Modern Physics", "Physics and Astronomy", "Various", "https://ocw.uci.edu/courses/physics_3_modern.html", "undergraduate", ["Physics", "Quantum Mechanics"]),
            ("Astronomy: The Sky in Motion", "Physics and Astronomy", "Various", "https://ocw.uci.edu/courses/astronomy_sky_in_motion.html", "undergraduate", ["Astronomy"]),
            ("Introduction to Biology", "Biological Sciences", "Various", "https://ocw.uci.edu/courses/intro_biology_uci.html", "undergraduate", ["Biology"]),
            ("Genetics", "Biological Sciences", "Various", "https://ocw.uci.edu/courses/genetics_uci.html", "undergraduate", ["Biology", "Genetics"]),
            ("Introduction to Economics", "Economics", "Various", "https://ocw.uci.edu/courses/intro_economics.html", "undergraduate", ["Economics"]),
            ("Microeconomics", "Economics", "Various", "https://ocw.uci.edu/courses/microeconomics_uci.html", "undergraduate", ["Economics"]),
            ("Macroeconomics", "Economics", "Various", "https://ocw.uci.edu/courses/macroeconomics_uci.html", "undergraduate", ["Economics"]),
            ("Introduction to Psychology", "Psychology and Social Behavior", "Various", "https://ocw.uci.edu/courses/intro_psychology_uci.html", "undergraduate", ["Psychology"]),
            ("Introduction to Political Science", "Political Science", "Various", "https://ocw.uci.edu/courses/intro_political_science.html", "undergraduate", ["Political Science"]),
            ("Environmental Science", "Earth System Science", "Various", "https://ocw.uci.edu/courses/environmental_science_uci.html", "undergraduate", ["Environmental Science"]),
            ("World History", "History", "Various", "https://ocw.uci.edu/courses/world_history_uci.html", "undergraduate", ["History"]),
            ("Introduction to Philosophy", "Philosophy", "Various", "https://ocw.uci.edu/courses/intro_philosophy_uci.html", "undergraduate", ["Philosophy"]),
            ("Introduction to Sociology", "Sociology", "Various", "https://ocw.uci.edu/courses/intro_sociology_uci.html", "undergraduate", ["Sociology"]),
            ("Writing for Social Science", "Social Sciences", "Various", "https://ocw.uci.edu/courses/writing_social_science.html", "undergraduate", ["Writing", "Social Science"]),
        ]
    },
    "jhsph_ocw": {
        "name": "Johns Hopkins Bloomberg School of Public Health", "slug": "jhsph",
        "website": "https://ocw.jhsph.edu", "country": "US",
        "description": "JHSPH OpenCourseWare — free educational content from the Johns Hopkins Bloomberg School of Public Health.",
        "courses": [
            ("Introduction to the Epidemiology of Infectious Diseases", "Epidemiology", "Various", "https://ocw.jhsph.edu/courses/InfectiousDiseaseEpi/", "graduate", ["Epidemiology", "Infectious Disease", "Public Health"]),
            ("Methods in Observational Epidemiology", "Epidemiology", "Various", "https://ocw.jhsph.edu/courses/MethodsObservationalEpi/", "graduate", ["Epidemiology", "Research Methods"]),
            ("Epidemiologic Methods I", "Epidemiology", "Various", "https://ocw.jhsph.edu/courses/EpiMethods1/", "graduate", ["Epidemiology", "Biostatistics"]),
            ("Epidemiologic Methods II", "Epidemiology", "Various", "https://ocw.jhsph.edu/courses/EpiMethods2/", "graduate", ["Epidemiology", "Biostatistics"]),
            ("Probability and Statistical Inference", "Biostatistics", "Various", "https://ocw.jhsph.edu/courses/ProbStatInference/", "graduate", ["Biostatistics", "Statistics"]),
            ("Statistical Methods in Public Health I", "Biostatistics", "Various", "https://ocw.jhsph.edu/courses/StatMethodsPH1/", "graduate", ["Biostatistics", "Public Health"]),
            ("Statistical Methods in Public Health II", "Biostatistics", "Various", "https://ocw.jhsph.edu/courses/StatMethodsPH2/", "graduate", ["Biostatistics", "Public Health"]),
            ("Statistical Methods in Public Health III", "Biostatistics", "Various", "https://ocw.jhsph.edu/courses/StatMethodsPH3/", "graduate", ["Biostatistics", "Statistics"]),
            ("Statistical Methods in Public Health IV", "Biostatistics", "Various", "https://ocw.jhsph.edu/courses/StatMethodsPH4/", "graduate", ["Biostatistics", "Statistics"]),
            ("Introduction to R for Public Health Researchers", "Biostatistics", "Various", "https://ocw.jhsph.edu/courses/IntroToR/", "graduate", ["Biostatistics", "Data Science"]),
            ("Environmental Health Sciences", "Environmental Health Sciences", "Various", "https://ocw.jhsph.edu/courses/EnvironmentalHealthSciences/", "graduate", ["Environmental Health", "Public Health"]),
            ("Air Pollution and Health", "Environmental Health Sciences", "Various", "https://ocw.jhsph.edu/courses/AirPollutionHealth/", "graduate", ["Environmental Health", "Public Health"]),
            ("Global Environmental Health", "Environmental Health Sciences", "Various", "https://ocw.jhsph.edu/courses/GlobalEnvHealth/", "graduate", ["Environmental Health", "Global Health"]),
            ("Introduction to Global Health", "International Health", "Various", "https://ocw.jhsph.edu/courses/IntroToGlobalHealth/", "graduate", ["Global Health", "Public Health"]),
            ("Global Disease Control: Concepts and Practice", "International Health", "Various", "https://ocw.jhsph.edu/courses/GlobalDiseaseControl/", "graduate", ["Global Health", "Epidemiology"]),
            ("Challenges in Global Health", "International Health", "Various", "https://ocw.jhsph.edu/courses/ChallengesGlobalHealth/", "graduate", ["Global Health", "Public Health"]),
            ("Child Health in the Developing World", "International Health", "Various", "https://ocw.jhsph.edu/courses/ChildHealthDevelopingWorld/", "graduate", ["Global Health", "Child Health"]),
            ("Principles of Human Nutrition", "Human Nutrition", "Various", "https://ocw.jhsph.edu/courses/PrinciplesHumanNutrition/", "graduate", ["Nutrition", "Public Health"]),
            ("Nutrition Epidemiology", "Human Nutrition", "Various", "https://ocw.jhsph.edu/courses/NutritionEpidemiology/", "graduate", ["Nutrition", "Epidemiology"]),
            ("Introduction to Health Policy", "Health Policy and Management", "Various", "https://ocw.jhsph.edu/courses/IntroHealthPolicy/", "graduate", ["Health Policy", "Public Health"]),
            ("Health Program Planning and Evaluation", "Health Policy and Management", "Various", "https://ocw.jhsph.edu/courses/HealthProgramPlanning/", "graduate", ["Public Health", "Health Policy"]),
            ("Introduction to Maternal and Child Health", "Maternal and Child Health", "Various", "https://ocw.jhsph.edu/courses/IntroMaternalChildHealth/", "graduate", ["Public Health", "Maternal Health"]),
            ("Social Behavioral Health Sciences", "Health Behavior and Society", "Various", "https://ocw.jhsph.edu/courses/SocialBehavioralHealthSci/", "graduate", ["Public Health", "Behavioral Science"]),
            ("Family Planning and Reproductive Health", "Population, Family and Reproductive Health", "Various", "https://ocw.jhsph.edu/courses/FamilyPlanningRepHealth/", "graduate", ["Public Health", "Reproductive Health"]),
            ("Principles of Epidemiology in Public Health Practice", "Epidemiology", "Various", "https://ocw.jhsph.edu/courses/PrinciplesEpidemiology/", "professional", ["Epidemiology", "Public Health"]),
            ("Mapping and Visualizing Spatial Data", "Biostatistics", "Various", "https://ocw.jhsph.edu/courses/MappingVisualizingData/", "graduate", ["Data Science", "Public Health"]),
            ("Public Health Preparedness", "Health Policy and Management", "Various", "https://ocw.jhsph.edu/courses/PublicHealthPreparedness/", "professional", ["Public Health", "Emergency Management"]),
            ("Tropical Medicine", "International Health", "Various", "https://ocw.jhsph.edu/courses/TropicalMedicine/", "graduate", ["Medicine", "Global Health"]),
            ("Genetics and Public Health", "Epidemiology", "Various", "https://ocw.jhsph.edu/courses/GeneticsPublicHealth/", "graduate", ["Genetics", "Public Health"]),
            ("Communicating Public Health Information", "Health Behavior and Society", "Various", "https://ocw.jhsph.edu/courses/CommPublicHealthInfo/", "graduate", ["Public Health", "Communication"]),
            ("Leadership and Management in Public Health", "Health Policy and Management", "Various", "https://ocw.jhsph.edu/courses/LeadershipManagementPH/", "professional", ["Public Health", "Leadership"]),
            ("Introduction to Public Health", "General", "Various", "https://ocw.jhsph.edu/courses/IntroPublicHealth/", "professional", ["Public Health"]),
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
