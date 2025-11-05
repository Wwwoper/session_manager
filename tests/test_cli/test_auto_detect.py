"""
Тесты для автоопределения проекта в CLI
tests/test_cli/test_auto_detect.py
"""

import pytest
from pathlib import Path

from session_manager.core.config import GlobalConfig
from session_manager.core.project_registry import ProjectRegistry
from session_manager.cli.commands import CLI


class TestAutoDetectProject:
    """Тесты автоопределения проекта"""

    @pytest.fixture
    def cli_with_projects(self, tmp_path, monkeypatch):
        """CLI с несколькими зарегистрированными проектами"""
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

        # Создать несколько проектов
        project1_path = tmp_path / "project1"
        project1_path.mkdir()
        registry.add("project1", str(project1_path), alias="p1")

        project2_path = tmp_path / "project2"
        project2_path.mkdir()
        registry.add("project2", str(project2_path))

        return CLI(config, registry), project1_path, project2_path

    def test_resolve_project_by_name(self, cli_with_projects):
        """Тест разрешения проекта по имени"""
        cli, _, _ = cli_with_projects

        project = cli._resolve_project("project1")

        assert project is not None
        assert project.name == "project1"

    def test_resolve_project_by_alias(self, cli_with_projects):
        """Тест разрешения проекта по псевдониму"""
        cli, _, _ = cli_with_projects

        project = cli._resolve_project("p1")

        assert project is not None
        assert project.name == "project1"

    def test_resolve_project_cached(self, cli_with_projects):
        """Тест кэширования результата"""
        cli, _, _ = cli_with_projects

        # Первое разрешение
        project1 = cli._resolve_project("project1")
        assert project1 is not None

        # Второе разрешение без имени должно использовать кэш
        project2 = cli._resolve_project(None)
        assert project2 is not None
        assert project2.name == "project1"

    def test_resolve_project_auto_detect(self, cli_with_projects, monkeypatch):
        """Тест автоопределения проекта"""
        cli, project1_path, _ = cli_with_projects

        # Имитируем нахождение в директории проекта
        monkeypatch.chdir(project1_path)

        project = cli._resolve_project(None, auto_detect=True)

        assert project is not None
        assert project.name == "project1"

    def test_resolve_project_not_found(self, cli_with_projects, capsys):
        """Тест несуществующего проекта"""
        cli, _, _ = cli_with_projects

        project = cli._resolve_project("nonexistent")

        assert project is None
        captured = capsys.readouterr()
        assert "не найден" in captured.out.lower()

    def test_resolve_project_no_options(self, cli_with_projects, capsys):
        """Тест без опций разрешения"""
        cli, _, _ = cli_with_projects

        project = cli._resolve_project(None, auto_detect=False)

        assert project is None
        captured = capsys.readouterr()
        assert "не удалось определить" in captured.out.lower()


class TestStartCommandAutoDetect:
    """Тесты команды start с автоопределением"""

    @pytest.fixture
    def cli_setup(self, tmp_path, monkeypatch):
        """Настройка CLI с проектом"""
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

        project_path = tmp_path / "myproject"
        project_path.mkdir()
        registry.add("myproject", str(project_path))

        return CLI(config, registry), project_path

    def test_start_with_explicit_project(self, cli_setup, capsys):
        """Тест start с явным указанием проекта"""
        cli, _ = cli_setup

        result = cli.cmd_start(["myproject", "Working on feature"])

        assert result == 0
        captured = capsys.readouterr()
        assert "начата" in captured.out.lower()

    def test_start_with_description_only(self, cli_setup, monkeypatch, capsys):
        """Тест start только с описанием (автоопределение)"""
        cli, project_path = cli_setup

        # Имитируем нахождение в директории проекта
        monkeypatch.chdir(project_path)

        result = cli.cmd_start(["Working on feature"])

        assert result == 0
        captured = capsys.readouterr()
        assert "автоопределен" in captured.out.lower()
        assert "начата" in captured.out.lower()

    def test_start_no_args_auto_detect(self, cli_setup, monkeypatch, capsys):
        """Тест start без аргументов с автоопределением"""
        cli, project_path = cli_setup

        monkeypatch.chdir(project_path)

        result = cli.cmd_start([])

        assert result == 0
        captured = capsys.readouterr()
        assert "автоопределен" in captured.out.lower()

    def test_start_no_args_no_detect(self, cli_setup, capsys):
        """Тест start без аргументов без автоопределения"""
        cli, _ = cli_setup

        result = cli.cmd_start([])

        assert result == 1
        captured = capsys.readouterr()
        assert "не удалось определить" in captured.out.lower()


