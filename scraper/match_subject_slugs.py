"""
match_subject_slugs.py
----------------------
Fills roadmap_entries.subject_slug by matching each entry's course title
against the subjects table.

Used as a fallback link for entries that have no matched course_id:
  → /subjects/{subject_slug}  (shows all our courses on that topic)

Matching strategy (first hit wins):
  1. Override table  — hand-crafted mappings for tricky/ambiguous titles
  2. Exact phrase    — subject name appears verbatim in the normalized title
  3. Singular form   — subject name minus trailing 's' appears in title
  4. Word subset     — all words of a 2+-word subject appear in title words
                       (handles "linear algebra" ↔ "matrices and linear transformations")

Longer subject names are always preferred over shorter ones (more specific).

Run:
  py -3.13 -u match_subject_slugs.py
"""

import re
import psycopg2

CONN = "postgresql://ocw:ocwpassword@127.0.0.1:5432/opencourseware"


def normalize(s: str) -> str:
    s = s.lower()
    s = re.sub(r"[^a-z0-9 ]+", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


# Hand-crafted overrides: if this phrase (normalized) is IN the title → use that slug.
# Checked before the automatic matching so specific beats generic.
OVERRIDES: list[tuple[str, str]] = [
    # Math
    ("matrices",                  "linear-algebra"),
    ("matrix ",                   "linear-algebra"),
    ("linear transformations",    "linear-algebra"),
    ("eigenvectors",              "linear-algebra"),
    ("eigenvalues",               "linear-algebra"),
    ("multivariable calculus",    "calculus"),
    ("single variable calculus",  "calculus"),
    ("calculus in three",         "calculus"),
    ("differential equations",    "differential-equations"),
    ("partial differential",      "differential-equations"),
    ("ordinary differential",     "differential-equations"),
    ("real analysis",             "real-analysis"),
    ("complex analysis",          "complex-analysis"),
    ("number theory",             "number-theory"),
    ("graph theory",              "graph-theory"),
    ("discrete math",             "discrete-mathematics"),
    ("bayesian",                  "bayesian-statistics"),
    ("statistical inference",     "statistics"),
    ("statistical learning",      "machine-learning"),
    # CS theory
    ("theoretical ideas",         "theory-of-computing"),
    ("great ideas in",            "theory-of-computing"),
    ("computability",             "theory-of-computing"),
    ("complexity theory",         "computational-complexity"),
    ("formal methods",            "formal-verification"),
    ("program verification",      "formal-verification"),
    ("bug catching",              "formal-verification"),
    ("automated verification",    "formal-verification"),
    ("model checking",            "formal-verification"),
    # Systems / OS
    ("operating system",          "operating-systems"),
    ("os design",                 "operating-systems"),
    ("computer architecture",     "computer-architecture"),
    ("computer organization",     "computer-architecture"),
    ("digital logic",             "digital-systems"),
    ("digital circuits",          "digital-systems"),
    ("vlsi",                      "vlsi"),
    ("embedded system",           "embedded-systems"),
    ("distributed system",        "distributed-systems"),
    ("concurrent programming",    "concurrent-programming"),
    ("parallel programming",      "parallel-computing"),
    # Networks / Security
    ("computer network",          "computer-networks"),
    ("network security",          "cybersecurity"),
    ("information security",      "cybersecurity"),
    ("cryptography",              "cryptography"),
    # AI / ML
    ("machine learning",          "machine-learning"),
    ("deep learning",             "deep-learning"),
    ("neural network",            "neural-networks"),
    ("computer vision",           "computer-vision"),
    ("natural language",          "natural-language-processing"),
    ("reinforcement learning",    "reinforcement-learning"),
    ("generative model",          "generative-models"),
    ("artificial intelligence",   "artificial-intelligence"),
    # Data
    ("data structure",            "data-structures"),
    ("data analysis",             "data-science"),
    ("data visualization",        "data-science"),
    ("data mining",               "data-science"),
    ("big data",                  "big-data"),
    ("database",                  "databases"),
    ("sql",                       "sql"),
    # Programming / Languages
    ("programming language",      "programming-languages"),
    ("compiler",                  "compilers"),
    ("functional programming",    "functional-programming"),
    ("systems programming",       "systems-programming"),
    ("back end",                  "web-development"),
    ("backend",                   "web-development"),
    ("front end",                 "web-development"),
    ("frontend",                  "web-development"),
    ("web development",           "web-development"),
    ("node.js",                   "node-js"),
    ("nodejs",                    "node-js"),
    ("react",                     "react"),
    ("python",                    "python"),
    ("java ",                     "java"),
    ("javascript",                "javascript"),
    ("typescript",                "typescript"),
    # Software engineering
    ("software engineering",      "software-engineering"),
    ("software design",           "software-engineering"),
    ("object oriented",           "software-engineering"),
    ("design pattern",            "software-engineering"),
    # Signals / EE
    ("signal processing",         "signal-processing"),
    ("control system",            "control-systems"),
    ("power system",              "power-systems"),
    ("electromagnet",             "electromagnetism"),
    # Other stem
    ("quantum mechanic",          "quantum-mechanics"),
    ("thermodynamics",            "thermodynamics"),
    ("fluid mechanic",            "fluid-mechanics"),
    ("solid state",               "solid-state-physics"),
    ("statistical mechanic",      "statistical-mechanics"),
    ("bioinformatics",            "bioinformatics"),
    ("computational biology",     "computational-biology"),
    ("game theory",               "game-theory"),
    ("information theory",        "information-theory"),
    ("robotics",                  "robotics"),
    ("mobile development",        "mobile-development"),
    ("ios development",           "ios-development"),
    ("cloud computing",           "cloud-computing"),
    ("devops",                    "devops"),
    ("blockchain",                "blockchain"),
    # Additional tricky titles
    ("signals and systems",                    "signal-processing"),
    ("fourier transform",                      "signal-processing"),
    ("galois",                                 "algebra"),
    ("groups and rings",                       "algebra"),
    ("linear models",                          "statistics"),
    ("generalized linear",                     "statistics"),
    ("statistical models",                     "statistics"),
    ("stochastic processes",                   "probability"),
    ("probabilistic systems",                  "probability"),
    ("single variable analysis",               "real-analysis"),
    ("analysis ii",                            "real-analysis"),
    ("analysis i",                             "real-analysis"),
    ("functions of a real variable",           "real-analysis"),
    ("fundamental concepts of analysis",       "real-analysis"),
    ("theory of numbers",                      "number-theory"),
    ("industrial organization",                "economics"),
    ("international trade",                    "economics"),
    ("econometrics",                           "statistics"),
    ("introduction to econometrics",           "statistics"),
    ("data, inference",                        "statistics"),
    ("mining massive",                         "data-science"),
    ("massive datasets",                       "data-science"),
    ("data systems",                           "databases"),
    ("relativity",                             "physics"),
    ("electricity and magnetism",              "electromagnetism"),
    ("electrodynamics",                        "electromagnetism"),
    ("circuits i",                             "electrical-engineering"),
    ("circuits ii",                            "electrical-engineering"),
    ("circuit analysis",                       "electrical-engineering"),
    ("semiconductor devices",                  "electrical-engineering"),
    ("designing information devices",          "electrical-engineering"),
    ("automatic controls",                     "control-systems"),
    ("dynamics and control",                   "control-systems"),
    ("linear dynamical systems",               "control-systems"),
    ("dynamics of rigid",                      "mechanics"),
    ("asymptotic and perturbation",            "numerical-methods"),
    ("computation structures",                 "computer-architecture"),
    ("introduction to computer systems",       "computer-architecture"),
    ("introduction to computing organization", "computer-architecture"),
    ("introduction to computing",              "computer-science"),
    ("mathematical foundations of computing",  "theory-of-computing"),
    ("models of computation",                  "theory-of-computing"),
    ("theory of computation",                  "theory-of-computing"),
    ("reasoning about computation",            "theory-of-computing"),
    ("computational learning",                 "machine-learning"),
    ("introduction to machine translation",    "natural-language-processing"),
    ("introduction to graphics",               "computer-graphics"),
    ("computer systems security",              "cybersecurity"),
    ("elements of software construction",      "software-engineering"),
    ("principles of imperative computation",   "programming"),
    ("structure and interpretation",           "programming"),
    ("introduction to formal proof",           "mathematics"),
    ("introduction to time series",            "statistics"),
    ("robot intelligence",                     "robotics"),
    ("genetics",                               "biology"),
    ("cellular neurobiology",                  "neuroscience"),
    ("computational vision",                   "computer-vision"),
    ("quality assurance",                      "software-engineering"),
    ("chemical principles",                    "chemistry"),
    ("security",                               "cybersecurity"),
    ("linear modelling",                       "statistics"),
]


def _matches(pattern: str, text: str) -> bool:
    """True if pattern (normalized subject name) appears in text (normalized title).
    Short patterns (<4 chars) require word boundaries to avoid false positives
    like 'c' matching inside 'science' or 'architecture'."""
    if len(pattern) < 4:
        return bool(re.search(r'\b' + re.escape(pattern) + r'\b', text))
    return pattern in text


def find_subject(title: str, subjects: list[tuple[str, str]]) -> str | None:
    """
    subjects: list of (slug, norm_name) sorted by len(norm_name) desc
    Returns the best matching subject slug or None.
    """
    title_norm = normalize(title)
    title_words = set(title_norm.split())

    # 1. Override table
    for phrase, slug in OVERRIDES:
        if normalize(phrase) in title_norm:
            return slug

    best_slug = None
    best_len = 0

    for slug, norm_name in subjects:
        name_len = len(norm_name)

        # 2. Exact phrase match (word-boundary for short names, substring for longer)
        if _matches(norm_name, title_norm) and name_len > best_len:
            best_slug = slug
            best_len = name_len
            continue

        # 3. Singular form (strip trailing 's')
        if norm_name.endswith("s"):
            singular = norm_name[:-1]
            if len(singular) >= 4 and _matches(singular, title_norm) and name_len > best_len:
                best_slug = slug
                best_len = name_len
                continue

        # 4. Word subset for multi-word subjects
        name_words = set(norm_name.split())
        if len(name_words) >= 2 and name_words.issubset(title_words) and name_len > best_len:
            best_slug = slug
            best_len = name_len

    return best_slug


def main():
    conn = psycopg2.connect(CONN)
    cur = conn.cursor()

    # Load all subjects, sorted by name length desc (prefer more specific matches)
    cur.execute("SELECT slug, name FROM subjects ORDER BY length(name) DESC, name")
    subjects = [(slug, normalize(name)) for slug, name in cur.fetchall()]

    # Load all entries
    cur.execute("""
        SELECT id, course_title
        FROM roadmap_entries
        ORDER BY id
    """)
    entries = cur.fetchall()

    matched = 0
    unmatched = []

    for eid, title in entries:
        slug = find_subject(title, subjects)
        if slug:
            cur.execute(
                "UPDATE roadmap_entries SET subject_slug=%s WHERE id=%s",
                (slug, eid)
            )
            matched += 1
        else:
            unmatched.append(title)

    conn.commit()
    cur.close()
    conn.close()

    print(f"Subject matched: {matched} / {len(entries)}")
    if unmatched:
        print(f"\nNo subject found ({len(unmatched)}):")
        for t in sorted(set(unmatched)):
            print(f"  {t}")


if __name__ == "__main__":
    main()
