"""
Search YouTube for university course playlists using course code scraping
(no API key required). Uses the same approach as discover_missing_courses.py:
HTML scraping to find playlist IDs, yt-dlp for playlist details.

Strategy: For each university, generate search queries from known course
code patterns (e.g., "MIT 18.01 lecture", "Stanford CS229 full course"),
scrape YouTube search results, and collect playlists not already in our DB.

Usage:
    python search_by_course_code.py --mode sample --school "MIT"
    python search_by_course_code.py --mode full --school "Stanford"
    python search_by_course_code.py --mode sample  (all schools)
"""

import json, os, re, sys, time, urllib.request, urllib.parse, subprocess
from collections import OrderedDict
from dotenv import load_dotenv
import psycopg2

load_dotenv(os.path.join(os.path.dirname(__file__), "..", "backend", ".env"))

DB_URL = (os.environ.get("DATABASE_URL", "")
          .replace("postgresql+asyncpg://", "postgresql://"))

# ═══════════════════════════════════════════════════════════════════════════
# Course code patterns per university
# ═══════════════════════════════════════════════════════════════════════════

UNIVERSITY_PATTERNS = OrderedDict()

def _add(short, full_name, depts, numbers, extra_queries=None):
    UNIVERSITY_PATTERNS[short] = {
        "name": full_name,
        "depts": depts,
        "numbers": numbers,
        "extra": extra_queries or [],
    }

# ── US Major ────────────────────────────────────────────────────────────
_add("MIT", "MIT", [
    "6.001", "6.002", "6.003", "6.004", "6.005", "6.006", "6.007",
    "6.01", "6.02", "6.03", "6.033", "6.034", "6.035", "6.036", "6.037",
    "6.041", "6.042", "6.045", "6.046", "6.047", "6.050",
    "18.01", "18.02", "18.03", "18.04", "18.05", "18.06",
    "18.100", "18.101", "18.102", "18.103", "18.104", "18.112",
    "18.200", "18.202", "18.204", "18.212", "18.300", "18.303",
    "18.400", "18.404", "18.600", "18.650", "18.700", "18.701",
    "8.01", "8.02", "8.03", "8.04", "8.05", "8.06", "8.07",
    "8.200", "8.231", "8.282", "8.300", "8.321", "8.322", "8.323",
    "5.111", "5.112", "5.12", "5.13", "5.301", "5.310", "5.60", "5.61",
    "5.111", "5.112", "5.12", "5.13", "5.301", "5.310",
    "7.01", "7.012", "7.013", "7.014", "7.016", "7.03", "7.05", "7.06",
    "7.20", "7.21", "7.22", "7.23", "7.24", "7.26", "7.27", "7.28",
    "7.29", "7.30", "7.31", "7.32", "7.33", "7.340",
    "9.00", "9.01", "9.03", "9.04", "9.10", "9.14", "9.40", "9.46",
    "14.01", "14.02", "14.03", "14.04", "14.05", "14.06", "14.12",
    "14.13", "14.15", "14.20", "14.26", "14.30", "14.381", "14.382",
    "14.385", "14.386", "14.387", "14.41", "14.44", "14.451",
    "15.053", "15.075", "15.279", "15.301", "15.401", "15.431",
    "15.501", "15.628", "15.812",
    "16.00", "16.01", "16.02", "16.06", "16.07", "16.09",
    "2.001", "2.002", "2.003", "2.004", "2.005", "2.006",
    "2.011", "2.016", "2.017", "2.019", "2.050", "2.080",
    "3.021", "3.022", "3.024", "3.032", "3.042", "3.044",
    "3.054", "3.091", "3.094",
    "22.01", "22.02", "22.05", "22.06", "22.071", "22.081",
    "24.09", "24.118", "24.200", "24.201", "24.213", "24.221",
    "24.222", "24.231", "24.241", "24.242", "24.251",
    "ESD.04", "ESD.05", "ESD.10", "ESD.30", "ESD.33", "ESD.34", "ESD.36",
    "MAS.110", "MAS.111", "MAS.131", "MAS.160", "MAS.450", "MAS.622",
    "MAS.712", "MAS.771", "MAS.863", "MAS.878", "MAS.961", "MAS.962",
    "RES.6-001", "RES.6-002", "RES.6-003", "RES.6-004", "RES.6-005",
    "RES.6-006", "RES.6-007", "RES.6-008", "RES.6-009", "RES.6-010",
    "RES.18-001", "RES.18-002", "RES.18-003", "RES.18-004", "RES.18-005",
    "RES.8-001", "RES.8-002", "RES.8-003", "RES.8-004",
    "RES.LL-001", "RES.LL-002", "21G.101", "21G.102", "21G.103",
    "21G.104", "21G.105", "21G.106", "21G.107", "21G.108", "21G.109",
    "21H.101", "21H.102", "21H.104", "21H.105", "21H.106", "21H.107",
    "21L.000", "21L.001", "21L.002", "21L.003", "21L.004", "21L.005",
    "21L.006", "21L.007", "21L.008", "21L.009", "21L.010", "21L.011",
    "21L.012", "21L.013", "21L.014", "21L.015",
    "CMS.100", "CMS.300", "CMS.301", "CMS.600", "CMS.601", "CMS.603",
    "CMS.608", "CMS.610", "CMS.611", "CMS.615", "CMS.621", "CMS.631",
    "STS.001", "STS.002", "STS.003", "STS.004", "STS.005", "STS.006",
    "STS.007", "STS.008", "STS.009", "STS.010", "STS.011", "STS.012",
], [""], extra_queries=[
    "MIT full course", "MIT OCW full course", "MIT lecture series",
    "MIT course playlist", "MIT OpenCourseWare",
])

_add("Stanford", "Stanford", [
    "CS 229", "CS 230", "CS 231N", "CS 224N", "CS 221", "CS 228",
    "CS 229M", "CS 234", "CS 236", "CS 238", "CS 242", "CS 243",
    "CS 246", "CS 248", "CS 255", "CS 261", "CS 265", "CS 273A",
    "CS 276", "CS 279", "CS 330", "CS 348",
    "EE 263", "EE 364A", "EE 364B", "EE 278", "EE 376A", "EE 376B",
    "MATH 104", "MATH 113", "MATH 115", "MATH 120", "MATH 171",
    "MATH 172", "MATH 173", "MATH 205",
    "PHYSICS 21", "PHYSICS 41", "PHYSICS 61", "PHYSICS 81",
    "PHYSICS 120", "PHYSICS 130", "PHYSICS 131", "PHYSICS 134",
    "PHYSICS 152", "PHYSICS 160", "PHYSICS 170", "PHYSICS 171",
    "STATS 200", "STATS 202", "STATS 203", "STATS 216", "STATS 217",
    "STATS 315A", "STATS 315B",
    "MS&E 111", "MS&E 211", "MS&E 221", "MS&E 226", "MS&E 232",
    "MS&E 252", "MS&E 271", "MS&E 310", "MS&E 311", "MS&E 317",
    "ECON 50", "ECON 102A", "ECON 102B", "ECON 136", "ECON 137",
    "ECON 155", "ECON 202", "ECON 203", "ECON 210", "ECON 211",
    "PSYCH 1", "PSYCH 30", "PSYCH 45", "PSYCH 50", "PSYCH 60",
    "PHIL 1", "PHIL 2", "PHIL 80", "PHIL 150", "PHIL 151",
    "ENGR 108", "ENGR 202", "CME 100", "CME 102", "CME 106", "CME 108",
], [""], extra_queries=[
    "Stanford full course", "Stanford lecture series",
    "Stanford online course", "Stanford University playlist",
]),

_add("Harvard", "Harvard", [
    "CS 50", "CS 51", "CS 61", "CS 121", "CS 124", "CS 181", "CS 182",
    "CS 221", "CS 222", "CS 224", "CS 226", "CS 229",
    "MATH 21A", "MATH 21B", "MATH 22A", "MATH 25", "MATH 55",
    "MATH 112", "MATH 113", "MATH 114", "MATH 121", "MATH 122",
    "MATH 130", "MATH 131", "MATH 132", "MATH 136", "MATH 137",
    "PHYSICS 15A", "PHYSICS 15B", "PHYSICS 15C", "PHYSICS 16",
    "PHYSICS 123", "PHYSICS 143A", "PHYSICS 143B",
    "PHYSICS 181", "PHYSICS 210", "PHYSICS 232",
    "CHEM 17", "CHEM 20", "CHEM 27", "CHEM 30", "CHEM 40",
    "ECON 10A", "ECON 10B", "ECON 1010A", "ECON 1010B",
    "ECON 1011A", "ECON 1011B", "ECON 1123", "ECON 1126",
    "STAT 110", "STAT 111", "STAT 139", "STAT 149", "STAT 171",
    "PSYCH 1", "PSYCH 15", "PSYCH 16", "PSYCH 18", "PSYCH 1900",
    "PHIL 3", "PHIL 6", "PHIL 8", "PHIL 34", "PHIL 129",
    "GOV 20", "GOV 30", "GOV 40", "HIST 1050", "HIST 1051",
    "ESE 1", "ESE 6", "ESE 101", "ESE 162", "ESE 168",
    "APMTH 21A", "APMTH 21B", "APMTH 105", "APMTH 106", "APMTH 107",
], [""], extra_queries=[
    "Harvard full course", "Harvard lecture series",
    "Harvard University course", "Harvard College lecture",
]),

_add("UC Berkeley", "UC Berkeley", [
    "CS 61A", "CS 61B", "CS 61C", "CS 70", "CS 161", "CS 162",
    "CS 164", "CS 168", "CS 170", "CS 172", "CS 176", "CS 182",
    "CS 186", "CS 188", "CS 189", "CS 191",
    "CS 267", "CS 270", "CS 271", "CS 276", "CS 280", "CS 281",
    "CS 285", "CS 287", "CS 288", "CS 289", "CS 294",
    "EE 16A", "EE 16B", "EE 20", "EE 120", "EE 122", "EE 123",
    "EE 126", "EE 127", "EE 130", "EE 140", "EE 142", "EE 143",
    "EE 221A", "EE 222", "EE 224A", "EE 225A", "EE 227A",
    "EE 229A", "EE 240A", "EE 240B", "EE 290",
    "MATH 1A", "MATH 1B", "MATH 53", "MATH 54", "MATH 55",
    "MATH 104", "MATH 110", "MATH 113", "MATH 114", "MATH 115",
    "MATH 118", "MATH 121A", "MATH 121B", "MATH 123", "MATH 125A",
    "MATH 126", "MATH 128A", "MATH 130", "MATH 135",
    "MATH 140", "MATH 142", "MATH 143", "MATH 151", "MATH 170",
    "MATH 185", "MATH 202A", "MATH 202B", "MATH 215A", "MATH 215B",
    "PHYSICS 7A", "PHYSICS 7B", "PHYSICS 7C", "PHYSICS 105",
    "PHYSICS 110A", "PHYSICS 110B", "PHYSICS 111", "PHYSICS 112",
    "PHYSICS 137A", "PHYSICS 137B", "PHYSICS 138", "PHYSICS 139",
    "PHYSICS 141A", "PHYSICS 141B", "PHYSICS 142", "PHYSICS 151",
    "PHYSICS 161", "PHYSICS 171", "PHYSICS 211", "PHYSICS 212",
    "PHYSICS 216", "PHYSICS 221A", "PHYSICS 221B",
    "CHEM 1A", "CHEM 1B", "CHEM 3A", "CHEM 3B", "CHEM 4A", "CHEM 4B",
    "CHEM 12A", "CHEM 12B", "CHEM 103", "CHEM 104A", "CHEM 104B",
    "CHEM 105", "CHEM 108", "CHEM 115", "CHEM 120A", "CHEM 120B",
    "CHEM 125", "CHEM 130A", "CHEM 130B", "CHEM 135", "CHEM 143",
    "BIO 1A", "BIO 1B", "MCB 100A", "MCB 100B", "MCB 102", "MCB 110",
    "STAT 20", "STAT 131A", "STAT 133", "STAT 134", "STAT 135",
    "STAT 150", "STAT 151A", "STAT 153", "STAT 154", "STAT 155",
    "STAT 156", "STAT 157", "STAT 158", "STAT 159", "STAT 200A",
    "STAT 201A", "STAT 205A", "STAT 210A", "STAT 215A", "STAT 215B",
    "ECON 1", "ECON 2", "ECON 100A", "ECON 100B", "ECON 101A",
    "ECON 101B", "ECON 119", "ECON 121", "ECON 136", "ECON 140",
    "ECON 141", "ECON 142", "ECON 152", "ECON 157", "ECON 201A",
    "ECON 201B", "ECON 202A", "ECON 202B", "ECON 208", "ECON 210A",
    "ECON 211", "ECON 219A", "ECON 219B",
    "DATA 8", "DATA 100", "DATA 102", "DATA 140",
], [""], extra_queries=[
    "Berkeley full course", "UC Berkeley lecture",
    "Berkeley course playlist", "Cal full course",
]),

