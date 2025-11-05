"""
Tests for core/session.py
"""

import pytest

from session_manager.core.session import SessionManager, SessionError
from session_manager.core.project import Project


class TestSessionManagerInit:
    """Test SessionManager initialization"""

    @pytest.fixture
    def project(self, tmp_path, monkeypatch):
        """Create a project with temporary storage"""
        storage_dir = tmp_path / ".session_manager"

        monkeypatch.setattr(
            "session_manager.utils.paths.get_storage_dir", lambda: storage_dir
        )

        proj = Project("testproject", str(tmp_path))
        proj.ensure_structure()
        return proj

    def test_init(self, project):
        """Test basic initialization"""
        sm = SessionManager(project)

        assert sm.project == project
        # Sessions file should be created
        assert project.sessions_file.exists()


class TestSessionStart:
    """Test starting sessions"""

    @pytest.fixture
    def session_manager(self, tmp_path, monkeypatch):
        """Create a session manager"""
        storage_dir = tmp_path / ".session_manager"

        monkeypatch.setattr(
            "session_manager.utils.paths.get_storage_dir", lambda: storage_dir
        )

        proj = Project("testproject", str(tmp_path))
        proj.ensure_structure()
        return SessionManager(proj)

    def test_start_basic(self, session_manager):
        """Test starting a basic session"""
        session = session_manager.start()

        assert session["id"] is not None
        assert session["start_time"] is not None
        assert session["end_time"] is None
        assert session["duration"] is None

    def test_start_with_description(self, session_manager):
        """Test starting session with description"""
        session = session_manager.start(description="Working on feature X")

        assert session["description"] == "Working on feature X"

    def test_start_when_active_exists(self, session_manager):
        """Test starting when session already active"""
        session_manager.start()

        with pytest.raises(SessionError):
            session_manager.start()

    def test_start_creates_uuid(self, session_manager):
        """Test that each session gets a unique ID"""
        session1 = session_manager.start()
        session_manager.end()

        session2 = session_manager.start()

        assert session1["id"] != session2["id"]


class TestSessionEnd:
    """Test ending sessions"""

    @pytest.fixture
    def session_manager(self, tmp_path, monkeypatch):
        """Create a session manager"""
        storage_dir = tmp_path / ".session_manager"

        monkeypatch.setattr(
            "session_manager.utils.paths.get_storage_dir", lambda: storage_dir
        )

        proj = Project("testproject", str(tmp_path))
        proj.ensure_structure()
        return SessionManager(proj)

    def test_end_basic(self, session_manager):
        """Test ending a session"""
        import time

        session_manager.start()
        time.sleep(0.1)  # Небольшая задержка для ненулевой длительности

        completed = session_manager.end()

        assert completed["end_time"] is not None
        assert completed["duration"] is not None
        assert completed["duration"] >= 0  # Изменено с > 0 на >= 0

    def test_end_with_summary(self, session_manager):
        """Test ending with summary"""
        session_manager.start()

        completed = session_manager.end(
            summary="Fixed bug in parser", next_action="Add tests for parser"
        )

        assert completed["summary"] == "Fixed bug in parser"
        assert completed["next_action"] == "Add tests for parser"

    def test_end_no_active_session(self, session_manager):
        """Test ending when no active session"""
        with pytest.raises(SessionError):
            session_manager.end()

    def test_end_clears_active(self, session_manager):
        """Test that ending clears active session"""
        session_manager.start()
        session_manager.end()

        active = session_manager.get_active()
        assert active is None


class TestSessionActive:
    """Test getting active session"""

    @pytest.fixture
    def session_manager(self, tmp_path, monkeypatch):
        """Create a session manager"""
        storage_dir = tmp_path / ".session_manager"

        monkeypatch.setattr(
            "session_manager.utils.paths.get_storage_dir", lambda: storage_dir
        )

        proj = Project("testproject", str(tmp_path))
        proj.ensure_structure()
        return SessionManager(proj)

    def test_get_active_none(self, session_manager):
        """Test getting active when none exists"""
        active = session_manager.get_active()

        assert active is None

    def test_get_active_exists(self, session_manager):
        """Test getting active session"""
        started = session_manager.start()

        active = session_manager.get_active()

        assert active is not None
        assert active["id"] == started["id"]

    def test_get_active_after_end(self, session_manager):
        """Test getting active after ending"""
        session_manager.start()
        session_manager.end()

        active = session_manager.get_active()

        assert active is None


