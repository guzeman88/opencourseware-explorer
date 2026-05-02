import psycopg2
conn = psycopg2.connect(host='127.0.0.1', port=5432, dbname='opencourseware', user='ocw', password='ocwpassword')
cur = conn.cursor()
cur.execute("SELECT column_name, data_type FROM information_schema.columns WHERE table_name='courses' ORDER BY ordinal_position")
for r in cur.fetchall():
    print(r)
conn.close()
