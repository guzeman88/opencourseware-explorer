"""Wait for Railway DB to come back online, then restart the backfill."""
import os, subprocess, sys, time

if not os.environ.get("DATABASE_URL"):
    print("ERROR: DATABASE_URL env var is required", flush=True)
    sys.exit(1)
os.environ['PYTHONUNBUFFERED'] = '1'
os.environ['PYTHONUTF8'] = '1'
os.environ['PYTHONIOENCODING'] = 'utf-8'

from db_utils import get_connection

print("Waiting for Railway DB to come back online...")
attempt = 0
while True:
    attempt += 1
    try:
        conn = get_connection()
        conn.close()
        print(f"DB is up! (attempt {attempt})")
        break
    except Exception as e:
        wait = min(30, attempt * 5)
        print(f"  [{attempt}] Still down: {e.__class__.__name__} — retrying in {wait}s")
        time.sleep(wait)

print("Launching backfill...")
result = subprocess.run(
    [sys.executable, '-u', 'backfill_videos.py'],
    env=os.environ.copy()
)
sys.exit(result.returncode)
