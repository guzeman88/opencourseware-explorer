"""Check Edge browser for Railway and GitHub session cookies."""
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
    # Use GetFileSizeEx for correct size
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

def check_cookies(browser_name, local_state_path, profiles_base):
    if not os.path.exists(local_state_path):
        print(f'{browser_name}: not found')
        return
    
    with open(local_state_path) as f:
        local_state = json.load(f)
    key = win32crypt.CryptUnprotectData(
        base64.b64decode(local_state['os_crypt']['encrypted_key'])[5:],
        None, None, None, 0
    )[1]

    for profile in ['Default', 'Profile', 'Profile 1', 'Profile 2']:
        src = os.path.join(profiles_base, profile, 'Network', 'Cookies')
        if not os.path.exists(src):
            continue
        
        data = read_file_locked(src)
        if data is None or len(data) == 0:
            print(f'{browser_name}/{profile}: could not read or empty')
            continue
        
        tmp = tempfile.mktemp(suffix='.db')
        with open(tmp, 'wb') as f:
            f.write(data)
        
        try:
            conn = sqlite3.connect(tmp)
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) FROM cookies WHERE host_key LIKE '%railway%' OR host_key LIKE '%github%'")
            cnt = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM cookies")
            total = cur.fetchone()[0]
            
            if cnt > 0:
                print(f'\n{browser_name}/{profile}: {cnt} rows for railway/github (total: {total})')
                cur.execute("SELECT host_key, name, encrypted_value FROM cookies WHERE host_key LIKE '%railway%' OR host_key LIKE '%github%' ORDER BY host_key, name")
                for host, name, ev in cur.fetchall():
                    try:
                        v = AES.new(key, AES.MODE_GCM, nonce=ev[3:15]).decrypt_and_verify(ev[15:-16], ev[-16:]).decode()
                        print(f'  {host} | {name}={v[:70]}')
                    except Exception as e:
                        print(f'  {host} | {name}=<err: {e}>')
            else:
                print(f'{browser_name}/{profile}: no railway/github cookies (total: {total})')
            
            conn.close()
        except Exception as e:
            print(f'{browser_name}/{profile}: error: {e}')
        finally:
            try: os.unlink(tmp)
            except: pass

# Edge
edge_base = os.path.join(os.environ['LOCALAPPDATA'], 'Microsoft', 'Edge', 'User Data')
check_cookies('Edge', os.path.join(edge_base, 'Local State'), edge_base)

# Chrome  
chrome_base = os.path.join(os.environ['LOCALAPPDATA'], 'Google', 'Chrome', 'User Data')
check_cookies('Chrome', os.path.join(chrome_base, 'Local State'), chrome_base)
