"""Quick check of Neon DB tables and row counts."""
import psycopg2, os

import os
NEON_URL = os.environ["DATABASE_URL"]

try:
    conn = psycopg2.connect(NEON_URL, connect_timeout=15)
    cur = conn.cursor()
    
    # List all tables
    cur.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public' 
        ORDER BY table_name
    """)
    tables = [r[0] for r in cur.fetchall()]
    print(f"Tables: {tables}")
    
    # Count rows in key tables
    for t in tables:
        cur.execute(f"SELECT COUNT(*) FROM {t}")
        print(f"  {t}: {cur.fetchone()[0]:,} rows")
    
    cur.close()
    conn.close()
except Exception as e:
    print(f"Error: {e}")
    import traceback; traceback.print_exc()
