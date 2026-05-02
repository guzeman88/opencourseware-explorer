"""
tag_courses.py
Auto-tags every course in the DB with one or more subjects based on
keyword rules matched against the course title (case-insensitive).
Existing tags are preserved; only new ones are inserted.
"""

import psycopg2
import re

CONN_STR = "postgresql://ocw:ocwpassword@127.0.0.1:5432/opencourseware"

# Rules: list of (subject_slug, [keywords_that_match_in_title])
# Order matters only for readability. A course can match multiple subjects.
# MIT department number → list of subject slugs (used as fallback when keyword match fails)
MIT_DEPT_MAP: dict[str, list[str]] = {
    "1":   ["engineering", "ecology"],                          # Civil & Environmental
    "2":   ["engineering", "mechanics"],                        # Mechanical Engineering
    "3":   ["engineering", "chemistry"],                        # Materials Science
    "4":   ["engineering"],                                     # Architecture
    "5":   ["chemistry"],                                       # Chemistry
    "6":   ["computer-science", "electrical-engineering"],      # EECS
    "7":   ["biology"],                                         # Biology
    "8":   ["physics"],                                         # Physics
    "9":   ["biology", "psychology"],                           # Brain & Cognitive Sciences
    "10":  ["engineering", "chemistry"],                        # Chemical Engineering
    "11":  ["political-science", "sociology"],                  # Urban Studies & Planning
    "12":  ["physics", "ecology"],                              # Earth, Atmospheric, Planetary
    "14":  ["economics"],                                       # Economics
    "15":  ["economics", "finance"],                            # Sloan School of Management
    "16":  ["engineering", "mechanics"],                        # Aeronautics & Astronautics
    "17":  ["political-science"],                               # Political Science
    "18":  ["mathematics"],                                     # Mathematics
    "20":  ["biology", "engineering"],                          # Biological Engineering
    "21a": ["sociology"],                                       # Anthropology
    "21g": ["literature"],                                      # Global Languages
    "21h": ["history"],                                         # History
    "21l": ["literature"],                                      # Literature
    "21m": ["literature"],                                      # Music & Theater Arts
    "21w": ["literature"],                                      # Writing
    "22":  ["engineering", "physics"],                          # Nuclear Engineering
    "24":  ["philosophy"],                                      # Linguistics & Philosophy
    "wgs": ["sociology"],                                       # Women's & Gender Studies
    "res": ["engineering"],                                     # Resources (default)
    "sts": ["sociology"],                                       # Science, Technology & Society
    "sp":  ["engineering"],                                     # Special programs
    "esd": ["engineering", "economics"],                        # Engineering Systems
    "hsst": ["life-sciences"],                                  # Health Sciences & Technology
    "hst": ["life-sciences"],
    "mas": ["computer-science"],                                # Media Arts & Sciences
    "ids": ["statistics"],                                      # Institute for Data, Systems
    "cms": ["literature"],                                      # Comparative Media Studies
    "ccs": ["sociology"],
    "ec":  ["engineering"],
    "es":  ["engineering"],
}

