"""Parse NPTEL __data.json - properly resolve SvelteKit references."""
import requests, json

s = requests.Session()
s.headers.update({"User-Agent": "Mozilla/5.0"})

def resolve(flat, idx):
    """Recursively resolve SvelteKit serialized data."""
    if idx >= len(flat):
        return None
    val = flat[idx]
    if isinstance(val, dict):
        return {k: resolve(flat, v) if isinstance(v, int) else v for k, v in val.items()}
    elif isinstance(val, list):
        return [resolve(flat, v) if isinstance(v, int) else v for v in val]
    else:
        return val

def extract_nptel_thumb(course_id):
    url = f"https://nptel.ac.in/courses/{course_id}/__data.json"
    try:
        r = s.get(url, timeout=12)
        if not r.ok:
            return None
        data = r.json()
        for node in data.get('nodes', []):
            if not node or node.get('type') != 'data':
                continue
            flat = node.get('data', [])
            if not flat or not isinstance(flat[0], dict):
                continue
            resolved = resolve(flat, 0)
            # Print full structure for first course
            print(f"  Resolved keys: {list(resolved.keys())[:10]}")
            # Navigate into courseOutline
            co = resolved.get('courseOutline') or {}
            print(f"  courseOutline keys: {list(co.keys())[:20]}")
            # Look at nocCourse
            noc = co.get('nocCourse') or {}
            print(f"  nocCourse type: {type(noc)}, keys: {list(noc.keys())[:20] if isinstance(noc, dict) else str(noc)[:80]}")
            # Recursively find any thumbnail/image fields
            def find_images(obj, path=""):
                results = []
                if isinstance(obj, dict):
                    for k, v in obj.items():
                        if any(word in k.lower() for word in ['image', 'thumb', 'photo', 'photo', 'cover', 'poster', 'youtube', 'playlist', 'media']):
                            results.append((path+"."+k, str(v)[:100]))
                        results.extend(find_images(v, path+"."+k))
                elif isinstance(obj, list):
                    for i, v in enumerate(obj[:5]):
                        results.extend(find_images(v, path+f"[{i}]"))
                return results
            imgs = find_images(resolved)
            print(f"\n  Image/media fields found:")
            for field, val in imgs[:20]:
                print(f"    {field}: {val}")
            return resolved
    except Exception as e:
        print(f"  Error: {e}")
    return None

print("=== NPTEL __data.json for course 106106212 ===")
result = extract_nptel_thumb("106106212")

print("\n=== NPTEL __data.json for course with playlist (106106001) ===")
# Try another course ID
r = s.get("https://nptel.ac.in/courses/106101061/__data.json", timeout=12)
if r.ok:
    data = r.json()
    for node in data.get('nodes', []):
        if node and node.get('type') == 'data':
            flat = node.get('data', [])
            if flat and isinstance(flat[0], dict):
                resolved = resolve(flat, 0)
                def find_images(obj, path=""):
                    results = []
                    if isinstance(obj, dict):
                        for k, v in obj.items():
                            if any(word in k.lower() for word in ['image', 'thumb', 'photo', 'cover', 'poster', 'youtube', 'playlist', 'media', 'video']):
                                results.append((path+"."+k, str(v)[:100]))
                            results.extend(find_images(v, path+"."+k))
                    elif isinstance(obj, list):
                        for i, v in enumerate(obj[:3]):
                            results.extend(find_images(v, path+f"[{i}]"))
                    return results
                imgs = find_images(resolved)
                print(f"  Image/media fields:")
                for field, val in imgs[:20]:
                    print(f"    {field}: {val}")
