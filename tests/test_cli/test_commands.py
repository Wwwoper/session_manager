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


class TestCLILsCommand:
    """Тест команды ls — все активные сессии"""

    @pytest.fixture
    def cli(self, tmp_path, monkeypatch):
        """Создать экземпляр CLI"""
        from session_manager.core.project import Project
        from session_manager.core.session import SessionManager

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

    def test_ls_no_active_sessions(self, cli, tmp_path, capsys):
        """Тест ls когда нет активных сессий"""
        project_path = tmp_path / "myproject"
        project_path.mkdir()
        cli.project_add(["myproject", str(project_path)])

        result = cli.cmd_ls([])

        assert result == 0
        captured = capsys.readouterr()
        assert "Нет активных сессий" in captured.out

    def test_ls_with_active_sessions(self, cli, tmp_path, capsys, monkeypatch):
        """Тест ls с активными сессиями"""
        from session_manager.core.project import Project
        from session_manager.core.session import SessionManager

        project_path = tmp_path / "myproject"
        project_path.mkdir()
        cli.project_add(["myproject", str(project_path)])

        # Начать сессию
        project = Project("myproject", str(project_path))
        sm = SessionManager(project)
        sm.start(description="Тестовая сессия")

        result = cli.cmd_ls([])

        assert result == 0
        captured = capsys.readouterr()
        assert "Активные сессии" in captured.out
        assert "myproject" in captured.out
        assert "Тестовая сессия" in captured.out


class TestCLIAbortCommand:
    """Тест команды abort"""

    @pytest.fixture
    def cli(self, tmp_path, monkeypatch):
        """Создать экземпляр CLI"""
        from session_manager.core.project import Project
        from session_manager.core.session import SessionManager

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

    def test_abort_no_active_session(self, cli, tmp_path, capsys):
        """Тест abort когда нет активной сессии"""
        project_path = tmp_path / "myproject"
        project_path.mkdir()
        cli.project_add(["myproject", str(project_path)])

        result = cli.cmd_abort(["myproject"])

        assert result == 1
        captured = capsys.readouterr()
        assert "Нет активной сессии" in captured.out

    def test_abort_session(self, cli, tmp_path, capsys, monkeypatch):
        """Тест abort активной сессии"""
        from session_manager.core.project import Project
        from session_manager.core.session import SessionManager

        project_path = tmp_path / "myproject"
        project_path.mkdir()
        cli.project_add(["myproject", str(project_path)])

        # Начать сессию
        project = Project("myproject", str(project_path))
        sm = SessionManager(project)
        sm.start(description="Тестовая сессия")

        # Прервать
        result = cli.cmd_abort(["myproject"])

        assert result == 0
        captured = capsys.readouterr()
        assert "принудительно завершена" in captured.out

        # Проверить что сессия завершена
        active = sm.get_active()
        assert active is None


class TestCLIForceFlags:
    """Тест флагов --force/-y"""

    @pytest.fixture
    def cli(self, tmp_path, monkeypatch):
        """Создать экземпляр CLI"""
        from session_manager.core.project import Project
        from session_manager.core.session import SessionManager

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

    def test_end_with_force(self, cli, tmp_path, capsys, monkeypatch):
        """Тест session end --force"""
        from session_manager.core.project import Project
        from session_manager.core.session import SessionManager

        project_path = tmp_path / "myproject"
        project_path.mkdir()
        cli.project_add(["myproject", str(project_path)])

        # Начать сессию
        project = Project("myproject", str(project_path))
        sm = SessionManager(project)
        sm.start(description="Тестовая сессия")

        # Завершить с --force (без интерактивных вопросов)
        result = cli.cmd_end(["--force", "myproject"])

        assert result == 0
        captured = capsys.readouterr()
        assert "завершена" in captured.out

    def test_project_remove_with_force(self, cli, tmp_path, capsys):
        """Тест session project remove --force"""
        project_path = tmp_path / "myproject"
        project_path.mkdir()
        cli.project_add(["myproject", str(project_path)])

        # Удалить с --force (без подтверждения)
        result = cli.project_remove(["--force", "myproject"])

        assert result == 0
        captured = capsys.readouterr()
        assert "Удален проект" in captured.out

    def test_start_with_force(self, cli, tmp_path, capsys, monkeypatch):
        """Тест session start --force (пропускает контекст)"""
        project_path = tmp_path / "myproject"
        project_path.mkdir()
        cli.project_add(["myproject", str(project_path)])

        result = cli.cmd_start(["--force", "myproject", "Тестовое описание"])

        assert result == 0
        captured = capsys.readouterr()
        assert "Сессия начата" in captured.out
        # --force не должен показывать контекст
        assert "Запуск новой сессии" not in captured.out