RULES = [
    # ── Computer Science & Programming ─────────────────────────────────────
    ("computer-science",         ["computer science", "cs 6", "cs 7", "cs 8", "cs 9",
                                   "cs 1", "cs 2", "cs 3", "cs 4", "cs 5",
                                   "eecs", "computing", "informatics", "software engineering",
                                   "software design", "computation", "computer systems",
                                   "computer organization", "computer architecture",
                                   "operating system", "compiler", "programming language"]),
    ("algorithms",               ["algorithm", "data structure", "discrete math",
                                   "combinatorics", "graph theory", "complexity",
                                   "theory of computation", "computational"]),
    ("data-structures",          ["data structure", "data organization"]),
    ("operating-systems",        ["operating system", "os kernel", "linux kernel"]),
    ("computer-architecture",    ["computer architecture", "computer organization",
                                   "digital system", "digital logic", "vlsi",
                                   "microprocessor", "cpu design", "hardware design"]),
    ("databases",                ["database", "sql", "relational", "data management",
                                   "data engineering", "nosql"]),
    ("networking",               ["network", "internet", "protocol", "tcp", "web security",
                                   "distributed system"]),
    ("cybersecurity",            ["security", "cybersecurity", "cryptography",
                                   "information security", "network security"]),
    ("web-development",          ["web development", "web design", "html", "css", "javascript",
                                   "node.js", "react", "frontend", "backend", "full stack",
                                   "web application", "rest api"]),
    ("mobile-development",       ["mobile", "android", "ios", "swift", "react native",
                                   "flutter", "app development"]),
    ("game-development",         ["game development", "game design", "game engine",
                                   "unity", "unreal"]),
    ("programming",              ["programming", "coding", "software", "python",
                                   "java ", "c++", "c programming", "lua", "r programming",
                                   "matlab", "introduction to computer"]),
    ("python",                   ["python"]),
    ("java",                     ["java "]),
    ("javascript",               ["javascript", "node.js", "typescript"]),
    ("c-programming",            ["c programming", " c ", "c++", "systems programming"]),
    ("c",                        [" c language", "c programming"]),
    ("swift",                    ["swift ", "ios development"]),
    ("sql",                      ["sql", "database query", "relational database"]),

    # ── AI / ML ─────────────────────────────────────────────────────────────
    ("machine-learning",         ["machine learning", "ml ", "supervised learning",
                                   "unsupervised learning", "classification", "regression",
                                   "neural network", "deep learning", "data science"]),
    ("deep-learning",            ["deep learning", "neural network", "cnn", "lstm",
                                   "transformer", "generative model", "diffusion"]),
    ("artificial-intelligence",  ["artificial intelligence", "ai ", " ai,", "intelligent system",
                                   "knowledge representation", "expert system",
                                   "planning", "search algorithm"]),
    ("natural-language-processing", ["natural language", "nlp", "text mining",
                                     "sentiment analysis", "language model",
                                     "computational linguistics"]),
    ("computer-vision",          ["computer vision", "image processing", "object detection",
                                   "image recognition", "visual", "pattern recognition"]),
    ("reinforcement-learning",   ["reinforcement learning", "rl ", "reward", "markov decision"]),
    ("robotics",                 ["robot", "autonomous", "control system",
                                   "mechatronic", "manipulation"]),
    ("graph-neural-networks",    ["graph neural", "gnn", "graph learning"]),
    ("meta-learning",            ["meta learning", "meta-learning", "few-shot", "transfer learning"]),

    # ── Mathematics ─────────────────────────────────────────────────────────
    ("mathematics",              ["mathematics", "math ", "mathematical", "algebra",
                                   "geometry", "topology", "analysis", "number theory",
                                   "combinatorics", "real analysis", "complex analysis",
                                   "abstract algebra", "linear algebra", "discrete math",
                                   "differential geometry", "algebraic"]),
    ("linear-algebra",           ["linear algebra", "matrix", "vector space", "eigenvalue"]),
    ("calculus",                 ["calculus", "differentiation", "integration", "multivariable",
                                   "single variable", "differential calculus"]),
    ("differential-equations",   ["differential equation", "ode", "pde",
                                   "partial differential", "ordinary differential",
                                   "dynamical system"]),
    ("probability",              ["probability", "stochastic", "random process",
                                   "bayesian", "markov chain", "monte carlo"]),
    ("statistics",               ["statistics", "statistical", "regression",
                                   "inference", "hypothesis", "data analysis",
                                   "econometrics", "biostatistics"]),
    ("discrete-mathematics",     ["discrete math", "combinatorics", "graph theory",
                                   "logic ", "boolean algebra", "set theory"]),

    # ── Physics ─────────────────────────────────────────────────────────────
    ("physics",                  ["physics", "mechanics", "electromagnetism",
                                   "thermodynamics", "quantum", "relativity",
                                   "optics", "waves", "classical mechanics"]),
    ("quantum-mechanics",        ["quantum", "quantum mechanics", "quantum field",
                                   "quantum information", "quantum computing"]),
    ("thermodynamics",           ["thermodynamics", "heat transfer", "statistical mechanics",
                                   "thermal"]),
    ("astrophysics",             ["astrophysics", "cosmology", "stellar", "galaxy"]),
    ("astronomy",                ["astronomy", "telescope", "celestial", "solar system",
                                   "planet"]),
    ("mechanics",                ["mechanics", "classical mechanics", "statics",
                                   "dynamics", "continuum"]),
    ("fluid-mechanics",          ["fluid", "fluid mechanics", "aerodynamics",
                                   "hydraulic", "flow "]),
    ("signal-processing",        ["signal processing", "fourier", "filter design",
                                   "dsp", "communications", "control system"]),
    ("control-systems",          ["control system", "feedback", "pid", "optimal control"]),
    ("digital-systems",          ["digital system", "digital circuit", "vhdl",
                                   "fpga", "embedded system"]),

    # ── Engineering ─────────────────────────────────────────────────────────
    ("engineering",              ["engineering", "design", "manufacturing",
                                   "materials", "structural", "civil",
                                   "mechanical engineering", "electrical engineering",
                                   "chemical engineering", "aerospace"]),
    ("electrical-engineering",   ["electrical engineering", "circuits", "electronics",
                                   "signal", "power system", "semiconductor"]),

    # ── Chemistry ───────────────────────────────────────────────────────────
    ("chemistry",                ["chemistry", "chemical", "organic chemistry",
                                   "inorganic", "biochemistry", "molecular",
                                   "thermochemistry"]),
    ("organic-chemistry",        ["organic chemistry", "organic synthesis",
                                   "reaction mechanism"]),

    # ── Biology & Life Sciences ──────────────────────────────────────────────
    ("biology",                  ["biology", "biological", "cell biology",
                                   "molecular biology", "genetics", "evolution",
                                   "ecology", "neuroscience", "neurobiology",
                                   "biochemistry", "microbiology", "virology",
                                   "immunology", "physiology", "anatomy"]),
    ("life-sciences",            ["life science", "medicine", "health", "biomedical",
                                   "public health", "epidemiology", "pharmacology",
                                   "clinical"]),
    ("evolution",                ["evolution", "evolutionary", "natural selection",
                                   "darwinian", "phylogenetics"]),
    ("ecology",                  ["ecology", "environmental", "ecosystem",
                                   "sustainability", "climate", "biodiversity"]),
    ("food-science",             ["food", "nutrition", "food science", "gastronomy"]),

    # ── Economics & Finance ──────────────────────────────────────────────────
    ("economics",                ["economics", "economic", "microeconomics", "macroeconomics",
                                   "market", "trade", "fiscal", "monetary"]),
    ("microeconomics",           ["microeconomics", "micro ", "consumer theory",
                                   "producer theory", "market structure"]),
    ("macroeconomics",           ["macroeconomics", "macro ", "gdp", "inflation",
                                   "monetary policy", "fiscal policy", "growth"]),
    ("finance",                  ["finance", "financial", "investment", "portfolio",
                                   "asset pricing", "derivatives", "banking", "accounting"]),
    ("game-theory",              ["game theory", "strategic", "nash equilibrium"]),

    # ── Social Sciences ──────────────────────────────────────────────────────
    ("psychology",               ["psychology", "cognitive", "behavioral", "neuroscience",
                                   "perception", "learning theory", "mental"]),
    ("sociology",                ["sociology", "social", "society", "culture",
                                   "anthropology", "ethnography", "race ", "gender"]),
    ("political-science",        ["political science", "politics", "government",
                                   "public policy", "international relations",
                                   "democracy", "policy"]),
    ("philosophy",               ["philosophy", "ethics", "epistemology", "logic",
                                   "ontology", "moral"]),
    ("ethics",                   ["ethics", "moral philosophy", "bioethics",
                                   "professional ethics", "justice"]),

    # ── History ──────────────────────────────────────────────────────────────
    ("history",                  ["history", "historical", "ancient", "medieval",
                                   "modern history", "world history"]),
    ("american-history",         ["american history", "united states history",
                                   "us history", "colonial america"]),
    ("european-history",         ["european history", "europe ", "european civilization"]),
    ("ancient-history",          ["ancient history", "ancient world", "classical antiquity",
                                   "rome", "greek ", "mesopotamia"]),
    ("world-history",            ["world history", "global history", "civilization"]),

    # ── Humanities & Literature ──────────────────────────────────────────────
    ("literature",               ["literature", "literary", "poetry", "novel",
                                   "fiction", "writing", "rhetoric", "composition",
                                   "language", "linguistics", "phonology", "syntax",
                                   "semantics", "grammar", "translation", "discourse",
                                   "reading", "communication"]),
    ("english",                  ["english ", "english language", "english literature",
                                   "creative writing", "academic writing"]),
    ("religious-studies",        ["religion", "religious", "theology", "islam",
                                   "christianity", "buddhism", "hinduism", "spirituality",
                                   "scripture", "sacred"]),
    ("american-studies",         ["american studies", "american culture",
                                   "american society"]),
    ("african-american-studies", ["african american", "black history",
                                   "civil rights", "african diaspora"]),

    # ── Additional broad catches ────────────────────────────────────────────
    ("engineering",              ["transportation", "infrastructure", "architecture",
                                   "urban", "construction", "aerospace", "aviation",
                                   "aircraft", "antenna", "radar", "satellite",
                                   "geophysics", "geology", "petrology", "seismology",
                                   "oceanography", "atmosphere", "meteorology",
                                   "polymer", "semiconductor", "nuclear",
                                   "system architecture", "system design",
                                   "product design", "urban planning"]),
    ("physics",                  ["acoustics", "acoustical", "wave ", "oscillation",
                                   "electromagnetic", "optics", "laser", "photonics",
                                   "spectroscopy", "geophysics"]),
    ("ecology",                  ["ocean", "atmosphere", "climate change",
                                   "environmental science", "earth science",
                                   "global warming", "sustainability", "water",
                                   "watershed", "urban ecology"]),
    ("sociology",                ["urban", "city", "cities", "community",
                                   "development", "negotiation", "public sector",
                                   "human rights", "immigration", "poverty",
                                   "inequality", "governance", "public health",
                                   "media", "journalism"]),
    ("economics",                ["industrial organization", "capitalism", "poverty",
                                   "development economics", "international development",
                                   "world poverty", "political economy"]),
    ("mathematics",              ["optimization", "quantitative", "numerical method",
                                   "simulation", "modeling", "stochastic process"]),
    ("life-sciences",            ["nuclear magnetic resonance", "nmr", "spectroscopy",
                                   "drug", "pharmaceutical", "vaccine", "immune",
                                   "pandemic", "infectious disease"]),
    ("history",                  ["columbus", "colonial", "civilization", "war ",
                                   "revolution", "empire", "dynasty"]),
]


