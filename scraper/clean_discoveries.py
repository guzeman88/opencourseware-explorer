"""
Clean course code discoveries: dedup, derive titles, filter non-English,
validate college-level courses, output clean JSON + review HTML.

Steps:
1. Dedup courses across channels (keep most videos)
2. Derive proper course title from search query + best playlist title
3. Filter non-English titles
4. Validate: must look like an actual college course
"""
import json, os, re, html as html_mod
from collections import defaultdict

DISCOVERIES_PATH = os.path.join(
    os.path.dirname(__file__), "..", "course_code_discoveries.json"
)
OUT_JSON = os.path.join(
    os.path.dirname(__file__), "..", "course_code_discoveries_clean.json"
)
OUT_HTML = os.path.join(
    os.path.dirname(__file__), "..", "course_code_review_clean.html"
)

with open(DISCOVERIES_PATH, encoding="utf-8") as f:
    raw = json.load(f)

# ═══════════════════════════════════════════════════════════════════════════
# 1. Dedup: group same course across channels, keep most videos
# ═══════════════════════════════════════════════════════════════════════════

def extract_course_code(query):
    """Extract course code from search query like '\"6.001\" full course'."""
    m = re.search(r'"([^"]+)"', query)
    if m:
        return m.group(1)
    # Also try without quotes: "MIT 18.01 lecture" -> "18.01"
    m = re.search(r'([A-Z]+\s*\d+[A-Za-z]*)', query)
    if m:
        return m.group(1)
    return query

def title_similarity(t1, t2):
    """Simple similarity: how many words overlap."""
    w1 = set(re.sub(r'[^a-z0-9]', ' ', t1.lower()).split())
    w2 = set(re.sub(r'[^a-z0-9]', ' ', t2.lower()).split())
    if not w1 or not w2:
        return 0
    return len(w1 & w2) / min(len(w1), len(w2))

def course_title_score(title, code, university):
    """Score how well a playlist title matches a course.
    Higher = better title for the course."""
    score = 0
    t = title.lower()
    # Prefer titles that contain the university name
    if university.lower() in t:
        score += 10
    # Prefer titles that contain the course code
    code_clean = code.replace(" ", "").lower()
    if code_clean in t.replace(" ", ""):
        score += 20
    # Prefer titles that look like proper course titles (not "My videos", "Lol", etc.)
    if len(title) > 15:
        score += 5
    # Penalize obviously bad titles
    bad_words = ["my videos", "lol", "funny", "misc", "important", "gregooooor"]
    if any(b in t for b in bad_words):
        score -= 30
    # Prefer titles with course indicators
    good_words = ["lecture", "course", "introduction", "university", "college", "professor"]
    if any(g in t for g in good_words):
        score += 5
    return score

# Group by (university, course_code)
groups = defaultdict(list)
all_items = []
for school, items in raw.items():
    for item in items:
        code = extract_course_code(item.get("search_query", ""))
        key = (item.get("university", ""), code)
        groups[key].append(item)
        all_items.append(item)

print(f"Total raw items: {len(all_items)}")
print(f"Unique (school, code) groups: {len(groups)}")

# For each group, pick the best playlist title and the entry with most videos
deduped = []
for (uni, code), items in groups.items():
    # Find the entry with most videos
    best_entry = max(items, key=lambda x: x.get("video_count", 0))

    # Find the best title among all entries
    best_title_entry = max(items, key=lambda x: course_title_score(
        x.get("title", ""), code, uni
    ))

    # Use the best title, but from the entry with most videos
    combined = dict(best_entry)
    combined["course_code"] = code
    # If the best-title entry has a significantly better title, use it
    if course_title_score(best_title_entry["title"], code, uni) > course_title_score(best_entry["title"], code, uni) + 5:
        combined["display_title"] = best_title_entry["title"]
    else:
        combined["display_title"] = best_entry["title"]
    combined["duplicate_count"] = len(items)
    combined["all_channels"] = list(set(i.get("channel", "") for i in items))
    combined["max_videos"] = max(i.get("video_count", 0) for i in items)
    combined["total_videos_in_group"] = sum(i.get("video_count", 0) for i in items)
    deduped.append(combined)

print(f"After dedup: {len(deduped)}")

# ═══════════════════════════════════════════════════════════════════════════
# 2. Filter non-English titles
# ═══════════════════════════════════════════════════════════════════════════

NON_ENGLISH_RE = re.compile(
    r'[Ѐ-ԯⷠ-ⷿꙀ-ꚟͰ-Ͽ'
    r'぀-ヿ㐀-鿿가-힯'
    r'؀-ۿऀ-ॿ฀-๿]'
)