class TestP1Improvements:
    """Тесты улучшений P1"""

    @pytest.fixture
    def cli(self, tmp_path, monkeypatch):
        """Создать экземпляр CLI"""
        from session_manager.core.project import Project
        from session_manager.core.session import SessionManager

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

    def test_status_shows_today_total_time(self, cli, tmp_path, capsys, monkeypatch):
        """Тест: session status показывает общее время за сегодня"""
        from session_manager.core.project import Project
        from session_manager.core.session import SessionManager
        from datetime import datetime, timedelta

        project_path = tmp_path / "myproject"
        project_path.mkdir()
        cli.project_add(["myproject", str(project_path)])

        # Начать и завершить сессию сегодня
        project = Project("myproject", str(project_path))
        sm = SessionManager(project)
        session = sm.start(description="Тест")

        # Завершить сессию с известной длительностью (3600 сек = 1ч)
        active = sm.get_active()
        active["end_time"] = datetime.now().isoformat()
        active["duration"] = 3600
        active["summary"] = "test"
        active["next_action"] = ""
        data = project.get_sessions_data()
        for i, s in enumerate(data["sessions"]):
            if s["id"] == active["id"]:
                data["sessions"][i] = active
                break
        data["active_session"] = None
        project.save_sessions_data(data)

        # Проверить статус
        result = cli.cmd_status(["myproject"])

        assert result == 0
        captured = capsys.readouterr()
        assert "Всего за сегодня" in captured.out
        assert "1ч" in captured.out

    def test_start_no_tests_flag(self, cli, tmp_path, capsys):
        """Тест: session start --no-tests пропускает тесты"""
        project_path = tmp_path / "myproject"
        project_path.mkdir()
        cli.project_add(["myproject", str(project_path)])

        result = cli.cmd_start(["--no-tests", "myproject"])

        assert result == 0
        captured = capsys.readouterr()
        assert "Сессия начата" in captured.out
        assert "Тесты пропущены" in captured.out

    def test_status_no_tests_flag(self, cli, tmp_path, capsys):
        """Тест: session status --no-tests пропускает тесты"""
        project_path = tmp_path / "myproject"
        project_path.mkdir()
        cli.project_add(["myproject", str(project_path)])

        result = cli.cmd_status(["--no-tests", "myproject"])

        assert result == 0
        captured = capsys.readouterr()
        assert "Тесты пропущены" in captured.out

    def test_status_no_active_session_hint(self, cli, tmp_path, capsys):
        """Тест: session status без активной сессии показывает подсказку"""
        project_path = tmp_path / "myproject"
        project_path.mkdir()
        cli.project_add(["myproject", str(project_path)])

        result = cli.cmd_status(["myproject"])

        assert result == 0
        captured = capsys.readouterr()
        assert "Начните сессию" in captured.out