_add("Carnegie Mellon", "Carnegie Mellon", [
    "15-112", "15-122", "15-150", "15-210", "15-213", "15-214",
    "15-251", "15-312", "15-317", "15-319", "15-381", "15-384",
    "15-385", "15-386", "15-388", "15-411", "15-414", "15-418",
    "15-440", "15-441", "15-445", "15-451", "15-455", "15-458",
    "15-462", "15-721", "15-780", "15-781", "15-883",
    "10-701", "10-702", "10-703", "10-704", "10-705", "10-707",
    "10-708", "10-715", "10-725", "10-805",
    "11-711", "11-731", "11-751", "11-755", "11-761", "11-785",
    "18-100", "18-202", "18-240", "18-290", "18-341", "18-349",
    "18-400", "18-447", "18-613", "18-623", "18-725",
    "21-241", "21-259", "21-260", "21-268", "21-301", "21-325",
    "21-355", "21-366", "21-369", "21-373", "21-476",
    "36-201", "36-217", "36-218", "36-225", "36-226", "36-309",
    "36-315", "36-350", "36-401", "36-402", "36-410", "36-461",
    "36-462", "36-700", "36-705", "36-755",
], [""], extra_queries=[
    "Carnegie Mellon full course", "CMU lecture series",
    "CMU course playlist", "Carnegie Mellon University lecture",
]),

_add("Caltech", "Caltech", [
    "CS 1", "CS 2", "CS 21", "CS 24", "CS 38", "CS 42",
    "CS 156A", "CS 156B", "CS 159", "CS 171", "CS 179",
    "Ph 1A", "Ph 1B", "Ph 1C", "Ph 2A", "Ph 2B", "Ph 2C",
    "Ph 106A", "Ph 106B", "Ph 106C", "Ph 125A", "Ph 125B",
    "Ph 127A", "Ph 127B", "Ph 129A", "Ph 135", "Ph 136A",
    "Ph 205", "Ph 219", "Ph 229", "Ph 236", "Ph 237",
    "Ma 1A", "Ma 1B", "Ma 1C", "Ma 2", "Ma 3", "Ma 5",
    "Ma 108A", "Ma 108B", "Ma 109A", "Ma 109B", "Ma 110A",
    "Ma 118", "Ma 120", "Ma 121A", "Ma 121B", "Ma 130", "Ma 147",
    "Ma 151A", "Ma 151B", "Ma 157", "Ma 160A", "Ma 160B",
    "Ch 1A", "Ch 1B", "Ch 21A", "Ch 21B", "Ch 41A", "Ch 41B",
    "Ch 101", "Ch 102", "Ch 112", "Ch 120", "Ch 125", "Ch 126",
    "Bi 1", "Bi 8", "Bi 9", "Bi 10", "Bi 110", "Bi 114",
    "Bi 117", "Bi 118", "Bi 122", "Bi 145A", "Bi 145B",
    "BEM 103", "BEM 105", "BEM 106", "BEM 108",
    "ACM 95", "ACM 100", "ACM 101", "ACM 104", "ACM 105",
    "ACM 106", "ACM 113", "ACM 116", "ACM 118", "ACM 201",
    "CDS 110", "CDS 131", "CDS 140", "CDS 232", "CDS 240",
], [""], extra_queries=[
    "Caltech full course", "Caltech lecture series",
    "Caltech course playlist",
]),

_add("Princeton", "Princeton", [
    "COS 126", "COS 217", "COS 226", "COS 240", "COS 302",
    "COS 316", "COS 320", "COS 324", "COS 326", "COS 333",
    "COS 340", "COS 343", "COS 375", "COS 382", "COS 402",
    "COS 418", "COS 424", "COS 426", "COS 429", "COS 432",
    "COS 433", "COS 435", "COS 436", "COS 445", "COS 448",
    "COS 451", "COS 461", "COS 485", "COS 488", "COS 511",
    "MAT 201", "MAT 202", "MAT 203", "MAT 204", "MAT 215",
    "MAT 216", "MAT 217", "MAT 218", "MAT 300", "MAT 320",
    "MAT 325", "MAT 330", "MAT 335", "MAT 345", "MAT 355",
    "MAT 365", "MAT 375", "MAT 385", "MAT 392",
    "PHY 101", "PHY 102", "PHY 103", "PHY 104", "PHY 105",
    "PHY 106", "PHY 115", "PHY 205", "PHY 207", "PHY 208",
    "PHY 209", "PHY 210", "PHY 301", "PHY 304", "PHY 305",
    "PHY 312", "PHY 401", "PHY 402", "PHY 405", "PHY 408",
    "ECO 201", "ECO 202", "ECO 301", "ECO 302", "ECO 310",
    "ECO 311", "ECO 312", "ECO 313", "ECO 317", "ECO 326",
    "ECO 341", "ECO 342", "ECO 348", "ECO 349", "ECO 361",
    "ECO 362", "ECO 363", "ECO 364", "ECO 371", "ECO 372",
    "ECO 462", "ECO 463", "ECO 512", "ECO 513", "ECO 517",
    "ECO 518", "ECO 521", "ECO 522", "ECO 523", "ECO 524",
    "ORF 245", "ORF 309", "ORF 335", "ORF 350", "ORF 363",
    "ORF 405", "ORF 406", "ORF 407", "ORF 408", "ORF 409",
    "ORF 411", "ORF 418", "ORF 467", "ORF 515", "ORF 522",
    "ORF 523", "ORF 525", "ORF 526", "ORF 527", "ORF 530",
    "ELE 201", "ELE 203", "ELE 301", "ELE 302", "ELE 341",
    "ELE 342", "ELE 351", "ELE 352", "ELE 381", "ELE 382",
    "ELE 391", "ELE 396", "ELE 397", "ELE 398", "ELE 482",
    "ELE 486", "ELE 488", "ELE 491", "ELE 519", "ELE 525",
], [""], extra_queries=[
    "Princeton full course", "Princeton lecture series",
    "Princeton University course",
]),

_add("Yale", "Yale", [
    "CPSC 100", "CPSC 112", "CPSC 201", "CPSC 202", "CPSC 223",
    "CPSC 323", "CPSC 327", "CPSC 365", "CPSC 366", "CPSC 421",
    "CPSC 422", "CPSC 423", "CPSC 424", "CPSC 425", "CPSC 426",
    "CPSC 427", "CPSC 428", "CPSC 429", "CPSC 430", "CPSC 431",
    "CPSC 432", "CPSC 433", "CPSC 434", "CPSC 435", "CPSC 436",
    "CPSC 437", "CPSC 439", "CPSC 440", "CPSC 445", "CPSC 446",
    "CPSC 447", "CPSC 452", "CPSC 453", "CPSC 462", "CPSC 465",
    "CPSC 467", "CPSC 468", "CPSC 469", "CPSC 470", "CPSC 471",
    "CPSC 473", "CPSC 474", "CPSC 475", "CPSC 476", "CPSC 477",
    "CPSC 478", "CPSC 479", "CPSC 480", "CPSC 481", "CPSC 482",
    "CPSC 483", "CPSC 484", "CPSC 485", "CPSC 486", "CPSC 487",
    "CPSC 488", "CPSC 489", "CPSC 490",
    "MATH 112", "MATH 115", "MATH 120", "MATH 225", "MATH 230",
    "MATH 231", "MATH 232", "MATH 233", "MATH 240", "MATH 241",
    "MATH 242", "MATH 244", "MATH 246", "MATH 247", "MATH 250",
    "MATH 251", "MATH 255", "MATH 256", "MATH 260", "MATH 261",
    "MATH 262", "MATH 265", "MATH 270", "MATH 275", "MATH 280",
    "MATH 285", "MATH 290", "MATH 300", "MATH 301", "MATH 302",
    "MATH 305", "MATH 310", "MATH 315", "MATH 320",
    "PHYS 200", "PHYS 201", "PHYS 205", "PHYS 206",
    "PHYS 260", "PHYS 261", "PHYS 300", "PHYS 301",
    "PHYS 343", "PHYS 344", "PHYS 345", "PHYS 346",
    "PHYS 400", "PHYS 401", "PHYS 402", "PHYS 403",
    "PHYS 410", "PHYS 411", "PHYS 412", "PHYS 420",
    "PHYS 430", "PHYS 440", "PHYS 441", "PHYS 442",
    "PHYS 443", "PHYS 444", "PHYS 448", "PHYS 449",
    "PHYS 450", "PHYS 460", "PHYS 461", "PHYS 462",
    "PHYS 469", "PHYS 470", "PHYS 471", "PHYS 500",
    "PHYS 501", "PHYS 502", "PHYS 510", "PHYS 511",
    "PHYS 512", "PHYS 520", "PHYS 521", "PHYS 522",
    "PHYS 530", "PHYS 531", "PHYS 532", "PHYS 540",
    "PHYS 541", "PHYS 542", "PHYS 548", "PHYS 549",
    "PHYS 550", "PHYS 551", "PHYS 552", "PHYS 560",
    "PHYS 561", "PHYS 562",
    "ECON 115", "ECON 116", "ECON 117", "ECON 121", "ECON 122",
    "ECON 125", "ECON 131", "ECON 132", "ECON 136", "ECON 159",
    "ECON 170", "ECON 171", "ECON 184", "ECON 186",
    "ECON 350", "ECON 351", "ECON 410", "ECON 411",
    "ECON 414", "ECON 417", "ECON 425", "ECON 430",
    "ECON 433", "ECON 440", "ECON 441", "ECON 450",
    "ECON 500", "ECON 501", "ECON 502", "ECON 510",
    "ECON 511", "ECON 512", "ECON 520", "ECON 521",
    "ECON 522", "ECON 525", "ECON 530", "ECON 531",
    "ECON 540", "ECON 541", "ECON 542", "ECON 545",
    "ECON 546", "ECON 550", "ECON 551", "ECON 552",
    "ECON 555", "ECON 556", "ECON 558", "ECON 559",
    "ECON 560", "ECON 561", "ECON 562", "ECON 563",
    "ECON 564", "ECON 565", "ECON 566", "ECON 567",
    "ECON 568", "ECON 569", "ECON 570", "ECON 571",
    "ECON 572", "ECON 573", "ECON 574", "ECON 575",
    "ECON 576", "ECON 577", "ECON 578", "ECON 579",
    "ECON 580", "ECON 581", "ECON 582", "ECON 583",
    "ECON 584", "ECON 585", "ECON 586", "ECON 587",
    "ECON 588", "ECON 589", "ECON 590",
    "CHEM 124", "CHEM 125", "CHEM 126", "CHEM 128",
    "CHEM 131", "CHEM 132", "CHEM 134", "CHEM 136",
    "CHEM 140", "CHEM 141", "CHEM 145", "CHEM 150",
    "CHEM 160", "CHEM 161", "CHEM 162", "CHEM 174",
    "CHEM 175", "CHEM 220", "CHEM 221", "CHEM 222",
    "CHEM 223", "CHEM 224", "CHEM 225", "CHEM 226",
    "CHEM 227", "CHEM 228", "CHEM 229", "CHEM 230",
    "CHEM 231", "CHEM 232", "CHEM 234",
], [""], extra_queries=[
    "Yale full course", "Yale lecture series",
    "Yale University course", "YaleCourses",
]),

# ── More schools (abbreviated to keep file manageable) ──────────────────

_add("Columbia", "Columbia", [
    "COMS W4111", "COMS W4115", "COMS W4118", "COMS W4701",
    "COMS W4705", "COMS W4706", "COMS W4721", "COMS W4771",
    "COMS W4772", "COMS W4995",
    "MATH V1101", "MATH V1102", "MATH V1201", "MATH V1202",
    "MATH V1207", "MATH V1208", "MATH V2000", "MATH V2010",
    "MATH V2020", "MATH V2030", "MATH V2500", "MATH V3001",
    "MATH V3002", "MATH V3020", "MATH V3027", "MATH V3028",
    "PHYS C1401", "PHYS C1402", "PHYS C1403", "PHYS W1401",
    "PHYS W1402", "PHYS W3003", "PHYS G4017", "PHYS G4018",
    "PHYS G4019", "PHYS G4020", "PHYS G4021", "PHYS G4022",
    "PHYS G4023", "PHYS G4024", "PHYS G4025", "PHYS G4026",
    "PHYS G4027", "PHYS G4028", "PHYS G4029", "PHYS G4030",
    "ELEN E4312", "ELEN E4314", "ELEN E4321", "ELEN E4702",
    "ELEN E4810", "ELEN E4815", "ELEN E6711", "ELEN E6712",
    "ELEN E6713", "ELEN E6717", "ELEN E6718",
    "ECON W3211", "ECON W3213", "ECON W3412", "ECON W3413",
    "ECON W3415", "ECON W4412", "ECON W4415", "ECON G6211",
    "ECON G6212", "ECON G6215", "ECON G6216", "ECON G6220",
    "ECON G6221", "ECON G6222", "ECON G6223",
    "STAT W4105", "STAT W4107", "STAT W4109", "STAT W4201",
    "STAT W4202", "STAT W4203", "STAT W4280", "STAT W4281",
    "STAT W4403", "STAT G4224", "STAT G4225", "STAT G4226",
    "STAT G4227", "STAT G4228", "STAT G4229", "STAT G4231",
    "STAT G4232", "STAT G4233",
], [""], extra_queries=[
    "Columbia full course", "Columbia University lecture",
    "Columbia course playlist",
]),

_add("Cornell", "Cornell", [
    "CS 2110", "CS 2800", "CS 3110", "CS 3410", "CS 3780",
    "CS 4110", "CS 4120", "CS 4160", "CS 4210", "CS 4220",
    "CS 4300", "CS 4320", "CS 4410", "CS 4420", "CS 4450",
    "CS 4620", "CS 4670", "CS 4700", "CS 4740", "CS 4750",
    "CS 4752", "CS 4754", "CS 4756", "CS 4758", "CS 4775",
    "CS 4780", "CS 4782", "CS 4783", "CS 4786", "CS 4787",
    "CS 4789", "CS 4810", "CS 4812", "CS 4820", "CS 4830",
    "CS 4840", "CS 4850", "CS 4860", "CS 4999",
    "MATH 1101", "MATH 1106", "MATH 1110", "MATH 1120",
    "MATH 1340", "MATH 1710", "MATH 1910", "MATH 1920",
    "MATH 2130", "MATH 2210", "MATH 2220", "MATH 2230",
    "MATH 2240", "MATH 2310", "MATH 2810", "MATH 2930",
    "MATH 2940", "MATH 3040", "MATH 3110", "MATH 3210",
    "MATH 3220", "MATH 3230", "MATH 3260", "MATH 3270",
    "MATH 3320", "MATH 3340", "MATH 3360", "MATH 3560",
    "MATH 3610", "MATH 3620", "MATH 4130", "MATH 4140",
    "MATH 4150", "MATH 4180", "MATH 4200", "MATH 4210",
    "MATH 4220", "MATH 4250", "MATH 4260", "MATH 4280",
    "MATH 4310", "MATH 4315", "MATH 4320", "MATH 4330",
    "MATH 4340", "MATH 4370", "MATH 4410", "MATH 4420",
    "MATH 4430", "MATH 4440", "MATH 4500", "MATH 4510",
    "MATH 4520", "MATH 4530", "MATH 4540", "MATH 4550",
    "MATH 4560", "MATH 4710", "MATH 4720", "MATH 4740",
    "MATH 4810", "MATH 4820", "MATH 4860", "MATH 4900",
    "MATH 5080", "MATH 6110", "MATH 6120", "MATH 6150",
    "MATH 6160", "MATH 6170", "MATH 6180", "MATH 6190",
    "MATH 6200", "MATH 6210", "MATH 6220", "MATH 6230",
    "MATH 6240", "MATH 6260", "MATH 6270", "MATH 6280",
    "MATH 6290", "MATH 6310", "MATH 6320", "MATH 6330",
    "MATH 6340", "MATH 6350", "MATH 6370", "MATH 6390",
    "MATH 6410", "MATH 6420", "MATH 6430", "MATH 6500",
    "MATH 6510", "MATH 6520", "MATH 6530", "MATH 6540",
    "PHYS 1110", "PHYS 1116", "PHYS 2207", "PHYS 2208",
    "PHYS 2213", "PHYS 2214", "PHYS 2217", "PHYS 2218",
    "PHYS 3310", "PHYS 3316", "PHYS 3317", "PHYS 3318",
    "PHYS 3327", "PHYS 3330", "PHYS 3360", "PHYS 4410",
    "PHYS 4433", "PHYS 4443", "PHYS 4444", "PHYS 4454",
    "PHYS 4456", "PHYS 4460", "PHYS 4470", "PHYS 4480",
    "PHYS 4484", "PHYS 4486", "PHYS 4490", "PHYS 4500",
    "PHYS 6500", "PHYS 6510", "PHYS 6511", "PHYS 6516",
    "PHYS 6517", "PHYS 6518", "PHYS 6520", "PHYS 6521",
    "PHYS 6525", "PHYS 6530", "PHYS 6531", "PHYS 6553",
    "PHYS 6554", "PHYS 6561", "PHYS 6562", "PHYS 6570",
    "PHYS 6572", "PHYS 6574", "PHYS 6580", "PHYS 6590",
    "PHYS 6599", "PHYS 7600", "PHYS 7601", "PHYS 7635",
    "PHYS 7636", "PHYS 7641", "PHYS 7645", "PHYS 7650",
    "PHYS 7651", "PHYS 7652", "PHYS 7660", "PHYS 7661",
    "PHYS 7666", "PHYS 7670", "PHYS 7671", "PHYS 7680",
    "PHYS 7681", "PHYS 7682", "PHYS 7683", "PHYS 7684",
    "PHYS 7685", "PHYS 7686", "PHYS 7687", "PHYS 7688",
    "PHYS 7689", "PHYS 7690", "PHYS 7691", "PHYS 7692",
    "PHYS 7693", "PHYS 7694",
    "ECON 1110", "ECON 1120", "ECON 3030", "ECON 3110",
    "ECON 3120", "ECON 3130", "ECON 3140", "ECON 3160",
    "ECON 3170", "ECON 3171", "ECON 3180", "ECON 3190",
    "ECON 3200", "ECON 3210", "ECON 3250", "ECON 3300",
    "ECON 3310", "ECON 3320", "ECON 3330", "ECON 3340",
    "ECON 3410", "ECON 3420", "ECON 3430", "ECON 3440",
    "ECON 3460", "ECON 3480", "ECON 3490",
    "ECON 3510", "ECON 3530", "ECON 3540", "ECON 3550",
    "ECON 3560", "ECON 3570", "ECON 3580", "ECON 3590",
    "ECON 3610", "ECON 3640", "ECON 3650", "ECON 3660",
    "ECON 3670", "ECON 3680", "ECON 3710", "ECON 3720",
    "ECON 3740", "ECON 3750", "ECON 3760", "ECON 3770",
    "ECON 3780", "ECON 3790", "ECON 3800", "ECON 3810",
    "ECON 3820", "ECON 3830", "ECON 3840", "ECON 3850",
    "ECON 3860", "ECON 3870",
    "ECON 4110", "ECON 4120", "ECON 4130", "ECON 4140",
    "ECON 4210", "ECON 4220", "ECON 4230", "ECON 4240",
    "ECON 4250", "ECON 4260", "ECON 4270", "ECON 4280",
    "ECON 4290", "ECON 4300", "ECON 4310", "ECON 4320",
    "ECON 4330", "ECON 4340", "ECON 4350", "ECON 4360",
    "ECON 4370", "ECON 4380", "ECON 4390", "ECON 4400",
    "ECON 4410", "ECON 4420", "ECON 4430", "ECON 4440",
    "ECON 4450", "ECON 4460", "ECON 4470", "ECON 4480",
    "ECON 4490",
    "ECON 6110", "ECON 6120", "ECON 6130", "ECON 6140",
    "ECON 6150", "ECON 6160", "ECON 6170", "ECON 6180",
    "ECON 6190", "ECON 6200", "ECON 6210", "ECON 6220",
    "ECON 6230", "ECON 6240", "ECON 6250", "ECON 6260",
    "ECON 6270", "ECON 6280", "ECON 6290", "ECON 6300",
    "ECON 6310", "ECON 6320", "ECON 6330", "ECON 6340",
    "ECON 6350", "ECON 6360", "ECON 6370", "ECON 6380",
    "ECON 6390", "ECON 6400", "ECON 6410", "ECON 6420",
    "ECON 6430", "ECON 6440", "ECON 6450", "ECON 6460",
    "ECON 6470", "ECON 6480", "ECON 6490",
], [""], extra_queries=[
    "Cornell full course", "Cornell University lecture",
    "Cornell course playlist",
]),

