import psycopg2, os

conn = psycopg2.connect(os.environ["DATABASE_URL"])
cur = conn.cursor()

# Known junk GaTech playlist IDs (events, not courses)
junk_gatech_ids = [
    "PLme0Eox75uXYgg38CCSUPuf87RA7P9W27",  # Avant South 2023
    "PLme0Eox75uXYpM0eX_t46QbMvy_l0Dl5J",  # National Robotics Week 2015
    "PLme0Eox75uXagnkNcOnhWRQJmSVVwrv8K",  # Tech Performances
    "PLme0Eox75uXaFqBUUZqEU94uP9mB6l1n_",  # Commencement 2020
    "PLme0Eox75uXZnWyl6PxjqKYKw6VrPsWpY",  # Holiday Greetings
    "PLme0Eox75uXb4naLQGSfY5tlgmdQ2qO-B",  # Georgia Tech Observatory
    "FLFkaWOGpyFBVRf5jEeD_wrA",            # Favorites
]

# Known junk CMU playlist IDs
junk_cmu_ids = [
    "PL1HxVG_mcukv1KtTvrbVOp9AjqyB3XEYk",  # Orientation
    "PL1HxVG_mcukuoX-TZbt_6c-d12UdLZiyh",  # CMU Experts
    "PL067950B03636F306",                   # Randy Pausch Last Lecture
    "PL9F2DBD90274842E6",                   # Spring Carnival
]

all_junk = junk_gatech_ids + junk_cmu_ids

# Find a default Unsplash-style placeholder URL
cur.execute("SELECT thumbnail_url FROM courses WHERE source_key='gatech' AND thumbnail_url LIKE '%unsplash%' LIMIT 1")
row = cur.fetchone()
fallback = row[0] if row else "https://images.unsplash.com/photo-1523580494863-6f3031224c94?w=1280&q=80"
print(f"Fallback URL: {fallback}")

cur.execute(
    "SELECT id, title, source_key, youtube_playlist_id FROM courses WHERE youtube_playlist_id = ANY(%s)",
    (all_junk,)
)
rows = cur.fetchall()
print(f"\nCourses to revert: {len(rows)}")
for r in rows:
    print(f"  [{r[2]}] {r[1][:60]}: {r[3]}")

# Revert: clear playlist ID and reset thumbnail to Unsplash fallback
if rows:
    cur.execute(
        "UPDATE courses SET youtube_playlist_id = NULL, thumbnail_url = %s WHERE youtube_playlist_id = ANY(%s)",
        (fallback, all_junk)
    )
    conn.commit()
    print(f"\nReverted {cur.rowcount} courses to Unsplash fallback.")

conn.close()
