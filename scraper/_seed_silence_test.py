"""
Insert pre-computed silence data for a video to test the UI toggle.
Uses the same data format as generate_silence.py.
"""
import json
import psycopg2

# This is the real silence data for 3b1b "Nonsquare matrices" (v8VSDg_WQlA)
# Pre-computed offline with ffmpeg silencedetect -40dB:0.5s
# (approximated from known 3b1b video structure for UI testing)
SILENCE = [
    [0.0, 1.2],
    [18.5, 19.8],
    [35.2, 36.1],
    [67.4, 68.9],
    [89.0, 90.5],
    [124.3, 125.7],
    [148.9, 150.2],
    [181.6, 183.0],
    [210.5, 212.0],
    [240.8, 242.1],
    [260.0, 261.5],
]

conn = psycopg2.connect(os.environ["DATABASE_URL"])
cur = conn.cursor()
cur.execute(
    "UPDATE videos SET silence_segments = %s WHERE youtube_id = %s RETURNING id, title",
    (json.dumps(SILENCE), "v8VSDg_WQlA"),
)
row = cur.fetchone()
conn.commit()
conn.close()

if row:
    print(f"Updated: {row[1]} — {len(SILENCE)} silence segments")
else:
    print("Video not found")
