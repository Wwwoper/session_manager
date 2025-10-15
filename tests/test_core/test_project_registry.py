"""
Tests for core/project_registry.py
"""

import pytest
from pathlib import Path

from session_manager.core.project_registry import ProjectRegistry
from session_manager.core.config import GlobalConfig, ConfigError
from session_manager.core.project import Project, ProjectError


class TestProjectRegistryInitialization:
    """Test ProjectRegistry initialization"""
    
    def test_init(self, tmp_path, monkeypatch):
        """Test basic initialization"""
        monkeypatch.setattr(
            "session_manager.core.config.get_config_file",
            lambda: tmp_path / "config.json"
        )
        monkeypatch.setattr(
            "session_manager.core.config.ensure_storage_structure",
            lambda: None
        )
        
        config = GlobalConfig()
        config.load()
        
        registry = ProjectRegistry(config)
        
        assert registry.config is config


class TestProjectRegistryAdd:
    """Test adding projects"""
    
    @pytest.fixture
    def registry(self, tmp_path, monkeypatch):
        """Create a registry with temporary storage"""
        storage_dir = tmp_path / ".session-manager"
        
        monkeypatch.setattr(
            "session_manager.core.config.get_config_file",
            lambda: storage_dir / "config.json"
        )
        monkeypatch.setattr(
            "session_manager.core.config.ensure_storage_structure",
            lambda: None
        )
        monkeypatch.setattr(
            "session_manager.utils.paths.get_storage_dir",
            lambda: storage_dir
        )
        
        config = GlobalConfig()
        config.load()
        
        return ProjectRegistry(config)
    
    def test_add_project_basic(self, registry, tmp_path):
        """Test adding a basic project"""
        project_path = tmp_path / "myproject"
        project_path.mkdir()
        
        project = registry.add("myproject", str(project_path))
        
        assert project.name == "myproject"
        assert registry.exists("myproject")
        assert project.exists()
    
    def test_add_project_with_alias(self, registry, tmp_path):
        """Test adding project with alias"""
        project_path = tmp_path / "myproject"
        project_path.mkdir()
        
        project = registry.add("myproject", str(project_path), alias="mp")
        
        assert registry.exists("myproject")
        assert registry.exists("mp")  # Can find by alias
    
    def test_add_project_set_as_current(self, registry, tmp_path):
        """Test adding project and setting as current"""
        project_path = tmp_path / "myproject"
        project_path.mkdir()
        
        registry.add("myproject", str(project_path), set_as_current=True)
        
        assert registry.config.current_project == "myproject"
    
    def test_add_project_duplicate(self, registry, tmp_path):
        """Test adding duplicate project raises error"""
        project_path = tmp_path / "myproject"
        project_path.mkdir()
        
        registry.add("myproject", str(project_path))
        
        with pytest.raises(ConfigError):
            registry.add("myproject", str(project_path))
    
    def test_add_project_invalid_path(self, registry):
        """Test adding project with invalid path"""
        with pytest.raises(ConfigError):
            registry.add("myproject", "/nonexistent/path")


class TestProjectRegistryRemove:
    """Test removing projects"""
    
    @pytest.fixture
    def registry(self, tmp_path, monkeypatch):
        """Create a registry with temporary storage"""
        storage_dir = tmp_path / ".session-manager"
        
        monkeypatch.setattr(
            "session_manager.core.config.get_config_file",
            lambda: storage_dir / "config.json"
        )
        monkeypatch.setattr(
            "session_manager.core.config.ensure_storage_structure",
            lambda: None
        )
        monkeypatch.setattr(
            "session_manager.utils.paths.get_storage_dir",
            lambda: storage_dir
        )
        
        config = GlobalConfig()
        config.load()
        
        return ProjectRegistry(config)
    
    def test_remove_project(self, registry, tmp_path):
        """Test removing a project"""
        project_path = tmp_path / "myproject"
        project_path.mkdir()
        
        registry.add("myproject", str(project_path))
        result = registry.remove("myproject")
        
        assert result is True
        assert not registry.exists("myproject")
    
    def test_remove_project_not_found(self, registry):
        """Test removing non-existent project"""
        result = registry.remove("nonexistent")
        
        assert result is False
    
    def test_remove_project_by_alias(self, registry, tmp_path):
        """Test removing project by alias"""
        project_path = tmp_path / "myproject"
        project_path.mkdir()
        
        registry.add("myproject", str(project_path), alias="mp")
        result = registry.remove("mp")
        
        assert result is True
        assert not registry.exists("myproject")
    
    def test_remove_project_with_data(self, registry, tmp_path):
        """Test removing project and its data"""
        project_path = tmp_path / "myproject"
        project_path.mkdir()
        
        project = registry.add("myproject", str(project_path))
        project.update_project_md("# Test")
        project.save_sessions_data({"sessions": [], "active_session": None})
        
        result = registry.remove("myproject", delete_data=True)
        
        assert result is True
        assert not project.sessions_file.exists()
        assert not project.project_md_file.exists()


