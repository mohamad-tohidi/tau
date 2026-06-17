from pathlib import Path

from tau_coding.paths import TauPaths
from tau_coding.session_manager import SessionManager


def test_session_manager_creates_and_lists_sessions(tmp_path: Path) -> None:
    manager = SessionManager(TauPaths(home=tmp_path / ".tau", agents_home=tmp_path / ".agents"))
    cwd = tmp_path / "project"
    cwd.mkdir()

    record = manager.create_session(cwd=cwd, model="fake", title="Test session")

    assert record.path.parent.parent == tmp_path / ".tau" / "sessions"
    assert record.path.name == f"{record.id}.jsonl"
    assert manager.get_session(record.id) == record
    assert manager.list_sessions() == [record]


def test_session_manager_gets_or_creates_default_session(tmp_path: Path) -> None:
    manager = SessionManager(TauPaths(home=tmp_path / ".tau", agents_home=tmp_path / ".agents"))
    cwd = tmp_path / "project"
    cwd.mkdir()

    first = manager.get_or_create_default_session(cwd=cwd, model="fake")
    second = manager.get_or_create_default_session(cwd=cwd, model="other")

    assert first == second
    assert first.id.startswith("default-")
    assert first.path.name == "default.jsonl"
    assert first.path.parent.exists()


def test_session_manager_touch_updates_metadata(tmp_path: Path) -> None:
    manager = SessionManager(TauPaths(home=tmp_path / ".tau", agents_home=tmp_path / ".agents"))
    cwd = tmp_path / "project"
    cwd.mkdir()
    record = manager.create_session(cwd=cwd, model="fake")

    updated = manager.touch_session(record.id, model="new-model", title="Updated")

    assert updated is not None
    assert updated.id == record.id
    assert updated.model == "new-model"
    assert updated.title == "Updated"
    assert updated.updated_at >= record.updated_at
    assert manager.get_session(record.id) == updated


def test_session_manager_sorts_newest_updated_first(tmp_path: Path) -> None:
    manager = SessionManager(TauPaths(home=tmp_path / ".tau", agents_home=tmp_path / ".agents"))
    cwd = tmp_path / "project"
    cwd.mkdir()
    older = manager.create_session(cwd=cwd, model="fake", session_id="older")
    newer = manager.create_session(cwd=cwd, model="fake", session_id="newer")
    manager.touch_session(older.id)

    sessions = manager.list_sessions()

    assert [session.id for session in sessions] == ["older", "newer"]
    assert newer in sessions
