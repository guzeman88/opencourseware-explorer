"""Debug Chrome cookie decryption for Profile 2."""
import ctypes, ctypes.wintypes, os, sqlite3, json, base64, win32crypt, tempfile

def read_file_locked(src):
    GENERIC_READ = 0x80000000
    h = ctypes.windll.kernel32.CreateFileW(
        src, GENERIC_READ, 0x7, None, 3, 0x80, None  # SHARE_READ|WRITE|DELETE
    )
    if h == ctypes.wintypes.HANDLE(-1).value:
        return None
    file_size = ctypes.c_ulonglong(0)
    ctypes.windll.kernel32.GetFileSizeEx(h, ctypes.byref(file_size))
    sz = file_size.value
    if sz == 0:
        ctypes.windll.kernel32.CloseHandle(h)
        return b''
    buf = ctypes.create_string_buffer(sz)
    br = ctypes.wintypes.DWORD(0)
    ctypes.windll.kernel32.ReadFile(h, buf, sz, ctypes.byref(br), None)
    ctypes.windll.kernel32.CloseHandle(h)
    return buf.raw[:br.value]

chrome_base = os.path.join(os.environ['LOCALAPPDATA'], 'Google', 'Chrome', 'User Data')
local_state_path = os.path.join(chrome_base, 'Local State')
with open(local_state_path) as f:
    local_state = json.load(f)
key = win32crypt.CryptUnprotectData(
    base64.b64decode(local_state['os_crypt']['encrypted_key'])[5:],
    None, None, None, 0
)[1]
print(f"AES key length: {len(key)} bytes")

src = os.path.join(chrome_base, 'Profile 2', 'Network', 'Cookies')
data = read_file_locked(src)
tmp = tempfile.mktemp(suffix='.db')
with open(tmp, 'wb') as f:
    f.write(data)

conn = sqlite3.connect(tmp)
cur = conn.cursor()
cur.execute("SELECT host_key, name, encrypted_value FROM cookies WHERE host_key LIKE '%github%' LIMIT 5")
for host, name, ev in cur.fetchall():
    print(f"\n{host} | {name}")
    print(f"  Version prefix: {ev[:3]}")
    print(f"  Total length: {len(ev)}")
    print(f"  First 20 bytes hex: {ev[:20].hex()}")
conn.close()
os.unlink(tmp)
