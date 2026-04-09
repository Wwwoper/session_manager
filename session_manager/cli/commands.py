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
            "abort": self.cmd_abort,
            "ls": self.cmd_ls,
            "resume": self.cmd_resume,
            "edit": self.cmd_edit,
            "status": self.cmd_status,
            "history": self.cmd_history,
            "stats": self.cmd_stats,
            "completion": self.cmd_completion,
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
            print_error("Использование: session project remove <название> [--force]")
            return 1

        force = False
        name = None

        for arg in args:
            if arg in ("--force", "-y"):
                force = True
            elif not arg.startswith("--"):
                name = arg

        if not name:
            print_error("Использование: session project remove <название> [--force]")
            return 1

        # Подтверждение удаления
        if not force:
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

    # ==================== Команда ls — все активные сессии ====================

    def cmd_ls(self, args: List[str]) -> int:
        """Показать все активные сессии across все проекты."""
        projects_info = self.registry.list(sort_by_usage=True)

        if not projects_info:
            print_info("Пока нет зарегистрированных проектов")
            print_info("Добавьте проект: session project add <название> <путь>")
            return 0

        # Собираем информацию об активных сессиях
        active_sessions = []
        for proj_info in projects_info:
            try:
                project = self.registry.get(proj_info.name)
                if not project:
                    continue

                sm = SessionManager(project)
                active = sm.get_active()
                if active:
                    active_sessions.append({
                        "project": project.name,
                        "alias": proj_info.alias or "-",
                        "start_time": active["start_time"],
                        "description": active.get("description") or "-",
                        "session": active,
                    })
            except Exception:
                continue

        if not active_sessions:
            print_info("Нет активных сессий")
            print_info("Начните сессию: session start [проект]")
            return 0

        print_header("🔍 Активные сессии")

        from datetime import datetime

        for i, session_info in enumerate(active_sessions, 1):
            project_name = session_info["project"]
            alias = session_info["alias"]
            active = session_info["session"]

            display_name = project_name
            if alias != "-":
                display_name = f"{project_name} ({alias})"

            print(f"\n{i}. {display_name}")

            start = datetime.fromisoformat(active["start_time"])
            duration = int((datetime.now() - start).total_seconds())

            print(f"   Начата: {format_timestamp(active['start_time'])}")
            print(f"   Длительность: {format_duration(duration)}")
            if active.get("description"):
                print(f"   Описание: {active['description']}")
            if active.get("branch"):
                print(f"   Ветка: {active['branch']}")

        print(f"\n Всего активных: {len(active_sessions)}")

        return 0

    # ==================== Команды сессий ====================

    def cmd_start(self, args: List[str]) -> int:
        """Начать новую сессию."""
        # Разбор аргументов: [--force|-y] [--no-tests] [проект] [описание]
        force = False
        no_tests = False
        remaining_args = []

        for arg in args:
            if arg in ("--force", "-y"):
                force = True
            elif arg == "--no-tests":
                no_tests = True
            else:
                remaining_args.append(arg)

        # Попытка разобрать аргументы
        project_name = None
        description = ""

        # Если первый аргумент похож на название проекта (короткий, без пробелов)
        # и проект существует, то считаем его названием проекта
        if remaining_args:
            potential_project = remaining_args[0]
            if self.registry.exists(potential_project):
                project_name = potential_project
                description = " ".join(remaining_args[1:]) if len(remaining_args) > 1 else ""
            else:
                # Иначе всё считаем описанием
                description = " ".join(remaining_args)

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

            if not force:
                print_header(f"🚀 Запуск новой сессии: {project.name}")

                # Показать последний контекст
                self._show_last_context(project)

                # Показать статус git
                self._show_git_status(project)

                # Показать задачи GitHub
                self._show_github_issues(project)

                # Запустить тесты (если не пропущено)
                if not no_tests:
                    self._show_test_status(project)
                else:
                    print_info("⏩ Тесты пропущены (--no-tests)")

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
            print_info(f"ID сессии: {session['id']}")

            return 0

        except SessionError as e:
            print_error(f"Не удалось начать сессию: {e}")
            return 1

    def cmd_end(self, args: List[str]) -> int:
        """Завершить активную сессию."""
        # Разбор аргументов: [--force|-y] [--diff] [проект]
        force = False
        show_diff = False
        project_name = None

        for arg in args:
            if arg in ("--force", "-y"):
                force = True
            elif arg == "--diff":
                show_diff = True
            elif not arg.startswith("--"):
                project_name = arg

        # Если проект не указан явно — ищем активную сессию среди всех проектов
        if project_name is None:
            project = self._find_active_session()
            if not project:
                return 1
        else:
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

            # Режим --force: завершить без вопросов
            if force:
                return self._end_session_forced(project, sm, active)

            return self._end_session_interactive(project, sm, active, show_diff=show_diff)

        except SessionError as e:
            print_error(f"Не удалось завершить сессию: {e}")
            return 1

    def _end_session_interactive(self, project, sm, active, show_diff=False) -> int:
        """Интерактивное завершение сессии."""
        from datetime import datetime

        print_header(f"💾 Завершение сессии: {project.name}")

        # Показать подсказку с текущим next_action
        cm = ContextManager(project)
        current_next_action = cm.get_next_action_from_project_md()

        # Показать изменения git
        git = GitIntegration(project.path)
        if git.is_git_repo() and git.has_uncommitted_changes():
            if show_diff:
                print_subsection("📝 Изменения (diff)")
                diff_output = git.get_diff()
                if diff_output:
                    print(diff_output)
                else:
                    print_info("Нет изменений в diff")
            else:
                print_subsection("📋 Изменённые файлы")
                files = git.get_changed_files()
                if files:
                    for f in files:
                        print(f"  • {f}")
                else:
                    print_info("Нет изменённых файлов")

        # Получить итог
        print("Что было выполнено в этой сессии?")
        summary = input("Итог: ").strip()

        print("\nКакое следующее конкретное действие?")
        print("(например, 'Добавить тесты для функции parse_data')")
        if current_next_action:
            print(f"[Текущее: {current_next_action}]")
        next_action = input("Следующее действие: ").strip()

        # Проверить незакоммиченные изменения (для коммита)
        if git.has_uncommitted_changes():
            print_warning("\n⚠️  Обнаружены незакоммиченные изменения!")
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
        print_info(f"ID сессии: {completed['id']}")
        print_info(f"Снимок сохранен: {Path(snapshot_path).name}")
        print_info("PROJECT.md обновлен")

        return 0

    def _end_session_forced(self, project, sm, active) -> int:
        """Принудительное завершение сессии без вопросов."""
        from datetime import datetime

        # Рассчитать продолжительность
        start_time = datetime.fromisoformat(active["start_time"])
        end_time = datetime.now()
        duration = int((end_time - start_time).total_seconds())

        # Завершить сессию без резюме и next_action
        active["end_time"] = end_time.isoformat()
        active["duration"] = duration
        active["summary"] = ""
        active["next_action"] = ""

        # Сохранить
        try:
            data = project.get_sessions_data()
            for i, session in enumerate(data["sessions"]):
                if session["id"] == active["id"]:
                    data["sessions"][i] = active
                    break
            data["active_session"] = None
            project.save_sessions_data(data)
        except ProjectError as e:
            raise SessionError(f"Не удалось завершить сессию: {e}")

        print_success(f"Сессия в проекте '{project.name}' завершена!")
        print_info(f"Продолжительность: {format_duration(duration)}")

        return 0

    def cmd_abort(self, args: List[str]) -> int:
        """Принудительно завершить активную сессию без вопросов."""
        # Получить проект (args[0] если передан)
        project_name = args[0] if args else None

        # Если проект не указан — ищем активную сессию среди всех проектов
        if project_name is None:
            project = self._find_active_session()
            if not project:
                return 1
        else:
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

            # Рассчитать продолжительность
            from datetime import datetime

            start_time = datetime.fromisoformat(active["start_time"])
            end_time = datetime.now()
            duration = int((end_time - start_time).total_seconds())

            # Завершить сессию без резюме и next_action
            active["end_time"] = end_time.isoformat()
            active["duration"] = duration
            active["summary"] = ""
            active["next_action"] = ""

            # Сохранить
            try:
                data = project.get_sessions_data()
                for i, session in enumerate(data["sessions"]):
                    if session["id"] == active["id"]:
                        data["sessions"][i] = active
                        break
                data["active_session"] = None
                project.save_sessions_data(data)
            except ProjectError as e:
                raise SessionError(f"Не удалось завершить сессию: {e}")

            print_success(f"Сессия в проекте '{project.name}' принудительно завершена!")
            print_info(f"Продолжительность: {format_duration(duration)}")
            print_info("Резюме и следующее действие не сохранены")

            return 0

        except SessionError as e:
            print_error(f"Не удалось завершить сессию: {e}")
            return 1

    def cmd_resume(self, args: List[str]) -> int:
        """Продолжить работу на основе последней завершённой сессии."""
        # Разбор аргументов: [--force|-y] [проект]
        force = False
        project_name = None

        for arg in args:
            if arg in ("--force", "-y"):
                force = True
            elif not arg.startswith("--"):
                project_name = arg

        # Если проект не указан — ищем активную или последнюю сессию
        if project_name is None:
            # Сначала проверим активную сессию
            project = self._find_active_session()
            if project:
                # Показать контекст активной сессии
                print_warning("Уже есть активная сессия!")
                print()
                print_subsection("📋 Активная сессия")
                print(f"   Проект: {project.name}")
                sm = SessionManager(project)
                active = sm.get_active()
                if active:
                    print(f"   Начата: {format_timestamp(active['start_time'])}")
                    if active.get("description"):
                        print(f"   Описание: {active['description']}")
                    from datetime import datetime
                    start = datetime.fromisoformat(active["start_time"])
                    duration = int((datetime.now() - start).total_seconds())
                    print(f"   Длительность: {format_duration(duration)}")
                print()
                print_info("Варианты:")
                print("  session end        — завершить активную сессию")
                print("  session abort      — завершить без резюме")
                print("  session resume <проект> — продолжить другой проект")
                return 1

            # Нет активной — ищем current_project или автоопределяем
            if self.config.current_project:
                project = self.registry.get(self.config.current_project)
                if project:
                    self._cached_project = project
            if not project:
                project = self.registry.detect_current()
                if project:
                    print_info(f"📍 Автоопределен проект: {project.name}")
                    self._cached_project = project
        else:
            project = self._resolve_project(project_name, auto_detect=True)

        if not project:
            return 1

        try:
            sm = SessionManager(project)

            # Проверить активную сессию
            if sm.get_active():
                print_warning("Уже есть активная сессия!")
                print_info("Завершите её: session end или session abort")
                return 1

            # Найти последнюю завершённую сессию
            history = sm.get_history(limit=1)

            if not history:
                print_info(f"Нет завершённых сессий в проекте '{project.name}'")
                print_info("Начните первую сессию: session start")
                return 0

            last_session = history[0]

            # Показать контекст последней сессии
            print_header(f"▶️  Продолжение сессии: {project.name}")

            print_subsection("📋 Последняя сессия")
            print(f"   Начало: {format_timestamp(last_session['start_time'])}")
            if last_session.get("end_time"):
                print(f"   Конец: {format_timestamp(last_session['end_time'])}")
            print(f"   Длительность: {format_duration(last_session['duration'])}")

            if last_session.get("description"):
                print(f"   Описание: {last_session['description']}")

            if last_session.get("summary"):
                print(f"\n   Резюме: {last_session['summary']}")

            next_action = last_session.get("next_action", "")

            # Показать next_action
            if next_action:
                print(f"\n📌 Запланированное действие:")
                print(f"   {next_action}")
            else:
                # Попробовать из PROJECT.md
                cm = ContextManager(project)
                next_action_md = cm.get_next_action_from_project_md()
                if next_action_md:
                    print(f"\n📌 Запланированное действие (из PROJECT.md):")
                    print(f"   {next_action_md}")
                    next_action = next_action_md

            if force:
                # Автоматически начать сессию с next_action как описанием
                description = next_action if next_action else ""
                session = sm.start(description=description)

                git = GitIntegration(project.path)
                if git.is_git_repo():
                    sm.update_session_metadata(
                        session["id"],
                        branch=git.get_current_branch(),
                        last_commit=git.get_last_commit(),
                    )

                print_success("\nСессия продолжена!")
                print_info(f"ID сессии: {session['id']}")
                if description:
                    print_info(f"Описание: {description}")

                return 0

            # Интерактивный режим
            print("\nНачать новую сессию?")
            print("(Enter — начать, описание из запланированного действия)")
            response = input("Продолжить? (Y/n): ").strip().lower()

            if response == "n":
                print_info("Отменено")
                return 0

            description = next_action if next_action else ""
            session = sm.start(description=description)

            git = GitIntegration(project.path)
            if git.is_git_repo():
                sm.update_session_metadata(
                    session["id"],
                    branch=git.get_current_branch(),
                    last_commit=git.get_last_commit(),
                )

            print_success("\nСессия продолжена!")
            print_info(f"ID сессии: {session['id']}")
            if description:
                print_info(f"Описание: {description}")

            return 0

        except SessionError as e:
            print_error(f"Не удалось продолжить сессию: {e}")
            return 1

    def cmd_edit(self, args: List[str]) -> int:
        """Редактировать завершённую сессию по ID."""
        if len(args) < 1:
            print_error("Использование: session edit <id> [проект]")
            print_info("Найдите ID в истории: session history")
            return 1

        session_id = args[0]
        project_name = args[1] if len(args) > 1 else None

        # Поддержать сокращённый ID (первые 8 символов)
        if len(session_id) < 8:
            print_error("ID сессии слишком короткий (минимум 8 символов)")
            return 1

        # Разрешить проект
        if project_name:
            project = self._resolve_project(project_name, auto_detect=True)
        else:
            # Ищем сессию по ID во всех проектах
            project = self._find_session_by_id(session_id)

        if not project:
            return 1

        try:
            sm = SessionManager(project)
            # Найти по частичному ID
            session = self._find_session_partial(sm, session_id)

            if not session:
                print_error(f"Сессия '{session_id[:8]}...' не найдена в проекте '{project.name}'")
                return 1

            if session.get("end_time") is None:
                print_warning("Это активная сессия. Используйте session end для завершения.")
                return 1

            print_header(f"✏️  Редактирование сессии: {project.name}")

            # Показать текущие значения
            print_subsection("Текущие значения")
            print(f"Описание: {session.get('description') or '-'}")
            print(f"Резюме: {session.get('summary') or '-'}")
            print(f"Следующее действие: {session.get('next_action') or '-'}")

            # Запросить новые значения
            print("\nНовые значения (Enter — оставить без изменений):")
            new_description = input(f"Описание [{session.get('description') or '-'}]: ").strip()
            new_summary = input(f"Резюме [{session.get('summary') or '-'}]: ").strip()
            new_next_action = input(f"Следующее действие [{session.get('next_action') or '-'}]: ").strip()

            # Обновить только если введены новые значения
            updated = False
            if new_description:
                session["description"] = new_description
                updated = True
            if new_summary:
                session["summary"] = new_summary
                updated = True
            if new_next_action:
                session["next_action"] = new_next_action
                updated = True

            if not updated:
                print_info("Ничего не изменено")
                return 0

            # Сохранить
            try:
                data = project.get_sessions_data()
                for i, s in enumerate(data["sessions"]):
                    if s["id"] == session_id:
                        data["sessions"][i] = session
                        break
                project.save_sessions_data(data)
            except ProjectError as e:
                raise SessionError(f"Не удалось сохранить изменения: {e}")

            print_success("Сессия обновлена!")
            return 0

        except SessionError as e:
            print_error(f"Ошибка: {e}")
            return 1

    def _find_session_by_id(self, session_id: str) -> Optional[Project]:
        """
        Найти проект по ID сессии (поддержка сокращённого ID).

        Возвращает:
            Project или None
        """
        # Проверить текущий/кэшированный проект первым
        if self._cached_project:
            sm = SessionManager(self._cached_project)
            session = self._find_session_partial(sm, session_id)
            if session:
                return self._cached_project

        if self.config.current_project:
            project = self.registry.get(self.config.current_project)
            if project:
                sm = SessionManager(project)
                session = self._find_session_partial(sm, session_id)
                if session:
                    self._cached_project = project
                    return project

        # Искать во всех проектах
        projects = self.registry.list(sort_by_usage=True)
        for proj_info in projects:
            project = self.registry.get(proj_info.name)
            if not project:
                continue

            sm = SessionManager(project)
            session = self._find_session_partial(sm, session_id)
            if session:
                # Обновить session_id на полный
                return project

        print_error(f"Сессия '{session_id[:8]}...' не найдена ни в одном проекте")
        print_info("Укажите проект явно: session edit <id> <проект>")
        return None

    def _find_session_partial(self, sm, session_id: str):
        """Найти сессию по частичному ID."""
        sessions = sm.get_all_sessions()
        for s in sessions:
            if s.get("id", "").startswith(session_id):
                return s
        return None

    def cmd_status(self, args: List[str]) -> int:
        """Показать статус проекта."""
        # Разбор аргументов: [--no-tests] [проект]
        no_tests = False
        project_name = None

        for arg in args:
            if arg == "--no-tests":
                no_tests = True
            elif not arg.startswith("--"):
                project_name = arg

        # Если проект не указан — ищем активную сессию, затем current_project
        if project_name is None:
            project = self._find_active_session()
            if not project:
                # Если нет активной сессии — пробуем current_project
                if self.config.current_project:
                    project = self.registry.get(self.config.current_project)
                    if project:
                        self._cached_project = project
                    else:
                        # Попробовать автоопределение
                        project = self.registry.detect_current()
                        if project:
                            print_info(f"📍 Автоопределен проект: {project.name}")
                            self._cached_project = project
                if not project:
                    # Попробовать автоопределение
                    project = self.registry.detect_current()
                    if project:
                        print_info(f"📍 Автоопределен проект: {project.name}")
                        self._cached_project = project
        else:
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
            print("Нет активной сессии")
            print_info("Начните сессию: session start [проект]")
            print()

        # Общее время за сегодня
        today_time = sm.get_total_time_today()
        if today_time > 0:
            print_subsection("⏱️  Всего за сегодня")
            print(f"   {format_duration(today_time)}\n")

        # Последний контекст
        self._show_last_context(project)

        # Статус Git
        self._show_git_status(project)

        # Статус тестов
        if not no_tests:
            self._show_test_status(project)
        else:
            print_info("⏩ Тесты пропущены (--no-tests)")

        return 0

    def cmd_history(self, args: List[str]) -> int:
        """Показать историю сессий."""
        # Разбор аргументов: может быть [проект] или [--limit N] [--full]
        project_name = None
        limit = 10
        full = False

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
            elif arg == "--full":
                full = True
                i += 1
            elif not arg.startswith("--"):
                # Предполагаем, что это название проекта
                project_name = arg
                i += 1
            else:
                i += 1

        # Получить проект
        if project_name is None:
            project = self._find_active_session()
            if not project:
                # Если нет активной сессии — пробуем current_project
                if self.config.current_project:
                    project = self.registry.get(self.config.current_project)
                    if project:
                        self._cached_project = project
                if not project:
                    project = self.registry.detect_current()
                    if project:
                        print_info(f"📍 Автоопределен проект: {project.name}")
                        self._cached_project = project
        else:
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
            sid = session['id'] if full else session['id'][:12]
            if len(session['id']) > 12 and not full:
                sid += "..."
            print(f"   ID: {sid}")
            print(f"   Начата: {format_timestamp(session['start_time'])}")
            if session.get("end_time"):
                print(f"   Завершена: {format_timestamp(session['end_time'])}")
            print(f"   Продолжительность: {format_duration(session['duration'])}")

            if session.get("description"):
                desc = session["description"] if full else session["description"][:80]
                if len(session.get("description", "")) > 80 and not full:
                    desc += "..."
                print(f"   Описание: {desc}")

            if session.get("summary"):
                summary = session["summary"] if full else session["summary"][:80]
                if len(session.get("summary", "")) > 80 and not full:
                    summary += "..."
                print(f"   Итог: {summary}")

            if session.get("next_action"):
                action = session["next_action"] if full else session["next_action"][:60]
                if len(session.get("next_action", "")) > 60 and not full:
                    action += "..."
                print(f"   Следующее: {action}")

            if session.get("branch"):
                print(f"   Ветка: {session['branch']}")

        print(f"\nПоказано {len(history)} последних сессий")

        return 0

    def cmd_stats(self, args: List[str]) -> int:
        """Показать статистику сессий."""
        # Получить проект
        project_name = args[0] if args else None

        if project_name is None:
            project = self._find_active_session()
            if not project:
                # Если нет активной сессии — пробуем current_project
                if self.config.current_project:
                    project = self.registry.get(self.config.current_project)
                    if project:
                        self._cached_project = project
                if not project:
                    project = self.registry.detect_current()
                    if project:
                        print_info(f"📍 Автоопределен проект: {project.name}")
                        self._cached_project = project
        else:
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

    def _find_active_session(self) -> Optional[Project]:
        """
        Найти проект с активной сессией среди всех проектов.

        Возвращает:
            Project с активной сессией или None
        """
        projects = self.registry.list(sort_by_usage=True)

        for project_info in projects:
            project = self.registry.get(project_info.name)
            if not project:
                continue

            sm = SessionManager(project)
            if sm.get_active():
                print_info(f"🔍 Найдена активная сессия в проекте: {project.name}")
                self._cached_project = project
                return project

        print_warning("Нет активной сессии ни в одном проекте")
        print_info("Начните сессию с помощью: session start [проект]")
        return None

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
        print("  start [проект] [описание] [--no-tests]")
        print("    Начать новую сессию")
        print("  end [проект] [--force|-y] [--diff]")
        print("    Завершить активную сессию")
        print("  abort [проект]")
        print("    Принудительно завершить без вопросов")
        print("  resume [проект] [--force|-y]")
        print("    Продолжить сессию на основе последней")
        print("  edit <id> [проект]")
        print("    Редактировать завершённую сессию")
        print("  ls")
        print("    Все активные сессии")
        print("  status [проект] [--no-tests]")
        print("    Показать текущий статус")
        print("  history [проект] [--limit N] [--full]")
        print("    Показать историю сессий")
        print("  stats [проект]")
        print("    Показать статистику сессий\n")

        print("ДРУГИЕ КОМАНДЫ:")
        print("  help")
        print("    Показать эту справку")
        print("  version")
        print("    Показать версию")
        print("  completion [bash|zsh|fish]")
        print("    Сгенерировать скрипт автодополнения\n")

        print("ОБЩИЕ ФЛАГИ:")
        print("  --force, -y")
        print("    Пропустить интерактивные подтверждения")
        print("  --no-tests")
        print("    Пропустить запуск тестов при start/status")
        print("  --diff")
        print("    Показать полный diff при session end")
        print("  --full")
        print("    Полный текст без обрезки в history\n")

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

    def cmd_completion(self, args: List[str]) -> int:
        """Сгенерировать скрипт автодополнения для shell."""
        shell = "bash"
        if args and args[0] in ("bash", "zsh", "fish"):
            shell = args[0]

        if shell == "bash":
            self._print_bash_completion()
        elif shell == "zsh":
            self._print_zsh_completion()
        elif shell == "fish":
            self._print_fish_completion()

        return 0

    def _print_bash_completion(self) -> None:
        """Bash completion script."""
        print("""# Session Manager — Bash автодополнение
# Добавьте в ~/.bashrc:
#   source <(session completion bash)

_session_completion() {
    local cur="${COMP_WORDS[COMP_CWORD]}"
    local commands="project start end abort ls resume edit status history stats help version completion"
    local project_commands="add list remove info"

    if [[ ${COMP_CWORD} -eq 1 ]]; then
        COMPREPLY=( $(compgen -W "${commands}" -- "${cur}") )
    elif [[ ${COMP_WORDS[1]} == "project" && ${COMP_CWORD} -eq 2 ]]; then
        COMPREPLY=( $(compgen -W "${project_commands}" -- "${cur}") )
    elif [[ ${COMP_WORDS[1]} =~ ^(start|end|abort|resume|status|history|stats|edit|project)$ ]]; then
        # Автодополнение имён проектов
        local projects
        projects=$(python3 -c "
import json, pathlib
config = pathlib.Path.home() / '.session_manager' / 'config.json'
if config.exists():
    data = json.loads(config.read_text())
    for name, info in data.get('projects', {}).items():
        print(name)
        if info.get('alias'):
            print(info['alias'])
" 2>/dev/null)
        COMPREPLY=( $(compgen -W "${projects}" -- "${cur}") )
    else
        COMPREPLY=( $(compgen -W "--force -y --no-tests --diff --full --limit" -- "${cur}") )
    fi
}
complete -F _session_completion session""")

    def _print_zsh_completion(self) -> None:
        """Zsh completion script."""
        print("""# Session Manager — Zsh автодополнение
# Добавьте в ~/.zshrc:
#   eval "$(session completion zsh)"

_session() {
    local -a commands
    commands=(
        'project:Управление проектами'
        'start:Начать сессию'
        'end:Завершить сессию'
        'abort:Принудительно завершить'
        'ls:Список активных сессий'
        'resume:Продолжить сессию'
        'edit:Редактировать сессию'
        'status:Показать статус'
        'history:История сессий'
        'stats:Статистика'
        'help:Справка'
        'version:Версия'
        'completion:Генерация автодополнения'
    )

    local -a project_cmds
    project_cmds=(
        'add:Добавить проект'
        'list:Список проектов'
        'remove:Удалить проект'
        'info:Информация о проекте'
    )

    local -a projects
    projects=("${(@f)$(python3 -c \"
import json, pathlib
config = pathlib.Path.home() / '.session_manager' / 'config.json'
if config.exists():
    data = json.loads(config.read_text())
    for name in data.get('projects', {}):
        print(name)
\" 2>/dev/null)}")

    _arguments \\
        '1: :->command' \\
        '*: :->args' \\
        '--force[Пропустить подтверждения]' \\
        '--no-tests[Пропустить тесты]' \\
        '--diff[Показать diff]' \\
        '--full[Полный текст]' && return 0

    case $state in
        command)
            _describe 'command' commands
            ;;
        args)
            case $words[2] in
                project)
                    _describe 'подкоманда' project_cmds
                    ;;
                start|end|abort|resume|status|history|stats|edit)
                    _describe 'проект' projects
                    ;;
            esac
            ;;
    esac
}

compdef _session session""")

    def _print_fish_completion(self) -> None:
        """Fish completion script."""
        print("""# Session Manager — Fish автодополнение
# Добавьте в ~/.config/fish/completions/session.fish

complete -c session -n "__fish_use_subcommand" -a "project" -d "Управление проектами"
complete -c session -n "__fish_use_subcommand" -a "start" -d "Начать сессию"
complete -c session -n "__fish_use_subcommand" -a "end" -d "Завершить сессию"
complete -c session -n "__fish_use_subcommand" -a "abort" -d "Принудительно завершить"
complete -c session -n "__fish_use_subcommand" -a "ls" -d "Список активных сессий"
complete -c session -n "__fish_use_subcommand" -a "resume" -d "Продолжить сессию"
complete -c session -n "__fish_use_subcommand" -a "edit" -d "Редактировать сессию"
complete -c session -n "__fish_use_subcommand" -a "status" -d "Показать статус"
complete -c session -n "__fish_use_subcommand" -a "history" -d "История сессий"
complete -c session -n "__fish_use_subcommand" -a "stats" -d "Статистика"
complete -c session -n "__fish_use_subcommand" -a "help" -d "Справка"
complete -c session -n "__fish_use_subcommand" -a "version" -d "Версия"

complete -c session -n "__fish_seen_subcommand_from project" -a "add" -d "Добавить проект"
complete -c session -n "__fish_seen_subcommand_from project" -a "list" -d "Список проектов"
complete -c session -n "__fish_seen_subcommand_from project" -a "remove" -d "Удалить проект"
complete -c session -n "__fish_seen_subcommand_from project" -a "info" -d "Информация"

complete -c session -n "__fish_seen_subcommand_from start end abort resume status history stats edit" -a "(python3 -c \\"
import json, pathlib
config = pathlib.Path.home() / '.session_manager' / 'config.json'
if config.exists():
    data = json.loads(config.read_text())
    for name in data.get('projects', {}):
        print(name)
\\" 2>/dev/null)" -d "Проект"

complete -c session -s f -l force -d "Пропустить подтверждения"
complete -c session -l no-tests -d "Пропустить тесты"
complete -c session -l diff -d "Показать diff"
complete -c session -l full -d "Полный текст"
""")

    def show_version(self, args: List[str] = None) -> int:
        """Показать информацию о версии."""
        from .. import __version__

        print(f"Session Manager v{__version__}")
        print("Умное отслеживание сессий для разработчиков")

        return 0