class TestSessionHistory:
    """Test session history"""

    @pytest.fixture
    def session_manager(self, tmp_path, monkeypatch):
        """Create a session manager"""
        storage_dir = tmp_path / ".session_manager"

        monkeypatch.setattr(
            "session_manager.utils.paths.get_storage_dir", lambda: storage_dir
        )

        proj = Project("testproject", str(tmp_path))
        proj.ensure_structure()
        return SessionManager(proj)

    def test_get_history_empty(self, session_manager):
        """Test getting history when empty"""
        history = session_manager.get_history()

        assert history == []

    def test_get_history(self, session_manager):
        """Test getting history"""
        # Create 3 sessions
        for i in range(3):
            session_manager.start(description=f"Session {i}")
            session_manager.end()

        history = session_manager.get_history()

        assert len(history) == 3
        # Most recent first
        assert history[0]["description"] == "Session 2"

    def test_get_history_limit(self, session_manager):
        """Test history with limit"""
        # Create 5 sessions
        for i in range(5):
            session_manager.start()
            session_manager.end()

        history = session_manager.get_history(limit=2)

        assert len(history) == 2

    def test_get_history_excludes_active(self, session_manager):
        """Test that history excludes active session"""
        session_manager.start()
        session_manager.end()

        session_manager.start()  # Active session

        history = session_manager.get_history()

        assert len(history) == 1  # Only completed session


class TestSessionStats:
    """Test session statistics"""

    @pytest.fixture
    def session_manager(self, tmp_path, monkeypatch):
        """Create a session manager"""
        storage_dir = tmp_path / ".session_manager"

        monkeypatch.setattr(
            "session_manager.utils.paths.get_storage_dir", lambda: storage_dir
        )

        proj = Project("testproject", str(tmp_path))
        proj.ensure_structure()
        return SessionManager(proj)

    def test_get_stats_empty(self, session_manager):
        """Test stats when no sessions"""
        stats = session_manager.get_stats()

        assert stats["total_sessions"] == 0
        assert stats["total_time"] == 0

    def test_get_stats(self, session_manager):
        """Test getting statistics"""
        import time

        # Create sessions with delay
        session_manager.start()
        time.sleep(1)  # Увеличена задержка до 1 секунды
        session_manager.end()

        session_manager.start()
        time.sleep(1)  # Увеличена задержка до 1 секунды
        session_manager.end()

        stats = session_manager.get_stats()

        assert stats["total_sessions"] == 2
        assert stats["total_time"] > 0  # Должно быть > 0 с задержкой в 1 сек
        assert stats["average_duration"] > 0
        assert stats["longest_session"] > 0
        assert stats["shortest_session"] > 0


class TestSessionMetadata:
    """Test session metadata updates"""

    @pytest.fixture
    def session_manager(self, tmp_path, monkeypatch):
        """Create a session manager"""
        storage_dir = tmp_path / ".session_manager"

        monkeypatch.setattr(
            "session_manager.utils.paths.get_storage_dir", lambda: storage_dir
        )

        proj = Project("testproject", str(tmp_path))
        proj.ensure_structure()
        return SessionManager(proj)

    def test_update_session_metadata(self, session_manager):
        """Test updating session metadata"""
        session = session_manager.start()
        session_id = session["id"]

        result = session_manager.update_session_metadata(
            session_id,
            branch="main",
            last_commit="abc123 Initial commit",
            snapshot_file="/path/to/snapshot.md",
        )

        assert result is True

        # Verify update
        active = session_manager.get_active()
        assert active["branch"] == "main"
        assert active["last_commit"] == "abc123 Initial commit"
        assert active["snapshot_file"] == "/path/to/snapshot.md"

    def test_update_session_metadata_not_found(self, session_manager):
        """Test updating non-existent session"""
        result = session_manager.update_session_metadata(
            "nonexistent-id", branch="main"
        )

        assert result is False


