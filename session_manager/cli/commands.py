"""
Команды CLI для Session Manager
Реализует все команды интерфейса командной строки.
"""
from typing import List, Optional
from pathlib import Path
from ..core.config import GlobalConfig, ConfigError
from ..core.project_registry import ProjectRegistry
from ..core.project import Project, ProjectError
from ..core.session import SessionManager, SessionError
from ..core.context import ContextManager, ContextError
from ..integrations.git import GitIntegration
from ..integrations.tests import TestsIntegration
from ..integrations.github import GitHubIntegration
from ..utils.formatters import (
    print_success, print_error, print_warning, print_info,
    print_subsection, format_duration, format_timestamp,
    format_table, format_stats,
    print_header
)

class CLI:
    """
    Интерфейс командной строки для Session Manager.

    Обрабатывает все пользовательские команды и предоставляет интерактивный опыт.
    """

    def __init__(self, config: GlobalConfig, registry: ProjectRegistry):
        """
        Инициализация CLI.

        Args:
            config: Экземпляр глобальной конфигурации
            registry: Экземпляр реестра проектов
        """
        self.config = config
        self.registry = registry

    def run(self, args: List[str]) -> int:
        """
        Запустить команду CLI.

        Args:
            args: Аргументы командной строки

        Returns:
            Код выхода (0 — успех, ненулевое — ошибки)
        """
        if not args:
            return self.show_help()

        command = args[0].lower()
        rest_args = args[1:]

        # Маршрутизация команд
        commands = {
            "project": self.cmd_project,
            "start": self.cmd_start,
            "end": self.cmd_end,
            "status": self.cmd_status,
            "history": self.cmd_history,
            "stats": self.cmd_stats,
            "help": self.show_help,
            "version": self.show_version,
        }

        if command in commands:
            try:
                return commands[command](rest_args)
            except (ConfigError, ProjectError, SessionError, ContextError) as e:
                print_error(str(e))
                return 1
            except Exception as e:
                print_error(f"Unexpected error: {e}")
                return 1
        else:
            print_error(f"Unknown command: {command}")
            print_info("Run 'session help' for usage information")
            return 1

    # ==================== Команды проекта ====================

    def cmd_project(self, args: List[str]) -> int:
        """Обработка подкоманд проекта."""
        if not args:
            print_error("Missing project subcommand")
            print_info("Available: add, list, remove, info")
            return 1

        subcommand = args[0].lower()
        sub_args = args[1:]

        if subcommand == "add":
            return self.project_add(sub_args)
        elif subcommand == "list":
            return self.project_list(sub_args)
        elif subcommand == "remove":
            return self.project_remove(sub_args)
        elif subcommand == "info":
            return self.project_info(sub_args)
        else:
            print_error(f"Unknown project subcommand: {subcommand}")
            return 1

    def project_add(self, args: List[str]) -> int:
        """Добавить новый проект."""
        if len(args) < 2:
            print_error("Usage: session project add <name> <path> [--alias <alias>]")
            return 1

        name = args[0]
        path = args[1]
        alias = None

        # Разбор необязательного псевдонима
        if len(args) >= 4 and args[2] == "--alias":
            alias = args[3]

        try:
            project = self.registry.add(name, path, alias=alias, set_as_current=True)
            print_success(f"Added project '{name}'")
            print_info(f"Path: {project.path}")
            if alias:
                print_info(f"Alias: {alias}")
            print_info("Set as current project")
            return 0
        except (ConfigError, ProjectError) as e:
            print_error(f"Failed to add project: {e}")
            return 1

    def project_list(self, args: List[str]) -> int:
        """Вывести список всех проектов."""
        projects_info = self.registry.list(sort_by_usage=True)

        if not projects_info:
            print_info("No projects registered yet")
            print_info("Add a project with: session project add <name> <path>")
            return 0

        print_header("Registered Projects")

        # Подготовка данных для отображения
        projects_data = []
        for proj_info in projects_info:
            projects_data.append({
                "name": proj_info.name,
                "alias": proj_info.alias or "-",
                "path": str(proj_info.path)[:40] + "..." if len(str(proj_info.path)) > 40 else str(proj_info.path),
            })

        # Показать текущий проект
        if self.config.current_project:
            print(f"📌 Current: {self.config.current_project}\n")

        # Печать таблицы
        table = format_table(projects_data, ["name", "alias", "path"])
        print(table)

        print(f"\n Total: {len(projects_info)} projects")

        return 0

    def project_remove(self, args: List[str]) -> int:
        """Удалить проект."""
        if len(args) < 1:
            print_error("Usage: session project remove <name>")
            return 1

        name = args[0]

        # Подтверждение удаления
        response = input(f"Remove project '{name}'? (y/N): ").strip().lower()
        if response != 'y':
            print_info("Cancelled")
            return 0

        try:
            success = self.registry.remove(name, delete_data=False)
            if success:
                print_success(f"Removed project '{name}'")
                print_info("Project data preserved in ~/.session-manager/")
                return 0
            else:
                print_error(f"Project '{name}' not found")
                return 1
        except ProjectError as e:
            print_error(f"Failed to remove project: {e}")
            return 1

    def project_info(self, args: List[str]) -> int:
        """Показать информацию о проекте."""
        if len(args) < 1:
            print_error("Usage: session project info <name>")
            return 1

        name = args[0]
        project = self.registry.get(name)

        if not project:
            print_error(f"Project '{name}' not found")
            return 1

        print_header(f"Project: {name}")

        info = project.get_project_info()

        print(f"Path: {info['path']}")
        print(f"Exists: {'✅' if info['exists'] else '❌'}")
        print(f"Has PROJECT.md: {'✅' if info['has_project_md'] else '❌'}")
        print(f"\nTotal Sessions: {info['total_sessions']}")
        print(f"Active Session: {info['active_session'] if info['active_session'] else 'None'}")
        print(f"Total Snapshots: {info['total_snapshots']}")

        if info['latest_snapshot']:
            print(f"Latest Snapshot: {info['latest_snapshot']}")

        return 0

    # ==================== Команды сессий ====================

    def cmd_start(self, args: List[str]) -> int:
        """Начать новую сессию."""
        # Получить проект
        project_name = args[0] if args else None
        project = self._resolve_project(project_name)

        if not project:
            return 1

        # Получить описание
        description = ""
        if len(args) > 1:
            description = " ".join(args[1:])

        try:
            sm = SessionManager(project)

            # Проверить активную сессию
            if sm.get_active():
                print_warning("Session already active!")
                print_info("End it with: session end")
                return 1

            print_header("🚀 Starting New Session")
            print(f"Project: {project.name}\n")

            # Показать последний контекст
            self._show_last_context(project)

            # Показать статус git
            self._show_git_status(project)

            # Показать задачи GitHub
            self._show_github_issues(project)

            # Запустить тесты
            self._show_test_status(project)

            # Запустить сессию
            session = sm.start(description=description)

            # Обновить метаданные по git
            git = GitIntegration(project.path)
            if git.is_git_repo():
                sm.update_session_metadata(
                    session["id"],
                    branch=git.get_current_branch(),
                    last_commit=git.get_last_commit()
                )

            print_success("Session started!")
            print_info(f"Session ID: {session['id'][:8]}...")

            return 0

        except SessionError as e:
            print_error(f"Failed to start session: {e}")
            return 1

    def cmd_end(self, args: List[str]) -> int:
        """Завершить активную сессию."""
        # Получить проект
        project_name = args[0] if args else None
        project = self._resolve_project(project_name)

        if not project:
            return 1

        try:
            sm = SessionManager(project)

            active = sm.get_active()
            if not active:
                print_warning("No active session")
                return 1

            print_header("💾 Ending Session")

            # Получить итог
            print("What was accomplished in this session?")
            summary = input("Summary: ").strip()

            print("\nWhat is the next concrete action?")
            print("(e.g., 'Add tests for parse_data function')")
            next_action = input("Next action: ").strip()

            # Проверить незакоммиченные изменения
            git = GitIntegration(project.path)
            if git.has_uncommitted_changes():
                print_warning("\nUncommitted changes detected!")
                changes = git.get_uncommitted_changes()
                print(changes[:200])  # Показать первые 200 символов

                response = input("\nCreate a commit? (y/N): ").strip().lower()
                if response == 'y':
                    commit_msg = input("Commit message: ").strip()
                    if commit_msg:
                        git.add_all()
                        if git.create_commit(commit_msg):
                            print_success("Commit created")
                        else:
                            print_error("Failed to create commit")

            # Завершить сессию
            completed = sm.end(summary=summary, next_action=next_action)

            # Сохранить снимок контекста
            cm = ContextManager(project)
            git_info = git.get_git_info() if git.is_git_repo() else None
            tests = TestsIntegration(project.path)
            test_info = tests.get_test_info() if tests.is_pytest_available() else None

            snapshot_path = cm.save_snapshot(
                completed,
                summary,
                next_action,
                git_info=git_info,
                test_info=test_info
            )

            # Сгенерировать PROJECT.md
            cm.generate_project_md(completed, summary, next_action)

            print_success("\nSession ended!")
            print_info(f"Duration: {format_duration(completed['duration'])}")
            print_info(f"Snapshot saved: {Path(snapshot_path).name}")
            print_info("PROJECT.md updated")

            return 0

        except (SessionError, ContextError) as e:
            print_error(f"Failed to end session: {e}")
            return 1

    def cmd_status(self, args: List[str]) -> int:
        """Показать статус проекта."""
        # Получить проект
        project_name = args[0] if args else None
        project = self._resolve_project(project_name)

        if not project:
            return 1

        print_header(f"📊 Status: {project.name}")

        # Информация о сессии
        sm = SessionManager(project)
        active = sm.get_active()

        if active:
            print_subsection("Active Session")
            print(f"Started: {format_timestamp(active['start_time'])}")
            if active.get('description'):
                print(f"Description: {active['description']}")

            # Подсчитать текущую длительность
            from datetime import datetime
            start = datetime.fromisoformat(active['start_time'])
            duration = int((datetime.now() - start).total_seconds())
            print(f"Duration: {format_duration(duration)}")
        else:
            print("No active session\n")

        # Последний контекст
        self._show_last_context(project)

        # Статус Git
        self._show_git_status(project)

        # Статус тестов
        self._show_test_status(project)

        return 0

    def cmd_history(self, args: List[str]) -> int:
        """Показать историю сессий."""
        # Получить проект
        project_name = args[0] if args and not args[0].startswith('--') else None
        project = self._resolve_project(project_name)

        if not project:
            return 1

        # Разобрать лимит
        limit = 10
        for i, arg in enumerate(args):
            if arg == "--limit" and i + 1 < len(args):
                try:
                    limit = int(args[i + 1])
                except ValueError:
                    print_error("Invalid limit value")
                    return 1

        sm = SessionManager(project)
        history = sm.get_history(limit=limit)

        if not history:
            print_info("No completed sessions yet")
            return 0

        print_header(f"📜 Session History: {project.name}")

        for i, session in enumerate(history, 1):
            print(f"\n{i}. Session")
            print(f"   Started: {format_timestamp(session['start_time'])}")
            print(f"   Duration: {format_duration(session['duration'])}")

            if session.get('summary'):
                summary = session['summary'][:60]
                if len(session['summary']) > 60:
                    summary += "..."
                print(f"   Summary: {summary}")

        print(f"\nShowing {len(history)} most recent sessions")

        return 0

    def cmd_stats(self, args: List[str]) -> int:
        """Показать статистику сессий."""
        # Получить проект
        project_name = args[0] if args else None
        project = self._resolve_project(project_name)

        if not project:
            return 1
        sm = SessionManager(project)
        stats = sm.get_stats()

        print_header(f"📊 Statistics: {project.name}")

        print(format_stats(stats))

        # Время за сегодня
        today_time = sm.get_total_time_today()
        if today_time > 0:
            print(f"\nToday's Total: {format_duration(today_time)}")
        return 0

    # ==================== Вспомогательные методы ====================

    def _resolve_project(self, project_name: Optional[str]) -> Optional[Project]:
        """Преобразовать имя проекта в экземпляр Project."""
        if project_name:
            project = self.registry.get(project_name)
            if not project:
                print_error(f"Project '{project_name}' not found")
                return None
            return project

        # Попробовать текущий проект
        if self.config.current_project:
            return self.registry.get(self.config.current_project)

        # Попробовать автоопределение
        project = self.registry.detect_current()
        if project:
            print_info(f"Auto-detected project:
