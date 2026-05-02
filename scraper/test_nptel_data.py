"""Parse NPTEL __data.json to find thumbnail fields."""
import re, requests, json

s = requests.Session()
s.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
})

print("=== NPTEL __data.json full parse ===")
r = s.get("https://nptel.ac.in/courses/106106212/__data.json", timeout=15)
data = r.json()
print(f"Type: {data.get('type')}")
nodes = data.get('nodes', [])
print(f"Nodes count: {len(nodes)}")

# Each node has 'data' which is a flat array of values  
# The first element is an object mapping keys to indices in the array
for i, node in enumerate(nodes):
    if node and node.get('type') == 'data':
        flat = node.get('data', [])
        print(f"\nNode {i}: data array len={len(flat)}")
        # Print all keys in the first object
        if flat and isinstance(flat[0], dict):
            obj = flat[0]
            print(f"  Keys: {list(obj.keys())}")
            # Print first 30 values with their meanings
            for key, idx in obj.items():
                val = flat[idx] if isinstance(idx, int) and idx < len(flat) else idx
                if isinstance(val, (str, int, float, bool)) or val is None:
                    print(f"  {key}: {str(val)[:100]}")
                elif isinstance(val, dict):
                    print(f"  {key} (dict): keys={list(val.keys())[:5]}")
                elif isinstance(val, list):
                    print(f"  {key} (list len={len(val)}): {str(val[:2])[:80]}")