class TestP2Improvements:
    """Тесты улучшений P2"""

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

    def test_resume_no_history(self, cli, tmp_path, capsys):
        """Тест: session resume без истории сессий"""
        project_path = tmp_path / "myproject"
        project_path.mkdir()
        cli.project_add(["myproject", str(project_path)])

        result = cli.cmd_resume(["myproject"])

        assert result == 0
        captured = capsys.readouterr()
        assert "Нет завершённых сессий" in captured.out

    def test_resume_with_history(self, cli, tmp_path, capsys, monkeypatch):
        """Тест: session resume с историей"""
        from session_manager.core.project import Project
        from session_manager.core.session import SessionManager
        from datetime import datetime

        project_path = tmp_path / "myproject"
        project_path.mkdir()
        cli.project_add(["myproject", str(project_path)])

        # Создать завершённую сессию
        project = Project("myproject", str(project_path))
        sm = SessionManager(project)
        session = sm.start(description="Первая сессия")
        active = sm.get_active()
        active["end_time"] = datetime.now().isoformat()
        active["duration"] = 1800
        active["summary"] = "Сделал работу"
        active["next_action"] = "Продолжить работу"
        data = project.get_sessions_data()
        for i, s in enumerate(data["sessions"]):
            if s["id"] == active["id"]:
                data["sessions"][i] = active
                break
        data["active_session"] = None
        project.save_sessions_data(data)

        # Продолжить с --force (без интерактивных вопросов)
        result = cli.cmd_resume(["--force", "myproject"])

        assert result == 0
        captured = capsys.readouterr()
        assert "Продолжение сессии" in captured.out
        assert "Сделал работу" in captured.out
        assert "Продолжить работу" in captured.out
        assert "Сессия продолжена" in captured.out

    def test_edit_session(self, cli, tmp_path, capsys, monkeypatch):
        """Тест: session edit <id>"""
        from session_manager.core.project import Project
        from session_manager.core.session import SessionManager
        from datetime import datetime

        project_path = tmp_path / "myproject"
        project_path.mkdir()
        cli.project_add(["myproject", str(project_path)])

        # Создать завершённую сессию
        project = Project("myproject", str(project_path))
        sm = SessionManager(project)
        session = sm.start(description="Старое описание")
        session_id = session["id"]
        active = sm.get_active()
        active["end_time"] = datetime.now().isoformat()
        active["duration"] = 3600
        active["summary"] = "Старое резюме"
        active["next_action"] = "Старое действие"
        data = project.get_sessions_data()
        for i, s in enumerate(data["sessions"]):
            if s["id"] == active["id"]:
                data["sessions"][i] = active
                break
        data["active_session"] = None
        project.save_sessions_data(data)

        # Редактировать с имитацией ввода
        monkeypatch.setattr("builtins.input", lambda prompt: "Новое значение")

        result = cli.cmd_edit([session_id, "myproject"])

        assert result == 0
        captured = capsys.readouterr()
        assert "Сессия обновлена" in captured.out

        # Проверить что данные обновлены
        updated = sm.get_session_by_id(session_id)
        assert updated["description"] == "Новое значение"
        assert updated["summary"] == "Новое значение"
        assert updated["next_action"] == "Новое значение"


class TestP2FinalImprovements:
    """Тесты финальных P2 улучшений"""

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

    def test_completion_bash(self, cli, capsys):
        """Тест: session completion bash"""
        result = cli.cmd_completion(["bash"])

        assert result == 0
        captured = capsys.readouterr()
        assert "complete -F _session_completion session" in captured.out

    def test_completion_zsh(self, cli, capsys):
        """Тест: session completion zsh"""
        result = cli.cmd_completion(["zsh"])

        assert result == 0
        captured = capsys.readouterr()
        assert "compdef _session session" in captured.out

    def test_completion_fish(self, cli, capsys):
        """Тест: session completion fish"""
        result = cli.cmd_completion(["fish"])

        assert result == 0
        captured = capsys.readouterr()
        assert "complete -c session" in captured.out

    def test_history_full_flag(self, cli, tmp_path, capsys, monkeypatch):
        """Тест: session history --full показывает полный текст"""
        from session_manager.core.project import Project
        from session_manager.core.session import SessionManager
        from datetime import datetime

        project_path = tmp_path / "myproject"
        project_path.mkdir()
        cli.project_add(["myproject", str(project_path)])

        # Создать длинную сессию
        project = Project("myproject", str(project_path))
        sm = SessionManager(project)
        session = sm.start(description="A" * 200)
        active = sm.get_active()
        active["end_time"] = datetime.now().isoformat()
        active["duration"] = 3600
        active["summary"] = "B" * 200
        active["next_action"] = "C" * 200
        data = project.get_sessions_data()
        for i, s in enumerate(data["sessions"]):
            if s["id"] == active["id"]:
                data["sessions"][i] = active
                break
        data["active_session"] = None
        project.save_sessions_data(data)

        # Без --full
        result = cli.cmd_history(["myproject"])
        captured = capsys.readouterr()
        assert "..." in captured.out

        # С --full
        result = cli.cmd_history(["myproject", "--full"])
        captured = capsys.readouterr()
        assert "..." not in captured.out