def is_english(title):
    return not NON_ENGLISH_RE.search(title)

before_noneng = len(deduped)
deduped = [d for d in deduped if is_english(d.get("display_title", ""))]
print(f"After non-English filter: {len(deduped)} (removed {before_noneng - len(deduped)})")

# ═══════════════════════════════════════════════════════════════════════════
# 3. Validate college-level courses
# ═══════════════════════════════════════════════════════════════════════════

COLLEGE_INDICATORS = [
    "lecture", "course", "university", "college", "professor",
    "semester", "syllabus", "introduction to", "intro to",
    "department", "school of", "institute", "faculty",
    "undergraduate", "graduate", "MIT", "Stanford", "Harvard",
    "Berkeley", "Yale", "Princeton", "CMU", "Caltech",
    "Oxford", "Cambridge", "Imperial", "UCL", "ETH", "EPFL",
]

NON_COLLEGE_TITLES = [
    # Playlist titles that are clearly not college courses
    "my videos", "lol", "funny", "misc ", "important ",
    "gregooooor", "htdp", "procrastination", "videos that get",
    "complete rationalized grade", "grade 4 english",
    "class 8 math", "class 11th", "hsc cs-1",
    "bsc 1st semester", "igcse", "gcse", "o-level", "a level buddy",
    "k-8", "cna state exam", "tsi practice test",
    "national pesticide", "cpr ", "first aid",
    "lead auditor", "comptia", "security plus",
    "intermediate accounting", "c++ full course", "c programming for beginners",
    "python apna college", "web development tutorials for beginners in hindi",
    "20 hour", "full course |", "full course 202",  # low quality online course mills
]

def is_college_course(item):
    title = item.get("display_title", "").lower()
    channel = item.get("channel", "").lower()
    search = item.get("search_query", "").lower()
    code = item.get("course_code", "")
    uni = item.get("university", "").lower()

    score = 0

    # Course code is strong signal
    if code and len(code) > 2:
        score += 3

    # University in title or search is strong
    if uni in title:
        score += 4

    # Has college indicators in title
    for ind in COLLEGE_INDICATORS:
        if ind.lower() in title:
            score += 2
            break

    # Check for non-college patterns
    for bad in NON_COLLEGE_TITLES:
        if bad in title:
            score -= 5
            break

    # Title should be reasonably substantive
    if len(title) < 10:
        score -= 3

    # Search query mentions "full course" or "lecture" (we were looking for courses)
    if "full course" in search or "lecture" in search:
        score += 2

    # If the course code is numeric-only and short (like just "1" or "2"), likely noise
    if re.match(r'^\d{1,2}$', code.strip()):
        score -= 4

    # Channel with "university" or "college" is a good sign
    if "university" in channel or "college" in channel:
        score += 1

    return score >= 4  # threshold for being a college course

before_valid = len(deduped)
validated = []
rejected = []
for d in deduped:
    if is_college_course(d):
        validated.append(d)
    else:
        rejected.append(d)

print(f"After college validation: {len(validated)} kept, {len(rejected)} rejected")

# ═══════════════════════════════════════════════════════════════════════════
# 4. Derive proper display title from course code + best info
# ═══════════════════════════════════════════════════════════════════════════

for d in validated:
    display = d.get("display_title", "")
    code = d.get("course_code", "")
    uni = d.get("university", "")

    # If display title is weak but we have a course code, build a title
    if course_title_score(display, code, uni) < 5 and code:
        # Try to extract a meaningful phrase from any of the titles
        all_titles = [d.get("title", "")] + [display]
        best = max(all_titles, key=lambda t: course_title_score(t, code, uni))
        if course_title_score(best, code, uni) > 0:
            d["display_title"] = best
        else:
            d["display_title"] = f"{uni} {code} — Course Lectures"

    # Clean up display title
    d["display_title"] = d["display_title"].strip()

# ═══════════════════════════════════════════════════════════════════════════
# Save clean JSON
# ═══════════════════════════════════════════════════════════════════════════

# Group by university for output
clean_by_uni = defaultdict(list)
for d in validated:
    clean_by_uni[d["university"]].append(d)

with open(OUT_JSON, "w", encoding="utf-8") as f:
    json.dump(dict(clean_by_uni), f, indent=2, ensure_ascii=False)

# Also save rejected for review
rejected_by_uni = defaultdict(list)
for d in rejected:
    rejected_by_uni[d["university"]].append(d)

rejected_path = os.path.join(
    os.path.dirname(__file__), "..", "course_code_discoveries_rejected.json"
)
with open(rejected_path, "w", encoding="utf-8") as f:
    json.dump(dict(rejected_by_uni), f, indent=2, ensure_ascii=False)

