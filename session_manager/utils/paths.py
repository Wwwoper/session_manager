"""
Утилиты для работы с путями в Session Manager

Управляет всеми файловыми путями и структурой директорий.
"""

from pathlib import Path
from typing import Optional


def get_storage_dir() -> Path:
    """
    Получает основную директорию хранения для Session Manager.

    Returns:
        Путь к ~/.session_manager/
    """
    return Path.home() / ".session_manager"


def get_projects_dir() -> Path:
    """
    Получает директорию проектов.

    Returns:
        Путь к ~/.session_manager/projects/
    """
    return get_storage_dir() / "projects"


def get_project_dir(project_name: str) -> Path:
    """
    Получает директорию для конкретного проекта.

    Args:
        project_name: Название проекта

    Returns:
        Путь к ~/.session_manager/projects/{project_name}/
    """
    return get_projects_dir() / project_name


def get_snapshots_dir(project_name: str) -> Path:
    """
    Получает директорию снимков для конкретного проекта.

    Args:
        project_name: Название проекта

    Returns:
        Путь к ~/.session_manager/projects/{project_name}/snapshots/
    """
    return get_project_dir(project_name) / "snapshots"


def get_config_file() -> Path:
    """
    Получает путь к глобальному файлу конфигурации.

    Returns:
        Путь к ~/.session_manager/config.json
    """
    return get_storage_dir() / "config.json"


def get_sessions_file(project_name: str) -> Path:
    """
    Получает файл сессий для конкретного проекта.

    Args:
        project_name: Название проекта

    Returns:
        Путь к ~/.session_manager/projects/{project_name}/sessions.json
    """
    return get_project_dir(project_name) / "sessions.json"


def get_project_md_file(project_name: str) -> Path:
    """
    Получает путь к файлу PROJECT.md для конкретного проекта.

    Args:
        project_name: Название проекта

    Returns:
        Путь к ~/.session_manager/projects/{project_name}/PROJECT.md
    """
    return get_project_dir(project_name) / "PROJECT.md"


def ensure_directories(*paths: Path) -> None:
    """
    Обеспечивает существование директорий, создавая их при необходимости.

    Args:
        *paths: Переменное количество объектов Path для проверки существования
    """
    for path in paths:
        path.mkdir(parents=True, exist_ok=True)


def ensure_storage_structure() -> None:
    """
    Обеспечивает существование полной структуры хранения.
    Создает все необходимые директории для Session Manager.
    """
    ensure_directories(
        get_storage_dir(),
        get_projects_dir(),
    )


def ensure_project_structure(project_name: str) -> None:
    """
    Обеспечивает существование структуры директорий для конкретного проекта.

    Args:
        project_name: Название проекта
    """
    ensure_directories(
        get_project_dir(project_name),
        get_snapshots_dir(project_name),
    )


def detect_current_project(registry_projects: dict) -> Optional[str]:
    """
    Определяет текущий проект на основе текущей рабочей директории.

    Пытается сопоставить путь текущей директории с зарегистрированными проектами.
    Также ищет директорию .git для сопоставления с git-репозиториями.

    Args:
        registry_projects: Словарь зарегистрированных проектов {name: {"path": str, ...}}

    Returns:
        Название проекта если найдено, иначе None
    """
    cwd = Path.cwd().resolve()

    # Сначала попробовать точное совпадение или если CWD внутри пути проекта
    for project_name, project_info in registry_projects.items():
        project_path = Path(project_info.get("path", "")).resolve()

        try:
            # Проверить, является ли текущая директория проектом или внутри него
            cwd.relative_to(project_path)
            return project_name
        except ValueError:
            # Не поддиректория, продолжить
            continue

    # Затем попробовать найти директорию .git и сопоставить по пути
    git_dir = find_git_root(cwd)
    if git_dir:
        for project_name, project_info in registry_projects.items():
            project_path = Path(project_info.get("path", "")).resolve()
            if project_path == git_dir:
                return project_name

    return None


def find_git_root(start_path: Path) -> Optional[Path]:
    """
    Находит корень git-репозитория путем поиска директории .git.

    Ищет от start_path вверх по родительским директориям.

    Args:
        start_path: Путь для начала поиска

    Returns:
        Путь к корню git-репозитория или None, если не найден
    """
    current = start_path.resolve()

    # Поиск вплоть до корневой директории
    while current != current.parent:
        git_dir = current / ".git"
        if git_dir.exists():
            return current
        current = current.parent

    return None


def is_valid_project_path(path: str) -> bool:
    """
    Проверяет, является ли путь допустимым для проекта.

    Args:
        path: Строка пути для проверки

    Returns:
        True если путь существует и является директорией
    """
    try:
        p = Path(path).resolve()
        return p.exists() and p.is_dir()
    except (OSError, ValueError):
        return False


def normalize_project_path(path: str) -> str:
    """
    Нормализует путь проекта к абсолютному разрешенному пути.

    Args:
        path: Строка пути для нормализации

    Returns:
        Абсолютный разрешенный путь в виде строки
    """
    return str(Path(path).resolve())