_add("Duke", "Duke", [
    "COMPSCI 101", "COMPSCI 201", "COMPSCI 230", "COMPSCI 250",
    "COMPSCI 260", "COMPSCI 290", "COMPSCI 310", "COMPSCI 320",
    "COMPSCI 330", "COMPSCI 340", "COMPSCI 350", "COMPSCI 356",
    "COMPSCI 370", "COMPSCI 371", "COMPSCI 390",
    "MATH 111", "MATH 112", "MATH 122", "MATH 202", "MATH 212",
    "MATH 216", "MATH 218", "MATH 219", "MATH 221", "MATH 222",
    "MATH 225", "MATH 230", "MATH 231", "MATH 232",
    "PHYSICS 131", "PHYSICS 132", "PHYSICS 133", "PHYSICS 134",
    "PHYSICS 141", "PHYSICS 142", "PHYSICS 143", "PHYSICS 144",
    "PHYSICS 151", "PHYSICS 152", "PHYSICS 153", "PHYSICS 154",
    "PHYSICS 161", "PHYSICS 162", "PHYSICS 163", "PHYSICS 164",
    "PHYSICS 171", "PHYSICS 172", "PHYSICS 173", "PHYSICS 174",
    "ECON 101", "ECON 102", "ECON 201D", "ECON 202D", "ECON 205D",
    "ECON 210D", "ECON 211D", "ECON 220D", "ECON 230D",
    "ECON 250D", "ECON 255D", "ECON 260D", "ECON 270D",
    "ECON 301", "ECON 302", "ECON 312", "ECON 314",
    "ECON 316", "ECON 320", "ECON 325", "ECON 328",
    "ECON 331", "ECON 332", "ECON 341", "ECON 342",
    "ECON 343", "ECON 344", "ECON 345", "ECON 348",
    "ECON 349", "ECON 351", "ECON 352", "ECON 353",
    "ECON 354", "ECON 355", "ECON 356", "ECON 357",
    "ECON 358", "ECON 359", "ECON 361", "ECON 362",
    "ECON 363", "ECON 364", "ECON 365",
    "STA 101", "STA 102", "STA 111", "STA 112", "STA 210",
    "STA 211", "STA 212", "STA 213", "STA 214", "STA 221",
    "STA 222", "STA 223", "STA 230", "STA 231", "STA 240",
    "STA 250", "STA 260", "STA 270", "STA 280",
    "ECE 110", "ECE 230", "ECE 250", "ECE 270",
    "ECE 280", "ECE 350", "ECE 353", "ECE 355",
    "ECE 356", "ECE 358", "ECE 359", "ECE 381",
    "ECE 382", "ECE 383", "ECE 384", "ECE 459",
    "ECE 550", "ECE 551", "ECE 552", "ECE 553",
    "ECE 554", "ECE 555", "ECE 556", "ECE 557",
    "ECE 558", "ECE 559",
    "ME 101", "ME 201", "ME 202", "ME 203", "ME 204",
    "ME 205", "ME 206", "ME 207", "ME 208", "ME 209",
    "ME 210", "ME 211", "ME 212", "ME 213", "ME 214",
    "ME 215", "ME 216", "ME 217", "ME 218", "ME 219",
    "ME 220", "ME 221", "ME 222", "ME 223", "ME 224",
    "ME 225", "ME 226", "ME 227", "ME 228", "ME 229",
    "ME 230", "ME 231", "ME 232", "ME 233", "ME 234",
    "ME 235", "ME 236", "ME 237", "ME 238", "ME 239",
    "ME 240", "ME 241", "ME 242", "ME 243", "ME 244",
    "ME 245", "ME 246", "ME 247", "ME 248", "ME 249",
    "ME 250", "ME 251", "ME 252", "ME 253", "ME 254",
    "ME 255", "ME 256", "ME 257", "ME 258", "ME 259",
    "ME 260", "ME 261", "ME 262",
    "ME 301", "ME 302", "ME 303", "ME 304", "ME 305",
    "ME 306", "ME 307", "ME 308", "ME 309", "ME 310",
    "ME 311", "ME 312", "ME 313", "ME 314", "ME 315",
    "ME 316", "ME 317", "ME 318", "ME 319", "ME 320",
    "ME 321", "ME 322", "ME 323", "ME 324", "ME 325",
    "ME 326", "ME 327", "ME 328", "ME 329", "ME 330",
    "ME 331", "ME 332", "ME 333", "ME 334", "ME 335",
    "ME 336", "ME 337", "ME 338", "ME 339", "ME 340",
    "ME 341", "ME 342", "ME 343", "ME 344", "ME 345",
    "ME 346", "ME 347", "ME 348", "ME 349",
    "ME 401", "ME 402", "ME 403", "ME 404",
    "ME 405", "ME 406", "ME 407", "ME 408", "ME 409",
    "ME 410", "ME 411", "ME 412", "ME 413", "ME 414",
    "ME 415", "ME 416", "ME 417", "ME 418",
    "ME 419", "ME 420", "ME 421", "ME 422", "ME 423",
    "ME 424", "ME 425", "ME 426", "ME 427", "ME 428",
    "ME 429", "ME 430", "ME 431", "ME 432", "ME 433",
    "ME 434", "ME 435", "ME 436", "ME 437", "ME 438",
    "ME 439", "ME 440", "ME 441", "ME 442", "ME 443",
    "ME 444", "ME 445", "ME 446", "ME 447", "ME 448",
    "ME 449",
    "BIOLOGY 201L", "BIOLOGY 202L", "BIOLOGY 203L",
    "BIOLOGY 212", "BIOLOGY 213", "BIOLOGY 214",
    "BIOLOGY 215", "BIOLOGY 216", "BIOLOGY 217",
    "BIOLOGY 218", "BIOLOGY 219", "BIOLOGY 220",
    "BIOLOGY 221", "BIOLOGY 222", "BIOLOGY 223",
    "BIOLOGY 224", "BIOLOGY 225", "BIOLOGY 226",
    "BIOLOGY 227", "BIOLOGY 228", "BIOLOGY 229",
    "BIOLOGY 301", "BIOLOGY 302", "BIOLOGY 303",
    "BIOLOGY 304", "BIOLOGY 305", "BIOLOGY 306",
    "BIOLOGY 307", "BIOLOGY 308", "BIOLOGY 309",
    "BIOLOGY 310", "BIOLOGY 311", "BIOLOGY 312",
    "BIOLOGY 313", "BIOLOGY 314", "BIOLOGY 315",
    "BIOLOGY 316", "BIOLOGY 317", "BIOLOGY 318",
    "BIOLOGY 319", "BIOLOGY 320", "BIOLOGY 321",
    "BIOLOGY 322", "BIOLOGY 323", "BIOLOGY 324",
    "BIOLOGY 325", "BIOLOGY 326", "BIOLOGY 327",
    "BIOLOGY 328", "BIOLOGY 329",
    "BIOLOGY 401", "BIOLOGY 402", "BIOLOGY 403",
    "BIOLOGY 404", "BIOLOGY 405", "BIOLOGY 406",
], [""], extra_queries=[
    "Duke full course", "Duke University lecture",
    "Duke course playlist",
]),

_add("Georgia Tech", "Georgia Tech", [
    "CS 1301", "CS 1331", "CS 1332", "CS 2050", "CS 2110",
    "CS 2200", "CS 2340", "CS 3210", "CS 3220", "CS 3251",
    "CS 3510", "CS 3600", "CS 3630", "CS 3651", "CS 3750",
    "CS 3790", "CS 3873", "CS 4001", "CS 4100", "CS 4200",
    "CS 4210", "CS 4235", "CS 4240", "CS 4250", "CS 4251",
    "CS 4255", "CS 4260", "CS 4261", "CS 4270", "CS 4280",
    "CS 4290", "CS 4365", "CS 4400", "CS 4420", "CS 4430",
    "CS 4440", "CS 4452", "CS 4460", "CS 4464", "CS 4470",
    "CS 4472", "CS 4476", "CS 4480", "CS 4495", "CS 4496",
    "CS 4510", "CS 4520", "CS 4530", "CS 4540", "CS 4550",
    "CS 4560", "CS 4590", "CS 4600", "CS 4610", "CS 4611",
    "CS 4612", "CS 4613", "CS 4614", "CS 4615", "CS 4616",
    "CS 4620", "CS 4621", "CS 4622", "CS 4623", "CS 4624",
    "CS 4625", "CS 4630", "CS 4632", "CS 4635", "CS 4640",
    "CS 4641", "CS 4644", "CS 4646", "CS 4649", "CS 4650",
    "CS 4660", "CS 4670", "CS 4675", "CS 4680", "CS 4690",
    "CS 4710", "CS 4730", "CS 4731", "CS 4740", "CS 4750",
    "CS 4760", "CS 4770", "CS 4773", "CS 4777", "CS 4780",
    "CS 4782", "CS 4783", "CS 4786", "CS 4787", "CS 4789",
    "CS 4790", "CS 4791", "CS 4792", "CS 4793", "CS 4794",
    "CS 4795", "CS 4796", "CS 4797", "CS 4798", "CS 4799",
    "CS 4801", "CS 4803", "CS 4805", "CS 6001", "CS 6010",
    "CS 6230", "CS 6236", "CS 6240", "CS 6241", "CS 6245",
    "CS 6250", "CS 6260", "CS 6262", "CS 6263", "CS 6264",
    "CS 6265", "CS 6266", "CS 6267", "CS 6269", "CS 6270",
    "CS 6280", "CS 6290", "CS 6291", "CS 6300", "CS 6301",
    "CS 6310", "CS 6320", "CS 6340", "CS 6365", "CS 6400",
    "CS 6411", "CS 6421", "CS 6422", "CS 6430", "CS 6440",
    "CS 6451", "CS 6452", "CS 6453", "CS 6454", "CS 6455",
    "CS 6457", "CS 6460", "CS 6465", "CS 6470", "CS 6471",
    "CS 6475", "CS 6476", "CS 6480", "CS 6483", "CS 6485",
    "CS 6491", "CS 6492", "CS 6495", "CS 6505", "CS 6507",
    "CS 6510", "CS 6515", "CS 6520", "CS 6530", "CS 6535",
    "CS 6540", "CS 6550", "CS 6560", "CS 6601", "CS 6603",
    "CS 6604", "CS 6620", "CS 6630", "CS 6635", "CS 6640",
    "CS 6643", "CS 6644", "CS 6650", "CS 6660", "CS 6670",
    "CS 6675", "CS 6699", "CS 6705", "CS 6725", "CS 6726",
    "CS 6727", "CS 6730", "CS 6740", "CS 6747", "CS 6750",
    "CS 6755", "CS 6760", "CS 6763", "CS 6764", "CS 6766",
    "CS 6770", "CS 6772", "CS 6773", "CS 6774", "CS 6775",
    "CS 6776", "CS 6780", "CS 6782", "CS 6783", "CS 6784",
    "CS 6785", "CS 6786", "CS 6787", "CS 6788", "CS 6789",
    "CS 6790", "CS 6791", "CS 6792", "CS 6793", "CS 6794",
    "CS 6795", "CS 6796", "CS 6797", "CS 6798", "CS 6799",
    "CS 6800", "CS 6998", "CS 6999", "CS 7000", "CS 7001",
    "CS 7280", "CS 7290", "CS 7292", "CS 7370", "CS 7440",
    "CS 7450", "CS 7455", "CS 7460", "CS 7465", "CS 7467",
    "CS 7470", "CS 7475", "CS 7476",
    "CS 7480", "CS 7485", "CS 7486", "CS 7487", "CS 7488",
    "CS 7489", "CS 7490", "CS 7491", "CS 7492", "CS 7493",
    "CS 7495", "CS 7496", "CS 7497", "CS 7498", "CS 7499",
    "CS 7500", "CS 7501", "CS 7502", "CS 7510", "CS 7520",
    "CS 7521", "CS 7522", "CS 7523", "CS 7524", "CS 7525",
    "CS 7526", "CS 7530", "CS 7531", "CS 7532", "CS 7533",
    "CS 7534", "CS 7535", "CS 7536", "CS 7537", "CS 7538",
    "CS 7539", "CS 7540", "CS 7541", "CS 7542", "CS 7543",
    "CS 7544", "CS 7545", "CS 7560", "CS 7561", "CS 7562",
    "CS 7563", "CS 7564", "CS 7565", "CS 7570", "CS 7580",
    "CS 7585", "CS 7590", "CS 7600", "CS 7610", "CS 7611",
    "CS 7612", "CS 7613", "CS 7614", "CS 7615", "CS 7616",
    "CS 7620", "CS 7630", "CS 7631", "CS 7632", "CS 7633",
    "CS 7634", "CS 7635", "CS 7636", "CS 7637", "CS 7638",
    "CS 7639", "CS 7640", "CS 7641", "CS 7642", "CS 7643",
    "CS 7644", "CS 7645", "CS 7646", "CS 7647", "CS 7648",
    "CS 7649", "CS 7650", "CS 7655", "CS 7660", "CS 7670",
    "CS 7675", "CS 7680", "CS 7685", "CS 7690", "CS 7695",
    "CS 7700", "CS 7710", "CS 7720", "CS 7730", "CS 7740",
    "CS 7750", "CS 7760", "CS 7770", "CS 7780", "CS 7790",
    "CS 7800", "CS 7810", "CS 7820", "CS 7830", "CS 7840",
    "CS 7850", "CS 7860", "CS 7870", "CS 7880", "CS 7890",
    "CS 7900", "CS 7910", "CS 7920", "CS 7930", "CS 7940",
    "CS 7950", "CS 7960", "CS 7970", "CS 7980", "CS 7990",
    "CS 7999", "CS 8001", "CS 8002", "CS 8003", "CS 8004",
    "CS 8005", "CS 8010",
    "CS 8803", "CS 8901", "CS 8903", "CS 8998", "CS 8999",
    "CS 9900", "CS 9901", "CS 9902", "CS 9903", "CS 9904",
    "CS 9905", "CS 9910",
    "MATH 1501", "MATH 1502", "MATH 1522", "MATH 1551",
    "MATH 1552", "MATH 1553", "MATH 1554", "MATH 1564",
    "MATH 1711", "MATH 1712", "MATH 2011", "MATH 2012",
    "MATH 2106", "MATH 2401", "MATH 2403", "MATH 2551",
    "MATH 2552", "MATH 2602", "MATH 2603", "MATH 2605",
    "MATH 3012", "MATH 3215", "MATH 3225", "MATH 3235",
    "MATH 3406", "MATH 4022", "MATH 4032", "MATH 4107",
    "MATH 4108", "MATH 4150", "MATH 4221", "MATH 4222",
    "MATH 4255", "MATH 4260", "MATH 4261", "MATH 4262",
    "MATH 4270", "MATH 4280", "MATH 4305", "MATH 4317",
    "MATH 4318", "MATH 4320", "MATH 4347", "MATH 4348",
    "MATH 4431", "MATH 4432", "MATH 4441", "MATH 4442",
    "MATH 4451", "MATH 4452", "MATH 4544", "MATH 4580",
    "MATH 4581", "MATH 4640", "MATH 4670", "MATH 4690",
    "MATH 4750", "MATH 4770", "MATH 4781", "MATH 4782",
    "MATH 4801", "MATH 4803", "MATH 6001", "MATH 6010",
    "MATH 6120", "MATH 6221", "MATH 6241", "MATH 6260",
    "MATH 6267", "MATH 6301", "MATH 6307", "MATH 6310",
    "MATH 6320", "MATH 6330", "MATH 6337", "MATH 6338",
    "MATH 6340", "MATH 6342", "MATH 6360", "MATH 6370",
    "MATH 6380", "MATH 6390", "MATH 6400", "MATH 6410",
    "MATH 6420", "MATH 6430", "MATH 6440", "MATH 6450",
    "MATH 6460", "MATH 6470", "MATH 6480", "MATH 6490",
    "MATH 6500", "MATH 6510", "MATH 6520", "MATH 6530",
    "MATH 6540", "MATH 6550", "MATH 6560", "MATH 6570",
    "MATH 6580", "MATH 6590",
    "PHYS 2211", "PHYS 2212", "PHYS 2213", "PHYS 3122",
    "PHYS 3123", "PHYS 3201", "PHYS 3202", "PHYS 3210",
    "PHYS 3220", "PHYS 3230", "PHYS 3231", "PHYS 3232",
    "PHYS 3240", "PHYS 3250", "PHYS 3260", "PHYS 3270",
    "PHYS 3271", "PHYS 3280", "PHYS 3281", "PHYS 3282",
    "PHYS 3290", "PHYS 3291", "PHYS 3292",
    "PHYS 4101", "PHYS 4102", "PHYS 4110", "PHYS 4111",
    "PHYS 4112", "PHYS 4120", "PHYS 4121", "PHYS 4122",
    "PHYS 4130", "PHYS 4131", "PHYS 4132", "PHYS 4140",
    "PHYS 4141", "PHYS 4142", "PHYS 4150", "PHYS 4151",
    "PHYS 4152", "PHYS 4160", "PHYS 4161", "PHYS 4162",
    "PHYS 4170", "PHYS 4171", "PHYS 4172", "PHYS 4180",
    "PHYS 4181", "PHYS 4182", "PHYS 4190", "PHYS 4191",
    "PHYS 4192",
    "PHYS 6101", "PHYS 6102", "PHYS 6103", "PHYS 6104",
    "PHYS 6105", "PHYS 6106", "PHYS 6107", "PHYS 6108",
    "PHYS 6109", "PHYS 6110", "PHYS 6111", "PHYS 6112",
    "PHYS 6113", "PHYS 6114", "PHYS 6115", "PHYS 6116",
    "PHYS 6117", "PHYS 6118", "PHYS 6119",
    "ISYE 6420", "ISYE 6501", "ISYE 6644", "ISYE 6669",
    "ISYE 6740", "ISYE 6759", "ISYE 6767", "ISYE 6783",
    "ISYE 6804", "ISYE 7400", "ISYE 7401", "ISYE 7402",
    "ISYE 7403", "ISYE 7405", "ISYE 7406",
    "ECE 2020", "ECE 2025", "ECE 2030", "ECE 2031", "ECE 2035",
    "ECE 2036", "ECE 2040", "ECE 3020", "ECE 3025", "ECE 3030",
    "ECE 3031", "ECE 3040", "ECE 3041", "ECE 3042", "ECE 3043",
    "ECE 3044", "ECE 3045", "ECE 3046", "ECE 3050", "ECE 3060",
    "ECE 3065", "ECE 3070", "ECE 3071", "ECE 3072", "ECE 3075",
    "ECE 3077", "ECE 3080", "ECE 3084", "ECE 3090", "ECE 3550",
    "ECE 3600", "ECE 3710", "ECE 3741", "ECE 4001", "ECE 4002",
    "ECE 4003", "ECE 4010", "ECE 4011", "ECE 4012",
    "ECE 4100", "ECE 4110", "ECE 4115", "ECE 4117",
    "ECE 4120", "ECE 4122", "ECE 4130", "ECE 4140",
    "ECE 4150", "ECE 4160", "ECE 4170", "ECE 4180",
    "ECE 4190", "ECE 4200", "ECE 4210", "ECE 4220",
    "ECE 4230", "ECE 4240", "ECE 4250", "ECE 4260",
    "ECE 4270", "ECE 4280", "ECE 4290",
    "ECE 4300", "ECE 4310", "ECE 4320", "ECE 4330",
    "ECE 4340", "ECE 4350", "ECE 4360", "ECE 4370",
    "ECE 4380", "ECE 4390",
], [""], extra_queries=[
    "Georgia Tech full course", "GaTech lecture series",
    "Georgia Tech course playlist",
]),

