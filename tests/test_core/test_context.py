"""
Tests for core/context.py
"""

import pytest
from pathlib import Path

from session_manager.core.context import ContextManager
from session_manager.core.project import Project


class TestContextManagerInit:
    """Test ContextManager initialization"""
    
    @pytest.fixture
    def project(self, tmp_path, monkeypatch):
        """Create a project with temporary storage"""
        storage_dir = tmp_path / ".session-manager"
        
        monkeypatch.setattr(
            "session_manager.utils.paths.get_storage_dir",
            lambda: storage_dir
        )
        
        proj = Project("testproject", str(tmp_path))
        proj.ensure_structure()
        return proj
    
    def test_init(self, project):
        """Test basic initialization"""
        cm = ContextManager(project)
        
        assert cm.project == project


class TestSaveSnapshot:
    """Test saving context snapshots"""
    
    @pytest.fixture
    def context_manager(self, tmp_path, monkeypatch):
        """Create a context manager"""
        storage_dir = tmp_path / ".session-manager"
        
        monkeypatch.setattr(
            "session_manager.utils.paths.get_storage_dir",
            lambda: storage_dir
        )
        
        proj = Project("testproject", str(tmp_path))
        proj.ensure_structure()
        return ContextManager(proj)
    
    def test_save_snapshot_basic(self, context_manager):
        """Test saving a basic snapshot"""
        session_data = {
            "id": "test-id",
            "start_time": "2025-01-15T10:00:00",
            "end_time": "2025-01-15T11:00:00",
            "duration": 3600,
        }
        
        snapshot_path = context_manager.save_snapshot(
            session_data,
            summary="Fixed bug in parser",
            next_action="Add tests"
        )
        
        assert snapshot_path is not None
        assert Path(snapshot_path).exists()
    
    def test_save_snapshot_with_git_info(self, context_manager):
        """Test saving snapshot with git info"""
        session_data = {"id": "test-id"}
        git_info = {
            "branch": "main",
            "last_commit": "abc123 Initial commit",
            "uncommitted_changes": "M file.py"
        }
        
        snapshot_path = context_manager.save_snapshot(
            session_data,
            summary="Work done",
            next_action="Next step",
            git_info=git_info
        )
        
        # Verify content includes git info
        content = Path(snapshot_path).read_text()
        assert "main" in content
        assert "abc123" in content
    
    def test_save_snapshot_with_test_info(self, context_manager):
        """Test saving snapshot with test info"""
        session_data = {"id": "test-id"}
        test_info = {
            "summary": "5 tests passed"
        }
        
        snapshot_path = context_manager.save_snapshot(
            session_data,
            summary="Work done",
            next_action="Next step",
            test_info=test_info
        )
        
        # Verify content includes test info
        content = Path(snapshot_path).read_text()
        assert "5 tests passed" in content


class TestLoadSnapshot:
    """Test loading snapshots"""
    
    @pytest.fixture
    def context_manager(self, tmp_path, monkeypatch):
        """Create a context manager"""
        storage_dir = tmp_path / ".session-manager"
        
        monkeypatch.setattr(
            "session_manager.utils.paths.get_storage_dir",
            lambda: storage_dir
        )
        
        proj = Project("testproject", str(tmp_path))
        proj.ensure_structure()
        return ContextManager(proj)
    
    def test_load_last_snapshot_none(self, context_manager):
        """Test loading when no snapshots exist"""
        snapshot = context_manager.load_last_snapshot()
        
        assert snapshot is None
    
    def test_load_last_snapshot(self, context_manager):
        """Test loading the last snapshot"""
        session_data = {"id": "test-id"}
        
        # Create snapshot
        context_manager.save_snapshot(
            session_data,
            summary="Test summary",
            next_action="Test action"
        )
        
        # Load it
        loaded = context_manager.load_last_snapshot()
        
        assert loaded is not None
        assert "summary" in loaded
        assert "next_action" in loaded


class TestGenerateProjectMd:
    """Test PROJECT.md generation"""
    
    @pytest.fixture
    def context_manager(self, tmp_path, monkeypatch):
        """Create a context manager"""
        storage_dir = tmp_path / ".session-manager"
        
        monkeypatch.setattr(
            "session_manager.utils.paths.get_storage_dir",
            lambda: storage_dir
        )
        
        proj = Project("testproject", str(tmp_path))
        proj.ensure_structure()
        return ContextManager(proj)
    
    def test_generate_project_md(self, context_manager):
        """Test generating PROJECT.md"""
        session_data = {
            "id": "test-id",
            "start_time": "2025-01-15T10:00:00",
            "end_time": "2025-01-15T11:00:00",
            "duration": 3600,
            "branch": "main",
            "last_commit": "abc123 Initial"
        }
        
        context_manager.generate_project_md(
            session_data,
            summary="Fixed parser bug",
            next_action="Add parser tests"
        )
        
        # Verify PROJECT.md exists
        assert context_manager.project.has_project_md()
        
        # Verify content
        content = context_manager.project.get_project_md_content()
        assert "Next Action" in content
        assert "Add parser tests" in content
        assert "Fixed parser bug" in content
    
    def test_generate_project_md_duration_formatting(self, context_manager):
        """Test duration formatting in PROJECT.md"""
        session_data = {
            "id": "test-id",
            "start_time": "2025-01-15T10:00:00",
            "end_time": "2025-01-15T11:30:00",
            "duration": 5400,  # 1h 30m
        }
        
        context_manager.generate_project_md(
            session_data,
            summary="Work",
            next_action="Continue"
        )
        
        content = context_manager.project.get_project_md_content()
        assert "1h 30m" in content