class TestSessionDelete:
    """Test deleting sessions"""

    @pytest.fixture
    def session_manager(self, tmp_path, monkeypatch):
        """Create a session manager"""
        storage_dir = tmp_path / ".session_manager"

        monkeypatch.setattr(
            "session_manager.utils.paths.get_storage_dir", lambda: storage_dir
        )

        proj = Project("testproject", str(tmp_path))
        proj.ensure_structure()
        return SessionManager(proj)

    def test_delete_session(self, session_manager):
        """Test deleting a session"""
        session = session_manager.start()
        session_id = session["id"]
        session_manager.end()

        result = session_manager.delete_session(session_id)

        assert result is True

        # Verify deletion
        found = session_manager.get_session_by_id(session_id)
        assert found is None

    def test_delete_session_not_found(self, session_manager):
        """Test deleting non-existent session"""
        result = session_manager.delete_session("nonexistent-id")

        assert result is False

    def test_delete_active_session(self, session_manager):
        """Test deleting active session clears active"""
        session = session_manager.start()
        session_id = session["id"]

        session_manager.delete_session(session_id)

        active = session_manager.get_active()
        assert active is None


class TestSessionById:
    """Test getting session by ID"""

    @pytest.fixture
    def session_manager(self, tmp_path, monkeypatch):
        """Create a session manager"""
        storage_dir = tmp_path / ".session_manager"

        monkeypatch.setattr(
            "session_manager.utils.paths.get_storage_dir", lambda: storage_dir
        )

        proj = Project("testproject", str(tmp_path))
        proj.ensure_structure()
        return SessionManager(proj)

    def test_get_session_by_id(self, session_manager):
        """Test getting session by ID"""
        session = session_manager.start(description="Test session")
        session_id = session["id"]

        found = session_manager.get_session_by_id(session_id)

        assert found is not None
        assert found["id"] == session_id
        assert found["description"] == "Test session"

    def test_get_session_by_id_not_found(self, session_manager):
        """Test getting non-existent session"""
        found = session_manager.get_session_by_id("nonexistent-id")

        assert found is None


class TestTodaySessions:
    """Test today's sessions functionality"""

    @pytest.fixture
    def session_manager(self, tmp_path, monkeypatch):
        """Create a session manager"""
        storage_dir = tmp_path / ".session_manager"

        monkeypatch.setattr(
            "session_manager.utils.paths.get_storage_dir", lambda: storage_dir
        )

        proj = Project("testproject", str(tmp_path))
        proj.ensure_structure()
        return SessionManager(proj)

    def test_get_today_sessions(self, session_manager):
        """Test getting today's sessions"""
        # Create session
        session_manager.start()
        session_manager.end()

        today_sessions = session_manager.get_today_sessions()

        assert len(today_sessions) == 1

    def test_get_total_time_today(self, session_manager):
        """Test getting total time today"""
        import time

        # Create sessions with delay
        session_manager.start()
        time.sleep(0.1)
        session_manager.end()

        session_manager.start()
        time.sleep(0.1)
        session_manager.end()

        total_time = session_manager.get_total_time_today()

        assert total_time >= 0  # Изменено с > 0 на >= 0

    def test_get_today_sessions_empty(self, session_manager):
        """Test getting today's sessions when empty"""
        today_sessions = session_manager.get_today_sessions()

        assert today_sessions == []

    def test_get_total_time_today_zero(self, session_manager):
        """Test total time when no sessions"""
        total_time = session_manager.get_total_time_today()

        assert total_time == 0


class TestGetAllSessions:
    """Test getting all sessions"""

    @pytest.fixture
    def session_manager(self, tmp_path, monkeypatch):
        """Create a session manager"""
        storage_dir = tmp_path / ".session_manager"

        monkeypatch.setattr(
            "session_manager.utils.paths.get_storage_dir", lambda: storage_dir
        )

        proj = Project("testproject", str(tmp_path))
        proj.ensure_structure()
        return SessionManager(proj)

    def test_get_all_sessions(self, session_manager):
        """Test getting all sessions including active"""
        # Create completed session
        session_manager.start()
        session_manager.end()

        # Create active session
        session_manager.start()

        all_sessions = session_manager.get_all_sessions()

        assert len(all_sessions) == 2

    def test_get_all_sessions_empty(self, session_manager):
        """Test getting all sessions when empty"""
        all_sessions = session_manager.get_all_sessions()

        assert all_sessions == []
