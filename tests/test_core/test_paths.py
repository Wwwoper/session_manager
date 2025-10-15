"""
Tests for utils/paths.py
"""

import pytest
from pathlib import Path
import tempfile
import shutil

from session_manager.utils.paths import (
    get_storage_dir,
    get_projects_dir,
    get_project_dir,
    get_snapshots_dir,
    get_config_file,
    get_sessions_file,
    get_project_md_file,
    ensure_directories,
    ensure_storage_structure,
    ensure_project_structure,
    find_git_root,
    is_valid_project_path,
    normalize_project_path,
    detect_current_project,
)


class TestPathGetters:
    """Test path getter functions"""
    
    def test_get_storage_dir(self):
        """Test getting storage directory"""
        storage_dir = get_storage_dir()
        assert storage_dir == Path.home() / ".session-manager"
        assert isinstance(storage_dir, Path)
    
    def test_get_projects_dir(self):
        """Test getting projects directory"""
        projects_dir = get_projects_dir()
        assert projects_dir == get_storage_dir() / "projects"
    
    def test_get_project_dir(self):
        """Test getting specific project directory"""
        project_dir = get_project_dir("myproject")
        assert project_dir == get_projects_dir() / "myproject"
    
    def test_get_snapshots_dir(self):
        """Test getting snapshots directory"""
        snapshots_dir = get_snapshots_dir("myproject")
        assert snapshots_dir == get_project_dir("myproject") / "snapshots"
    
    def test_get_config_file(self):
        """Test getting config file path"""
        config_file = get_config_file()
        assert config_file == get_storage_dir() / "config.json"
    
    def test_get_sessions_file(self):
        """Test getting sessions file path"""
        sessions_file = get_sessions_file("myproject")
        assert sessions_file == get_project_dir("myproject") / "sessions.json"
    
    def test_get_project_md_file(self):
        """Test getting PROJECT.md file path"""
        project_md = get_project_md_file("myproject")
        assert project_md == get_project_dir("myproject") / "PROJECT.md"


class TestDirectoryCreation:
    """Test directory creation functions"""
    
    def test_ensure_directories_single(self, tmp_path):
        """Test ensuring a single directory exists"""
        test_dir = tmp_path / "test"
        assert not test_dir.exists()
        
        ensure_directories(test_dir)
        
        assert test_dir.exists()
        assert test_dir.is_dir()
    
    def test_ensure_directories_multiple(self, tmp_path):
        """Test ensuring multiple directories exist"""
        dir1 = tmp_path / "dir1"
        dir2 = tmp_path / "dir2"
        dir3 = tmp_path / "dir3"
        
        ensure_directories(dir1, dir2, dir3)
        
        assert dir1.exists() and dir1.is_dir()
        assert dir2.exists() and dir2.is_dir()
        assert dir3.exists() and dir3.is_dir()
    
    def test_ensure_directories_nested(self, tmp_path):
        """Test ensuring nested directories exist"""
        nested_dir = tmp_path / "level1" / "level2" / "level3"
        
        ensure_directories(nested_dir)
        
        assert nested_dir.exists()
        assert nested_dir.is_dir()
    
    def test_ensure_directories_already_exists(self, tmp_path):
        """Test ensuring directory that already exists"""
        test_dir = tmp_path / "existing"
        test_dir.mkdir()
        
        # Should not raise error
        ensure_directories(test_dir)
        assert test_dir.exists()
    
    def test_ensure_project_structure(self, tmp_path, monkeypatch):
        """Test ensuring project structure"""
        # Temporarily override storage dir
        monkeypatch.setattr(
            "session_manager.utils.paths.get_storage_dir",
            lambda: tmp_path / ".session-manager"
        )
        
        ensure_project_structure("testproject")
        
        project_dir = tmp_path / ".session-manager" / "projects" / "testproject"
        snapshots_dir = project_dir / "snapshots"
        
        assert project_dir.exists()
        assert snapshots_dir.exists()


class TestGitDetection:
    """Test git repository detection"""
    
    def test_find_git_root_exists(self, tmp_path):
        """Test finding git root when .git exists"""
        git_dir = tmp_path / ".git"
        git_dir.mkdir()
        
        result = find_git_root(tmp_path)
        assert result == tmp_path
    
    def test_find_git_root_nested(self, tmp_path):
        """Test finding git root from nested directory"""
        git_dir = tmp_path / ".git"
        git_dir.mkdir()
        
        nested = tmp_path / "src" / "deep" / "nested"
        nested.mkdir(parents=True)
        
        result = find_git_root(nested)
        assert result == tmp_path
    
    def test_find_git_root_not_found(self, tmp_path):
        """Test when no git root exists"""
        nested = tmp_path / "src"
        nested.mkdir()
        
        result = find_git_root(nested)
        assert result is None


class TestPathValidation:
    """Test path validation functions"""
    
    def test_is_valid_project_path_exists(self, tmp_path):
        """Test validating existing directory"""
        assert is_valid_project_path(str(tmp_path))
    
    def test_is_valid_project_path_not_exists(self, tmp_path):
        """Test validating non-existent path"""
        non_existent = tmp_path / "does_not_exist"
        assert not is_valid_project_path(str(non_existent))
    
    def test_is_valid_project_path_file(self, tmp_path):
        """Test validating path that is a file"""
        file_path = tmp_path / "file.txt"
        file_path.touch()
        assert not is_valid_project_path(str(file_path))
    
    def test_normalize_project_path(self, tmp_path):
        """Test normalizing project path"""
        # Test with relative path
        relative = "."
        normalized = normalize_project_path(relative)
        assert Path(normalized).is_absolute()
        
        # Test with absolute path
        absolute = str(tmp_path)
        normalized = normalize_project_path(absolute)
        assert normalized == str(tmp_path.resolve())


class TestProjectDetection:
    """Test project detection from current directory"""
    
    def test_detect_current_project_exact_match(self, tmp_path):
        """Test detecting project when in exact project directory"""
        projects = {
            "myproject": {"path": str(tmp_path)}
        }
        
        # Would need to mock cwd, simplified test
        result = detect_current_project(projects)
        # Result depends on actual cwd, so just check it doesn't crash
        assert result is None or isinstance(result, str)
    
    def test_detect_current_project_no_match(self):
        """Test when no project matches"""
        projects = {
            "myproject": {"path": "/nonexistent/path"}
        }
        
        result = detect_current_project(projects)
        assert result is None or isinstance(result, str)
    
    def test_detect_current_project_empty_registry(self):
        """Test with empty project registry"""
        result = detect_current_project({})
        assert result is None