# ── UK ──────────────────────────────────────────────────────────────────
_add("Oxford", "Oxford", [], [""], extra_queries=[
    "Oxford Mathematics full course", "Oxford Physics lecture series",
    "Oxford Computer Science course", "Oxford full course playlist",
    "Oxford University lecture series",
]),

_add("Cambridge", "Cambridge", [], [""], extra_queries=[
    "Cambridge Mathematics lecture series", "Cambridge Physics full course",
    "Cambridge Computer Science course", "Cambridge University lecture",
    "Cambridge Natural Sciences lectures",
]),

_add("Imperial", "Imperial College London", [
    "MATH 40001", "MATH 40002", "MATH 40003", "MATH 40004", "MATH 40005",
    "MATH 40006", "MATH 40007", "MATH 40008", "MATH 40009", "MATH 40010",
    "MATH 50001", "MATH 50002", "MATH 50003", "MATH 50004", "MATH 50005",
    "MATH 50006", "MATH 50007", "MATH 50008", "MATH 50009", "MATH 50010",
    "COMP 40001", "COMP 50001", "COMP 50002", "COMP 50003", "COMP 50004",
    "COMP 50005", "COMP 50006", "COMP 50007",
    "PHYS 40001", "PHYS 40002", "PHYS 40003", "PHYS 40004", "PHYS 40005",
    "PHYS 50001", "PHYS 50002", "PHYS 50003", "PHYS 50004", "PHYS 50005",
    "PHYS 50006", "PHYS 50007", "PHYS 50008",
    "ELEC 40001", "ELEC 40002", "ELEC 40003", "ELEC 40004",
    "ELEC 50001", "ELEC 50002", "ELEC 50003", "ELEC 50004",
    "ELEC 50005", "ELEC 50006", "ELEC 50007",
    "MECH 40001", "MECH 40002", "MECH 40003", "MECH 40004",
    "MECH 50001", "MECH 50002", "MECH 50003", "MECH 50004",
    "MECH 50005", "MECH 50006",
], [""], extra_queries=[
    "Imperial College full course", "Imperial College London lecture",
    "Imperial course playlist",
]),

_add("UCL", "University College London", [
    "COMP 0001", "COMP 0002", "COMP 0003", "COMP 0004", "COMP 0005",
    "COMP 0006", "COMP 0007", "COMP 0008", "COMP 0009", "COMP 0010",
    "COMP 0100", "COMP 0101", "COMP 0102", "COMP 0103", "COMP 0104",
    "COMP 0105", "COMP 0106", "COMP 0107", "COMP 0108", "COMP 0109",
    "COMP 0200", "COMP 0201", "COMP 0202", "COMP 0203", "COMP 0204",
    "COMP 0205", "COMP 0206", "COMP 0207",
    "MATH 0001", "MATH 0002", "MATH 0003", "MATH 0004", "MATH 0005",
    "MATH 0006", "MATH 0007", "MATH 0008",
    "MATH 6101", "MATH 6102", "MATH 6103", "MATH 6104", "MATH 6105",
    "MATH 6106", "MATH 6107", "MATH 6108",
    "PHYS 0001", "PHYS 0002", "PHYS 0003", "PHYS 0004", "PHYS 0005",
    "PHYS 0006", "PHYS 0007", "PHYS 0008",
    "PHYS 4101", "PHYS 4102", "PHYS 4103", "PHYS 4104", "PHYS 4105",
    "PHYS 4106", "PHYS 4107", "PHYS 4108",
    "ECON 0001", "ECON 0002", "ECON 0003", "ECON 0004", "ECON 0005",
    "ECON 0006", "ECON 0007", "ECON 0008",
    "ECON 2001", "ECON 2002", "ECON 2003", "ECON 2004", "ECON 2005",
    "ECON 2006", "ECON 2007", "ECON 2008",
    "STAT 0001", "STAT 0002", "STAT 0003", "STAT 0004", "STAT 0005",
    "STAT 0006", "STAT 0007", "STAT 0008",
    "STAT 2001", "STAT 2002", "STAT 2003", "STAT 2004", "STAT 2005",
    "STAT 2006", "STAT 2007", "STAT 2008",
    "ELEC 0001", "ELEC 0002", "ELEC 0003", "ELEC 0004", "ELEC 0005",
    "ELEC 0006", "ELEC 0007", "ELEC 0008",
    "ELEC 4001", "ELEC 4002", "ELEC 4003", "ELEC 4004", "ELEC 4005",
], [""], extra_queries=[
    "UCL full course", "University College London lecture",
    "UCL course playlist",
]),

_add("Edinburgh", "University of Edinburgh", [
    "INFR 08008", "INFR 08009", "INFR 08010", "INFR 08011",
    "INFR 08012", "INFR 08013", "INFR 08014", "INFR 08015",
    "INFR 08016", "INFR 08017", "INFR 08018", "INFR 08019",
    "INFR 08020", "INFR 08021", "INFR 08022", "INFR 08023",
    "INFR 08024", "INFR 08025", "INFR 08026", "INFR 08027",
    "INFR 08028", "INFR 08029", "INFR 08030", "INFR 08031",
    "INFR 09008", "INFR 09009", "INFR 09010", "INFR 09011",
    "INFR 09012", "INFR 09013", "INFR 09014", "INFR 09015",
    "INFR 10001", "INFR 10002", "INFR 10003", "INFR 10004",
    "INFR 10005", "INFR 10006", "INFR 10007", "INFR 10008",
    "INFR 11001", "INFR 11002", "INFR 11003", "INFR 11004",
    "INFR 11005", "INFR 11006", "INFR 11007", "INFR 11008",
    "INFR 11009", "INFR 11010", "INFR 11011", "INFR 11012",
    "INFR 11013", "INFR 11014", "INFR 11015", "INFR 11016",
    "INFR 11017", "INFR 11018", "INFR 11019", "INFR 11020",
    "INFR 11021", "INFR 11022", "INFR 11023", "INFR 11024",
    "INFR 11025", "INFR 11026", "INFR 11027", "INFR 11028",
    "INFR 11029", "INFR 11030", "INFR 11031", "INFR 11032",
    "INFR 11033", "INFR 11034", "INFR 11035", "INFR 11036",
    "INFR 11037", "INFR 11038", "INFR 11039", "INFR 11040",
    "INFR 11041", "INFR 11042", "INFR 11043", "INFR 11044",
    "INFR 11045", "INFR 11046", "INFR 11047", "INFR 11048",
    "INFR 11049", "INFR 11050",
    "MATH 08008", "MATH 08009", "MATH 08010", "MATH 08011",
    "MATH 08012", "MATH 08013", "MATH 08014",
    "MATH 10001", "MATH 10002", "MATH 10003", "MATH 10004",
    "MATH 10005", "MATH 10006", "MATH 10007",
    "MATH 11001", "MATH 11002", "MATH 11003", "MATH 11004",
    "PHYS 08008", "PHYS 08009", "PHYS 08010", "PHYS 08011",
    "PHYS 08012", "PHYS 08013",
    "PHYS 09008", "PHYS 09009", "PHYS 09010", "PHYS 09011",
    "PHYS 09012", "PHYS 09013",
    "PHYS 10001", "PHYS 10002", "PHYS 10003", "PHYS 10004",
], [""], extra_queries=[
    "Edinburgh full course", "University of Edinburgh lecture",
    "Edinburgh course playlist",
]),

