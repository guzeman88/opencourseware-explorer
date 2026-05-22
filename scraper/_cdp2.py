"""
Get Railway cookies from Chrome via CDP using websocket-client library.
"""
import urllib.request, json, sys

# Get browser WS URL
try:
    with urllib.request.urlopen("http://127.0.0.1:9222/json/version", timeout=5) as r:
        info = json.loads(r.read())
    ws_url = info["webSocketDebuggerUrl"]
    print(f"WS: {ws_url}", flush=True)
except Exception as e:
    print(f"CDP not reachable: {e}")
    sys.exit(1)

try:
    import websocket
    ws = websocket.create_connection(ws_url, timeout=10, origin="http://localhost")
    ws.send(json.dumps({"id": 1, "method": "Storage.getCookies", "params": {}}))
    result = json.loads(ws.recv())
    cookies = result.get("result", {}).get("cookies", [])
    ws.close()
    
    print(f"\nTotal cookies: {len(cookies)}")
    railway = [c for c in cookies if "railway" in c.get("domain","").lower()]
    github = [c for c in cookies if "github" in c.get("domain","").lower()]
    
    print(f"\nRailway cookies ({len(railway)}):")
    for c in railway:
        print(f"  {c['name']} = {c['value'][:80]}")
    
    print(f"\nGitHub cookies ({len(github)}):")
    for c in github:
        print(f"  {c['name']} = {c['value'][:80]}")
        
except ImportError:
    print("websocket-client not installed, trying requests approach...")
    # Fallback: use a background page target
    with urllib.request.urlopen("http://127.0.0.1:9222/json", timeout=5) as r:
        targets = json.loads(r.read())
    print(f"Targets: {json.dumps([t.get('url','') for t in targets[:5]], indent=2)}")
except Exception as e:
    import traceback
    print(f"Error: {e}")
    traceback.print_exc()