class TestStatusCommandAutoDetect:
    """Тесты команды status с автоопределением"""

    @pytest.fixture
    def cli_with_session(self, tmp_path, monkeypatch):
        """CLI с активной сессией"""
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

        project_path = tmp_path / "myproject"
        project_path.mkdir()
        project = registry.add("myproject", str(project_path))

        # Создать активную сессию
        from session_manager.core.session import SessionManager

        sm = SessionManager(project)
        sm.start("Test session")

        return CLI(config, registry), project_path

    def test_status_with_explicit_project(self, cli_with_session, capsys):
        """Тест status с явным проектом"""
        cli, _ = cli_with_session

        result = cli.cmd_status(["myproject"])

        assert result == 0
        captured = capsys.readouterr()
        assert "активная сессия" in captured.out.lower()

    def test_status_auto_detect(self, cli_with_session, monkeypatch, capsys):
        """Тест status с автоопределением"""
        cli, project_path = cli_with_session

        monkeypatch.chdir(project_path)

        result = cli.cmd_status([])

        assert result == 0
        captured = capsys.readouterr()
        assert "автоопределен" in captured.out.lower()
        assert "активная сессия" in captured.out.lower()


class TestHistoryCommandParsing:
    """Тесты парсинга команды history"""

    @pytest.fixture
    def cli_setup(self, tmp_path, monkeypatch):
        """Настройка CLI"""
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

        project_path = tmp_path / "myproject"
        project_path.mkdir()
        registry.add("myproject", str(project_path))

        return CLI(config, registry), project_path

    def test_history_with_project_and_limit(self, cli_setup, capsys):
        """Тест history с проектом и лимитом"""
        cli, _ = cli_setup

        result = cli.cmd_history(["myproject", "--limit", "5"])

        assert result == 0

    def test_history_with_limit_only(self, cli_setup, monkeypatch, capsys):
        """Тест history только с лимитом (автоопределение)"""
        cli, project_path = cli_setup

        monkeypatch.chdir(project_path)

        result = cli.cmd_history(["--limit", "5"])

        assert result == 0
        captured = capsys.readouterr()
        assert "автоопределен" in captured.out.lower()


class TestCacheClearing:
    """Тесты очистки кэша"""

    @pytest.fixture
    def cli_setup(self, tmp_path, monkeypatch):
        """Настройка CLI с двумя проектами"""
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

        project1_path = tmp_path / "project1"
        project1_path.mkdir()
        registry.add("project1", str(project1_path))

        project2_path = tmp_path / "project2"
        project2_path.mkdir()
        registry.add("project2", str(project2_path))

        return CLI(config, registry)

    def test_cache_updates_on_explicit_project(self, cli_setup):
        """Тест обновления кэша при явном указании проекта"""
        cli = cli_setup

        # Разрешаем project1
        project1 = cli._resolve_project("project1")
        assert project1.name == "project1"

        # Разрешаем project2 - должен обновить кэш
        project2 = cli._resolve_project("project2")
        assert project2.name == "project2"

        # Без аргументов должен вернуть project2 из кэша
        cached = cli._resolve_project(None)
        assert cached.name == "project2"