# ── Canada ──────────────────────────────────────────────────────────────
_add("Toronto", "University of Toronto", [
    "CSC 108", "CSC 148", "CSC 165", "CSC 207", "CSC 209",
    "CSC 236", "CSC 240", "CSC 258", "CSC 263", "CSC 265",
    "CSC 300", "CSC 301", "CSC 302", "CSC 309", "CSC 311",
    "CSC 318", "CSC 320", "CSC 321", "CSC 324", "CSC 336",
    "CSC 343", "CSC 358", "CSC 369", "CSC 373", "CSC 384",
    "CSC 385", "CSC 400", "CSC 401", "CSC 404", "CSC 410",
    "CSC 411", "CSC 412", "CSC 413", "CSC 418", "CSC 419",
    "CSC 420", "CSC 428", "CSC 434", "CSC 436", "CSC 438",
    "CSC 443", "CSC 446", "CSC 454", "CSC 456", "CSC 457",
    "CSC 458", "CSC 463", "CSC 465", "CSC 466", "CSC 467",
    "CSC 468", "CSC 469", "CSC 470", "CSC 471", "CSC 472",
    "CSC 473", "CSC 484", "CSC 485", "CSC 486", "CSC 487",
    "CSC 488", "CSC 489", "CSC 490", "CSC 491", "CSC 494",
    "CSC 495", "CSC 2209", "CSC 2210", "CSC 2301", "CSC 2302",
    "CSC 2304", "CSC 2305", "CSC 2306", "CSC 2307", "CSC 2308",
    "CSC 2309", "CSC 2310", "CSC 2311", "CSC 2312", "CSC 2313",
    "CSC 2314", "CSC 2315", "CSC 2316", "CSC 2317", "CSC 2318",
    "CSC 2319", "CSC 2320", "CSC 2321", "CSC 2322",
    "CSC 2410", "CSC 2411", "CSC 2412", "CSC 2413", "CSC 2414",
    "CSC 2415", "CSC 2416", "CSC 2417", "CSC 2418",
    "CSC 2420", "CSC 2421", "CSC 2422", "CSC 2423", "CSC 2424",
    "CSC 2425", "CSC 2426", "CSC 2427", "CSC 2428", "CSC 2429",
    "CSC 2430", "CSC 2431",
    "CSC 2500", "CSC 2501", "CSC 2502", "CSC 2503", "CSC 2504",
    "CSC 2505", "CSC 2506", "CSC 2507", "CSC 2508",
    "CSC 2510", "CSC 2511", "CSC 2512", "CSC 2513", "CSC 2514",
    "CSC 2515", "CSC 2516", "CSC 2517", "CSC 2518", "CSC 2519",
    "CSC 2520", "CSC 2521", "CSC 2522", "CSC 2523", "CSC 2524",
    "CSC 2525", "CSC 2526", "CSC 2527", "CSC 2528", "CSC 2529",
    "CSC 2530", "CSC 2531", "CSC 2532", "CSC 2533",
    "MAT 135", "MAT 136", "MAT 137", "MAT 157", "MAT 223",
    "MAT 224", "MAT 235", "MAT 237", "MAT 240", "MAT 244",
    "MAT 246", "MAT 247", "MAT 257", "MAT 267", "MAT 301",
    "MAT 302", "MAT 309", "MAT 315", "MAT 327", "MAT 329",
    "MAT 332", "MAT 334", "MAT 335", "MAT 336", "MAT 337",
    "MAT 344", "MAT 347", "MAT 351", "MAT 354", "MAT 357",
    "MAT 363", "MAT 367", "MAT 371", "MAT 378", "MAT 379",
    "MAT 385", "MAT 389", "MAT 390",
    "MAT 1001", "MAT 1002", "MAT 1003", "MAT 1004", "MAT 1005",
    "MAT 1006", "MAT 1007", "MAT 1008", "MAT 1009", "MAT 1010",
    "MAT 1011", "MAT 1012", "MAT 1013", "MAT 1014", "MAT 1015",
    "MAT 1016", "MAT 1017", "MAT 1018", "MAT 1019", "MAT 1020",
    "MAT 1021", "MAT 1022", "MAT 1023", "MAT 1024",
    "PHY 131", "PHY 132", "PHY 151", "PHY 152", "PHY 250",
    "PHY 251", "PHY 252", "PHY 254", "PHY 255", "PHY 256",
    "PHY 350", "PHY 351", "PHY 352", "PHY 353", "PHY 354",
    "PHY 355", "PHY 356", "PHY 357", "PHY 358", "PHY 359",
    "PHY 450", "PHY 451", "PHY 452", "PHY 453", "PHY 454",
    "PHY 455", "PHY 456", "PHY 457", "PHY 458", "PHY 459",
    "PHY 460",
    "ECO 100", "ECO 101", "ECO 102", "ECO 200", "ECO 202",
    "ECO 204", "ECO 206", "ECO 208", "ECO 209", "ECO 210",
    "ECO 220", "ECO 227", "ECO 239", "ECO 240", "ECO 260",
    "ECO 305", "ECO 306", "ECO 313", "ECO 316", "ECO 320",
    "ECO 321", "ECO 322", "ECO 324", "ECO 325", "ECO 326",
    "ECO 327", "ECO 328", "ECO 329", "ECO 331", "ECO 332",
    "ECO 333", "ECO 334", "ECO 336", "ECO 337", "ECO 338",
    "ECO 339", "ECO 340", "ECO 341", "ECO 342", "ECO 349",
    "ECO 350", "ECO 351", "ECO 358", "ECO 359", "ECO 362",
    "ECO 364", "ECO 365", "ECO 369", "ECO 372", "ECO 374",
    "ECO 375", "ECO 376", "ECO 380", "ECO 381", "ECO 383",
    "ECO 400", "ECO 401", "ECO 402", "ECO 403", "ECO 404",
    "ECO 405", "ECO 406", "ECO 407", "ECO 408", "ECO 409",
    "ECO 410", "ECO 411", "ECO 412", "ECO 413", "ECO 414",
    "ECO 415", "ECO 416", "ECO 417", "ECO 418", "ECO 419",
    "ECO 420", "ECO 421", "ECO 422", "ECO 423", "ECO 424",
    "ECO 425", "ECO 426", "ECO 427", "ECO 428",
    "STA 130", "STA 201", "STA 220", "STA 221", "STA 237",
    "STA 238", "STA 247", "STA 248", "STA 255", "STA 257",
    "STA 261", "STA 302", "STA 303", "STA 304", "STA 305",
    "STA 310", "STA 312", "STA 313", "STA 314", "STA 315",
    "STA 347", "STA 352", "STA 355", "STA 410", "STA 414",
    "STA 422", "STA 437", "STA 442", "STA 447", "STA 450",
    "STA 452", "STA 457", "STA 460", "STA 465", "STA 490",
], [""], extra_queries=[
    "University of Toronto full course", "UofT lecture series",
    "Toronto course playlist",
]),

_add("UBC", "UBC", [
    "CPSC 110", "CPSC 121", "CPSC 210", "CPSC 213", "CPSC 221",
    "CPSC 259", "CPSC 261", "CPSC 301", "CPSC 302", "CPSC 303",
    "CPSC 304", "CPSC 310", "CPSC 311", "CPSC 312", "CPSC 313",
    "CPSC 314", "CPSC 317", "CPSC 319", "CPSC 320", "CPSC 322",
    "CPSC 330", "CPSC 340", "CPSC 344", "CPSC 349", "CPSC 368",
    "CPSC 402", "CPSC 404", "CPSC 406", "CPSC 410", "CPSC 411",
    "CPSC 412", "CPSC 415", "CPSC 416", "CPSC 418", "CPSC 420",
    "CPSC 421", "CPSC 422", "CPSC 425", "CPSC 426", "CPSC 427",
    "CPSC 430", "CPSC 436", "CPSC 437", "CPSC 440", "CPSC 444",
    "CPSC 445", "CPSC 447", "CPSC 448", "CPSC 449", "CPSC 450",
    "MATH 100", "MATH 101", "MATH 102", "MATH 104", "MATH 105",
    "MATH 200", "MATH 215", "MATH 217", "MATH 220", "MATH 221",
    "MATH 223", "MATH 226", "MATH 227", "MATH 253", "MATH 256",
    "MATH 257", "MATH 258", "MATH 264", "MATH 267", "MATH 300",
    "MATH 301", "MATH 302", "MATH 303", "MATH 307", "MATH 308",
    "MATH 309", "MATH 312", "MATH 316", "MATH 317", "MATH 318",
    "MATH 319", "MATH 320", "MATH 321", "MATH 322", "MATH 323",
    "MATH 331", "MATH 335", "MATH 340", "MATH 341", "MATH 342",
    "MATH 345", "MATH 346", "MATH 400", "MATH 401",
    "PHYS 101", "PHYS 102", "PHYS 105", "PHYS 106", "PHYS 200",
    "PHYS 201", "PHYS 203", "PHYS 206", "PHYS 209", "PHYS 210",
    "PHYS 211", "PHYS 215", "PHYS 216", "PHYS 229", "PHYS 230",
    "PHYS 231", "PHYS 232", "PHYS 250", "PHYS 251",
    "ECON 101", "ECON 102", "ECON 200", "ECON 201", "ECON 202",
    "ECON 205", "ECON 206", "ECON 207", "ECON 210", "ECON 211",
    "ECON 220", "ECON 221", "ECON 222", "ECON 224", "ECON 225",
    "ECON 226", "ECON 227", "ECON 228", "ECON 234", "ECON 235",
    "ECON 236", "ECON 237", "ECON 238", "ECON 240",
    "ECON 301", "ECON 302", "ECON 303", "ECON 304", "ECON 305",
    "ECON 306", "ECON 307", "ECON 308", "ECON 309", "ECON 310",
    "ECON 311", "ECON 312", "ECON 313", "ECON 314", "ECON 315",
    "ECON 316", "ECON 317", "ECON 318", "ECON 319",
    "ECON 320", "ECON 321", "ECON 322", "ECON 323", "ECON 324",
    "ECON 325", "ECON 326", "ECON 327", "ECON 328",
    "STAT 200", "STAT 201", "STAT 203", "STAT 241", "STAT 251",
    "STAT 300", "STAT 301", "STAT 302", "STAT 305", "STAT 306",
    "STAT 321", "STAT 344", "STAT 404", "STAT 406", "STAT 443",
    "STAT 447", "STAT 450", "STAT 460", "STAT 461",
], [""], extra_queries=[
    "UBC full course", "University of British Columbia lecture",
    "UBC course playlist",
]),

