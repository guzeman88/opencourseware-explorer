import psycopg2
conn = psycopg2.connect(host='127.0.0.1', port=5432, dbname='opencourseware', user='ocw', password='ocwpassword')
cur = conn.cursor()
cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='public' ORDER BY table_name")
print("Tables:", [r[0] for r in cur.fetchall()])

cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name='course_subjects' ORDER BY ordinal_position")
print("course_subjects cols:", [r[0] for r in cur.fetchall()])

cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name='subjects' ORDER BY ordinal_position")
print("subjects cols:", [r[0] for r in cur.fetchall()])
conn.close()