class TestGetNextAction:
    """Test extracting next action from PROJECT.md"""
    
    @pytest.fixture
    def context_manager(self, tmp_path, monkeypatch):
        """Create a context manager"""
        storage_dir = tmp_path / ".session-manager"
        
        monkeypatch.setattr(
            "session_manager.utils.paths.get_storage_dir",
            lambda: storage_dir
        )
        
        proj = Project("testproject", str(tmp_path))
        proj.ensure_structure()
        return ContextManager(proj)
    
    def test_get_next_action_none(self, context_manager):
        """Test getting next action when no PROJECT.md"""
        next_action = context_manager.get_next_action_from_project_md()
        
        assert next_action is None
    
    def test_get_next_action(self, context_manager):
        """Test extracting next action"""
        session_data = {"id": "test-id", "duration": 60}
        
        context_manager.generate_project_md(
            session_data,
            summary="Work done",
            next_action="Add tests for the parser module"
        )
        
        next_action = context_manager.get_next_action_from_project_md()
        
        assert next_action == "Add tests for the parser module"


class TestFormatDuration:
    """Test duration formatting"""
    
    @pytest.fixture
    def context_manager(self, tmp_path, monkeypatch):
        """Create a context manager"""
        storage_dir = tmp_path / ".session-manager"
        
        monkeypatch.setattr(
            "session_manager.utils.paths.get_storage_dir",
            lambda: storage_dir
        )
        
        proj = Project("testproject", str(tmp_path))
        proj.ensure_structure()
        return ContextManager(proj)
    
    def test_format_duration_seconds(self, context_manager):
        """Test formatting seconds"""
        formatted = context_manager._format_duration(45)
        
        assert formatted == "45s"
    
    def test_format_duration_minutes(self, context_manager):
        """Test formatting minutes"""
        formatted = context_manager._format_duration(180)
        
        assert formatted == "3m"
    
    def test_format_duration_minutes_seconds(self, context_manager):
        """Test formatting minutes and seconds"""
        formatted = context_manager._format_duration(150)
        
        assert formatted == "2m 30s"
    
    def test_format_duration_hours(self, context_manager):
        """Test formatting hours"""
        formatted = context_manager._format_duration(3600)
        
        assert formatted == "1h"
    
    def test_format_duration_hours_minutes(self, context_manager):
        """Test formatting hours and minutes"""
        formatted = context_manager._format_duration(5400)
        
        assert formatted == "1h 30m"


class TestFormatSnapshot:
    """Test snapshot formatting"""
    
    @pytest.fixture
    def context_manager(self, tmp_path, monkeypatch):
        """Create a context manager"""
        storage_dir = tmp_path / ".session-manager"
        
        monkeypatch.setattr(
            "session_manager.utils.paths.get_storage_dir",
            lambda: storage_dir
        )
        
        proj = Project("testproject", str(tmp_path))
        proj.ensure_structure()
        return ContextManager(proj)
    
    def test_format_snapshot_basic(self, context_manager):
        """Test basic snapshot formatting"""
        session_data = {
            "id": "test-id",
            "start_time": "2025-01-15T10:00:00",
            "end_time": "2025-01-15T11:00:00",
            "duration": 3600,
            "description": "Test work"
        }
        
        formatted = context_manager._format_snapshot(
            session_data,
            summary="Work summary",
            next_action="Next step",
            git_info=None,
            test_info=None
        )
        
        assert "test-id" in formatted
        assert "Work summary" in formatted
        assert "Next step" in formatted
        assert "1h" in formatted
    
    def test_format_snapshot_with_git(self, context_manager):
        """Test snapshot formatting with git info"""
        session_data = {"id": "test-id", "duration": 60}
        git_info = {
            "branch": "feature/new",
            "last_commit": "abc123 Commit",
            "has_changes": False
        }
        
        formatted = context_manager._format_snapshot(
            session_data,
            summary="Work",
            next_action="Next",
            git_info=git_info
        )
        
        assert "feature/new" in formatted
        assert "abc123" in formatted
        assert "clean" in formatted.lower()


class TestParseSnapshot:
    """Test snapshot parsing"""
    
    @pytest.fixture
    def context_manager(self, tmp_path, monkeypatch):
        """Create a context manager"""
        storage_dir = tmp_path / ".session-manager"
        
        monkeypatch.setattr(
            "session_manager.utils.paths.get_storage_dir",
            lambda: storage_dir
        )
        
        proj = Project("testproject", str(tmp_path))
        proj.ensure_structure()
        return ContextManager(proj)
    
    def test_parse_snapshot(self, context_manager):
        """Test parsing snapshot content"""
        content = """# Session Context Snapshot

**Session ID:** test-123

## 📝 Summary

This is the summary

## 🎯 Next Action

This is the next action
"""
        
        parsed = context_manager._parse_snapshot(content)
        
        assert parsed["session_id"] == "test-123"
        assert parsed["summary"] == "This is the summary"
        assert parsed["next_action"] == "This is the next action"