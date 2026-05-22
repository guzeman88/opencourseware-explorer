import psycopg2
conn = psycopg2.connect("postgresql://neondb_owner:npg_GbATRcy2v8Fo@ep-gentle-cherry-an1c9y9a-pooler.c-6.us-east-1.aws.neon.tech/opencourseware?sslmode=require")
cur = conn.cursor()
cur.execute("SELECT tablename FROM pg_tables WHERE schemaname='public' ORDER BY tablename")
print("Tables:", [r[0] for r in cur.fetchall()])
conn.close()
