"""Check all Chrome profiles for Railway and GitHub session cookies."""
import ctypes, ctypes.wintypes, os, sqlite3, json, base64, win32crypt, tempfile
from Crypto.Cipher import AES

def read_file_locked(src):
    GENERIC_READ = 0x80000000
    FILE_SHARE_READ, FILE_SHARE_WRITE, FILE_SHARE_DELETE = 0x1, 0x2, 0x4
    OPEN_EXISTING, FILE_ATTRIBUTE_NORMAL = 3, 0x80
    h = ctypes.windll.kernel32.CreateFileW(
        src, GENERIC_READ,
        FILE_SHARE_READ | FILE_SHARE_WRITE | FILE_SHARE_DELETE,
        None, OPEN_EXISTING, FILE_ATTRIBUTE_NORMAL, None
    )
    if h == ctypes.wintypes.HANDLE(-1).value:
        return None
    sz = ctypes.windll.kernel32.GetFileSize(h, None)
    buf = ctypes.create_string_buffer(sz)
    br = ctypes.wintypes.DWORD(0)
    ctypes.windll.kernel32.ReadFile(h, buf, sz, ctypes.byref(br), None)
    ctypes.windll.kernel32.CloseHandle(h)
    return buf.raw[:br.value]

local_state_path = os.environ['LOCALAPPDATA'] + '/Google/Chrome/User Data/Local State'
with open(local_state_path) as f:
    local_state = json.load(f)
key = win32crypt.CryptUnprotectData(
    base64.b64decode(local_state['os_crypt']['encrypted_key'])[5:],
    None, None, None, 0
)[1]

for profile in ['Default', 'Profile', 'Profile 1', 'Profile 2']:
    src = os.environ['LOCALAPPDATA'] + f'/Google/Chrome/User Data/{profile}/Network/Cookies'
    if not os.path.exists(src):
        continue
    
    data = read_file_locked(src)
    if data is None:
        print(f'{profile}: could not read')
        continue
    
    tmp = tempfile.mktemp(suffix='.db')
    with open(tmp, 'wb') as f:
        f.write(data)
    
    conn = sqlite3.connect(tmp)
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM cookies WHERE host_key LIKE '%railway%' OR host_key LIKE '%github%'")
    cnt = cur.fetchone()[0]
    
    if cnt > 0:
        print(f'{profile}: {cnt} rows for railway/github')
        cur.execute("SELECT host_key, name, encrypted_value FROM cookies WHERE host_key LIKE '%railway%' OR host_key LIKE '%github%'")
        for host, name, ev in cur.fetchall():
            try:
                v = AES.new(key, AES.MODE_GCM, nonce=ev[3:15]).decrypt_and_verify(ev[15:-16], ev[-16:]).decode()
                print(f'  {host} | {name}={v[:60]}')
            except Exception as e:
                print(f'  {host} | {name}=<decrypt error: {e}>')
    else:
        cur.execute("SELECT COUNT(*) FROM cookies")
        total = cur.fetchone()[0]
        print(f'{profile}: no railway/github cookies (has {total} total)')
    
    conn.close()
    os.unlink(tmp)