# ═══════════════════════════════════════════════════════════════════════════
# Generate clean HTML
# ═══════════════════════════════════════════════════════════════════════════

def write_html(items_by_uni, html_path, title_label):
    rows = ""
    total = 0

    # Sort universities by count
    sorted_unis = sorted(items_by_uni.items(), key=lambda x: -len(x[1]))

    for uni, items in sorted_unis:
        # Sort items within university by video count desc
        items_sorted = sorted(items, key=lambda x: -x.get("video_count", 0))
        for d in items_sorted:
            total += 1
            thumb_html = ""
            if d.get("thumbnail"):
                thumb_html = f'<img src="{html_mod.escape(d["thumbnail"])}" loading="lazy">'

            # Show duplicate info if applicable
            dup_info = ""
            if d.get("duplicate_count", 1) > 1:
                dup_info = f'<span class="dup">x{d["duplicate_count"]} channels</span>'

            rows += f"""<tr>
                <td class="thumb">{thumb_html}</td>
                <td class="title"><a href="{html_mod.escape(d.get('url',''))}" target="_blank">{html_mod.escape(d.get('display_title','')[:100])}</a>{dup_info}</td>
                <td class="chan">{html_mod.escape(d.get('channel','')[:50])}</td>
                <td class="school">{html_mod.escape(uni)}</td>
                <td class="code">{html_mod.escape(d.get('course_code',''))}</td>
                <td class="n">{d.get('video_count','?')}</td>
            </tr>"""

    html = f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<title>Course Code Discoveries - {title_label} ({total})</title>
<style>
*{{box-sizing:border-box;margin:0;padding:0}}
body{{background:#0d1117;color:#c9d1d9;font-family:system-ui;padding:2rem}}
h1{{font-size:1.6rem;font-weight:700;color:#f0f6fc;margin-bottom:.25rem}}
.summary{{color:#8b949e;margin-bottom:2rem}}.green{{color:#3fb950}}.yellow{{color:#d2991d}}
table{{width:100%;border-collapse:collapse;font-size:13px}}
th{{text-align:left;padding:10px 12px;border-bottom:2px solid #30363d;color:#8b949e;font-size:11px;font-weight:600;text-transform:uppercase;background:#161b22;position:sticky;top:0;z-index:1}}
td{{padding:10px 12px;border-bottom:1px solid #21262d;vertical-align:middle}}
tr:hover td{{background:#1c2128}}
.thumb{{width:130px}}.thumb img{{width:120px;height:68px;object-fit:cover;border-radius:6px;border:1px solid #30363d}}
.title{{max-width:480px}}.title a{{color:#58a6ff;text-decoration:none;font-weight:500}}.title a:hover{{text-decoration:underline}}
.chan{{color:#8b949e;font-size:12px;max-width:180px}}
.school{{color:#8b949e;font-size:12px;max-width:150px}}
.code{{color:#d2a8ff;font-size:12px;font-weight:600;max-width:100px}}
.n{{text-align:center;font-weight:600;color:#f0f6fc}}
.dup{{display:inline-block;background:#1f6feb33;color:#58a6ff;padding:1px 6px;border-radius:3px;font-size:10px;font-weight:700;margin-left:6px;white-space:nowrap}}
</style></head><body>
<h1>Course Code Discoveries — {title_label}</h1>
<p class="summary">
<b class="green">{total} clean courses</b> across {len(items_by_uni)} schools &middot;
deduped, English-only, college-validated &middot;
sorted by video count within school
</p>
<table><thead><tr>
<th class="thumb">Thumb</th><th>Title</th><th>Channel</th><th>School</th><th>Code</th><th class="n">Videos</th>
</tr></thead><tbody>{rows}</tbody></table>
</body></html>"""

    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html)
    return total

clean_total = write_html(dict(clean_by_uni), OUT_HTML, "Clean")

# Also generate rejected HTML for comparison
rej_html = os.path.join(
    os.path.dirname(__file__), "..", "course_code_review_rejected.html"
)
rej_total = write_html(dict(rejected_by_uni), rej_html, "Rejected")

print()
print(f"Clean HTML: {OUT_HTML} ({clean_total} courses)")
print(f"Rejected HTML: {rej_html} ({rej_total} courses)")
print(f"Clean JSON: {OUT_JSON}")

# Show top schools after cleaning
print()
print("Top schools after cleaning:")
sorted_unis = sorted(clean_by_uni.items(), key=lambda x: -len(x[1]))
for uni, items in sorted_unis[:15]:
    print(f"  {uni}: {len(items)}")
