import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scraper" / "match_roadmap_entries.py"


def run_script(*args: str) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env.pop("DATABASE_URL", None)
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
        timeout=15,
        check=False,
    )


def test_help_does_not_connect() -> None:
    result = run_script("--help")

    assert result.returncode == 0
    assert "--apply" in result.stdout


def test_database_url_is_required() -> None:
    result = run_script()

    assert result.returncode != 0
    assert "DATABASE_URL is required" in result.stderr
