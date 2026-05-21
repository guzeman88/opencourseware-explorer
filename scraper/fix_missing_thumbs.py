"""Debug why some courses still have NULL thumbnails, then fix them directly."""
import psycopg2
import re
from db_utils import get_connection

SUBJECT_MAP = [
    ("machine learning",      "https://images.unsplash.com/photo-1677442135703-1787eea5ce01?w=640&q=80"),
    ("artificial intelligence","https://images.unsplash.com/photo-1677442135703-1787eea5ce01?w=640&q=80"),
    ("deep learning",         "https://images.unsplash.com/photo-1677442135703-1787eea5ce01?w=640&q=80"),
    ("data science",          "https://images.unsplash.com/photo-1551288049-bebda4e38f71?w=640&q=80"),
    ("computer science",      "https://images.unsplash.com/photo-1517694712202-14dd9538aa97?w=640&q=80"),
    ("software",              "https://images.unsplash.com/photo-1550745165-9bc0b252726f?w=640&q=80"),
    ("programming",           "https://images.unsplash.com/photo-1550745165-9bc0b252726f?w=640&q=80"),
    ("algorithm",             "https://images.unsplash.com/photo-1517694712202-14dd9538aa97?w=640&q=80"),
    ("web development",       "https://images.unsplash.com/photo-1547658719-da2b51169166?w=640&q=80"),
    ("linear algebra",        "https://images.unsplash.com/photo-1509228468518-180dd4864904?w=640&q=80"),
    ("calculus",              "https://images.unsplash.com/photo-1509228468518-180dd4864904?w=640&q=80"),
    ("mathematics",           "https://images.unsplash.com/photo-1509228468518-180dd4864904?w=640&q=80"),
    ("algebra",               "https://images.unsplash.com/photo-1509228468518-180dd4864904?w=640&q=80"),
    ("statistics",            "https://images.unsplash.com/photo-1460925895917-afdab827c52f?w=640&q=80"),
    ("probability",           "https://images.unsplash.com/photo-1460925895917-afdab827c52f?w=640&q=80"),
    ("quantum",               "https://images.unsplash.com/photo-1635070041078-e363dbe005cb?w=640&q=80"),
    ("thermodynamics",        "https://images.unsplash.com/photo-1635070041078-e363dbe005cb?w=640&q=80"),
    ("astrophysics",          "https://images.unsplash.com/photo-1419242902214-272b3f66ee7a?w=640&q=80"),
    ("astronomy",             "https://images.unsplash.com/photo-1419242902214-272b3f66ee7a?w=640&q=80"),
    ("physics",               "https://images.unsplash.com/photo-1635070041078-e363dbe005cb?w=640&q=80"),
    ("organic chemistry",     "https://images.unsplash.com/photo-1532187863486-abf9dbad1b69?w=640&q=80"),
    ("chemistry",             "https://images.unsplash.com/photo-1532187863486-abf9dbad1b69?w=640&q=80"),
    ("genetics",              "https://images.unsplash.com/photo-1530026405186-ed1f139313f0?w=640&q=80"),
    ("biology",               "https://images.unsplash.com/photo-1530026405186-ed1f139313f0?w=640&q=80"),
    ("ecology",               "https://images.unsplash.com/photo-1473448912268-2022ce9509d8?w=640&q=80"),
    ("neuroscience",          "https://images.unsplash.com/photo-1559757148-5c350d0d3c56?w=640&q=80"),
    ("epidemiology",          "https://images.unsplash.com/photo-1576091160399-112ba8d25d1d?w=640&q=80"),
    ("public health",         "https://images.unsplash.com/photo-1576091160399-112ba8d25d1d?w=640&q=80"),
    ("medicine",              "https://images.unsplash.com/photo-1576091160399-112ba8d25d1d?w=640&q=80"),
    ("medical",               "https://images.unsplash.com/photo-1576091160399-112ba8d25d1d?w=640&q=80"),
    ("nursing",               "https://images.unsplash.com/photo-1576091160399-112ba8d25d1d?w=640&q=80"),
    ("nutrition",             "https://images.unsplash.com/photo-1490818387583-1baba5e638af?w=640&q=80"),
    ("food",                  "https://images.unsplash.com/photo-1490818387583-1baba5e638af?w=640&q=80"),
    ("chemical engineering",  "https://images.unsplash.com/photo-1532187863486-abf9dbad1b69?w=640&q=80"),
    ("electrical engineering","https://images.unsplash.com/photo-1518770660439-4636190af475?w=640&q=80"),
    ("mechanical engineering","https://images.unsplash.com/photo-1581091226825-a6a2a5aee158?w=640&q=80"),
    ("civil engineering",     "https://images.unsplash.com/photo-1486325212027-8081e485255e?w=640&q=80"),
    ("engineering",           "https://images.unsplash.com/photo-1581091226825-a6a2a5aee158?w=640&q=80"),
    ("materials",             "https://images.unsplash.com/photo-1581091226825-a6a2a5aee158?w=640&q=80"),
    ("architecture",          "https://images.unsplash.com/photo-1486325212027-8081e485255e?w=640&q=80"),
    ("entrepreneurship",      "https://images.unsplash.com/photo-1454165804606-c3d57bc86b40?w=640&q=80"),
    ("management",            "https://images.unsplash.com/photo-1454165804606-c3d57bc86b40?w=640&q=80"),
    ("marketing",             "https://images.unsplash.com/photo-1454165804606-c3d57bc86b40?w=640&q=80"),
    ("business",              "https://images.unsplash.com/photo-1454165804606-c3d57bc86b40?w=640&q=80"),
    ("finance",               "https://images.unsplash.com/photo-1611974789855-9c2a0a7236a3?w=640&q=80"),
    ("economics",             "https://images.unsplash.com/photo-1611974789855-9c2a0a7236a3?w=640&q=80"),
    ("psychology",            "https://images.unsplash.com/photo-1576091160550-2173dba999ef?w=640&q=80"),
    ("philosophy",            "https://images.unsplash.com/photo-1481627834876-b7833e8f5570?w=640&q=80"),
    ("ethics",                "https://images.unsplash.com/photo-1481627834876-b7833e8f5570?w=640&q=80"),
    ("history",               "https://images.unsplash.com/photo-1461360370896-22624d12aa1?w=640&q=80"),
    ("literature",            "https://images.unsplash.com/photo-1507842217343-583bb7270b66?w=640&q=80"),
    ("writing",               "https://images.unsplash.com/photo-1507842217343-583bb7270b66?w=640&q=80"),
    ("linguistics",           "https://images.unsplash.com/photo-1486312338219-ce68d2c6f44d?w=640&q=80"),
    ("language",              "https://images.unsplash.com/photo-1486312338219-ce68d2c6f44d?w=640&q=80"),
    ("music",                 "https://images.unsplash.com/photo-1507838153414-b4b713384a76?w=640&q=80"),
    ("design",                "https://images.unsplash.com/photo-1559028006-448665bd7c7f?w=640&q=80"),
    ("art",                   "https://images.unsplash.com/photo-1513364776144-60967b0f800f?w=640&q=80"),
    ("climate",               "https://images.unsplash.com/photo-1473448912268-2022ce9509d8?w=640&q=80"),
    ("environment",           "https://images.unsplash.com/photo-1473448912268-2022ce9509d8?w=640&q=80"),
    ("legal",                 "https://images.unsplash.com/photo-1589829545856-d10d557cf95f?w=640&q=80"),
    ("law",                   "https://images.unsplash.com/photo-1589829545856-d10d557cf95f?w=640&q=80"),
    ("political",             "https://images.unsplash.com/photo-1529156069898-49953e39b3ac?w=640&q=80"),
    ("sociology",             "https://images.unsplash.com/photo-1529156069898-49953e39b3ac?w=640&q=80"),
    ("social",                "https://images.unsplash.com/photo-1529156069898-49953e39b3ac?w=640&q=80"),
    ("geography",             "https://images.unsplash.com/photo-1524661135-423995f22d0b?w=640&q=80"),
    ("hydraulics",            "https://images.unsplash.com/photo-1581091226825-a6a2a5aee158?w=640&q=80"),
    ("hydrology",             "https://images.unsplash.com/photo-1581091226825-a6a2a5aee158?w=640&q=80"),
    ("irrigation",            "https://images.unsplash.com/photo-1581091226825-a6a2a5aee158?w=640&q=80"),
    ("water",                 "https://images.unsplash.com/photo-1581091226825-a6a2a5aee158?w=640&q=80"),
    ("soil",                  "https://images.unsplash.com/photo-1473448912268-2022ce9509d8?w=640&q=80"),
    ("animal",                "https://images.unsplash.com/photo-1473448912268-2022ce9509d8?w=640&q=80"),
    ("astrobiology",          "https://images.unsplash.com/photo-1419242902214-272b3f66ee7a?w=640&q=80"),
    ("extraterrestrial",      "https://images.unsplash.com/photo-1419242902214-272b3f66ee7a?w=640&q=80"),
    ("disability",            "https://images.unsplash.com/photo-1529156069898-49953e39b3ac?w=640&q=80"),
]
DEFAULT_IMAGE = "https://images.unsplash.com/photo-1503676260728-1c00da094a0b?w=640&q=80"


def subject_image(title, desc=""):
    text = (title + " " + (desc or "")).lower()
    for kw, url in SUBJECT_MAP:
        if kw in text:
            return url
    return DEFAULT_IMAGE


conn = get_connection()
cur = conn.cursor()

cur.execute("SELECT id, title, description FROM courses WHERE thumbnail_url IS NULL ORDER BY title")
rows = cur.fetchall()
print(f"Still missing: {len(rows)}")

updated = 0
for cid, title, desc in rows:
    thumb = subject_image(title, desc or "")
    print(f"  [{cid}] {title[:50]:50s}  -> match: {thumb[:60]}")
    cur.execute("UPDATE courses SET thumbnail_url = %s WHERE id = %s", (thumb, cid))
    updated += 1

conn.commit()
print(f"\nCommitted {updated} updates.")
cur.close()
conn.close()
