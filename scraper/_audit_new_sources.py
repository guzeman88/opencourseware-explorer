import psycopg2, os

conn = psycopg2.connect(os.environ["DATABASE_URL"])
cur = conn.cursor()

# Check Cyrillic titles in math_at_hse
cur.execute("""
    SELECT COUNT(*) FROM courses
    WHERE is_published = TRUE AND source_key = 'math_at_hse'
    AND title ~ '[\\u0400-\\u04FF]'
""")
print(f"math_at_hse courses with Cyrillic titles: {cur.fetchone()[0]}")

cur.execute("""
    SELECT title FROM courses
    WHERE is_published = TRUE AND source_key = 'math_at_hse'
    AND title ~ '[\\u0400-\\u04FF]'
    LIMIT 5
""")
print("Sample Cyrillic titles:")
for r in cur.fetchall():
    print(f"  {r[0][:70]}")

# What source_keys did NOT exist before today (these are all new from API scraper)
# The API scraper inserted new universities and courses
# We know the old sources from prior sessions
old_source_keys = [
    'mit_ocw', 'harvard', 'oxford', 'berkeley', 'cambridge', 'khan', 'cmu',
    'princeton', 'umich', 'caltech', 'ucsd', 'stanford', 'gatech', 'freecodecamp',
    'yale', 'duke', 'simons', 'mit_youtube', '3b1b', 'crashcourse', 'edinburgh',
    'glasgow', 'purdue', 'rice', 'upenn', 'uwashington', 'ucsd', 'vanderbilt',
    'unsw', 'ut_austin', 'umelbourne', 'anu', 'uf', 'open_university_uk',
    'saylor', 'tufts', 'uci', 'jhsph_ocw', 'utah_state', 'nptel',
    'khanacademy', 'cs50', 'neso_academy', 'michelvanbiezen', 'patrickjmt',
    'coding_train', 'sentdex', 'statquest', 'eigensteve', 'octutor',
    'prof_dave', 'wandb', 'yannic_kilcher', 'zach_star', 'borcherds',
    'michael_penn', 'bill_kinney', 'bright_side_math', 'drtefor', 'prof_leonard',
    'kimberly_brehm', 'jacob_sorber', 'james_cook_math', 'computerphile',
    'numberphile', 'ben_eater', 'reducible', 'mathologer', 'deepmind',
]

cur.execute("""
    SELECT DISTINCT source_key, u.name FROM courses c
    JOIN universities u ON c.university_id = u.id
    WHERE c.is_published = TRUE
    ORDER BY source_key
""")
all_sources = {r[0]: r[1] for r in cur.fetchall()}
new_sources = {k: v for k, v in all_sources.items() if k not in old_source_keys}
print(f"\nNew source_keys added by API scraper ({len(new_sources)}):")
for sk, name in sorted(new_sources.items()):
    cur.execute("SELECT COUNT(*) FROM courses WHERE is_published=TRUE AND source_key=%s", (sk,))
    cnt = cur.fetchone()[0]
    print(f"  {sk:35s} {cnt:4d}  [{name}]")

conn.close()
