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
    print_success,
    print_error,
    print_warning,
    print_info,
    print_subsection,
    format_duration,
    format_timestamp,
    format_table,
    format_stats,
    print_header,
)


class CLI:
    """
    Интерфейс командной строки для Session Manager.

    Обрабатывает все пользовательские команды и предоставляет интерактивный опыт.
    """

    def __init__(self, config: GlobalConfig, registry: ProjectRegistry):
        """
        Инициализация CLI.

        Аргументы:
            config: Экземпляр глобальной конфигурации
            registry: Экземпляр реестра проектов
        """
        self.config = config
        self.registry = registry
        self._cached_project = None  # Кэш для автоопределённого проекта

    def run(self, args: List[str]) -> int:
        """
        Запустить команду CLI.

        Аргументы:
            args: Аргументы командной строки

        Возвращает:
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
                print_error(f"Неожиданная ошибка: {e}")
                return 1
        else:
            print_error(f"Неизвестная команда: {command}")
            print_info(
                "Запустите 'session help' для получения информации об использовании"
            )
            return 1

    # ==================== Команды проекта ====================

    def cmd_project(self, args: List[str]) -> int:
        """Обработка подкоманд проекта."""
        if not args:
            print_error("Отсутствует подкоманда проекта")
            print_info("Доступные: add, list, remove, info")
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
            print_error(f"Неизвестная подкоманда проекта: {subcommand}")
            return 1

    def project_add(self, args: List[str]) -> int:
        """Добавить новый проект."""
        if len(args) < 2:
            print_error(
                "Использование: session project add <название> <путь> [--alias <псевдоним>]"
            )
            return 1

        name = args[0]
        path = args[1]
        alias = None

        # Разбор необязательного псевдонима
        if len(args) >= 4 and args[2] == "--alias":
            alias = args[3]

        try:
            project = self.registry.add(name, path, alias=alias, set_as_current=True)
            print_success(f"Добавлен проект '{name}'")
            print_info(f"Путь: {project.path}")
            if alias:
                print_info(f"Псевдоним: {alias}")
            print_info("Установлен как текущий проект")
            return 0
        except (ConfigError, ProjectError) as e:
            print_error(f"Не удалось добавить проект: {e}")
            return 1

    def project_list(self, args: List[str]) -> int:
        """Вывести список всех проектов."""
        projects_info = self.registry.list(sort_by_usage=True)

        if not projects_info:
            print_info("Пока нет зарегистрированных проектов")
            print_info(
                "Добавьте проект с помощью: session project add <название> <путь>"
            )
            return 0

        print_header("Зарегистрированные проекты")

        # Подготовка данных для отображения
        projects_data = []
        for proj_info in projects_info:
            projects_data.append(
                {
                    "name": proj_info.name,
                    "alias": proj_info.alias or "-",
                    "path": str(proj_info.path)[:40] + "..."
                    if len(str(proj_info.path)) > 40
                    else str(proj_info.path),
                }
            )

        # Показать текущий проект
        if self.config.current_project:
            print(f"📌 Текущий: {self.config.current_project}\n")

        # Печать таблицы
        table = format_table(projects_data, ["name", "alias", "path"])
        print(table)

        print(f"\n Всего: {len(projects_info)} проектов")

        return 0

    def project_remove(self, args: List[str]) -> int:
        """Удалить проект."""
        if len(args) < 1:
            print_error("Использование: session project remove <название>")
            return 1

        name = args[0]

        # Подтверждение удаления
        response = input(f"Удалить проект '{name}'? (y/N): ").strip().lower()
        if response != "y":
            print_info("Отменено")
            return 0

        try:
            success = self.registry.remove(name, delete_data=False)
            if success:
                print_success(f"Удален проект '{name}'")
                print_info("Данные проекта сохранены в ~/.session_manager/")
                return 0
            else:
                print_error(f"Проект '{name}' не найден")
                return 1
        except ProjectError as e:
            print_error(f"Не удалось удалить проект: {e}")
            return 1

    def project_info(self, args: List[str]) -> int:
        """Показать информацию о проекте."""
        if len(args) < 1:
            print_error("Использование: session project info <название>")
            return 1

        name = args[0]
        project = self.registry.get(name)

        if not project:
            print_error(f"Проект '{name}' не найден")
            return 1

        print_header(f"Проект: {name}")

        info = project.get_project_info()

        print(f"Путь: {info['path']}")
        print(f"Существует: {'✅' if info['exists'] else '❌'}")
        print(f"Есть PROJECT.md: {'✅' if info['has_project_md'] else '❌'}")
        print(f"\nВсего сессий: {info['total_sessions']}")
        print(
            f"Активная сессия: {info['active_session'] if info['active_session'] else 'Нет'}"
        )
        print(f"Всего снимков: {info['total_snapshots']}")

        if info["latest_snapshot"]:
            print(f"Последний снимок: {info['latest_snapshot']}")

        return 0

    # ==================== Команды сессий ====================

    def cmd_start(self, args: List[str]) -> int:
        """Начать новую сессию."""
        # Попытка разобрать аргументы
        project_name = None
        description = ""

        # Если первый аргумент похож на название проекта (короткий, без пробелов)
        # и проект существует, то считаем его названием проекта
        if args:
            potential_project = args[0]
            if self.registry.exists(potential_project):
                project_name = potential_project
                description = " ".join(args[1:]) if len(args) > 1 else ""
            else:
                # Иначе всё считаем описанием
                description = " ".join(args)

        # Получить проект
        project = self._resolve_project(project_name, auto_detect=True)
        if not project:
            return 1

        try:
            sm = SessionManager(project)

            # Проверить активную сессию
            if sm.get_active():
                print_warning("Сессия уже активна!")
                print_info("Завершите её с помощью: session end")
                return 1

            print_header(f"🚀 Запуск новой сессии: {project.name}")

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
                    last_commit=git.get_last_commit(),
                )

            print_success("Сессия начата!")
            print_info(f"ID сессии: {session['id'][:8]}...")

            return 0

        except SessionError as e:
            print_error(f"Не удалось начать сессию: {e}")
            return 1

    def cmd_end(self, args: List[str]) -> int:
        """Завершить активную сессию."""
        # Получить проект (args[0] если передан)
        project_name = args[0] if args else None
        project = self._resolve_project(project_name, auto_detect=True)

        if not project:
            return 1

        try:
            sm = SessionManager(project)

            active = sm.get_active()
            if not active:
                print_warning("Нет активной сессии")
                print_info(f"Начните сессию с помощью: session start")
                return 1

            print_header(f"💾 Завершение сессии: {project.name}")

            # Получить итог
            print("Что было выполнено в этой сессии?")
            summary = input("Итог: ").strip()

            print("\nКакое следующее конкретное действие?")
            print("(например, 'Добавить тесты для функции parse_data')")
            next_action = input("Следующее действие: ").strip()

            # Проверить незакоммиченные изменения
            git = GitIntegration(project.path)
            if git.has_uncommitted_changes():
                print_warning("\nОбнаружены незакоммиченные изменения!")
                changes = git.get_uncommitted_changes()
                print(changes[:200])

                response = input("\nСоздать коммит? (y/N): ").strip().lower()
                if response == "y":
                    commit_msg = input("Сообщение коммита: ").strip()
                    if commit_msg:
                        git.add_all()
                        if git.create_commit(commit_msg):
                            print_success("Коммит создан")
                        else:
                            print_error("Не удалось создать коммит")

            # Завершить сессию
            completed = sm.end(summary=summary, next_action=next_action)

            # Сохранить снимок контекста
            cm = ContextManager(project)
            git_info = git.get_git_info() if git.is_git_repo() else None
            tests = TestsIntegration(project.path)
            test_info = tests.get_test_info() if tests.is_pytest_available() else None

            snapshot_path = cm.save_snapshot(
                completed, summary, next_action, git_info=git_info, test_info=test_info
            )

            # Сгенерировать PROJECT.md
            cm.generate_project_md(completed, summary, next_action)

            print_success("\nСессия завершена!")
            print_info(f"Продолжительность: {format_duration(completed['duration'])}")
            print_info(f"Снимок сохранен: {Path(snapshot_path).name}")
            print_info("PROJECT.md обновлен")

            return 0

        except (SessionError, ContextError) as e:
            print_error(f"Не удалось завершить сессию: {e}")
            return 1

    def cmd_status(self, args: List[str]) -> int:
        """Показать статус проекта."""
        # Получить проект
        project_name = args[0] if args else None
        project = self._resolve_project(project_name, auto_detect=True)

        if not project:
            return 1

        print_header(f"📊 Статус: {project.name}")

        # Информация о сессии
        sm = SessionManager(project)
        active = sm.get_active()

        if active:
            print_subsection("Активная сессия")
            print(f"Начата: {format_timestamp(active['start_time'])}")
            if active.get("description"):
                print(f"Описание: {active['description']}")

            # Подсчитать текущую длительность
            from datetime import datetime

            start = datetime.fromisoformat(active["start_time"])
            duration = int((datetime.now() - start).total_seconds())
            print(f"Продолжительность: {format_duration(duration)}")
        else:
            print("Нет активной сессии\n")

        # Последний контекст
        self._show_last_context(project)

        # Статус Git
        self._show_git_status(project)

        # Статус тестов
        self._show_test_status(project)

        return 0

    def cmd_history(self, args: List[str]) -> int:
        """Показать историю сессий."""
        # Разбор аргументов: может быть [проект] или [--limit N]
        project_name = None
        limit = 10

        i = 0
        while i < len(args):
            arg = args[i]
            if arg == "--limit" and i + 1 < len(args):
                try:
                    limit = int(args[i + 1])
                    i += 2
                except ValueError:
                    print_error("Неверное значение лимита")
                    return 1
            elif not arg.startswith("--"):
                # Предполагаем, что это название проекта
                project_name = arg
                i += 1
            else:
                i += 1

        # Получить проект
        project = self._resolve_project(project_name, auto_detect=True)
        if not project:
            return 1

        sm = SessionManager(project)
        history = sm.get_history(limit=limit)

        if not history:
            print_info("Пока нет завершенных сессий")
            print_info(f"Начните сессию с помощью: session start")
            return 0

        print_header(f"📜 История сессий: {project.name}")

        for i, session in enumerate(history, 1):
            print(f"\n{i}. Сессия")
            print(f"   Начата: {format_timestamp(session['start_time'])}")
            print(f"   Продолжительность: {format_duration(session['duration'])}")

            if session.get("summary"):
                summary = session["summary"][:60]
                if len(session["summary"]) > 60:
                    summary += "..."
                print(f"   Итог: {summary}")

        print(f"\nПоказано {len(history)} последних сессий")

        return 0

    def cmd_stats(self, args: List[str]) -> int:
        """Показать статистику сессий."""
        # Получить проект
        project_name = args[0] if args else None
        project = self._resolve_project(project_name, auto_detect=True)

        if not project:
            return 1

        sm = SessionManager(project)
        stats = sm.get_stats()

        print_header(f"📊 Статистика: {project.name}")

        print(format_stats(stats))

        # Время за сегодня
        today_time = sm.get_total_time_today()
        if today_time > 0:
            print(f"\nВсего за сегодня: {format_duration(today_time)}")
        return 0

    # ==================== Вспомогательные методы ====================

    def _resolve_project(
        self, project_name: Optional[str], auto_detect: bool = False
    ) -> Optional[Project]:
        """
        Преобразовать название проекта в экземпляр Project.

        Аргументы:
            project_name: Название проекта (может быть None)
            auto_detect: Разрешить автоопределение проекта

        Возвращает:
            Project или None
        """
        # 1. Если передано название проекта явно
        if project_name:
            project = self.registry.get(project_name)
            if not project:
                print_error(f"Проект '{project_name}' не найден")
                print_info("Список проектов: session project list")
                return None
            # Кэшируем для последующих команд
            self._cached_project = project
            return project

        # 2. Попробовать использовать кэшированный проект из предыдущей команды
        if self._cached_project:
            return self._cached_project

        # 3. Попробовать current_project из конфигурации
        if self.config.current_project:
            project = self.registry.get(self.config.current_project)
            if project:
                self._cached_project = project
                return project

        # 4. Попробовать автоопределение, если разрешено
        if auto_detect:
            project = self.registry.detect_current()
            if project:
                print_info(f"📍 Автоопределен проект: {project.name}")
                self._cached_project = project
                return project

        # 5. Не удалось определить проект
        self._print_project_resolution_help()
        return None

    def _print_project_resolution_help(self) -> None:
        """Показать справку по разрешению проекта."""
        print_error("Не удалось определить, какой проект использовать")
        print()
        print("Вы можете:")
        print("  1. Указать проект явно: session <команда> <название-проекта>")
        print("  2. Запустить команду из директории проекта (автоопределение)")
        print("  3. Установить текущий проект: session project add <название> <путь>")
        print()
        print("Список всех проектов: session project list")

    def _show_last_context(self, project: Project) -> None:
        """Показать последний сохраненный контекст."""
        cm = ContextManager(project)
        next_action = cm.get_next_action_from_project_md()

        if next_action:
            print_subsection("📌 Следующее действие")
            print(f"   {next_action}\n")

    def _show_git_status(self, project: Project) -> None:
        """Показать статус git."""
        git = GitIntegration(project.path)

        if not git.is_git_repo():
            return

        print_subsection("🌿 Статус Git")

        branch = git.get_current_branch()
        if branch:
            print(f"   Ветка: {branch}")

        commit = git.get_last_commit()
        if commit:
            print(f"   Последний коммит: {commit}")

        if git.has_uncommitted_changes():
            print("   ⚠️  Обнаружены незакоммиченные изменения")
        else:
            print("   ✅ Рабочая директория чиста")

        print()

    def _show_github_issues(self, project: Project) -> None:
        """Показать задачи GitHub."""
        gh = GitHubIntegration(project.path)

        if not gh.is_github_repo():
            return

        issues = gh.get_open_issues(limit=3)

        if issues:
            print_subsection("📋 Открытые задачи")
            summary = gh.format_issues_summary(issues)
            print(summary)
            print()

    def _show_test_status(self, project: Project) -> None:
        """Показать статус тестов."""
        tests = TestsIntegration(project.path)

        if not tests.is_pytest_available():
            return

        print_subsection("🧪 Запуск тестов...")

        result = tests.run_tests(timeout=15, verbose=False)

        if result["success"]:
            print(f"   ✅ {result['summary']}")
        else:
            print(f"   ❌ {result['summary']}")

        print()

    # ==================== Команды информации ====================

    def show_help(self, args: List[str] = None) -> int:
        """Показать справочную информацию."""
        print_header("Session Manager - Справка")

        print("ИСПОЛЬЗОВАНИЕ:")
        print("  session <команда> [опции]\n")

        print("КОМАНДЫ ПРОЕКТОВ:")
        print("  project add <название> <путь> [--alias <псевдоним>]")
        print("    Добавить новый проект")
        print("  project list")
        print("    Список всех проектов")
        print("  project remove <название>")
        print("    Удалить проект")
        print("  project info <название>")
        print("    Показать информацию о проекте\n")

        print("КОМАНДЫ СЕССИЙ:")
        print("  start [проект] [описание]")
        print("    Начать новую сессию")
        print("  end [проект]")
        print("    Завершить активную сессию")
        print("  status [проект]")
        print("    Показать текущий статус")
        print("  history [проект] [--limit N]")
        print("    Показать историю сессий")
        print("  stats [проект]")
        print("    Показать статистику сессий\n")

        print("ДРУГИЕ КОМАНДЫ:")
        print("  help")
        print("    Показать эту справку")
        print("  version")
        print("    Показать версию\n")

        print("ПРИМЕРЫ:")
        print("  # Добавить проект")
        print("  session project add myapp /path/to/myapp --alias ma\n")

        print("  # Начать работу")
        print("  session start myapp\n")

        print("  # Завершить сессию")
        print("  session end\n")

        print("  # Проверить статус")
        print("  session status\n")

        return 0

    def show_version(self, args: List[str] = None) -> int:
        """Показать информацию о версии."""
        from .. import __version__

        print(f"Session Manager v{__version__}")
        print("Умное отслеживание сессий для разработчиков")

        return 0
