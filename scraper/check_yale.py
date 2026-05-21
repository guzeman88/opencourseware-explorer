import psycopg2
from db_utils import get_connection
conn = get_connection()
cur = conn.cursor()
cur.execute("SELECT title, source_url FROM courses WHERE source_key='yale' ORDER BY title")
for r in cur.fetchall():
    print(r[1], '|', r[0])
conn.close()