def slugify(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def build_title_lower(title: str, description: str | None) -> str:
    return (title + " " + (description or "")).lower()


def match_subjects(combined: str, subject_slugs: set[str]) -> list[str]:
    matched = []
    for slug, keywords in RULES:
        if slug not in subject_slugs:
            continue
        for kw in keywords:
            if kw in combined:
                matched.append(slug)
                break
    return matched


def extract_mit_dept(source_url: str | None) -> str | None:
    """Extract MIT course number prefix from source_url like 14-02-... → '14'"""
    if not source_url:
        return None
    m = re.search(r"/courses/([a-z0-9]+)-", source_url)
    if not m:
        return None
    raw = m.group(1)
    # Try multi-char alpha prefix first (21h, 21g, 21a, 21l, 21m, 21w, wgs, sts, hst, mas, cms, res, esd, ec, sp, ids)
    alpha_m = re.match(r"^([0-9]+[a-z]+|[a-z]+)", raw)
    if alpha_m:
        return alpha_m.group(1)
    # Pure numeric
    num_m = re.match(r"^([0-9]+)", raw)
    if num_m:
        return num_m.group(1)
    return None


def main():
    conn = psycopg2.connect(CONN_STR)
    cur = conn.cursor()

    # Load subject slug → id
    cur.execute("SELECT slug, id FROM subjects")
    slug_to_id = {row[0]: row[1] for row in cur.fetchall()}
    subject_slugs = set(slug_to_id.keys())

    # Load existing tags
    cur.execute("SELECT course_id, subject_id FROM course_subjects")
    existing = set(cur.fetchall())
    print(f"Existing tags: {len(existing)}", flush=True)

    # Load all courses (with source_url for MIT dept lookup)
    cur.execute("SELECT id, title, description, source_url, source_key FROM courses")
    courses = cur.fetchall()
    print(f"Courses to tag: {len(courses)}", flush=True)

    def tag(course_id, slugs):
        nonlocal inserted
        for slug in slugs:
            if slug not in slug_to_id:
                continue
            sid = slug_to_id[slug]
            key = (course_id, sid)
            if key not in existing:
                cur.execute(
                    "INSERT INTO course_subjects (course_id, subject_id) VALUES (%s, %s)"
                    " ON CONFLICT DO NOTHING",
                    (course_id, sid),
                )
                existing.add(key)
                inserted += 1

    inserted = 0
    for course_id, title, description, source_url, source_key in courses:
        combined = build_title_lower(title, description)
        matched_slugs = match_subjects(combined, subject_slugs)
        tag(course_id, matched_slugs)

        # MIT course-number fallback: if nothing matched, assign dept default
        current_tags = {k for k in existing if k[0] == course_id}
        if not current_tags and source_key == "mit_ocw":
            dept = extract_mit_dept(source_url)
            if dept and dept in MIT_DEPT_MAP:
                tag(course_id, MIT_DEPT_MAP[dept])

    conn.commit()
    print(f"Inserted {inserted} new tags", flush=True)

    # Report top subjects
    cur.execute("""
        SELECT s.name, COUNT(cs.course_id) cnt
        FROM subjects s
        LEFT JOIN course_subjects cs ON cs.subject_id = s.id
        GROUP BY s.name ORDER BY cnt DESC LIMIT 20
    """)
    print("\nTop subjects after tagging:")
    for name, cnt in cur.fetchall():
        print(f"  {name:35s} {cnt}")

    # Total tagged
    cur.execute("SELECT COUNT(DISTINCT course_id) FROM course_subjects")
    tagged = cur.fetchone()[0]
    print(f"\nCourses with at least 1 subject: {tagged}/{len(courses)} "
          f"= {tagged/len(courses)*100:.1f}%")

    conn.close()


if __name__ == "__main__":
    main()
