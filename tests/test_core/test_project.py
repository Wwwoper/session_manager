"""
Tests for core/project.py
"""

import pytest
from pathlib import Path
from datetime import datetime

from session_manager.core.project import Project, ProjectError


class TestProjectInitialization:
    """Test Project initialization"""
    
    def test_init_basic(self, tmp_path):
        """Test basic project initialization"""
        project = Project("testproject", str(tmp_path))
        
        assert project.name == "testproject"
        assert project.path == tmp_path.resolve()
        assert project.sessions_file is not None
        assert project.project_md_file is not None
        assert project.snapshots_dir is not None
    
    def test_init_paths_resolved(self, tmp_path):
        """Test that paths are resolved to absolute"""
        # Use relative path
        project = Project("test", ".")
        
        assert project.path.is_absolute()


class TestProjectStructure:
    """Test project structure management"""
    
    @pytest.fixture
    def project(self, tmp_path, monkeypatch):
        """Create a project with temporary storage"""
        # Override storage location
        storage_dir = tmp_path / ".session-manager"
        
        monkeypatch.setattr(
            "session_manager.utils.paths.get_storage_dir",
            lambda: storage_dir
        )
        
        return Project("testproject", str(tmp_path))
    
    def test_ensure_structure(self, project):
        """Test ensuring project structure"""
        project.ensure_structure()
        
        assert project._project_dir.exists()
        assert project.snapshots_dir.exists()
    
    def test_exists_false(self, project):
        """Test exists returns False when structure doesn't exist"""
        assert not project.exists()
    
    def test_exists_true(self, project):
        """Test exists returns True when structure exists"""
        project.ensure_structure()
        assert project.exists()


class TestProjectMD:
    """Test PROJECT.md management"""
    
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
    
    def test_has_project_md_false(self, project):
        """Test has_project_md returns False initially"""
        assert not project.has_project_md()
    
    def test_update_project_md(self, project):
        """Test updating PROJECT.md"""
        content = "# Test Project\n\nSome content"
        
        project.update_project_md(content)
        
        assert project.has_project_md()
        assert project.project_md_file.exists()
    
    def test_get_project_md_content(self, project):
        """Test getting PROJECT.md content"""
        content = "# Test Project\n\nSome content"
        project.update_project_md(content)
        
        loaded = project.get_project_md_content()
        
        assert loaded == content
    
    def test_get_project_md_content_empty(self, project):
        """Test getting content when file doesn't exist"""
        content = project.get_project_md_content()
        
        assert content == ""


class TestSessionsData:
    """Test sessions data management"""
    
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
    
    def test_get_sessions_data_empty(self, project):
        """Test getting sessions data when file doesn't exist"""
        data = project.get_sessions_data()
        
        assert "sessions" in data
        assert "active_session" in data
        assert data["sessions"] == []
        assert data["active_session"] is None
    
    def test_save_and_load_sessions_data(self, project):
        """Test saving and loading sessions data"""
        test_data = {
            "sessions": [
                {"id": "1", "start": "2025-01-15T10:00:00"},
                {"id": "2", "start": "2025-01-15T14:00:00"},
            ],
            "active_session": "2",
        }
        
        project.save_sessions_data(test_data)
        loaded = project.get_sessions_data()
        
        assert loaded == test_data
        assert len(loaded["sessions"]) == 2
        assert loaded["active_session"] == "2"


class TestSnapshots:
    """Test snapshot management"""
    
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
    
    def test_get_snapshot_path(self, project):
        """Test getting snapshot path"""
        path = project.get_snapshot_path("20250115_1430")
        
        assert path.name == "20250115_1430.md"
        assert path.parent == project.snapshots_dir
    
    def test_list_snapshots_empty(self, project):
        """Test listing snapshots when none exist"""
        snapshots = project.list_snapshots()
        
        assert snapshots == []
    
    def test_list_snapshots(self, project):
        """Test listing snapshots"""
        # Create some snapshots
        (project.snapshots_dir / "20250115_1000.md").touch()
        (project.snapshots_dir / "20250115_1400.md").touch()
        (project.snapshots_dir / "20250115_1200.md").touch()
        
        snapshots = project.list_snapshots()
        
        assert len(snapshots) == 3
        # Should be sorted by name
        assert snapshots[0].name == "20250115_1000.md"
        assert snapshots[1].name == "20250115_1200.md"
        assert snapshots[2].name == "20250115_1400.md"
    
    def test_get_latest_snapshot_none(self, project):
        """Test getting latest snapshot when none exist"""
        latest = project.get_latest_snapshot()
        
        assert latest is None
    
    def test_get_latest_snapshot(self, project):
        """Test getting latest snapshot"""
        (project.snapshots_dir / "20250115_1000.md").touch()
        (project.snapshots_dir / "20250115_1400.md").touch()
        
        latest = project.get_latest_snapshot()
        
        assert latest is not None
        assert latest.name == "20250115_1400.md"
    
    def test_delete_old_snapshots(self, project):
        """Test deleting old snapshots"""
        # Create 5 snapshots
        for i in range(5):
            (project.snapshots_dir / f"2025011510{i:02d}.md").touch()
        
        # Keep only 3 most recent
        deleted = project.delete_old_snapshots(keep=3)
        
        assert deleted == 2
        remaining = project.list_snapshots()
        assert len(remaining) == 3
        assert remaining[-1].name == "202501151004.md"  # Most recent
    
    def test_delete_old_snapshots_not_enough(self, project):
        """Test deleting when fewer snapshots than keep limit"""
        (project.snapshots_dir / "20250115_1000.md").touch()
        (project.snapshots_dir / "20250115_1100.md").touch()
        
        deleted = project.delete_old_snapshots(keep=5)
        
        assert deleted == 0
        assert len(project.list_snapshots()) == 2


class TestBackupOperations:
    """Test backup operations"""
    
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
    
    def test_backup_sessions_not_exists(self, project):
        """Test backing up when sessions file doesn't exist"""
        result = project.backup_sessions()
        
        assert result is None
    
    def test_backup_sessions(self, project):
        """Test backing up sessions file"""
        # Create sessions file
        data = {"sessions": [], "active_session": None}
        project.save_sessions_data(data)
        
        backup_path = project.backup_sessions()
        
        assert backup_path is not None
        assert backup_path.exists()
        assert backup_path.name == "sessions.json.backup"


class TestProjectInfo:
    """Test project info retrieval"""
    
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
    
    def test_get_project_info(self, project):
        """Test getting project info"""
        # Add some data
        project.update_project_md("# Test")
        project.save_sessions_data({
            "sessions": [{"id": "1"}, {"id": "2"}],
            "active_session": "2"
        })
        (project.snapshots_dir / "20250115_1000.md").touch()
        
        info = project.get_project_info()
        
        assert info["name"] == "testproject"
        assert info["exists"] is True
        assert info["has_project_md"] is True
        assert info["total_sessions"] == 2
        assert info["active_session"] == "2"
        assert info["total_snapshots"] == 1
        assert info["latest_snapshot"] == "20250115_1000.md"


class TestProjectRepresentation:
    """Test string representations"""
    
    def test_repr(self, tmp_path):
        """Test __repr__"""
        project = Project("test", str(tmp_path))
        
        repr_str = repr(project)
        
        assert "Project" in repr_str
        assert "test" in repr_str
    
    def test_str(self, tmp_path):
        """Test __str__"""
        project = Project("test", str(tmp_path))
        
        str_repr = str(project)
        
        assert "Project:" in str_repr
        assert "test" in str_repr