"""Create and verify a read-only JSONL backup of every public PostgreSQL table."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import zipfile
from datetime import datetime, timezone
from pathlib import Path

import psycopg
from psycopg import sql


ROOT = Path(__file__).resolve().parent.parent


def normalize_url(url: str) -> str:
    return url.replace("postgresql+asyncpg://", "postgresql://").replace(
        "postgresql+psycopg://", "postgresql://"
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--database-url", default=os.getenv("DATABASE_URL", ""))
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if not args.database_url:
        parser.error("DATABASE_URL or --database-url is required")

    captured_at = datetime.now(timezone.utc)
    output = args.output or (
        ROOT
        / "preservation"
        / "private-backups"
        / f"commons-{captured_at.strftime('%Y-%m-%dT%H-%M-%SZ')}.zip"
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    manifest: dict = {"captured_at": captured_at.isoformat(), "tables": {}}

    with psycopg.connect(normalize_url(args.database_url), connect_timeout=20) as connection:
        connection.execute("SET TRANSACTION READ ONLY")
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
                ORDER BY table_name
                """
            )
            tables = [row[0] for row in cursor.fetchall()]

        with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            for table in tables:
                digest = hashlib.sha256()
                count = 0
                query = sql.SQL(
                    "COPY (SELECT row_to_json(t)::text FROM {} t) TO STDOUT"
                ).format(sql.Identifier(table))
                with connection.cursor().copy(query) as copy:
                    with archive.open(f"tables/{table}.jsonl", "w") as destination:
                        for chunk in copy:
                            data = bytes(chunk)
                            digest.update(data)
                            destination.write(data)
                            count += data.count(b"\n")
                manifest["tables"][table] = {
                    "rows": count,
                    "sha256": digest.hexdigest(),
                }
            archive.writestr("manifest.json", json.dumps(manifest, indent=2, sort_keys=True))
        connection.rollback()

    with zipfile.ZipFile(output, "r") as archive:
        saved = json.loads(archive.read("manifest.json"))
        for table, expected in saved["tables"].items():
            digest = hashlib.sha256()
            count = 0
            with archive.open(f"tables/{table}.jsonl") as source:
                for line in source:
                    digest.update(line)
                    count += 1
            if count != expected["rows"] or digest.hexdigest() != expected["sha256"]:
                raise RuntimeError(f"Backup verification failed for {table}")

    print(output)
    print(f"verified_tables={len(manifest['tables'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
