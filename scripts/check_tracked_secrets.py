"""Find credential-shaped secrets without printing their values."""

from __future__ import annotations

import argparse
import re
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
MAX_HISTORY_BLOB_BYTES = 10 * 1024 * 1024
PATTERNS = {
    "Google API key": re.compile(r"AIza[0-9A-Za-z_-]{20,}"),
    "credentialed PostgreSQL URL": re.compile(
        r"postgres(?:ql)?://([^:\s/]+):([^@\s/]+)@([^\s\"']+)"
    ),
    "Netlify build hook": re.compile(r"https://api\.netlify\.com/build_hooks/[0-9A-Za-z_-]+"),
    "Vercel deploy hook": re.compile(
        r"https://api\.vercel\.com/v1/integrations/deploy/[0-9A-Za-z_/-]+"
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


def tracked_files(include_untracked: bool = False) -> list[Path]:
    args = ["git", "ls-files", "-z"]
    if include_untracked:
        args.extend(["--cached", "--others", "--exclude-standard"])
    output = subprocess.check_output(
        args, cwd=ROOT
    ).decode("utf-8", errors="replace")
    return [ROOT / item for item in output.split("\0") if item]


def findings_for_text(text: str, location: str) -> list[str]:
    findings: list[str] = []
    for name, pattern in PATTERNS.items():
        for match in pattern.finditer(text):
            if name == "credentialed PostgreSQL URL":
                password = match.group(2).lower()
                host = match.group(3).split("?", 1)[0].lower()
                if password in ALLOWED_VALUES or host in ALLOWED_HOSTS:
                    continue
            line = text.count("\n", 0, match.start()) + 1
            findings.append(f"{location}:{line}: {name}")
    return findings


def scan_files(paths: list[Path]) -> list[str]:
    findings: list[str] = []
    for path in paths:
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        findings.extend(findings_for_text(text, str(path.relative_to(ROOT))))
    return findings


def history_objects() -> list[tuple[str, str]]:
    output = subprocess.check_output(
        ["git", "rev-list", "--objects", "--all"], cwd=ROOT, text=True
    )
    objects: list[tuple[str, str]] = []
    seen: set[str] = set()
    for line in output.splitlines():
        sha, _, path = line.partition(" ")
        if not path or sha in seen:
            continue
        seen.add(sha)
        objects.append((sha, path))
    return objects


def scan_history() -> list[str]:
    findings: list[str] = []
    objects = history_objects()
    process = subprocess.Popen(
        ["git", "cat-file", "--batch"],
        cwd=ROOT,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
    )
    assert process.stdin is not None
    assert process.stdout is not None
    try:
        for sha, path in objects:
            process.stdin.write(f"{sha}\n".encode())
            process.stdin.flush()
            header = process.stdout.readline().decode("utf-8", errors="replace").strip()
            parts = header.split()
            if len(parts) != 3:
                continue
            size = int(parts[2])
            payload = process.stdout.read(size)
            process.stdout.read(1)
            if parts[1] != "blob" or size > MAX_HISTORY_BLOB_BYTES:
                continue
            try:
                text = payload.decode("utf-8")
            except UnicodeDecodeError:
                continue
            findings.extend(findings_for_text(text, f"history:{sha[:12]}:{path}"))
    finally:
        process.stdin.close()
        process.wait(timeout=30)
    return findings


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--working-tree",
        action="store_true",
        help="include untracked, non-ignored working-tree files",
    )
    parser.add_argument(
        "--history",
        action="store_true",
        help="scan unique Git-history blobs up to 10 MiB",
    )
    args = parser.parse_args()

    findings = scan_files(tracked_files(include_untracked=args.working_tree))
    if args.history:
        findings.extend(scan_history())

    if findings:
        print("Credential-shaped values found:")
        for finding in findings:
            print(f"  {finding}")
        return 1
    scope = "tracked files"
    if args.working_tree:
        scope = "tracked and untracked non-ignored files"
    if args.history:
        scope += " plus Git history"
    print(f"No credential-shaped values found in {scope}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
