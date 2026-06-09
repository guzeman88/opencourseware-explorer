import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scraper" / "verify_and_fix_video_courses.py"


def run_script(*args: str) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["DATABASE_URL"] = "postgresql://127.0.0.1:1/invalid"
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
    assert "connection" not in result.stderr.lower()


def test_no_arguments_refuses_before_connecting() -> None:
    result = run_script()

    assert result.returncode != 0
    assert "Refusing to mutate a database without --apply" in result.stderr
    assert "connection" not in result.stderr.lower()
