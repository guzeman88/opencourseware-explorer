import psycopg2, os, requests

conn = psycopg2.connect(os.environ['DATABASE_URL'])
cur = conn.cursor()

# Check sample source URLs for the worst-performing sources
for src in ['saylor', 'open_university_uk', 'utah_state', 'tufts', 'uci', 'jhsph_ocw', 'oxford']:
    cur.execute(
        "SELECT title, source_url FROM courses WHERE source_key=%s AND thumbnail_url LIKE %s AND is_published=TRUE LIMIT 2",
        (src, '%unsplash%')
    )
    rows = cur.fetchall()
    print(f"\n=== {src} ===")
    for title, url in rows:
        print(f"  {title[:50]}")
        print(f"  {url[:80]}")
        # Quick test
        try:
            r = requests.get(url, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
            print(f"  HTTP {r.status_code}, {len(r.text)} chars")
            if 'og:image' in r.text:
                print(f"  HAS og:image!")
            else:
                print(f"  no og:image in page")
        except Exception as e:
            print(f"  ERROR: {e}")

conn.close()
