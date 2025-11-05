"""
Интеграция с Git для Session Manager

Предоставляет информацию о репозитории git с корректной деградацией.
Все методы возвращают None, если git недоступен или это не репозиторий git.
"""

import subprocess
from pathlib import Path
from typing import Optional


class GitIntegration:
    """
    Интеграция с системой контроля версий Git.

    Предоставляет информацию о состоянии репозитория git.
    Все методы корректно обрабатывают отсутствие git или непохожие на git каталоги.
    """

    def __init__(self, project_path: Path):
        """
        Инициализировать интеграцию с git для проекта.

        Args:
            project_path: Путь к каталогу проекта
        """
        self.project_path = Path(project_path).resolve()
        self._git_available = None
        self._is_repo = None

    def is_git_available(self) -> bool:
        """
        Проверить, доступна ли команда git.

        Returns:
            True, если git установлен и доступен
        """
        if self._git_available is not None:
            return self._git_available

        try:
            result = subprocess.run(
                ["git", "--version"],
                capture_output=True,
                timeout=2,
                cwd=self.project_path,
            )
            self._git_available = result.returncode == 0
        except (subprocess.SubprocessError, FileNotFoundError, OSError):
            self._git_available = False

        return self._git_available

    def is_git_repo(self) -> bool:
        """
        Проверить, является ли каталог проекта репозиторием git.

        Returns:
            True, если каталог находится внутри репозитория git
        """
        if self._is_repo is not None:
            return self._is_repo

        if not self.is_git_available():
            self._is_repo = False
            return False

        try:
            result = subprocess.run(
                ["git", "rev-parse", "--git-dir"],
                capture_output=True,
                timeout=2,
                cwd=self.project_path,
            )
            self._is_repo = result.returncode == 0
        except (subprocess.SubprocessError, OSError):
            self._is_repo = False

        return self._is_repo

    def get_current_branch(self) -> Optional[str]:
        """
        Получить имя текущей ветки git.

        Returns:
            Имя ветки или None, если недоступно
        """
        if not self.is_git_repo():
            return None

        try:
            result = subprocess.run(
                ["git", "branch", "--show-current"],
                capture_output=True,
                text=True,
                timeout=2,
                cwd=self.project_path,
            )

            if result.returncode == 0:
                branch = result.stdout.strip()
                return branch if branch else None

        except (subprocess.SubprocessError, OSError):
            pass

        return None

    def get_last_commit(self) -> Optional[str]:
        """
        Получить последнее сообщение коммита (одна строка).

        Returns:
            Последний коммит в формате "хэш сообщение" или None, если недоступно
        """
        if not self.is_git_repo():
            return None

        try:
            result = subprocess.run(
                ["git", "log", "-1", "--oneline"],
                capture_output=True,
                text=True,
                timeout=2,
                cwd=self.project_path,
            )

            if result.returncode == 0:
                commit = result.stdout.strip()
                return commit if commit else None

        except (subprocess.SubprocessError, OSError):
            pass

        return None

    def get_uncommitted_changes(self) -> Optional[str]:
        """
        Получить незакоммиченные изменения в кратком формате.

        Returns:
            Вывод статуса git (краткий формат) или None, если недоступно
        """
        if not self.is_git_repo():
            return None

        try:
            result = subprocess.run(
                ["git", "status", "--short"],
                capture_output=True,
                text=True,
                timeout=2,
                cwd=self.project_path,
            )

            if result.returncode == 0:
                status = result.stdout.strip()
                return status if status else None

        except (subprocess.SubprocessError, OSError):
            pass

        return None

    def get_status_short(self) -> Optional[str]:
        """
        Получить статус git в формате porcelain.

        Returns:
            Вывод статуса git или None, если недоступно
        """
        if not self.is_git_repo():
            return None

        try:
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                capture_output=True,
                text=True,
                timeout=2,
                cwd=self.project_path,
            )

            if result.returncode == 0:
                return result.stdout.strip()

        except (subprocess.SubprocessError, OSError):
            pass

        return None

    def has_uncommitted_changes(self) -> bool:
        """
        Проверить, есть ли незакоммиченные изменения.

        Returns:
            True, если есть незакоммиченные изменения, иначе False
        """
        changes = self.get_uncommitted_changes()
        return changes is not None and len(changes) > 0

    def add_all(self) -> bool:
        """
        Добавить все изменения в индекс (git add .).

        Returns:
            True, если успешно, иначе False
        """
        if not self.is_git_repo():
            return False

        try:
            result = subprocess.run(
                ["git", "add", "."],
                capture_output=True,
                timeout=5,
                cwd=self.project_path,
            )
            return result.returncode == 0

        except (subprocess.SubprocessError, OSError):
            return False

    def create_commit(self, message: str) -> bool:
        """
        Создать коммит с указанным сообщением.

        Args:
            message: Сообщение коммита

        Returns:
            True, если коммит создан, иначе False
        """
        if not self.is_git_repo() or not message.strip():
            return False

        try:
            result = subprocess.run(
                ["git", "commit", "-m", message],
                capture_output=True,
                timeout=5,
                cwd=self.project_path,
            )
            return result.returncode == 0

        except (subprocess.SubprocessError, OSError):
            return False

    def get_remote_url(self) -> Optional[str]:
        """
        Получить URL удаленного репозитория (origin).

        Returns:
            URL удаленного репозитория или None, если недоступно
        """
        if not self.is_git_repo():
            return None

        try:
            result = subprocess.run(
                ["git", "remote", "get-url", "origin"],
                capture_output=True,
                text=True,
                timeout=2,
                cwd=self.project_path,
            )

            if result.returncode == 0:
                url = result.stdout.strip()
                return url if url else None

        except (subprocess.SubprocessError, OSError):
            pass

        return None

    def get_git_info(self) -> dict:
        """
        Получить всю информацию о git за один вызов.

        Returns:
            Словарь с информацией о git (все значения могут быть None)
        """
        return {
            "is_repo": self.is_git_repo(),
            "branch": self.get_current_branch(),
            "last_commit": self.get_last_commit(),
            "uncommitted_changes": self.get_uncommitted_changes(),
            "has_changes": self.has_uncommitted_changes(),
            "remote_url": self.get_remote_url(),
        }
