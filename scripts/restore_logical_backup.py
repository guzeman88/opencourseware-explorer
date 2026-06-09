"""Restore a Commons JSONL backup into an isolated PostgreSQL database."""

from __future__ import annotations

import argparse
import json
import sys
import zipfile
from pathlib import Path
from urllib.parse import urlsplit

import psycopg
from psycopg import sql
from psycopg.types.json import Jsonb

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.audit_catalog_integrity import decode_copy_text_line, psycopg_url  # noqa: E402


RESTORE_ORDER = (
    "universities",
    "departments",
    "subjects",
    "users",
    "courses",
    "videos",
    "course_subjects",
    "scraper_jobs",
    "user_library_courses",
    "user_watch_history",
)
LOCAL_HOSTS = {"localhost", "127.0.0.1", "::1"}


def ensure_safe_target(database_url: str, allow_remote: bool) -> None:
    host = urlsplit(psycopg_url(database_url)).hostname
    if not allow_remote and host not in LOCAL_HOSTS:
        raise SystemExit(
            f"Refusing non-local restore target {host!r}. "
            "Use --allow-remote only for an explicitly isolated database."
        )


def target_columns(conn, table: str) -> set[str]:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT column_name
            FROM information_schema.columns
            WHERE table_schema = 'public' AND table_name = %s
            """,
            (table,),
        )
        return {row[0] for row in cur.fetchall()}


def ensure_empty_target(conn) -> None:
    nonempty: list[str] = []
    with conn.cursor() as cur:
        for table in RESTORE_ORDER:
            cur.execute(
                """
                SELECT EXISTS (
                  SELECT 1 FROM information_schema.tables
                  WHERE table_schema = 'public' AND table_name = %s
                )
                """,
                (table,),
            )
            if not cur.fetchone()[0]:
                raise SystemExit(f"Target schema is missing required table {table!r}")
            cur.execute(sql.SQL("SELECT EXISTS (SELECT 1 FROM {} LIMIT 1)").format(sql.Identifier(table)))
            if cur.fetchone()[0]:
                nonempty.append(table)
    if nonempty:
        raise SystemExit(f"Refusing nonempty restore target; rows exist in: {', '.join(nonempty)}")


def adapt(value):
    return Jsonb(value) if isinstance(value, (dict, list)) else value


def restore_table(conn, archive: zipfile.ZipFile, table: str) -> int:
    path = f"tables/{table}.jsonl"
    if path not in archive.namelist():
        return 0
    rows: list[dict] = []
    with archive.open(path) as source:
        for line in source:
            rows.append(json.loads(decode_copy_text_line(line)))
    if not rows:
        return 0

    columns = [column for column in rows[0] if column in target_columns(conn, table)]
    statement = sql.SQL("INSERT INTO {} ({}) VALUES ({})").format(
        sql.Identifier(table),
        sql.SQL(", ").join(map(sql.Identifier, columns)),
        sql.SQL(", ").join(sql.Placeholder() for _ in columns),
    )
    with conn.cursor() as cur:
        cur.executemany(
            statement,
            [[adapt(row.get(column)) for column in columns] for row in rows],
        )
    return len(rows)


def validate_counts(conn, manifest: dict) -> dict[str, int]:
    counts: dict[str, int] = {}
    with conn.cursor() as cur:
        for table in RESTORE_ORDER:
            cur.execute(sql.SQL("SELECT COUNT(*) FROM {}").format(sql.Identifier(table)))
            actual = cur.fetchone()[0]
            expected = manifest["tables"].get(table, {}).get("rows", 0)
            if actual != expected:
                raise RuntimeError(f"{table}: restored {actual:,}, expected {expected:,}")
            counts[table] = actual

        orphan_checks = {
            "course_subjects": (
                "SELECT COUNT(*) FROM course_subjects cs "
                "LEFT JOIN courses c ON c.id = cs.course_id "
                "LEFT JOIN subjects s ON s.id = cs.subject_id "
                "WHERE c.id IS NULL OR s.id IS NULL"
            ),
            "videos": (
                "SELECT COUNT(*) FROM videos v LEFT JOIN courses c ON c.id = v.course_id "
                "WHERE c.id IS NULL"
            ),
            "library": (
                "SELECT COUNT(*) FROM user_library_courses l "
                "LEFT JOIN users u ON u.id = l.user_id "
                "LEFT JOIN courses c ON c.id = l.course_id "
                "WHERE u.id IS NULL OR c.id IS NULL"
            ),
            "watch_history": (
                "SELECT COUNT(*) FROM user_watch_history h "
                "LEFT JOIN users u ON u.id = h.user_id "
                "LEFT JOIN courses c ON c.id = h.course_id "
                "WHERE u.id IS NULL OR c.id IS NULL"
            ),
        }
        for name, query in orphan_checks.items():
            cur.execute(query)
            orphan_count = cur.fetchone()[0]
            if orphan_count:
                raise RuntimeError(f"{name}: found {orphan_count:,} orphan rows")
    return counts


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("backup", type=Path)
    parser.add_argument("--database-url", required=True)
    parser.add_argument("--allow-remote", action="store_true")
    args = parser.parse_args()
    ensure_safe_target(args.database_url, args.allow_remote)

    with zipfile.ZipFile(args.backup) as archive:
        manifest = json.loads(archive.read("manifest.json"))
        with psycopg.connect(psycopg_url(args.database_url)) as conn:
            ensure_empty_target(conn)
            restored = {
                table: restore_table(conn, archive, table) for table in RESTORE_ORDER
            }
            counts = validate_counts(conn, manifest)
            conn.commit()

    print(f"Restored and verified {sum(restored.values()):,} rows.")
    for table, count in counts.items():
        print(f"{table}={count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