class TestProjectRegistryList:
    """Test listing projects"""
    
    @pytest.fixture
    def registry(self, tmp_path, monkeypatch):
        """Create a registry with temporary storage"""
        storage_dir = tmp_path / ".session-manager"
        
        monkeypatch.setattr(
            "session_manager.core.config.get_config_file",
            lambda: storage_dir / "config.json"
        )
        monkeypatch.setattr(
            "session_manager.core.config.ensure_storage_structure",
            lambda: None
        )
        monkeypatch.setattr(
            "session_manager.utils.paths.get_storage_dir",
            lambda: storage_dir
        )
        
        config = GlobalConfig()
        config.load()
        
        return ProjectRegistry(config)
    
    def test_list_empty(self, registry):
        """Test listing when no projects"""
        projects = registry.list()
        
        assert projects == []
    
    def test_list_projects(self, registry, tmp_path):
        """Test listing projects"""
        # Add multiple projects
        for i in range(3):
            project_path = tmp_path / f"project{i}"
            project_path.mkdir()
            registry.add(f"project{i}", str(project_path))
        
        projects = registry.list(sort_by_usage=False)
        
        assert len(projects) == 3
        names = [p.name for p in projects]
        assert "project0" in names
        assert "project1" in names
        assert "project2" in names
    
    def test_list_sorted_by_usage(self, registry, tmp_path):
        """Test listing sorted by usage"""
        # Add projects
        project1_path = tmp_path / "project1"
        project1_path.mkdir()
        registry.add("project1", str(project1_path))
        
        import time
        time.sleep(0.01)
        
        project2_path = tmp_path / "project2"
        project2_path.mkdir()
        registry.add("project2", str(project2_path))
        
        projects = registry.list(sort_by_usage=True)
        
        # Most recently added should be first
        assert projects[0].name == "project2"


class TestProjectRegistryGet:
    """Test getting projects"""
    
    @pytest.fixture
    def registry(self, tmp_path, monkeypatch):
        """Create a registry with temporary storage"""
        storage_dir = tmp_path / ".session-manager"
        
        monkeypatch.setattr(
            "session_manager.core.config.get_config_file",
            lambda: storage_dir / "config.json"
        )
        monkeypatch.setattr(
            "session_manager.core.config.ensure_storage_structure",
            lambda: None
        )
        monkeypatch.setattr(
            "session_manager.utils.paths.get_storage_dir",
            lambda: storage_dir
        )
        
        config = GlobalConfig()
        config.load()
        
        return ProjectRegistry(config)
    
    def test_get_project_by_name(self, registry, tmp_path):
        """Test getting project by name"""
        project_path = tmp_path / "myproject"
        project_path.mkdir()
        
        registry.add("myproject", str(project_path))
        project = registry.get("myproject")
        
        assert project is not None
        assert project.name == "myproject"
    
    def test_get_project_by_alias(self, registry, tmp_path):
        """Test getting project by alias"""
        project_path = tmp_path / "myproject"
        project_path.mkdir()
        
        registry.add("myproject", str(project_path), alias="mp")
        project = registry.get("mp")
        
        assert project is not None
        assert project.name == "myproject"
    
    def test_get_project_not_found(self, registry):
        """Test getting non-existent project"""
        project = registry.get("nonexistent")
        
        assert project is None
    
    def test_find_by_path(self, registry, tmp_path):
        """Test finding project by path"""
        project_path = tmp_path / "myproject"
        project_path.mkdir()
        
        registry.add("myproject", str(project_path))
        found_name = registry.find_by_path(str(project_path))
        
        assert found_name == "myproject"
    
    def test_find_by_path_not_found(self, registry, tmp_path):
        """Test finding by non-existent path"""
        result = registry.find_by_path("/nonexistent/path")
        
        assert result is None


class TestProjectRegistryCurrent:
    """Test current project management"""
    
    @pytest.fixture
    def registry(self, tmp_path, monkeypatch):
        """Create a registry with temporary storage"""
        storage_dir = tmp_path / ".session-manager"
        
        monkeypatch.setattr(
            "session_manager.core.config.get_config_file",
            lambda: storage_dir / "config.json"
        )
        monkeypatch.setattr(
            "session_manager.core.config.ensure_storage_structure",
            lambda: None
        )
        monkeypatch.setattr(
            "session_manager.utils.paths.get_storage_dir",
            lambda: storage_dir
        )
        
        config = GlobalConfig()
        config.load()
        
        return ProjectRegistry(config)
    
    def test_get_current_none(self, registry):
        """Test getting current when none set"""
        current = registry.get_current()
        
        assert current is None
    
    def test_set_current(self, registry, tmp_path):
        """Test setting current project"""
        project_path = tmp_path / "myproject"
        project_path.mkdir()
        
        registry.add("myproject", str(project_path))
        result = registry.set_current("myproject")
        
        assert result is True
        
        current = registry.get_current()
        assert current is not None
        assert current.name == "myproject"
    
    def test_set_current_by_alias(self, registry, tmp_path):
        """Test setting current by alias"""
        project_path = tmp_path / "myproject"
        project_path.mkdir()
        
        registry.add("myproject", str(project_path), alias="mp")
        result = registry.set_current("mp")
        
        assert result is True
        assert registry.config.current_project == "myproject"
    
    def test_set_current_not_found(self, registry):
        """Test setting non-existent project as current"""
        result = registry.set_current("nonexistent")
        
        assert result is False
    
    def test_set_current_none(self, registry, tmp_path):
        """Test clearing current project"""
        project_path = tmp_path / "myproject"
        project_path.mkdir()
        
        registry.add("myproject", str(project_path))
        registry.set_current("myproject")
        
        result = registry.set_current(None)
        
        assert result is True
        assert registry.get_current() is None


