"""
Тесты для cli/commands.py
"""

import pytest

from session_manager.core.config import GlobalConfig
from session_manager.core.project_registry import ProjectRegistry
from session_manager.cli.commands import CLI


class TestCLIInit:
    """Тест инициализации CLI"""

    @pytest.fixture
    def cli(self, tmp_path, monkeypatch):
        """Создать экземпляр CLI"""
        storage_dir = tmp_path / ".session_manager"

        monkeypatch.setattr(
            "session_manager.core.config.get_config_file",
            lambda: storage_dir / "config.json",
        )
        monkeypatch.setattr(
            "session_manager.core.config.ensure_storage_structure", lambda: None
        )
        monkeypatch.setattr(
            "session_manager.utils.paths.get_storage_dir", lambda: storage_dir
        )

        config = GlobalConfig()
        config.load()
        registry = ProjectRegistry(config)

        return CLI(config, registry)

    def test_init(self, cli):
        """Тест базовой инициализации"""
        assert cli.config is not None
        assert cli.registry is not None


class TestCLIHelp:
    """Тест команд справки"""

    @pytest.fixture
    def cli(self, tmp_path, monkeypatch):
        """Создать экземпляр CLI"""
        storage_dir = tmp_path / ".session_manager"

        monkeypatch.setattr(
            "session_manager.core.config.get_config_file",
            lambda: storage_dir / "config.json",
        )
        monkeypatch.setattr(
            "session_manager.core.config.ensure_storage_structure", lambda: None
        )

        config = GlobalConfig()
        config.load()
        registry = ProjectRegistry(config)

        return CLI(config, registry)

    def test_show_help(self, cli, capsys):
        """Тест показа справки"""
        result = cli.show_help()

        assert result == 0

        captured = capsys.readouterr()
        assert "Session Manager" in captured.out
        assert "ИСПОЛЬЗОВАНИЕ" in captured.out

    def test_show_version(self, cli, capsys):
        """Тест показа версии"""
        result = cli.show_version()

        assert result == 0

        captured = capsys.readouterr()
        assert "Session Manager" in captured.out


class TestCLIProjectCommands:
    """Тест команд проекта"""

    @pytest.fixture
    def cli(self, tmp_path, monkeypatch):
        """Создать экземпляр CLI"""
        storage_dir = tmp_path / ".session_manager"

        monkeypatch.setattr(
            "session_manager.core.config.get_config_file",
            lambda: storage_dir / "config.json",
        )
        monkeypatch.setattr(
            "session_manager.core.config.ensure_storage_structure", lambda: None
        )
        monkeypatch.setattr(
            "session_manager.utils.paths.get_storage_dir", lambda: storage_dir
        )

        config = GlobalConfig()
        config.load()
        registry = ProjectRegistry(config)

        return CLI(config, registry)

    def test_project_add(self, cli, tmp_path, capsys):
        """Тест добавления проекта"""
        project_path = tmp_path / "myproject"
        project_path.mkdir()

        result = cli.project_add(["myproject", str(project_path)])

        assert result == 0

        captured = capsys.readouterr()
        assert "Добавлен проект" in captured.out

    def test_project_list_empty(self, cli, capsys):
        """Тест списка когда нет проектов"""
        result = cli.project_list([])

        assert result == 0

        captured = capsys.readouterr()
        assert "Пока нет зарегистрированных проектов" in captured.out

    def test_project_list(self, cli, tmp_path, capsys):
        """Тест списка проектов"""
        project_path = tmp_path / "myproject"
        project_path.mkdir()

        cli.project_add(["myproject", str(project_path)])

        result = cli.project_list([])

        assert result == 0

        captured = capsys.readouterr()
        assert "myproject" in captured.out


class TestCLIRun:
    """Тест метода run CLI"""

    @pytest.fixture
    def cli(self, tmp_path, monkeypatch):
        """Создать экземпляр CLI"""
        storage_dir = tmp_path / ".session_manager"

        monkeypatch.setattr(
            "session_manager.core.config.get_config_file",
            lambda: storage_dir / "config.json",
        )
        monkeypatch.setattr(
            "session_manager.core.config.ensure_storage_structure", lambda: None
        )

        config = GlobalConfig()
        config.load()
        registry = ProjectRegistry(config)

        return CLI(config, registry)

    def test_run_no_args(self, cli):
        """Тест запуска без аргументов"""
        result = cli.run([])

        assert result == 0

    def test_run_help(self, cli):
        """Тест запуска команды help"""
        result = cli.run(["help"])

        assert result == 0

    def test_run_version(self, cli):
        """Тест запуска команды version"""
        result = cli.run(["version"])

        assert result == 0

    def test_run_unknown_command(self, cli, capsys):
        """Тест запуска неизвестной команды"""
        result = cli.run(["unknown"])

        assert result == 1

        captured = capsys.readouterr()
        assert "Неизвестная команда" in captured.out
