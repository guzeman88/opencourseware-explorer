import pytest

from scripts.restore_logical_backup import ensure_safe_target


def test_restore_refuses_remote_target_by_default():
    with pytest.raises(SystemExit, match="Refusing non-local restore target"):
        ensure_safe_target("postgresql://user:pass@example.com/db", allow_remote=False)


def test_restore_allows_local_target():
    ensure_safe_target("postgresql://user:pass@127.0.0.1:5433/db", allow_remote=False)
