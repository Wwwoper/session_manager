"""
Tests for cli/commands.py
"""

import pytest
from pathlib import Path

from session_manager.core.config import GlobalConfig
from session_manager.core.project_registry import ProjectRegistry
from session_manager.cli.commands import CLI


class TestCLIInit:
    """Test CLI initialization"""
    
    @pytest.fixture
    def cli(self, tmp_path, monkeypatch):
        """Create a CLI instance"""
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
        registry = ProjectRegistry(config)
        
        return CLI(config, registry)
    
    def test_init(self, cli):
        """Test basic initialization"""
        assert cli.config is not None
        assert cli.registry is not None


class TestCLIHelp:
    """Test help commands"""
    
    @pytest.fixture
    def cli(self, tmp_path, monkeypatch):
        """Create a CLI instance"""
        storage_dir = tmp_path / ".session-manager"
        
        monkeypatch.setattr(
            "session_manager.core.config.get_config_file",
            lambda: storage_dir / "config.json"
        )
        monkeypatch.setattr(
            "session_manager.core.config.ensure_storage_structure",
            lambda: None
        )
        
        config = GlobalConfig()
        config.load()
        registry = ProjectRegistry(config)
        
        return CLI(config, registry)
    
    def test_show_help(self, cli, capsys):
        """Test showing help"""
        result = cli.show_help()
        
        assert result == 0
        
        captured = capsys.readouterr()
        assert "Session Manager" in captured.out
        assert "USAGE" in captured.out
    
    def test_show_version(self, cli, capsys):
        """Test showing version"""
        result = cli.show_version()
        
        assert result == 0
        
        captured = capsys.readouterr()
        assert "Session Manager" in captured.out


class TestCLIProjectCommands:
    """Test project commands"""
    
    @pytest.fixture
    def cli(self, tmp_path, monkeypatch):
        """Create a CLI instance"""
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
        registry = ProjectRegistry(config)
        
        return CLI(config, registry)
    
    def test_project_add(self, cli, tmp_path, capsys):
        """Test adding a project"""
        project_path = tmp_path / "myproject"
        project_path.mkdir()
        
        result = cli.project_add(["myproject", str(project_path)])
        
        assert result == 0
        
        captured = capsys.readouterr()
        assert "Added project" in captured.out
    
    def test_project_list_empty(self, cli, capsys):
        """Test listing when no projects"""
        result = cli.project_list([])
        
        assert result == 0
        
        captured = capsys.readouterr()
        assert "No projects" in captured.out
    
    def test_project_list(self, cli, tmp_path, capsys):
        """Test listing projects"""
        project_path = tmp_path / "myproject"
        project_path.mkdir()
        
        cli.project_add(["myproject", str(project_path)])
        
        result = cli.project_list([])
        
        assert result == 0
        
        captured = capsys.readouterr()
        assert "myproject" in captured.out


class TestCLIRun:
    """Test CLI run method"""
    
    @pytest.fixture
    def cli(self, tmp_path, monkeypatch):
        """Create a CLI instance"""
        storage_dir = tmp_path / ".session-manager"
        
        monkeypatch.setattr(
            "session_manager.core.config.get_config_file",
            lambda: storage_dir / "config.json"
        )
        monkeypatch.setattr(
            "session_manager.core.config.ensure_storage_structure",
            lambda: None
        )
        
        config = GlobalConfig()
        config.load()
        registry = ProjectRegistry(config)
        
        return CLI(config, registry)
    
    def test_run_no_args(self, cli):
        """Test running with no arguments"""
        result = cli.run([])
        
        assert result == 0
    
    def test_run_help(self, cli):
        """Test running help command"""
        result = cli.run(["help"])
        
        assert result == 0
    
    def test_run_version(self, cli):
        """Test running version command"""
        result = cli.run(["version"])
        
        assert result == 0
    
    def test_run_unknown_command(self, cli, capsys):
        """Test running unknown command"""
        result = cli.run(["unknown"])
        
        assert result == 1
        
        captured = capsys.readouterr()
        assert "Unknown command" in captured.out