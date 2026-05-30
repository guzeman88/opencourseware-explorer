import subprocess

handles = [
    ("berkeley", "https://www.youtube.com/@UCBerkeleyOfficial/playlists"),
    ("cmu", "https://www.youtube.com/@cmu/playlists"),
    ("oxford", "https://www.youtube.com/@universityofoxford/playlists"),
    ("glasgow", "https://www.youtube.com/@glauni/playlists"),
    ("umich", "https://www.youtube.com/@umich/playlists"),
    ("gatech", "https://www.youtube.com/@GeorgiaTech/playlists"),
    ("umelbourne", "https://www.youtube.com/@unimelb/playlists"),
    ("uwashington", "https://www.youtube.com/@UWashington/playlists"),
    ("ucsd", "https://www.youtube.com/@UCSD/playlists"),
    ("cambridge", "https://www.youtube.com/@cambridgeuniversity/playlists"),
]

for name, url in handles:
    r = subprocess.run(
        [".venv/Scripts/yt-dlp", "--flat-playlist", "--print", "id", "--playlist-end", "3", url],
        capture_output=True, text=True
    )
    ok = len(r.stdout.strip()) > 0
    err = r.stderr.strip().split("\n")[0][:80] if r.stderr else ""
    print(f"{name}: {'OK - got playlists' if ok else 'FAIL'} | {err}")
