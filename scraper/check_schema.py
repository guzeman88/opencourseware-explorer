import psycopg2
from db_utils import get_connection
conn = get_connection()
cur = conn.cursor()
cur.execute("SELECT column_name, data_type FROM information_schema.columns WHERE table_name='courses' ORDER BY ordinal_position")
for r in cur.fetchall():
    print(r)
conn.close()
