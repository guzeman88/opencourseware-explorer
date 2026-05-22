"""Find railway.com and github.com cookies from Firefox (unencrypted) and all Chrome profiles."""
import os, json, base64, sqlite3, shutil, tempfile
from pathlib import Path

def get_firefox_cookies(host_filter):
    ff_base = Path(os.environ['APPDATA']) / 'Mozilla/Firefox/Profiles'
    if not ff_base.exists():
        return {}
    
    results = {}
    for profile in ff_base.iterdir():
        cookie_path = profile / 'cookies.sqlite'
        if not cookie_path.exists():
            continue
        
        tmp = tempfile.mktemp(suffix='.db')
        shutil.copy2(str(cookie_path), tmp)
        
        try:
            conn = sqlite3.connect(tmp)
            cur = conn.cursor()
            cur.execute("""
                SELECT host, name, value FROM moz_cookies
                WHERE host LIKE ? ORDER BY lastAccessed DESC
            """, (f'%{host_filter}%',))
            for host, name, value in cur.fetchall():
                results[name] = value
            conn.close()
        except Exception as e:
            pass
        finally:
            try: os.unlink(tmp)
            except: pass
    
    return results

def get_chrome_cookies_from_path(browser_base, host_filter):
    import win32crypt
    from Crypto.Cipher import AES

    local_state_path = browser_base / 'Local State'
    if not local_state_path.exists():
        return {}
    
    with open(local_state_path) as f:
        local_state = json.load(f)
    
    encrypted_key = base64.b64decode(local_state['os_crypt']['encrypted_key'])
    encrypted_key = encrypted_key[5:]  # Remove DPAPI prefix
    decryption_key = win32crypt.CryptUnprotectData(encrypted_key, None, None, None, 0)[1]

    all_cookies = {}
    for profile_dir in ['Default', 'Profile', 'Profile 1', 'Profile 2', 'Profile 3']:
        cookie_path = browser_base / profile_dir / 'Network/Cookies'
        if not cookie_path.exists():
            continue
        
        tmp = tempfile.mktemp(suffix='.db')
        shutil.copy2(str(cookie_path), tmp)
        
        try:
            conn = sqlite3.connect(tmp)
            cur = conn.cursor()
            cur.execute("""
                SELECT host_key, name, encrypted_value FROM cookies
                WHERE host_key LIKE ? ORDER BY creation_utc DESC
            """, (f'%{host_filter}%',))
            
            for host_key, name, encrypted_value in cur.fetchall():
                try:
                    if encrypted_value[:3] == b'v10':
                        nonce = encrypted_value[3:3+12]
                        ciphertext = encrypted_value[3+12:-16]
                        tag = encrypted_value[-16:]
                        cipher = AES.new(decryption_key, AES.MODE_GCM, nonce=nonce)
                        value = cipher.decrypt_and_verify(ciphertext, tag).decode('utf-8')
                    else:
                        value = win32crypt.CryptUnprotectData(encrypted_value, None, None, None, 0)[1].decode('utf-8')
                    all_cookies[name] = value
                except Exception:
                    pass
            conn.close()
        except Exception as e:
            pass
        finally:
            try: os.unlink(tmp)
            except: pass
    
    return all_cookies

if __name__ == '__main__':
    print("=== Firefox: Railway.com cookies ===")
    rc = get_firefox_cookies('railway')
    for k, v in rc.items():
        print(f"  {k}={v[:80]}")
    
    print("\n=== Firefox: GitHub.com cookies ===")
    gc = get_firefox_cookies('github.com')
    important = ['user_session', '__Host-user_session_same_site', 'logged_in', 'dotcom_user', '_gh_sess']
    for k, v in gc.items():
        if k in important or 'session' in k.lower() or 'user' in k.lower():
            print(f"  {k}={v[:80]}")
    
    print("\n=== Chrome: Railway.com cookies ===")
    chrome_base = Path(os.environ['LOCALAPPDATA']) / 'Google/Chrome/User Data'
    rc = get_chrome_cookies_from_path(chrome_base, 'railway')
    for k, v in rc.items():
        print(f"  {k}={v[:80]}")
    
    print("\n=== Chrome: GitHub.com cookies ===")
    gc = get_chrome_cookies_from_path(chrome_base, 'github.com')
    for k, v in gc.items():
        if k in important or 'session' in k.lower() or 'user' in k.lower():
            print(f"  {k}={v[:80]}")
