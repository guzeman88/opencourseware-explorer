"""Extract railway.com and github.com cookies from Chrome to authenticate."""
import os, json, base64, sqlite3, shutil, tempfile
from pathlib import Path

def get_chrome_cookies(host_filter):
    import win32crypt
    from Crypto.Cipher import AES

    # Get encryption key
    # Try Edge first, then Chrome
    for browser_base in [
        Path(os.environ['LOCALAPPDATA']) / 'Microsoft/Edge/User Data',
        Path(os.environ['LOCALAPPDATA']) / 'Google/Chrome/User Data',
    ]:
        local_state_path = browser_base / 'Local State'
        cookie_path_candidate = browser_base / 'Default/Network/Cookies'
        if local_state_path.exists() and cookie_path_candidate.exists():
            break
    else:
        return {}

    local_state_path = browser_base / 'Local State'
    with open(local_state_path) as f:
        local_state = json.load(f)
    encrypted_key = base64.b64decode(local_state['os_crypt']['encrypted_key'])
    # Remove DPAPI prefix (first 5 bytes: DPAPI)
    encrypted_key = encrypted_key[5:]
    decryption_key = win32crypt.CryptUnprotectData(encrypted_key, None, None, None, 0)[1]

    # Copy cookie DB (browser locks it while open)
    cookie_path = browser_base / 'Default/Network/Cookies'
    tmp = tempfile.mktemp(suffix='.db')
    shutil.copy2(str(cookie_path), tmp)

    conn = sqlite3.connect(tmp)
    cur = conn.cursor()
    cur.execute("""
        SELECT host_key, name, encrypted_value, path, expires_utc, is_secure
        FROM cookies
        WHERE host_key LIKE ?
        ORDER BY creation_utc DESC
    """, (f'%{host_filter}%',))

    cookies = {}
    for host_key, name, encrypted_value, path, expires_utc, is_secure in cur.fetchall():
        try:
            # Chrome v80+ AES-256-GCM
            if encrypted_value[:3] == b'v10':
                nonce = encrypted_value[3:3+12]
                ciphertext = encrypted_value[3+12:-16]
                tag = encrypted_value[-16:]
                cipher = AES.new(decryption_key, AES.MODE_GCM, nonce=nonce)
                value = cipher.decrypt_and_verify(ciphertext, tag).decode('utf-8')
            else:
                value = win32crypt.CryptUnprotectData(encrypted_value, None, None, None, 0)[1].decode('utf-8')
            cookies[name] = value
        except Exception as e:
            pass

    conn.close()
    os.unlink(tmp)
    return cookies

if __name__ == '__main__':
    print("=== Railway.com cookies ===")
    rc = get_chrome_cookies('railway')
    for k, v in rc.items():
        print(f"  {k}: {v[:40]}{'...' if len(v)>40 else ''}")

    print("\n=== GitHub.com cookies ===")
    gc = get_chrome_cookies('github.com')
    # Only print session-related ones
    important = ['user_session', '__Host-user_session_same_site', 'logged_in', 'dotcom_user']
    for k, v in gc.items():
        if k in important or 'session' in k.lower():
            print(f"  {k}: {v[:60]}{'...' if len(v)>60 else ''}")
