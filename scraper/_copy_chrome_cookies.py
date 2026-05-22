"""Copy Chrome's locked cookie file using Windows low-level API."""
import ctypes, ctypes.wintypes, os, shutil, tempfile

def copy_locked_file(src, dst):
    """Copy a file that may be locked by another process."""
    GENERIC_READ = 0x80000000
    FILE_SHARE_READ = 0x1
    FILE_SHARE_WRITE = 0x2
    FILE_SHARE_DELETE = 0x4
    OPEN_EXISTING = 3
    FILE_ATTRIBUTE_NORMAL = 0x80

    CreateFile = ctypes.windll.kernel32.CreateFileW
    ReadFile = ctypes.windll.kernel32.ReadFile
    CloseHandle = ctypes.windll.kernel32.CloseHandle
    GetFileSize = ctypes.windll.kernel32.GetFileSize

    handle = CreateFile(
        src,
        GENERIC_READ,
        FILE_SHARE_READ | FILE_SHARE_WRITE | FILE_SHARE_DELETE,
        None,
        OPEN_EXISTING,
        FILE_ATTRIBUTE_NORMAL,
        None
    )

    if handle == ctypes.wintypes.HANDLE(-1).value:
        err = ctypes.windll.kernel32.GetLastError()
        raise PermissionError(f"CreateFile failed: error {err}")

    size = GetFileSize(handle, None)
    print(f"Cookie file size: {size} bytes")

    buf = ctypes.create_string_buffer(size)
    bytes_read = ctypes.wintypes.DWORD(0)
    ReadFile(handle, buf, size, ctypes.byref(bytes_read), None)
    CloseHandle(handle)

    with open(dst, 'wb') as f:
        f.write(buf.raw[:bytes_read.value])
    
    print(f"Copied {bytes_read.value} bytes to {dst}")
    return bytes_read.value

if __name__ == '__main__':
    import sqlite3, json, base64, win32crypt
    from Crypto.Cipher import AES

    src = os.path.join(os.environ['LOCALAPPDATA'], 'Google', 'Chrome', 'User Data', 'Default', 'Network', 'Cookies')
    dst = os.path.join(tempfile.gettempdir(), 'chrome_cookies_copy.db')
    
    copy_locked_file(src, dst)
    
    # Get decryption key
    local_state_path = os.path.join(os.environ['LOCALAPPDATA'], 'Google', 'Chrome', 'User Data', 'Local State')
    with open(local_state_path) as f:
        local_state = json.load(f)
    encrypted_key = base64.b64decode(local_state['os_crypt']['encrypted_key'])[5:]
    decryption_key = win32crypt.CryptUnprotectData(encrypted_key, None, None, None, 0)[1]
    
    conn = sqlite3.connect(dst)
    cur = conn.cursor()
    
    for host_filter in ['railway', 'github.com']:
        print(f"\n=== {host_filter} cookies ===")
        cur.execute("SELECT host_key, name, encrypted_value FROM cookies WHERE host_key LIKE ? ORDER BY creation_utc DESC", (f'%{host_filter}%',))
        rows = cur.fetchall()
        print(f"Found {len(rows)} rows")
        for host_key, name, encrypted_value in rows:
            try:
                if encrypted_value[:3] == b'v10':
                    nonce = encrypted_value[3:15]
                    ciphertext = encrypted_value[15:-16]
                    tag = encrypted_value[-16:]
                    cipher = AES.new(decryption_key, AES.MODE_GCM, nonce=nonce)
                    value = cipher.decrypt_and_verify(ciphertext, tag).decode('utf-8')
                    print(f"  {name}={value[:60]}")
                else:
                    print(f"  {name}=<legacy encrypted>")
            except Exception as e:
                print(f"  {name}=<decrypt failed: {e}>")
    
    conn.close()
    os.unlink(dst)
