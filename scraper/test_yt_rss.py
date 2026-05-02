"""Test YouTube RSS feed for playlist thumbnails."""
import re, requests

s = requests.Session()
s.headers.update({"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"})

print("=== YouTube RSS feed for playlists ===")
for pid in ["PL8dPuuaLjXtKZPLYPEGLHvPUiUcRe6n8h", "PLoROMvodv4rO0raveZzJDfBHMjCJ1wv51", "PLRe7s5JtDsYRPd3USSYQFIYMbPtEBbHsL", "PLZHQObOWTQDMsc_R5byN_zw_nJIDBBp25"]:
    try:
        r = s.get(f"https://www.youtube.com/feeds/videos.xml?playlist_id={pid}", timeout=12)
        print(f"  {pid[:30]}: status={r.status_code} len={len(r.text)}")
        if r.ok:
            # Extract first video ID or thumbnail from RSS
            m = re.search(r'<yt:videoId>([^<]+)</yt:videoId>', r.text)
            if m:
                vid_id = m.group(1)
                print(f"    First video ID: {vid_id}")
                print(f"    Thumb URL: https://i.ytimg.com/vi/{vid_id}/hqdefault.jpg")
            # Also check for media:thumbnail
            m2 = re.search(r'<media:thumbnail[^>]+url="([^"]+)"', r.text)
            if m2: print(f"    media:thumbnail: {m2.group(1)[:80]}")
            print(f"    First 300 chars: {r.text[:300]}")
    except Exception as e:
        print(f"  {pid}: error={e}")

print("\n=== Verify NPTEL youtube_id thumbnail works ===")
vid_ids = ["tA42nHmmEKw", "Z6f9ckEElsU"]
for vid in vid_ids:
    for size in ["maxresdefault", "hqdefault", "mqdefault"]:
        url = f"https://i.ytimg.com/vi/{vid}/{size}.jpg"
        try:
            r = s.head(url, timeout=8)
            print(f"  {vid}/{size}: status={r.status_code}")
            if r.ok: break
        except Exception as e:
            print(f"  {vid}/{size}: error={e}")
