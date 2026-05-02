"""
Check the full __data.json structure for a non-video NPTEL course.
"""
import re, requests, json

s = requests.Session()
s.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
})

def _svelte_resolve(flat, idx, depth=0):
    if depth > 30:
        return f"<maxdepth:{idx}>"
    if not isinstance(idx, int) or idx >= len(flat):
        return idx
    val = flat[idx]
    if isinstance(val, dict):
        return {k: _svelte_resolve(flat, v, depth+1) for k, v in val.items()}
    elif isinstance(val, list):
        return [_svelte_resolve(flat, v, depth+1) for v in val]
    return val

# Test the first NULL NPTEL course
surl = "https://nptel.ac.in/courses/106/105/106105078/"
m = re.search(r'/courses/\d+/\d+/(\d+)/?', surl)
course_id = m.group(1)
data_url = f"https://nptel.ac.in/courses/{course_id}/__data.json"
print(f"Fetching: {data_url}")

r = s.get(data_url, timeout=15)
print(f"HTTP {r.status_code}")
data = r.json()

for node in data.get("nodes", []):
    if not node or node.get("type") != "data":
        continue
    flat = node.get("data", [])
    if not flat or not isinstance(flat[0], dict):
        continue
    resolved = _svelte_resolve(flat, 0)
    
    # Print all keys at top level
    print(f"\nTop-level keys: {list(resolved.keys())}")
    
    # Look for any image-related fields
    def find_images(obj, path=""):
        if isinstance(obj, str):
            if any(ext in obj.lower() for ext in ['.jpg', '.jpeg', '.png', '.webp', 'image', 'img', 'thumb', 'poster']):
                print(f"  IMAGE-LIKE at {path}: {obj[:100]}")
        elif isinstance(obj, dict):
            for k, v in obj.items():
                find_images(v, f"{path}.{k}")
        elif isinstance(obj, list):
            for i, v in enumerate(obj[:3]):  # only first 3 items
                find_images(v, f"{path}[{i}]")
    
    find_images(resolved)
    
    # Print courseOutline structure more completely
    co = resolved.get("courseOutline") or {}
    units = co.get("units") or []
    print(f"\nunits: {len(units)}")
    if units:
        u0 = units[0] or {}
        lessons = u0.get("lessons") or []
        print(f"unit[0] lessons: {len(lessons)}")
        if lessons:
            l0 = lessons[0] or {}
            print(f"lesson[0]: {json.dumps(l0, default=str)}")
    
    # Also check other top-level keys
    for key in resolved.keys():
        if key != "courseOutline":
            val = resolved[key]
            if val and not isinstance(val, (list, dict)):
                print(f"  {key}: {str(val)[:100]}")
            elif isinstance(val, dict) and val:
                print(f"  {key} (dict keys): {list(val.keys())[:10]}")
    break
