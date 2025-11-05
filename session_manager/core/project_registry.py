"""
Управление реестром проектов
Предоставляет высокоуровневые операции для управления несколькими проектами.
"""

from typing import Optional, List, Dict
from pathlib import Path
from .config import GlobalConfig, ProjectInfo, ConfigError
from .project import Project, ProjectError
from ..utils.paths import detect_current_project


class ProjectRegistry:
    """
    Реестр для управления несколькими проектами.

    Предоставляет CRUD-операции и функциональность поиска для проектов.
    Интегрируется с GlobalConfig для сохранения состояния.
    """

    def __init__(self, config: GlobalConfig):
        """
        Инициализирует реестр проектов.

        Аргументы:
            config: Экземпляр GlobalConfig для сохранения состояния
        """
        self.config = config

    def add(
        self,
        name: str,
        path: str,
        alias: Optional[str] = None,
        set_as_current: bool = False,
    ) -> Project:
        """
        Добавляет новый проект в реестр.

        Аргументы:
            name: Уникальное название проекта
            path: Путь к директории проекта
            alias: Опциональное короткое псевдоним
            set_as_current: Если True, установить как текущий проект

        Возвращает:
            Созданный экземпляр Project

        Исключения:
            ConfigError: Если проект не может быть добавлен (ошибки валидации)
            ProjectError: Если структура проекта не может быть создана
        """
        # Добавляем в конфигурацию (обрабатывает валидацию)
        success = self.config.add_project(name, path, alias)

        if not success:
            raise ConfigError(f"Проект '{name}' уже существует")

        # Создаем экземпляр проекта
        project = Project(name, path)

        # Обеспечиваем существование структуры проекта
        try:
            project.ensure_structure()
        except Exception as e:
            # Откат: удаляем из конфигурации
            self.config.remove_project(name)
            raise ProjectError(f"Не удалось создать структуру проекта: {e}")

        # Устанавливаем как текущий, если запрошено
        if set_as_current:
            self.config.set_current_project(name)

        return project

    def remove(self, name: str, delete_data: bool = False) -> bool:
        """
        Удаляет проект из реестра.

        Аргументы:
            name: Название проекта или псевдоним
            delete_data: Если True, также удалить файлы данных проекта

        Возвращает:
            True, если проект был удален, False если не найден

        Исключения:
            ProjectError: Если удаление данных не удалось
        """
        # Получаем информацию о проекте для разрешения псевдонима
        project_info = self.config.get_project_info(name)
        if not project_info:
            return False

        actual_name = project_info.name

        # Удаляем данные, если запрошено
        if delete_data:
            project = Project(actual_name, project_info.path)
            try:
                # Удаляем файл сессий
                if project.sessions_file.exists():
                    project.sessions_file.unlink()

                # Удаляем PROJECT.md
                if project.project_md_file.exists():
                    project.project_md_file.unlink()

                # Удаляем директорию снимков
                if project.snapshots_dir.exists():
                    import shutil

                    shutil.rmtree(project.snapshots_dir)

                # Удаляем директорию проекта, если она пуста
                if project._project_dir.exists():
                    try:
                        project._project_dir.rmdir()
                    except OSError:
                        # Директория не пуста, оставляем ее
                        pass

            except Exception as e:
                raise ProjectError(f"Не удалось удалить данные проекта: {e}")

        # Удаляем из конфигурации
        return self.config.remove_project(actual_name)

    def list(self, sort_by_usage: bool = True) -> List[ProjectInfo]:
        """
        Перечисляет все зарегистрированные проекты.

        Аргументы:
            sort_by_usage: Если True, сортировать по последнему использованию (сначала последние)

        Возвращает:
            Список объектов ProjectInfo
        """
        if sort_by_usage:
            return self.config.get_projects_sorted_by_usage()
        else:
            return self.config.get_all_projects()

    def get(self, name: str) -> Optional[Project]:
        """
        Получает проект по имени или псевдониму.

        Аргументы:
            name: Название проекта или псевдоним

        Возвращает:
            Экземпляр Project или None, если не найден
        """
        project_info = self.config.get_project_info(name)
        if not project_info:
            return None

        return Project(project_info.name, project_info.path)

    def find_by_path(self, path: str) -> Optional[str]:
        """
        Находит название проекта по пути.

        Аргументы:
            path: Путь для поиска

        Возвращает:
            Название проекта, если найден, иначе None
        """
        search_path = Path(path).resolve()

        for project_info in self.config.get_all_projects():
            project_path = Path(project_info.path).resolve()
            if project_path == search_path:
                return project_info.name

        return None

    def get_current(self) -> Optional[Project]:
        """
        Получает текущий активный проект.

        Возвращает:
            Текущий экземпляр Project или None, если текущего проекта нет
        """
        if not self.config.current_project:
            return None

        return self.get(self.config.current_project)

    def set_current(self, name: Optional[str]) -> bool:
        """
        Устанавливает текущий активный проект.

        Аргументы:
            name: Название проекта/псевдоним для установки как текущий (или None для очистки)

        Возвращает:
            True если успешно, False если проект не найден
        """
        if name is not None:
            # Разрешаем псевдоним в фактическое имя
            project_info = self.config.get_project_info(name)
            if not project_info:
                return False
            name = project_info.name

        return self.config.set_current_project(name)

    def detect_current(self) -> Optional[Project]:
        """
        Автоматически определяет текущий проект на основе текущей рабочей директории.

        Возвращает:
            Обнаруженный экземпляр Project или None, если не найден
        """
        # Строим словарь проектов для обнаружения
        projects_dict = {
            name: {"path": info.path} for name, info in self.config.projects.items()
        }

        project_name = detect_current_project(projects_dict)

        if project_name:
            return self.get(project_name)

        return None

    def exists(self, name: str) -> bool:
        """
        Проверяет, существует ли проект в реестре.

        Аргументы:
            name: Название проекта или псевдоним

        Возвращает:
            True, если проект существует
        """
        return self.config.project_exists(name)

    def get_count(self) -> int:
        """
        Получает общее количество зарегистрированных проектов.

        Возвращает:
            Количество проектов
        """
        return self.config.get_project_count()

    def search(self, query: str) -> List[ProjectInfo]:
        """
        Ищет проекты по названию, псевдониму или пути.

        Аргументы:
            query: Поисковый запрос (без учета регистра)

        Возвращает:
            Список соответствующих объектов ProjectInfo
        """
        query_lower = query.lower()
        results = []

        for project_info in self.config.get_all_projects():
            # Поиск по названию
            if query_lower in project_info.name.lower():
                results.append(project_info)
                continue

            # Поиск по псевдониму
            if project_info.alias and query_lower in project_info.alias.lower():
                results.append(project_info)
                continue

            # Поиск по пути
            if query_lower in project_info.path.lower():
                results.append(project_info)
                continue

        return results

    def get_projects_summary(self) -> Dict[str, any]:
        """
        Получает сводную информацию обо всех проектах.

        Возвращает:
            Словарь со сводной статистикой
        """
        all_projects = self.config.get_all_projects()

        total_sessions = 0
        active_sessions = 0

        for project_info in all_projects:
            try:
                project = Project(project_info.name, project_info.path)
                sessions_data = project.get_sessions_data()
                total_sessions += len(sessions_data.get("sessions", []))
                if sessions_data.get("active_session"):
                    active_sessions += 1
            except ProjectError:
                # Пропускаем проекты с ошибками
                continue

        return {
            "total_projects": len(all_projects),
            "total_sessions": total_sessions,
            "active_sessions": active_sessions,
            "current_project": self.config.current_project,
        }

    def validate_all(self) -> Dict[str, List[str]]:
        """
        Проверяет все зарегистрированные проекты.

        Проверяет, существуют ли еще пути к проектам.

        Возвращает:
            Словарь с 'valid' и 'invalid' названиями проектов
        """
        valid = []
        invalid = []

        for project_info in self.config.get_all_projects():
            project_path = Path(project_info.path)
            if project_path.exists() and project_path.is_dir():
                valid.append(project_info.name)
            else:
                invalid.append(project_info.name)

        return {
            "valid": valid,
            "invalid": invalid,
        }
