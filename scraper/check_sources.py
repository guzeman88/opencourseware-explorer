import psycopg2
from db_utils import get_connection
conn = get_connection()
cur = conn.cursor()
for src in ['nptel','stanford','berkeley','oxford','yale','khan','crashcourse','3b1b','cambridge','princeton','gatech','mit_youtube','saylor','open_university_uk']:
    cur.execute("SELECT source_url, youtube_playlist_id FROM courses WHERE source_key=%s AND thumbnail_url LIKE '%%unsplash%%' LIMIT 3", (src,))
    rows = cur.fetchall()
    print(f'\n--- {src} ---')
    for r in rows:
        print(f'  url: {r[0]}  playlist: {r[1]}')
conn.close()
