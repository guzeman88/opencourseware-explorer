import psycopg2
conn = psycopg2.connect(host='127.0.0.1', port=5432, dbname='opencourseware', user='ocw', password='ocwpassword')
cur = conn.cursor()
cur.execute("SELECT title, source_url FROM courses WHERE source_key='yale' ORDER BY title")
for r in cur.fetchall():
    print(r[1], '|', r[0])
conn.close()
