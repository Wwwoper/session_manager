"""
Представление и управление проектом
Обрабатывает операции с отдельными проектами и управление файлами.
"""

from pathlib import Path
from typing import Optional
from ..utils.paths import (
    get_project_dir,
    get_sessions_file,
    get_project_md_file,
    get_snapshots_dir,
    ensure_project_structure,
)
from .storage import Storage, StorageError


class ProjectError(Exception):
    """Базовое исключение для ошибок, связанных с проектами"""

    pass


class Project:
    """
    Представляет отдельный проект в Session Manager.

    Управляет файлами и директориями конкретного проекта:
    - sessions.json: история сессий
    - PROJECT.md: файл контекста
    - snapshots/: директория для снимков контекста
    """

    def __init__(self, name: str, path: str):
        """
        Инициализирует проект.

        Аргументы:
            name: Название проекта (уникальный идентификатор)
            path: Путь к директории проекта на диске
        """
        self.name = name
        self.path = Path(path).resolve()

        # Директория данных проекта в ~/.session_manager/projects/{name}/
        self._project_dir = get_project_dir(name)

        # Пути к файлам
        self.sessions_file = get_sessions_file(name)
        self.project_md_file = get_project_md_file(name)
        self.snapshots_dir = get_snapshots_dir(name)

        self._storage = Storage()

    def ensure_structure(self) -> None:
        """
        Обеспечивает существование структуры директорий проекта.

        Создает:
        - Директорию проекта
        - Директорию снимков
        """
        ensure_project_structure(self.name)

    def exists(self) -> bool:
        """
        Проверяет, существует ли структура проекта.

        Возвращает:
            True, если директория проекта существует
        """
        return self._project_dir.exists()

    def get_project_md_content(self) -> str:
        """
        Читает содержимое PROJECT.md.

        Возвращает:
            Содержимое файла PROJECT.md или пустую строку, если файл не существует
        """
        try:
            return self._storage.read_text(self.project_md_file, default="")
        except StorageError as e:
            raise ProjectError(f"Не удалось прочитать PROJECT.md: {e}")

    def update_project_md(self, content: str) -> None:
        """
        Обновляет PROJECT.md новым содержимым.

        Аргументы:
            content: Новое содержимое для PROJECT.md

        Исключения:
            ProjectError: Если файл не может быть записан
        """
        try:
            self._storage.write_text(self.project_md_file, content)
        except StorageError as e:
            raise ProjectError(f"Не удалось обновить PROJECT.md: {e}")

    def has_project_md(self) -> bool:
        """
        Проверяет, существует ли PROJECT.md.

        Возвращает:
            True, если файл PROJECT.md существует
        """
        return self._storage.file_exists(self.project_md_file)

    def get_sessions_data(self) -> dict:
        """
        Загружает данные сессий из sessions.json.

        Возвращает:
            Словарь с данными сессий или пустой словарь, если файл не существует

        Исключения:
            ProjectError: Если файл существует, но не может быть прочитан
        """
        try:
            return self._storage.load_json(
                self.sessions_file, default={"sessions": [], "active_session": None}
            )
        except StorageError as e:
            raise ProjectError(f"Не удалось загрузить сессии: {e}")

    def save_sessions_data(self, data: dict) -> None:
        """
        Сохраняет данные сессий в sessions.json.

        Аргументы:
            data: Данные сессий для сохранения

        Исключения:
            ProjectError: Если данные не могут быть сохранены
        """
        try:
            self._storage.save_json(self.sessions_file, data)
        except StorageError as e:
            raise ProjectError(f"Не удалось сохранить сессии: {e}")

    def get_snapshot_path(self, timestamp: str) -> Path:
        """
        Получает путь к файлу снимка.

        Аргументы:
            timestamp: Строка временной метки (например, "20250115_1430")

        Возвращает:
            Путь к файлу снимка
        """
        return self.snapshots_dir / f"{timestamp}.md"

    def list_snapshots(self) -> list[Path]:
        """
        Перечисляет все файлы снимков.

        Возвращает:
            Список путей к файлам снимков, отсортированный по имени (сначала старые)
        """
        if not self.snapshots_dir.exists():
            return []

        snapshots = list(self.snapshots_dir.glob("*.md"))
        return sorted(snapshots)

    def get_latest_snapshot(self) -> Optional[Path]:
        """
        Получает самый последний файл снимка.

        Возвращает:
            Путь к последнему снимку или None, если снимков нет
        """
        snapshots = self.list_snapshots()
        return snapshots[-1] if snapshots else None

    def delete_old_snapshots(self, keep: int = 10) -> int:
        """
        Удаляет старые снимки, оставляя только самые последние.

        Аргументы:
            keep: Количество последних снимков для сохранения

        Возвращает:
            Количество удаленных снимков
        """
        snapshots = self.list_snapshots()

        if len(snapshots) <= keep:
            return 0

        to_delete = snapshots[:-keep]
        deleted = 0

        for snapshot in to_delete:
            try:
                self._storage.delete_file(snapshot)
                deleted += 1
            except StorageError:
                # Продолжаем удалять остальные, даже если один не удался
                pass

        return deleted

    def backup_sessions(self) -> Optional[Path]:
        """
        Создает резервную копию sessions.json.

        Возвращает:
            Путь к файлу резервной копии или None, если файл сессий не существует

        Исключения:
            ProjectError: Если создание резервной копии не удалось
        """
        try:
            return self._storage.backup_file(self.sessions_file)
        except StorageError as e:
            raise ProjectError(f"Не удалось создать резервную копию сессий: {e}")

    def get_project_info(self) -> dict:
        """
        Получает информацию о проекте.

        Возвращает:
            Словарь с информацией о проекте
        """
        sessions_data = self.get_sessions_data()
        snapshots = self.list_snapshots()

        return {
            "name": self.name,
            "path": str(self.path),
            "exists": self.exists(),
            "has_project_md": self.has_project_md(),
            "total_sessions": len(sessions_data.get("sessions", [])),
            "active_session": sessions_data.get("active_session"),
            "total_snapshots": len(snapshots),
            "latest_snapshot": str(snapshots[-1].name) if snapshots else None,
        }

    def __repr__(self) -> str:
        return f"Project(name={self.name!r}, path={self.path})"

    def __str__(self) -> str:
        return f"Project: {self.name} ({self.path})"
