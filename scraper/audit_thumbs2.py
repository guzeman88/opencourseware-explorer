import psycopg2

conn = psycopg2.connect(host='127.0.0.1', port=5432, dbname='opencourseware', user='ocw', password='ocwpassword')
cur = conn.cursor()

# Check NPTEL - do they have youtube_playlist_id?
cur.execute("""
SELECT COUNT(*) total,
  COUNT(youtube_playlist_id) has_playlist,
  COUNT(CASE WHEN thumbnail_url LIKE '%unsplash%' THEN 1 END) unsplash
FROM courses WHERE source_key = 'nptel'
""")
r = cur.fetchone()
print(f"NPTEL: total={r[0]}, has_playlist={r[1]}, unsplash={r[2]}")

# Sample NPTEL URLs
cur.execute("SELECT source_url, youtube_playlist_id FROM courses WHERE source_key='nptel' LIMIT 10")
print("\nNPTEL samples:")
for r in cur.fetchall():
    print(f"  url={r[0][:80]}  playlist={r[1]}")

# Berkeley archive.org - can we extract playlist from URL?
cur.execute("SELECT source_url, youtube_playlist_id FROM courses WHERE source_key='berkeley' AND thumbnail_url LIKE '%unsplash%' LIMIT 10")
print("\nBerkeley samples (unsplash):")
for r in cur.fetchall():
    print(f"  url={r[0][:80]}  playlist={r[1]}")

# Harvard URLs
cur.execute("SELECT source_url, youtube_playlist_id FROM courses WHERE source_key='harvard' AND thumbnail_url LIKE '%unsplash%' LIMIT 10")
print("\nHarvard samples:")
for r in cur.fetchall():
    print(f"  url={r[0][:80]}  playlist={r[1]}")

# Stanford
cur.execute("SELECT source_url, youtube_playlist_id FROM courses WHERE source_key='stanford' AND thumbnail_url LIKE '%unsplash%' LIMIT 10")
print("\nStanford samples:")
for r in cur.fetchall():
    print(f"  url={r[0][:80]}  playlist={r[1]}")

# Oxford
cur.execute("SELECT source_url, youtube_playlist_id FROM courses WHERE source_key='oxford' AND thumbnail_url LIKE '%unsplash%' LIMIT 10")
print("\nOxford samples:")
for r in cur.fetchall():
    print(f"  url={r[0][:80]}  playlist={r[1]}")

# edX-based: anu, cambridge, unsw, umelbourne
for src in ['anu', 'cambridge', 'unsw', 'umelbourne', 'uf', 'edinburgh', 'glasgow']:
    cur.execute(f"SELECT source_url, youtube_playlist_id FROM courses WHERE source_key='{src}' AND thumbnail_url LIKE '%unsplash%' LIMIT 3")
    rows = cur.fetchall()
    if rows:
        print(f"\n{src} samples:")
        for r in rows:
            print(f"  url={r[0][:80]}  playlist={r[1]}")

# Coursera-based
for src in ['princeton', 'vanderbilt', 'duke', 'uwashington']:
    cur.execute(f"SELECT source_url, youtube_playlist_id FROM courses WHERE source_key='{src}' AND thumbnail_url LIKE '%unsplash%' LIMIT 3")
    rows = cur.fetchall()
    if rows:
        print(f"\n{src} samples:")
        for r in rows:
            print(f"  url={r[0][:80]}  playlist={r[1]}")

# OCW sites
for src in ['utah_state', 'tufts', 'uci', 'jhsph_ocw', 'saylor', 'open_university_uk']:
    cur.execute(f"SELECT source_url, youtube_playlist_id FROM courses WHERE source_key='{src}' AND thumbnail_url LIKE '%unsplash%' LIMIT 3")
    rows = cur.fetchall()
    if rows:
        print(f"\n{src} samples:")
        for r in rows:
            print(f"  url={r[0][:80]}  playlist={r[1]}")

conn.close()
