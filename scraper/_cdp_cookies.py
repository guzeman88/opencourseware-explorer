"""
Get Railway/GitHub cookies from Chrome via Chrome DevTools Protocol (CDP).
Chrome is running with --remote-debugging-port=9222 --profile-directory="Profile 2"
"""
import urllib.request
import json

# Get list of targets
try:
    with urllib.request.urlopen("http://127.0.0.1:9222/json", timeout=5) as resp:
        targets = json.loads(resp.read())
    print(f"Found {len(targets)} Chrome targets")
    for t in targets[:3]:
        print(f"  - {t.get('type')}: {t.get('url', '')[:80]}")
except Exception as e:
    print(f"Could not connect to CDP: {e}")
    exit(1)

# Use /json/version to get the websocket debugger URL
import http.client
import socket

def cdp_request(ws_url, method, params=None):
    """Simple CDP request via websocket."""
    import struct
    
    # Parse ws URL: ws://127.0.0.1:9222/devtools/browser/...
    # We'll use HTTP GET with upgrade
    ws_url = ws_url.replace("ws://", "")
    host, path = ws_url.split("/", 1)
    path = "/" + path
    
    # Build websocket handshake
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(10)
    sock.connect(("127.0.0.1", 9222))
    
    import base64, hashlib, os
    key = base64.b64encode(os.urandom(16)).decode()
    
    handshake = (
        f"GET {path} HTTP/1.1\r\n"
        f"Host: 127.0.0.1:9222\r\n"
        f"Upgrade: websocket\r\n"
        f"Connection: Upgrade\r\n"
        f"Sec-WebSocket-Key: {key}\r\n"
        f"Sec-WebSocket-Version: 13\r\n\r\n"
    )
    sock.send(handshake.encode())
    
    resp = b""
    while b"\r\n\r\n" not in resp:
        resp += sock.recv(1024)
    
    # Send CDP command
    payload = json.dumps({"id": 1, "method": method, "params": params or {}}).encode()
    header = b"\x81"  # text frame, FIN
    length = len(payload)
    if length <= 125:
        header += bytes([length | 0x80])
    elif length <= 65535:
        header += bytes([126 | 0x80]) + struct.pack(">H", length)
    else:
        header += bytes([127 | 0x80]) + struct.pack(">Q", length)
    mask = os.urandom(4)
    header += mask
    masked = bytes(b ^ mask[i % 4] for i, b in enumerate(payload))
    sock.send(header + masked)
    
    # Read response
    data = b""
    while True:
        chunk = sock.recv(65536)
        if not chunk:
            break
        data += chunk
        # Try to parse
        if len(data) >= 2:
            fin_opcode = data[0]
            masked_len = data[1]
            is_masked = (masked_len & 0x80) != 0
            payload_len = masked_len & 0x7F
            offset = 2
            if payload_len == 126:
                payload_len = struct.unpack(">H", data[2:4])[0]
                offset = 4
            elif payload_len == 127:
                payload_len = struct.unpack(">Q", data[2:10])[0]
                offset = 10
            if is_masked:
                offset += 4
            if len(data) >= offset + payload_len:
                result_bytes = data[offset:offset + payload_len]
                sock.close()
                return json.loads(result_bytes.decode())
    
    sock.close()
    return None

# Get the browser target websocket URL
try:
    with urllib.request.urlopen("http://127.0.0.1:9222/json/version", timeout=5) as resp:
        version_info = json.loads(resp.read())
    ws_url = version_info.get("webSocketDebuggerUrl", "")
    print(f"\nBrowser WS URL: {ws_url[:80]}")
    
    result = cdp_request(ws_url, "Storage.getCookies")
    if result and "result" in result:
        cookies = result["result"].get("cookies", [])
        print(f"\nTotal cookies: {len(cookies)}")
        
        railway_cookies = [c for c in cookies if "railway" in c.get("domain", "").lower()]
        github_cookies = [c for c in cookies if "github" in c.get("domain", "").lower()]
        
        print(f"\nRailway cookies: {len(railway_cookies)}")
        for c in railway_cookies:
            print(f"  {c['name']} = {c['value'][:50]}...")
        
        print(f"\nGitHub cookies: {len(github_cookies)}")
        for c in github_cookies:
            print(f"  {c['name']} = {c['value'][:50]}...")
    else:
        print(f"CDP response: {result}")
        
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