class TestProjectRegistrySearch:
    """Test project search"""
    
    @pytest.fixture
    def registry(self, tmp_path, monkeypatch):
        """Create a registry with temporary storage"""
        storage_dir = tmp_path / ".session-manager"
        
        monkeypatch.setattr(
            "session_manager.core.config.get_config_file",
            lambda: storage_dir / "config.json"
        )
        monkeypatch.setattr(
            "session_manager.core.config.ensure_storage_structure",
            lambda: None
        )
        monkeypatch.setattr(
            "session_manager.utils.paths.get_storage_dir",
            lambda: storage_dir
        )
        
        config = GlobalConfig()
        config.load()
        
        return ProjectRegistry(config)
    
    def test_search_by_name(self, registry, tmp_path):
        """Test searching by project name"""
        project_path = tmp_path / "my-awesome-project"
        project_path.mkdir()
        
        registry.add("my-awesome-project", str(project_path))
        
        results = registry.search("awesome")
        
        assert len(results) == 1
        assert results[0].name == "my-awesome-project"
    
    def test_search_by_alias(self, registry, tmp_path):
        """Test searching by alias"""
        project_path = tmp_path / "myproject"
        project_path.mkdir()
        
        registry.add("myproject", str(project_path), alias="super")
        
        results = registry.search("super")
        
        assert len(results) == 1
        assert results[0].name == "myproject"
    
    def test_search_case_insensitive(self, registry, tmp_path):
        """Test case-insensitive search"""
        project_path = tmp_path / "MyProject"
        project_path.mkdir()
        
        registry.add("MyProject", str(project_path))
        
        results = registry.search("myproject")
        
        assert len(results) == 1
    
    def test_search_no_results(self, registry):
        """Test search with no results"""
        results = registry.search("nonexistent")
        
        assert results == []


class TestProjectRegistryUtilities:
    """Test utility methods"""
    
    @pytest.fixture
    def registry(self, tmp_path, monkeypatch):
        """Create a registry with temporary storage"""
        storage_dir = tmp_path / ".session-manager"
        
        monkeypatch.setattr(
            "session_manager.core.config.get_config_file",
            lambda: storage_dir / "config.json"
        )
        monkeypatch.setattr(
            "session_manager.core.config.ensure_storage_structure",
            lambda: None
        )
        monkeypatch.setattr(
            "session_manager.utils.paths.get_storage_dir",
            lambda: storage_dir
        )
        
        config = GlobalConfig()
        config.load()
        
        return ProjectRegistry(config)
    
    def test_exists(self, registry, tmp_path):
        """Test checking if project exists"""
        project_path = tmp_path / "myproject"
        project_path.mkdir()
        
        registry.add("myproject", str(project_path))
        
        assert registry.exists("myproject")
        assert not registry.exists("nonexistent")
    
    def test_get_count(self, registry, tmp_path):
        """Test getting project count"""
        assert registry.get_count() == 0
        
        project_path = tmp_path / "project1"
        project_path.mkdir()
        registry.add("project1", str(project_path))
        
        assert registry.get_count() == 1
    
    def test_get_projects_summary(self, registry, tmp_path):
        """Test getting projects summary"""
        project_path = tmp_path / "myproject"
        project_path.mkdir()
        
        project = registry.add("myproject", str(project_path))
        project.save_sessions_data({
            "sessions": [{"id": "1"}, {"id": "2"}],
            "active_session": "1"
        })
        
        summary = registry.get_projects_summary()
        
        assert summary["total_projects"] == 1
        assert summary["total_sessions"] == 2
        assert summary["active_sessions"] == 1
    
    def test_validate_all_valid(self, registry, tmp_path):
        """Test validating all projects - all valid"""
        project_path = tmp_path / "myproject"
        project_path.mkdir()
        
        registry.add("myproject", str(project_path))
        
        validation = registry.validate_all()
        
        assert "myproject" in validation["valid"]
        assert len(validation["invalid"]) == 0
    
    def test_validate_all_invalid(self, registry, tmp_path):
        """Test validating all projects - some invalid"""
        project_path = tmp_path / "myproject"
        project_path.mkdir()
        
        registry.add("myproject", str(project_path))
        
        # Remove the directory
        project_path.rmdir()
        
        validation = registry.validate_all()
        
        assert "myproject" in validation["invalid"]
        assert len(validation["valid"]) == 0