_add("Waterloo", "University of Waterloo", [
    "CS 135", "CS 136", "CS 240", "CS 241", "CS 245", "CS 246",
    "CS 251", "CS 341", "CS 343", "CS 348", "CS 349", "CS 350",
    "CS 354", "CS 360", "CS 365", "CS 370", "CS 371", "CS 442",
    "CS 444", "CS 445", "CS 446", "CS 447", "CS 448", "CS 449",
    "CS 450", "CS 451", "CS 452", "CS 454", "CS 456", "CS 457",
    "CS 458", "CS 462", "CS 463", "CS 464", "CS 465", "CS 466",
    "CS 467", "CS 468", "CS 469", "CS 470", "CS 471", "CS 472",
    "CS 473", "CS 474", "CS 475", "CS 476", "CS 477", "CS 478",
    "CS 479", "CS 480", "CS 481", "CS 482", "CS 483", "CS 484",
    "CS 485", "CS 486", "CS 487", "CS 488", "CS 489", "CS 490",
    "CS 491", "CS 492", "CS 493", "CS 494", "CS 495",
    "MATH 135", "MATH 136", "MATH 137", "MATH 138", "MATH 145",
    "MATH 146", "MATH 147", "MATH 148", "MATH 207", "MATH 208",
    "MATH 209", "MATH 211", "MATH 213", "MATH 215", "MATH 217",
    "MATH 225", "MATH 227", "MATH 229", "MATH 231", "MATH 233",
    "MATH 235", "MATH 237", "MATH 239", "MATH 245", "MATH 247",
    "MATH 249", "MATH 601", "MATH 602", "MATH 603", "MATH 604",
    "MATH 605", "MATH 606", "MATH 607", "MATH 608", "MATH 609",
    "MATH 610", "MATH 611", "MATH 612", "MATH 613", "MATH 614",
    "MATH 615", "MATH 616", "MATH 617",
    "PHYS 111", "PHYS 112", "PHYS 121", "PHYS 122", "PHYS 124",
    "PHYS 125", "PHYS 175", "PHYS 222", "PHYS 223", "PHYS 224",
    "PHYS 225", "PHYS 226", "PHYS 234", "PHYS 235", "PHYS 236",
    "PHYS 237", "PHYS 238", "PHYS 239", "PHYS 241", "PHYS 242",
    "PHYS 256", "PHYS 258", "PHYS 260", "PHYS 263", "PHYS 270",
    "PHYS 275", "PHYS 280",
    "PHYS 334", "PHYS 335", "PHYS 336", "PHYS 337", "PHYS 338",
    "PHYS 339", "PHYS 341", "PHYS 342", "PHYS 352", "PHYS 353",
    "PHYS 354", "PHYS 355", "PHYS 356", "PHYS 357", "PHYS 358",
    "PHYS 359", "PHYS 360",
    "PHYS 434", "PHYS 435", "PHYS 436", "PHYS 437", "PHYS 438",
    "PHYS 439", "PHYS 441", "PHYS 442", "PHYS 443", "PHYS 444",
    "PHYS 445", "PHYS 446", "PHYS 447", "PHYS 448", "PHYS 449",
    "PHYS 450", "PHYS 451", "PHYS 452",
    "PHYS 454", "PHYS 455", "PHYS 456", "PHYS 457",
    "PHYS 460", "PHYS 461", "PHYS 462", "PHYS 463",
    "PHYS 467", "PHYS 468", "PHYS 470", "PHYS 471",
    "PHYS 472", "PHYS 473", "PHYS 474", "PHYS 475",
    "PHYS 476", "PHYS 477", "PHYS 478", "PHYS 479",
    "PHYS 480", "PHYS 481", "PHYS 482", "PHYS 483",
    "PHYS 484", "PHYS 485", "PHYS 486", "PHYS 487",
    "PHYS 488", "PHYS 489", "PHYS 490", "PHYS 491",
    "PHYS 492", "PHYS 493", "PHYS 494", "PHYS 495",
    "PHYS 496", "PHYS 497", "PHYS 498", "PHYS 499",
    "ECON 101", "ECON 102", "ECON 201", "ECON 202",
    "ECON 206", "ECON 211", "ECON 221", "ECON 231",
    "ECON 241", "ECON 251", "ECON 255", "ECON 261",
    "ECON 271", "ECON 281", "ECON 290",
    "ECON 301", "ECON 302", "ECON 311", "ECON 312",
    "ECON 321", "ECON 322", "ECON 331", "ECON 332",
    "ECON 341", "ECON 342", "ECON 351", "ECON 352",
    "ECON 355", "ECON 361", "ECON 362", "ECON 371",
    "ECON 372", "ECON 381", "ECON 382", "ECON 391",
    "ECON 392", "ECON 393", "ECON 401", "ECON 402",
    "ECON 404", "ECON 405", "ECON 406", "ECON 407",
    "ECON 408", "ECON 409", "ECON 410", "ECON 411",
    "ECON 412", "ECON 413", "ECON 414", "ECON 415",
    "ECON 416", "ECON 417", "ECON 418", "ECON 419",
    "ECON 420", "ECON 421", "ECON 422", "ECON 423",
    "ECON 424", "ECON 425", "ECON 426", "ECON 427",
    "ECON 428", "ECON 429", "ECON 430", "ECON 431",
    "ECON 432", "ECON 433", "ECON 434", "ECON 435",
    "ECON 436", "ECON 437", "ECON 438", "ECON 439",
    "ECON 440", "ECON 441", "ECON 442", "ECON 443",
    "ECON 444", "ECON 445", "ECON 446", "ECON 447",
    "ECON 448", "ECON 449", "ECON 450", "ECON 451",
    "ECON 452", "ECON 453", "ECON 454", "ECON 455",
    "ECON 456", "ECON 457", "ECON 458", "ECON 459",
    "ECON 460", "ECON 461", "ECON 462", "ECON 463",
    "ECON 464", "ECON 465", "ECON 466", "ECON 467",
    "ECON 468", "ECON 469", "ECON 470", "ECON 471",
    "ECON 472", "ECON 473", "ECON 474", "ECON 475",
    "ECON 476", "ECON 477", "ECON 478",
    "STAT 220", "STAT 221", "STAT 224", "STAT 225",
    "STAT 230", "STAT 231", "STAT 240", "STAT 241",
    "STAT 330", "STAT 331", "STAT 332", "STAT 333",
    "STAT 334", "STAT 335", "STAT 336", "STAT 337",
    "STAT 338", "STAT 339", "STAT 340", "STAT 341",
    "STAT 342", "STAT 343", "STAT 344", "STAT 430",
    "STAT 431", "STAT 432", "STAT 433", "STAT 434",
    "STAT 435", "STAT 436", "STAT 437", "STAT 438",
    "STAT 439", "STAT 440", "STAT 441", "STAT 442",
    "STAT 443", "STAT 444", "STAT 445", "STAT 446",
    "STAT 447", "STAT 448", "STAT 449", "STAT 450",
    "STAT 451", "STAT 452", "STAT 453", "STAT 454",
], [""], extra_queries=[
    "Waterloo full course", "University of Waterloo lecture",
    "Waterloo course playlist",
]),

_add("McGill", "McGill", [
    "COMP 202", "COMP 206", "COMP 250", "COMP 251", "COMP 273",
    "COMP 302", "COMP 303", "COMP 310", "COMP 322", "COMP 330",
    "COMP 350", "COMP 360", "COMP 361", "COMP 362", "COMP 370",
    "COMP 409", "COMP 417", "COMP 421", "COMP 424", "COMP 462",
    "MATH 133", "MATH 140", "MATH 141", "MATH 222", "MATH 223",
    "MATH 235", "MATH 240", "MATH 242", "MATH 243", "MATH 247",
    "MATH 248", "MATH 249", "MATH 251", "MATH 262", "MATH 263",
    "MATH 264", "MATH 271", "MATH 308", "MATH 314", "MATH 315",
    "MATH 316", "MATH 317", "MATH 318", "MATH 319", "MATH 323",
    "MATH 324", "MATH 325", "MATH 326", "MATH 327", "MATH 329",
    "MATH 335", "MATH 338", "MATH 340", "MATH 346", "MATH 348",
    "MATH 352", "MATH 354", "MATH 356", "MATH 357", "MATH 358",
    "PHYS 101", "PHYS 102", "PHYS 131", "PHYS 142",
    "PHYS 180", "PHYS 181", "PHYS 182", "PHYS 183",
    "PHYS 184", "PHYS 186", "PHYS 214", "PHYS 224",
    "PHYS 225", "PHYS 226", "PHYS 228", "PHYS 230",
    "PHYS 231", "PHYS 232", "PHYS 241", "PHYS 242",
    "PHYS 250", "PHYS 251", "PHYS 257", "PHYS 258",
    "PHYS 260", "PHYS 271", "PHYS 328", "PHYS 329",
    "PHYS 331", "PHYS 332", "PHYS 333", "PHYS 334",
    "PHYS 335", "PHYS 339", "PHYS 340", "PHYS 342",
    "PHYS 346", "PHYS 350", "PHYS 351", "PHYS 352",
    "PHYS 357", "PHYS 358", "PHYS 359", "PHYS 362",
    "PHYS 404", "PHYS 408", "PHYS 410", "PHYS 413",
    "PHYS 428", "PHYS 432", "PHYS 434", "PHYS 439",
    "PHYS 442", "PHYS 446", "PHYS 447", "PHYS 449",
    "PHYS 451", "PHYS 454", "PHYS 455", "PHYS 456",
    "PHYS 457", "PHYS 459", "PHYS 469", "PHYS 479",
    "PHYS 489",
    "ECON 208", "ECON 209", "ECON 227", "ECON 230",
    "ECON 250", "ECON 257", "ECON 275", "ECON 295",
    "ECON 302", "ECON 303", "ECON 304", "ECON 305",
    "ECON 306", "ECON 307", "ECON 308", "ECON 309",
    "ECON 310", "ECON 311", "ECON 312", "ECON 313",
    "ECON 314", "ECON 316", "ECON 317", "ECON 319",
    "ECON 326", "ECON 327", "ECON 328", "ECON 329",
    "ECON 330", "ECON 331", "ECON 332", "ECON 333",
    "ECON 334", "ECON 335", "ECON 336", "ECON 337",
    "ECON 338", "ECON 339", "ECON 340", "ECON 341",
    "ECON 342", "ECON 343", "ECON 344", "ECON 345",
    "ECON 346", "ECON 347", "ECON 348", "ECON 349",
    "ECON 350", "ECON 351", "ECON 352", "ECON 408",
    "ECON 409", "ECON 411", "ECON 416", "ECON 420",
    "ECON 423", "ECON 424", "ECON 425", "ECON 426",
    "ECON 427", "ECON 428", "ECON 429", "ECON 430",
    "ECON 434", "ECON 435", "ECON 436", "ECON 437",
    "ECON 438", "ECON 440", "ECON 441", "ECON 442",
    "ECON 443", "ECON 444", "ECON 445",
    "ECON 446", "ECON 447", "ECON 448", "ECON 449",
    "ECON 450", "ECON 451", "ECON 452", "ECON 456",
    "ECON 460", "ECON 461", "ECON 462", "ECON 463",
    "ECON 464", "ECON 465", "ECON 466", "ECON 467",
    "ECON 468", "ECON 469",
], [""], extra_queries=[
    "McGill full course", "McGill University lecture",
    "McGill course playlist",
]),

# ── Additional Schools (just extra queries, no course codes needed) ────
_add("UMich", "University of Michigan", [], [""], extra_queries=[
    "University of Michigan full course", "Michigan lecture series",
    "UMich course playlist", "Michigan EECS lecture",
]),
_add("UT Austin", "UT Austin", [], [""], extra_queries=[
    "UT Austin full course", "University of Texas lecture series",
    "UT Austin course playlist", "UT CS lecture",
]),
_add("UCLA", "UCLA", [], [""], extra_queries=[
    "UCLA full course", "UCLA lecture series", "UCLA course playlist",
]),
_add("UCSD", "UC San Diego", [], [""], extra_queries=[
    "UCSD full course", "UC San Diego lecture series",
    "UCSD course playlist", "UCSD CSE lecture",
]),
_add("UIUC", "UIUC", [], [""], extra_queries=[
    "UIUC full course", "University of Illinois lecture series",
    "UIUC course playlist", "UIUC CS lecture",
]),
_add("Purdue", "Purdue", [], [""], extra_queries=[
    "Purdue full course", "Purdue University lecture series",
    "Purdue course playlist",
]),
_add("NYU", "NYU", [], [""], extra_queries=[
    "NYU full course", "New York University lecture series",
    "NYU course playlist", "NYU CS lecture",
]),
_add("ETH Zurich", "ETH Zurich", [], [""], extra_queries=[
    "ETH Zurich full course", "ETH lecture series",
    "ETH course playlist", "ETH computer science lecture",
]),
_add("EPFL", "EPFL", [], [""], extra_queries=[
    "EPFL full course", "EPFL lecture series", "EPFL course playlist",
]),
_add("NUS", "NUS", [], [""], extra_queries=[
    "NUS full course", "National University of Singapore lecture",
    "NUS course playlist",
]),
_add("UNSW", "UNSW", [], [""], extra_queries=[
    "UNSW full course", "UNSW lecture series",
    "University of New South Wales course",
]),
_add("Melbourne", "University of Melbourne", [], [""], extra_queries=[
    "University of Melbourne full course", "Melbourne lecture series",
    "Unimelb course playlist",
]),

