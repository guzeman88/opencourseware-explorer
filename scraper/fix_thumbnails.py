"""
fix_thumbnails.py
-----------------
Replaces Unsplash placeholder thumbnails on courses that have has_video_lectures=true.

Strategy:
  1. For courses whose source_url is already a YouTube playlist URL → extract playlist ID directly.
  2. For all others → search YouTube for "{title} {university} full course lectures"
     and take the thumbnail from the top playlist or video result.

Updates both thumbnail_url and youtube_playlist_id (when a playlist is found).
"""

import os, re, time, urllib.request
import psycopg2
import yt_dlp

DB = os.environ.get("DATABASE_URL") or exit("ERROR: DATABASE_URL env var is required")

# University → YouTube channel handle used for scoped searches.
# This narrows results so we get the right course, not a random video.
CHANNEL_MAP = {
    "UC Berkeley":                  "@UCBerkeleyWebcast",
    "University of California, Berkeley": "@UCBerkeleyWebcast",
    "MIT OpenCourseWare":           "@mitocw",
    "Stanford University":          "@stanfordonline",
    "Yale University":              "@yalecourses",
    "Harvard University":           "@HarvardUniversity",
    "Khan Academy":                 "@khanacademy",
    "Carnegie Mellon University":   "@CarnegieMellonUniversity",
    "Princeton University":         "@PrincetonUniversity",
    "3Blue1Brown":                  "@3blue1brown",
    "NPTEL — National Programme on Technology Enhanced Learning": "@iit",
    "University of Cambridge":      "@Cambridge",
    "University of Oxford":         "@Oxford",
    "Simons Institute for the Theory of Computing": "@SimonsInstituteTCS",
}


def playlist_id_from_url(url: str) -> str | None:
    m = re.search(r"list=([A-Za-z0-9_-]+)", url or "")
    return m.group(1) if m else None


def yt_thumbnail_for_playlist(playlist_id: str) -> tuple[str, str] | None:
    """Return (playlist_id, thumbnail_url) for the first video of the playlist."""
    url = f"https://www.youtube.com/playlist?list={playlist_id}"
    opts = {
        "quiet": True,
        "no_warnings": True,
        "extract_flat": "in_playlist",
        "playlist_items": "1",
    }
    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=False)
            entries = info.get("entries") or []
            if entries:
                vid_id = entries[0].get("id") or entries[0].get("url", "").split("?v=")[-1]
                if vid_id:
                    thumb = f"https://i.ytimg.com/vi/{vid_id}/hqdefault.jpg"
                    return playlist_id, thumb
    except Exception as e:
        print(f"    yt-dlp error for playlist {playlist_id}: {e}")
    return None


def yt_search_course(title: str, uni_name: str | None) -> tuple[str | None, str] | None:
    """Search YouTube for the course, return (playlist_id_or_None, thumbnail_url)."""
    channel = CHANNEL_MAP.get(uni_name or "", "")
    # Build a targeted query
    query = f"{title} {uni_name or ''} full course lectures"
    search_url = f"ytsearch5:{query}"

    opts = {
        "quiet": True,
        "no_warnings": True,
        "extract_flat": True,
    }
    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            results = ydl.extract_info(search_url, download=False)
            entries = results.get("entries") or []
            for entry in entries:
                # Prefer playlist results
                url_str = entry.get("url") or entry.get("id") or ""
                if "list=" in url_str or entry.get("ie_key") in ("YoutubePlaylist",):
                    pid = playlist_id_from_url(url_str)
                    if pid:
                        res = yt_thumbnail_for_playlist(pid)
                        if res:
                            return res
            # Fall back to best video result
            for entry in entries:
                vid_id = entry.get("id")
                if vid_id and not vid_id.startswith("PL"):
                    thumb = f"https://i.ytimg.com/vi/{vid_id}/hqdefault.jpg"
                    return None, thumb
    except Exception as e:
        print(f"    yt-dlp search error for '{title}': {e}")
    return None


def main():
    conn = psycopg2.connect(DB)
    cur = conn.cursor()

    cur.execute("""
        SELECT c.id, c.title, c.source_url, u.name
        FROM courses c
        LEFT JOIN universities u ON u.id = c.university_id
        WHERE c.thumbnail_url LIKE '%unsplash%'
          AND c.has_video_lectures = true
        ORDER BY u.name, c.title
    """)
    courses = cur.fetchall()
    print(f"Found {len(courses)} courses with Unsplash placeholders to fix\n")

    fixed = 0
    failed = 0

    for course_id, title, source_url, uni_name in courses:
        print(f"[{fixed+failed+1}/{len(courses)}] {title[:50]} ({uni_name})")

        result = None

        # Step 1: Direct playlist URL in source_url
        pid = playlist_id_from_url(source_url)
        if pid:
            print(f"  → Direct playlist from source_url: {pid}")
            result = yt_thumbnail_for_playlist(pid)
        
        # Step 2: Search YouTube
        if not result:
            print(f"  → Searching YouTube...")
            result = yt_search_course(title, uni_name)

        if result:
            new_pid, new_thumb = result
            print(f"  ✓ thumb={new_thumb[:70]}")
            
            # Verify the thumbnail URL is reachable
            try:
                req = urllib.request.Request(new_thumb, headers={"User-Agent": "Mozilla/5.0"})
                urllib.request.urlopen(req, timeout=5)
            except Exception:
                # Try mqdefault as fallback
                if "/hqdefault" in new_thumb:
                    new_thumb = new_thumb.replace("/hqdefault", "/mqdefault")

            update_args = [new_thumb]
            sql = "UPDATE courses SET thumbnail_url = %s"
            if new_pid:
                sql += ", youtube_playlist_id = %s"
                update_args.append(new_pid)
            sql += " WHERE id = %s"
            update_args.append(course_id)
            cur.execute(sql, update_args)
            conn.commit()
            fixed += 1
        else:
            print(f"  ✗ Could not find thumbnail")
            failed += 1

        # Be polite to YouTube
        time.sleep(1.5)

    print(f"\nDone: {fixed} fixed, {failed} failed")
    conn.close()


if __name__ == "__main__":
    main()
