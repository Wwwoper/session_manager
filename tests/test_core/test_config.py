"""
Tests for core/config.py
"""
import re
import pytest
from datetime import datetime
from pathlib import Path

from session_manager.core.config import (
    GlobalConfig,
    ProjectInfo,
    ConfigError,
)


class TestProjectInfo:
    """Test ProjectInfo class"""
    
    def test_create_basic(self):
        """Test creating basic ProjectInfo"""
        info = ProjectInfo("myproject", "/path/to/project")
        
        assert info.name == "myproject"
        assert info.path == str(Path("/path/to/project").resolve())
        assert info.alias is None
        assert info.created_at is not None
        assert info.last_used is not None
    
    def test_create_with_alias(self):
        """Test creating ProjectInfo with alias"""
        info = ProjectInfo("myproject", "/path/to/project", alias="mp")
        
        assert info.alias == "mp"
    
    def test_create_with_timestamps(self):
        """Test creating ProjectInfo with specific timestamps"""
        created = "2025-01-01T12:00:00"
        used = "2025-01-15T14:30:00"
        
        info = ProjectInfo(
            "myproject",
            "/path/to/project",
            created_at=created,
            last_used=used
        )
        
        assert info.created_at == created
        assert info.last_used == used
    
    def test_to_dict(self):
        """Test converting to dictionary"""
        info = ProjectInfo("myproject", "/path/to/project", alias="mp")
        
        data = info.to_dict()
        
        assert isinstance(data, dict)
        assert "path" in data
        assert "alias" in data
        assert "created_at" in data
        assert "last_used" in data
        assert data["alias"] == "mp"
    
    def test_from_dict(self):
        """Test creating from dictionary"""
        data = {
            "path": "/path/to/project",
            "alias": "mp",
            "created_at": "2025-01-01T12:00:00",
            "last_used": "2025-01-15T14:30:00",
        }
        
        info = ProjectInfo.from_dict("myproject", data)
        
        assert info.name == "myproject"
        assert info.alias == "mp"
        assert info.created_at == data["created_at"]
        assert info.last_used == data["last_used"]
    
    def test_update_last_used(self):
        """Test updating last_used timestamp"""
        info = ProjectInfo("myproject", "/path/to/project")
        old_timestamp = info.last_used
        
        # Wait a tiny bit to ensure different timestamp
        import time
        time.sleep(0.01)
        
        info.update_last_used()
        
        assert info.last_used != old_timestamp
        # Parse and compare datetimes
        old_dt = datetime.fromisoformat(old_timestamp)
        new_dt = datetime.fromisoformat(info.last_used)
        assert new_dt > old_dt