# ═══════════════════════════════════════════════════════════════════════════
# YouTube scraping (same approach as discover_missing_courses.py)
# ═══════════════════════════════════════════════════════════════════════════

EXCLUDE_WORDS = {
    "commencement", "graduation", "ceremony", "convocation", "orientation",
    "alumni", "reunion", "homecoming", "sports", "athletics",
    "trailer", "teaser", "podcast", "conference", "workshop",
    "symposium", "student life", "highlights", "shorts", "#short",
    "interview", "promo", "admissions", "testimonial", "recap",
    "vlog", "routine", "day in the life",
}
MIN_VIDEOS = 6
MAX_VIDEOS = 300


def extract_playlist_ids(html):
    """Parse ytInitialData from YouTube search HTML to find playlist IDs."""
    ids = set()
    for pattern in [
        r'ytInitialData\s*=\s*(\{.*?\});\s*</script>',
        r'ytInitialData\s*=\s*(\{.*?\});',
        r'var ytInitialData\s*=\s*(\{.*?\});',
    ]:
        m = re.search(pattern, html, re.DOTALL)
        if m:
            break
    if not m:
        return ids
    try:
        data = json.loads(m.group(1))
    except Exception:
        return ids

    def walk(obj):
        if isinstance(obj, dict):
            if "playlistId" in obj:
                pid = obj["playlistId"]
                if len(pid) > 20:
                    ids.add(pid)
            for v in obj.values():
                walk(v)
        elif isinstance(obj, list):
            for x in obj:
                walk(x)
    walk(data)
    return ids


def get_playlist_details(playlist_id):
    """Get playlist metadata via yt-dlp."""
    try:
        result = subprocess.run(
            ["yt-dlp",
             "https://www.youtube.com/playlist?list={}".format(playlist_id),
             "--dump-json", "--flat-playlist", "--no-warnings",
             "--extractor-args", "youtube:skip=authcheck"],
            capture_output=True, text=True, timeout=20,
        )
        lines = [l for l in result.stdout.strip().split("\n") if l]
        if not lines:
            return None
        data = json.loads(lines[0])
        count = data.get("playlist_count", len(lines))
        title = (data.get("playlist_title") or data.get("title") or "")
        channel = (data.get("playlist_channel") or
                   data.get("playlist_uploader") or
                   data.get("channel") or data.get("uploader") or "")
        desc = data.get("description", "") or ""
        thumb = None
        if data.get("thumbnails"):
            thumb = data["thumbnails"][-1].get("url")
        return {
            "title": title, "channel": channel,
            "description": desc, "video_count": count,
            "thumbnail": thumb,
        }
    except Exception:
        return None


def search_playlists_for_query(query, seen_ids):
    """Scrape YouTube search for a single query, return new playlist results."""
    qs = urllib.parse.quote_plus(query)
    url = "https://www.youtube.com/results?search_query={}".format(qs)
    req = urllib.request.Request(url, headers={
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "Accept-Language": "en-US,en;q=0.9",
    })
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            html = resp.read().decode("utf-8", errors="replace")
    except Exception:
        return []

    pids = extract_playlist_ids(html)
    results = []
    for pid in pids:
        if pid in seen_ids:
            continue
        seen_ids.add(pid)
        details = get_playlist_details(pid)
        if not details or not details.get("title"):
            continue
        if details["video_count"] < MIN_VIDEOS:
            continue
        if details["video_count"] > MAX_VIDEOS:
            continue

        t = details["title"].lower()
        if any(w in t for w in EXCLUDE_WORDS):
            continue

        results.append({
            "playlist_id": pid,
            "url": "https://www.youtube.com/playlist?list={}".format(pid),
            **details,
        })
        time.sleep(0.3)
    return results


# ═══════════════════════════════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════════════════════════════

def main():
    mode = "sample"
    target_school = None

    args = sys.argv[1:]
    i = 0
    while i < len(args):
        if args[i] == "--mode" and i + 1 < len(args):
            mode = args[i + 1]; i += 2
        elif args[i] == "--school" and i + 1 < len(args):
            target_school = args[i + 1]; i += 2
        else:
            i += 1

    # Filter schools
    schools = list(UNIVERSITY_PATTERNS.items())
    if target_school:
        schools = [(k, v) for k, v in schools
                   if target_school.lower() in k.lower()
                   or target_school.lower() in v["name"].lower()]
        if not schools:
            print("School '{}' not found. Available:".format(target_school))
            for key in UNIVERSITY_PATTERNS:
                print("  {}: {}".format(key, UNIVERSITY_PATTERNS[key]["name"]))
            return
        print("Targeting: {}".format(
            ", ".join("{} ({})".format(k, v["name"]) for k, v in schools)))

    # Load existing playlist IDs
    existing_pids = set()
    try:
        conn = psycopg2.connect(DB_URL, connect_timeout=10, sslmode="require")
        cur = conn.cursor()
        cur.execute(
            "SELECT youtube_playlist_id FROM courses "
            "WHERE youtube_playlist_id IS NOT NULL"
        )
        for (pid,) in cur.fetchall():
            if pid:
                existing_pids.add(pid)
        cur.close(); conn.close()
    except Exception as e:
        print("DB load failed: {}".format(e))
    print("Existing playlists in DB: {}".format(len(existing_pids)))

    all_discoveries = OrderedDict()
    seen = set(existing_pids)  # start with existing to skip them

    for key, uni in schools:
        name = uni["name"]
        depts = uni["depts"]
        extra = uni["extra"]

        if mode == "sample" and depts:
            # Use just a few codes for testing
            sample_depts = depts[:15]
        else:
            sample_depts = depts

        print("\n=== {} ({} codes + {} extra queries) ===".format(
            name, len(sample_depts), len(extra)))

        uni_discoveries = []

        # Search by course code
        for ci, code in enumerate(sample_depts):
            print("  [{}/{}] {}...".format(ci + 1, len(sample_depts), code),
                  end=" ", flush=True)
            queries = [
                '"{}" full course'.format(code),
                '"{}" lecture series'.format(code),
                '"{}" course playlist'.format(code),
            ]
            code_results = 0
            for query in queries:
                results = search_playlists_for_query(query, seen)
                for r in results:
                    r["search_query"] = query
                    r["university"] = name
                uni_discoveries.extend(results)
                code_results += len(results)
                time.sleep(1.0)
            print("+{}".format(code_results) if code_results else "-",
                  flush=True)

        # Search extra queries (generic university searches)
        for query in extra:
            results = search_playlists_for_query(query, seen)
            for r in results:
                r["search_query"] = query
                r["university"] = name
            uni_discoveries.extend(results)
            time.sleep(0.8)

        if uni_discoveries:
            all_discoveries[key] = uni_discoveries
            print("  Found: {} new playlists".format(len(uni_discoveries)))
            # Show a few
            for d in uni_discoveries[:5]:
                try:
                    print("    [{} vids] {} — {}".format(
                        d["video_count"], d["title"][:70], d["channel"]))
                except UnicodeEncodeError:
                    print("    [{} vids] (title with emoji)".format(
                        d["video_count"]))
        else:
            print("  No new playlists found")

        # Auto-save after each school (protects against crashes)
        _save_results(all_discoveries)

        # No limit — scan all schools

    # ── Final save ─────────────────────────────────────────────────────
    _save_results(all_discoveries)
    total = sum(len(v) for v in all_discoveries.values())
    print("\n" + "=" * 60)
    print("Final: {} discoveries across {} schools".format(
        total, len(all_discoveries)))
    for key, items in all_discoveries.items():
        print("  {}: {}".format(UNIVERSITY_PATTERNS[key]["name"], len(items)))


def _save_results(all_discoveries):
    """Save JSON and generate HTML review page."""
    out = os.path.join(
        os.path.dirname(__file__), "..", "course_code_discoveries.json"
    )
    with open(out, "w") as f:
        json.dump(
            {k: v for k, v in all_discoveries.items()},
            f, indent=2,
        )
    html_out = os.path.join(
        os.path.dirname(__file__), "..", "course_code_review.html"
    )
    _write_review_html(all_discoveries, html_out)


def _write_review_html(all_discoveries, html_path):
    """Generate an HTML review page for inspecting discovery quality."""
    import html as html_mod

    rows = ""
    total = 0
    for key, items in all_discoveries.items():
        school = UNIVERSITY_PATTERNS[key]["name"]
        for d in items:
            total += 1
            thumb_html = ""
            if d.get("thumbnail"):
                thumb_html = '<img src="{}" loading="lazy">'.format(
                    html_mod.escape(d["thumbnail"]))
            rows += """<tr>
                <td class="thumb">{thumb}</td>
                <td class="title"><a href="{url}" target="_blank">{title}</a></td>
                <td class="chan">{chan}</td>
                <td class="school">{school}</td>
                <td class="n">{vids}</td>
            </tr>""".format(
                thumb=thumb_html,
                url=html_mod.escape(d.get("url", "")),
                title=html_mod.escape(d.get("title", "")[:120]),
                chan=html_mod.escape(d.get("channel", "")[:60]),
                school=html_mod.escape(school),
                vids=d.get("video_count", "?"),
            )

    html = """<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<title>Course Code Discoveries ({total} new)</title>
<style>
*{{box-sizing:border-box;margin:0;padding:0}}
body{{background:#0d1117;color:#c9d1d9;font-family:system-ui;padding:2rem}}
h1{{font-size:1.6rem;font-weight:700;color:#f0f6fc;margin-bottom:.25rem}}
.summary{{color:#8b949e;margin-bottom:2rem}} .green{{color:#3fb950}}
table{{width:100%;border-collapse:collapse;font-size:13px}}
th{{text-align:left;padding:10px 12px;border-bottom:2px solid #30363d;color:#8b949e;font-size:11px;font-weight:600;text-transform:uppercase;background:#161b22;position:sticky;top:0;z-index:1}}
td{{padding:10px 12px;border-bottom:1px solid #21262d;vertical-align:middle}}
tr:hover td{{background:#1c2128}}
.thumb{{width:130px}} .thumb img{{width:120px;height:68px;object-fit:cover;border-radius:6px;border:1px solid #30363d}}
.title{{max-width:500px}} .title a{{color:#58a6ff;text-decoration:none;font-weight:500}} .title a:hover{{text-decoration:underline}}
.chan{{color:#8b949e;font-size:12px;max-width:200px}}
.school{{color:#8b949e;font-size:12px;max-width:180px}}
.n{{text-align:center;font-weight:600;color:#f0f6fc}}
</style></head><body>
<h1>Course Code Discoveries</h1>
<p class="summary"><b class="green">{total} new playlists</b> across {schools} schools &middot;
   not in database &middot; filtered by 6-300 videos, no excluded words</p>
<table><thead><tr>
<th class="thumb">Thumb</th><th>Title</th><th>Channel</th><th>School</th><th class="n">Videos</th>
</tr></thead><tbody>{rows}</tbody></table>
</body></html>""".format(
        total=total,
        schools=len(all_discoveries),
        rows=rows,
    )

    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html)


if __name__ == "__main__":
    main()
