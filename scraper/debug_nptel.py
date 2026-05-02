"""
Deep-debug the NPTEL NULL courses — look at the actual courseOutline structure.
"""
import re, requests, json

s = requests.Session()
s.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
})

def _svelte_resolve(flat, idx):
    if not isinstance(idx, int) or idx >= len(flat):
        return idx
    val = flat[idx]
    if isinstance(val, dict):
        return {k: _svelte_resolve(flat, v) for k, v in val.items()}
    elif isinstance(val, list):
        return [_svelte_resolve(flat, v) for v in val]
    return val

import psycopg2
conn = psycopg2.connect(host='127.0.0.1',port=5432,dbname='opencourseware',user='ocw',password='ocwpassword')
cur = conn.cursor()
cur.execute("SELECT id, source_url FROM courses WHERE source_key='nptel' AND thumbnail_url IS NULL LIMIT 5")
rows = cur.fetchall()
conn.close()

for cid, surl in rows:
    m = re.search(r'/courses/\d+/\d+/(\d+)/?', surl)
    if not m:
        m = re.search(r'/courses/(\d+)/?$', surl)
    if not m:
        print(f"NO MATCH: {surl}")
        continue
    course_id = m.group(1)
    data_url = f"https://nptel.ac.in/courses/{course_id}/__data.json"
    print(f"\n{'='*60}")
    print(f"URL: {surl}")
    print(f"DATA: {data_url}")
    try:
        r = s.get(data_url, timeout=15)
        if not r.ok:
            print(f"  HTTP {r.status_code}")
            continue
        data = r.json()
        for node in data.get("nodes", []):
            if not node or node.get("type") != "data":
                continue
            flat = node.get("data", [])
            if not flat or not isinstance(flat[0], dict):
                continue
            resolved = _svelte_resolve(flat, 0)
            co = resolved.get("courseOutline") or {}
            units = co.get("units") or []
            print(f"  units count: {len(units)}")
            if units:
                u0 = units[0] or {}
                lessons = u0.get("lessons") or []
                print(f"  lessons in unit[0]: {len(lessons)}")
                if lessons:
                    l0 = lessons[0] or {}
                    print(f"  lesson[0] keys: {list(l0.keys())}")
                    print(f"  lesson[0].youtube_id: {l0.get('youtube_id')}")
                    print(f"  lesson[0].video_url: {l0.get('video_url')}")
                    # Check ALL lessons for youtube_id
                    yt_ids = []
                    for u in units:
                        for l in (u or {}).get("lessons") or []:
                            yt = (l or {}).get("youtube_id")
                            if yt:
                                yt_ids.append(yt)
                    print(f"  All youtube_ids across lessons: {yt_ids[:5]}")
                else:
                    print(f"  unit[0] keys: {list(u0.keys())}")
                    # Dump courseOutline structure for debugging
                    print(f"  courseOutline keys: {list(co.keys())}")
                    print(f"  courseOutline sample: {json.dumps(co, default=str)[:500]}")
            else:
                # No units - dump courseOutline
                print(f"  courseOutline: {json.dumps(co, default=str)[:500]}")
            break
    except Exception as e:
        print(f"  ERROR: {e}")