class TestGlobalConfig:
    """Test GlobalConfig class"""
    
    @pytest.fixture
    def config(self, tmp_path, monkeypatch):
        """Create a GlobalConfig with temporary storage"""
        # Override storage location
        monkeypatch.setattr(
            "session_manager.core.config.get_config_file",
            lambda: tmp_path / "config.json"
        )
        monkeypatch.setattr(
            "session_manager.core.config.ensure_storage_structure",
            lambda: None  # Don't create real directories
        )
        
        cfg = GlobalConfig()
        return cfg
    
    def test_init(self, config):
        """Test initialization"""
        assert config.current_project is None
        assert config.projects == {}
    
    def test_load_empty(self, config):
        """Test loading when config file doesn't exist"""
        config.load()
        
        assert config.current_project is None
        assert config.projects == {}
    
    def test_save_and_load(self, config, tmp_path):
        """Test saving and loading configuration"""
        # Add a project
        config.projects["test"] = ProjectInfo("test", str(tmp_path))
        config.current_project = "test"
        
        # Save
        config.save()
        
        # Create new config and load
        config2 = GlobalConfig()
        config2.config_file = config.config_file
        config2.load()
        
        assert config2.current_project == "test"
        assert "test" in config2.projects
        assert config2.projects["test"].name == "test"
    
    def test_add_project_basic(self, config, tmp_path):
        """Test adding a basic project"""
        result = config.add_project("myproject", str(tmp_path))
        
        assert result is True
        assert "myproject" in config.projects
        assert config.projects["myproject"].name == "myproject"
    
    def test_add_project_with_alias(self, config, tmp_path):
        """Test adding project with alias"""
        result = config.add_project("myproject", str(tmp_path), alias="mp")
        
        assert result is True
        assert config.projects["myproject"].alias == "mp"
    
    def test_add_project_duplicate(self, config, tmp_path):
        """Test adding duplicate project"""
        config.add_project("myproject", str(tmp_path))
        result = config.add_project("myproject", str(tmp_path))
        
        assert result is False
    
    def test_add_project_invalid_name(self, config, tmp_path):
        """Test adding project with invalid name"""
        with pytest.raises(ConfigError, match="Имя проекта не может быть пустым"):
            config.add_project("", str(tmp_path))
        
        with pytest.raises(ConfigError, match="Имя проекта должно содержать только буквенно-цифровые символы, дефисы и подчеркивания"):
            config.add_project("invalid name!", str(tmp_path))
    
    def test_add_project_invalid_path(self, config):
        """Test adding project with invalid path"""
        with pytest.raises(ConfigError, match=re.escape("Невалидный путь проекта: /nonexistent/path (должен быть существующей директорией)")):
            config.add_project("myproject", "/nonexistent/path")
    
    def test_add_project_duplicate_alias(self, config, tmp_path):
        """Test adding project with duplicate alias"""
        config.add_project("project1", str(tmp_path), alias="p1")
        
        tmp_path2 = tmp_path / "other"
        tmp_path2.mkdir()
        
        with pytest.raises(ConfigError, match="Псевдоним 'p1' уже используется проектом 'project1'"):
            config.add_project("project2", str(tmp_path2), alias="p1")
    
    def test_remove_project_exists(self, config, tmp_path):
        """Test removing existing project"""
        config.add_project("myproject", str(tmp_path))
        
        result = config.remove_project("myproject")
        
        assert result is True
        assert "myproject" not in config.projects
    
    def test_remove_project_not_exists(self, config):
        """Test removing non-existent project"""
        result = config.remove_project("nonexistent")
        
        assert result is False
    
    def test_remove_project_clears_current(self, config, tmp_path):
        """Test removing project clears current_project"""
        config.add_project("myproject", str(tmp_path))
        config.set_current_project("myproject")
        
        config.remove_project("myproject")
        
        assert config.current_project is None
    
    def test_get_project_info_by_name(self, config, tmp_path):
        """Test getting project info by name"""
        config.add_project("myproject", str(tmp_path))
        
        info = config.get_project_info("myproject")
        
        assert info is not None
        assert info.name == "myproject"
    
    def test_get_project_info_by_alias(self, config, tmp_path):
        """Test getting project info by alias"""
        config.add_project("myproject", str(tmp_path), alias="mp")
        
        info = config.get_project_info("mp")
        
        assert info is not None
        assert info.name == "myproject"
    
    def test_get_project_info_not_found(self, config):
        """Test getting non-existent project info"""
        info = config.get_project_info("nonexistent")
        
        assert info is None
    
    def test_update_last_used(self, config, tmp_path):
        """Test updating last_used timestamp"""
        config.add_project("myproject", str(tmp_path))
        old_timestamp = config.projects["myproject"].last_used
        
        import time
        time.sleep(0.01)
        
        result = config.update_last_used("myproject")
        
        assert result is True
        assert config.projects["myproject"].last_used != old_timestamp
    
    def test_update_last_used_not_found(self, config):
        """Test updating last_used for non-existent project"""
        result = config.update_last_used("nonexistent")
        
        assert result is False
    
    def test_set_current_project(self, config, tmp_path):
        """Test setting current project"""
        config.add_project("myproject", str(tmp_path))
        
        result = config.set_current_project("myproject")
        
        assert result is True
        assert config.current_project == "myproject"
    
    def test_set_current_project_not_found(self, config):
        """Test setting non-existent project as current"""
        result = config.set_current_project("nonexistent")
        
        assert result is False
        assert config.current_project is None
    
    def test_set_current_project_none(self, config, tmp_path):
        """Test clearing current project"""
        config.add_project("myproject", str(tmp_path))
        config.set_current_project("myproject")
        
        result = config.set_current_project(None)
        
        assert result is True
        assert config.current_project is None
    
    def test_get_all_projects(self, config, tmp_path):
        """Test getting all projects"""
        config.add_project("project1", str(tmp_path))
        
        tmp_path2 = tmp_path / "other"
        tmp_path2.mkdir()
        config.add_project("project2", str(tmp_path2))
        
        projects = config.get_all_projects()
        
        assert len(projects) == 2
        names = [p.name for p in projects]
        assert "project1" in names
        assert "project2" in names
    
    def test_get_projects_sorted_by_usage(self, config, tmp_path):
        """Test getting projects sorted by usage"""
        config.add_project("project1", str(tmp_path))
        
        tmp_path2 = tmp_path / "other"
        tmp_path2.mkdir()
        config.add_project("project2", str(tmp_path2))
        
        import time
        time.sleep(0.01)
        
        # Update project1 to be most recent
        config.update_last_used("project1")
        
        projects = config.get_projects_sorted_by_usage()
        
        assert len(projects) == 2
        assert projects[0].name == "project1"  # Most recent first
    
    def test_project_exists(self, config, tmp_path):
        """Test checking if project exists"""
        config.add_project("myproject", str(tmp_path), alias="mp")
        
        assert config.project_exists("myproject")
        assert config.project_exists("mp")  # By alias
        assert not config.project_exists("nonexistent")
    
    def test_get_project_count(self, config, tmp_path):
        """Test getting project count"""
        assert config.get_project_count() == 0
        
        config.add_project("project1", str(tmp_path))
        assert config.get_project_count() == 1
        
        tmp_path2 = tmp_path / "other"
        tmp_path2.mkdir()
        config.add_project("project2", str(tmp_path2))
        assert config.get_project_count() == 2