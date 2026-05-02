"""
Deep-debug NPTEL NULL - check lecturelink format and structure variations.
"""
import re, requests, json, traceback

s = requests.Session()
s.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
})

def _svelte_resolve(flat, idx, depth=0):
    if depth > 20:
        return idx
    if not isinstance(idx, int) or idx >= len(flat):
        return idx
    val = flat[idx]
    if isinstance(val, dict):
        return {k: _svelte_resolve(flat, v, depth+1) for k, v in val.items()}
    elif isinstance(val, list):
        return [_svelte_resolve(flat, v, depth+1) for v in val]
    return val

import psycopg2
conn = psycopg2.connect(host='127.0.0.1',port=5432,dbname='opencourseware',user='ocw',password='ocwpassword')
cur = conn.cursor()
cur.execute("SELECT id, source_url FROM courses WHERE source_key='nptel' AND thumbnail_url IS NULL LIMIT 8")
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
            try:
                resolved = _svelte_resolve(flat, 0)
            except Exception as e:
                print(f"  resolve error: {e}")
                continue
            co = resolved.get("courseOutline") or {}
            units = co.get("units") or []
            if units:
                lessons = (units[0] or {}).get("lessons") or []
                if lessons:
                    l0 = lessons[0] or {}
                    print(f"  lesson[0] keys: {list(l0.keys())}")
                    print(f"  lesson[0].youtube_id: {l0.get('youtube_id')}")
                    print(f"  lesson[0].lecturelink: {l0.get('lecturelink')}")
                    print(f"  lesson[0].leccontenttype: {l0.get('leccontenttype')}")
                    # Search all lessons for any youtube-like field
                    for u in units:
                        for l in (u or {}).get("lessons") or []:
                            yt = (l or {}).get("youtube_id")
                            ll = (l or {}).get("lecturelink") or ""
                            if yt:
                                print(f"  FOUND youtube_id: {yt}")
                                break
                            if "youtube" in str(ll).lower() or "youtu.be" in str(ll).lower():
                                print(f"  FOUND youtube in lecturelink: {ll}")
                                break
            break
    except Exception as e:
        print(f"  EXCEPTION: {e}")
        traceback.print_exc()
