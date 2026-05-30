import psycopg2, os

conn = psycopg2.connect(os.environ["DATABASE_URL"])
cur = conn.cursor()

checks = {
    "vlsi": ["vlsi", "chip design", "cmos"],
    "social-psychology": ["social psychology", "social cognition"],
    "philosophy-of-mind": ["philosophy of mind", "mind and brain"],
    "political-philosophy": ["political philosophy", "political theory"],
    "data-management": ["data management", "database management"],
    "atmospheric-science": ["atmospheric", "meteorology", "weather", "climate"],
    "formal-verification": ["formal verification", "model checking", "proof assistant", "coq", "isabelle"],
    "global-politics": ["global politics", "world politics", "international security"],
    "human-rights": ["human rights"],
    "civil-rights": ["civil rights"],
    "biological-engineering": ["biological engineering", "bioengineering"],
    "origins-of-life": ["origin of life", "origins of life", "abiogenesis"],
    "literary-theory": ["literary theory", "critical theory"],
    "ocean-engineering": ["ocean engineering", "marine engineering", "offshore"],
    "clinical-trials": ["clinical trial", "randomized controlled", "clinical research"],
    "demographics": ["demographics", "demography", "population studies"],
    "media-history": ["media history", "history of media", "history of journalism"],
}

for subj, kws in checks.items():
    found = False
    for kw in kws:
        cur.execute("SELECT COUNT(*) FROM courses WHERE is_published=TRUE AND LOWER(title) LIKE %s", (f"%{kw}%",))
        n = cur.fetchone()[0]
        if n > 0:
            print(f"{subj:<30} {n:>4} courses matching '{kw}'")
            found = True
            break
    if not found:
        print(f"{subj:<30}    0  NO matches")

conn.close()
