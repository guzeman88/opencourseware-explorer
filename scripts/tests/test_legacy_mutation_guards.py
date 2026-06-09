import os
import subprocess
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = (
    "_add_silence_col.py",
    "cleanup_false_positives.py",
    "fix_labels_and_publish.py",
    "remove_nptel.py",
    "tag_courses.py",
    "tag_courses_prod.py",
)


def run_script(script: str, *args: str) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["DATABASE_URL"] = "postgresql://127.0.0.1:1/invalid"
    return subprocess.run(
        [sys.executable, str(ROOT / "scraper" / script), *args],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
        timeout=15,
        check=False,
    )


@pytest.mark.parametrize("script", SCRIPTS)
def test_help_does_not_connect(script: str) -> None:
    result = run_script(script, "--help")

    assert result.returncode == 0
    assert "--apply" in result.stdout
    assert "connection" not in result.stderr.lower()


@pytest.mark.parametrize("script", SCRIPTS)
def test_no_arguments_refuse_before_connecting(script: str) -> None:
    result = run_script(script)

    assert result.returncode != 0
    assert "Refusing to mutate a database without --apply" in result.stderr
    assert "connection" not in result.stderr.lower()
