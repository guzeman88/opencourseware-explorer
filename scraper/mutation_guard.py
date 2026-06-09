"""Shared safety gate for legacy database-mutating maintenance scripts."""

from __future__ import annotations

import argparse
import os


def require_explicit_apply(
    description: str,
    *,
    require_delete_confirmation: bool = False,
) -> str:
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument("--apply", action="store_true", help="perform database mutations")
    if require_delete_confirmation:
        parser.add_argument(
            "--allow-delete",
            action="store_true",
            help="confirm that permanent deletion is intended",
        )
    args = parser.parse_args()

    if not args.apply:
        raise SystemExit(
            "Refusing to mutate a database without --apply. "
            "Create a verified backup and set DATABASE_URL explicitly first."
        )
    if require_delete_confirmation and not args.allow_delete:
        raise SystemExit("Refusing permanent deletion without --allow-delete.")

    database_url = os.environ.get("DATABASE_URL", "")
    if not database_url:
        raise SystemExit("DATABASE_URL is required for --apply.")
    return database_url

