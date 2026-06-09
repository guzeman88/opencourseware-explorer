import pytest

from scripts.reconcile_video_counters import ensure_safe_target


def test_remote_apply_requires_explicit_authorization() -> None:
    with pytest.raises(SystemExit, match="Refusing remote target"):
        ensure_safe_target("postgresql://user:pass@example.com/db", allow_remote=False)


def test_local_apply_target_is_allowed() -> None:
    ensure_safe_target("postgresql://user:pass@127.0.0.1:5433/db", allow_remote=False)
