"""Fail when tracked working-tree files contain credential-shaped secrets."""

from __future__ import annotations

import re
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
PATTERNS = {
    "Google API key": re.compile(r"AIza[0-9A-Za-z_-]{20,}"),
    "credentialed PostgreSQL URL": re.compile(
        r"postgres(?:ql)?://([^:\s/]+):([^@\s/]+)@([^\s\"']+)"
    ),
}
ALLOWED_VALUES = {
    "password",
    "pass",
    "pw",
    "<password>",
    "<pw>",
    "ocwpass",
    "ocwpassword",
}
ALLOWED_HOSTS = {"localhost", "127.0.0.1", "db", "host", "host:port"}


def tracked_files() -> list[Path]:
    output = subprocess.check_output(
        ["git", "ls-files", "-z"], cwd=ROOT
    ).decode("utf-8", errors="replace")
    return [ROOT / item for item in output.split("\0") if item]


def main() -> int:
    findings: list[str] = []
    for path in tracked_files():
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        relative = path.relative_to(ROOT)
        for name, pattern in PATTERNS.items():
            for match in pattern.finditer(text):
                if name == "credentialed PostgreSQL URL":
                    password = match.group(2).lower()
                    host = match.group(3).split("?", 1)[0].lower()
                    if password in ALLOWED_VALUES or host in ALLOWED_HOSTS:
                        continue
                line = text.count("\n", 0, match.start()) + 1
                findings.append(f"{relative}:{line}: {name}")
    if findings:
        print("Credential-shaped values found in tracked files:")
        for finding in findings:
            print(f"  {finding}")
        return 1
    print("No credential-shaped values found in tracked files.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
