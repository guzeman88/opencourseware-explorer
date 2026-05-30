import psycopg2, os

conn = psycopg2.connect(os.environ["DATABASE_URL"])
cur = conn.cursor()

# Cambridge playlist IDs that are clearly unrelated to course content
junk_cambridge_ids = [
    "PL061FA6816406F70E",                   # Anthropology
    "PLoEBu2Q8ia_NvemMUcqCmyGUEAnLoNYki",  # Expert Analysis (misleads Analysis courses)
    "PLoEBu2Q8ia_NpeZRhagE5BKCPBBq7YmOE",  # The Rising Tide
    "PLoEBu2Q8ia_Ns0rDixLvubUV9bhRP17OA",  # Journeys of Discovery
    "PLoEBu2Q8ia_Nzldm-gqK12JzbYXIYqGqQ",  # Modern and Medieval Languages
    "PLoEBu2Q8ia_MW2IiSaPXuQIh2fOLlgXbf",  # Black Cantabs: History Makers
    "PLoEBu2Q8ia_O2SkexzzBMn-tsNUXGpZVr",  # Student clubs and societies
    "PLoEBu2Q8ia_P787z2xg1Zo1IV_ZVs1mzp",  # Rise of the Machines
    "PLoEBu2Q8ia_MqEALSYEkNWwHEey-yX_0S",  # Breaking the Silence
    "PL95D2C4EE146C3199",                   # The Arts and Humanities: Endangered Species
    "FLc5vZEM1MLUzCrg_aZIJdeA",             # Favorites (not a course playlist)
]

# Get a Cambridge fallback URL
cur.execute("SELECT thumbnail_url FROM courses WHERE source_key='cambridge' AND thumbnail_url LIKE '%unsplash%' LIMIT 1")
row = cur.fetchone()
fallback = row[0] if row else "https://images.unsplash.com/photo-1503676260728-1c00da094a0b?w=640&q=80"

# Also revert Quantum Mechanics course specifically (matched to Economics playlist — wrong)
cur.execute(
    "SELECT id, title, youtube_playlist_id FROM courses WHERE source_key='cambridge' AND youtube_playlist_id = ANY(%s)",
    (junk_cambridge_ids,)
)
rows = cur.fetchall()
print(f"Cambridge courses to revert: {len(rows)}")
for r in rows:
    print(f"  {r[1][:60]}: {r[2]}")

# Also revert Quantum Mechanics that was wrongly matched to Economics
cur.execute(
    "SELECT id, title, youtube_playlist_id FROM courses WHERE source_key='cambridge' AND title LIKE '%Quantum Mechanics%' AND youtube_playlist_id = 'PLoEBu2Q8ia_Mn850wAftopZlCXxBB6w_7'"
)
qm_rows = cur.fetchall()
print(f"\nQuantum Mechanics false match: {len(qm_rows)}")
for r in qm_rows:
    print(f"  {r[1]}: {r[2]}")

all_ids = [r[0] for r in rows] + [r[0] for r in qm_rows]

if all_ids:
    cur.execute(
        "UPDATE courses SET youtube_playlist_id = NULL, thumbnail_url = %s WHERE id = ANY(%s::uuid[])",
        (fallback, all_ids)
    )
    conn.commit()
    print(f"\nReverted {cur.rowcount} Cambridge courses to Unsplash fallback.")

conn.close()
