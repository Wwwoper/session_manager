"""
Интеграция с GitHub CLI для Session Manager

Предоставляет информацию о задачах GitHub через gh CLI с корректной деградацией.
"""

import subprocess
import json
from pathlib import Path
from typing import Optional, List, Dict


class GitHubIntegration:
    """
    Интеграция с GitHub через gh CLI.

    Предоставляет информацию о задачах и пулл-реквестах GitHub.
    Все методы корректно обрабатывают отсутствие gh CLI.
    """

    def __init__(self, project_path: Path):
        """
        Инициализировать интеграцию с GitHub для проекта.

        Args:
            project_path: Путь к каталогу проекта
        """
        self.project_path = Path(project_path).resolve()
        self._gh_available = None

    def is_gh_available(self) -> bool:
        """
        Проверить, установлен ли и доступен ли gh CLI.

        Returns:
            True, если gh CLI доступен
        """
        if self._gh_available is not None:
            return self._gh_available

        try:
            result = subprocess.run(
                ["gh", "--version"],
                capture_output=True,
                timeout=2,
            )
            self._gh_available = result.returncode == 0
        except (subprocess.SubprocessError, FileNotFoundError, OSError):
            self._gh_available = False

        return self._gh_available

    def is_github_repo(self) -> bool:
        """
        Проверить, является ли проект репозиторием GitHub.

        Returns:
            True, если проект подключен к GitHub
        """
        if not self.is_gh_available():
            return False

        try:
            result = subprocess.run(
                ["gh", "repo", "view", "--json", "name"],
                capture_output=True,
                timeout=3,
                cwd=self.project_path,
            )
            return result.returncode == 0

        except (subprocess.SubprocessError, OSError):
            return False

    def get_open_issues(self, limit: int = 5) -> Optional[List[Dict]]:
        """
        Получить список открытых задач.

        Args:
            limit: Максимальное количество задач для возврата

        Returns:
            Список словарей задач или None, если недоступно
        """
        if not self.is_github_repo():
            return None

        try:
            result = subprocess.run(
                [
                    "gh",
                    "issue",
                    "list",
                    "--state",
                    "open",
                    "--limit",
                    str(limit),
                    "--json",
                    "number,title,labels,updatedAt",
                ],
                capture_output=True,
                text=True,
                timeout=5,
                cwd=self.project_path,
            )

            if result.returncode == 0:
                issues = json.loads(result.stdout)
                return issues if issues else []

        except (subprocess.SubprocessError, OSError, json.JSONDecodeError):
            pass

        return None

    def get_assigned_issues(self, limit: int = 5) -> Optional[List[Dict]]:
        """
        Получить задачи, назначенные текущему пользователю.

        Args:
            limit: Максимальное количество задач для возврата

        Returns:
            Список словарей задач или None, если недоступно
        """
        if not self.is_github_repo():
            return None

        try:
            result = subprocess.run(
                [
                    "gh",
                    "issue",
                    "list",
                    "--assignee",
                    "@me",
                    "--state",
                    "open",
                    "--limit",
                    str(limit),
                    "--json",
                    "number,title,labels",
                ],
                capture_output=True,
                text=True,
                timeout=5,
                cwd=self.project_path,
            )

            if result.returncode == 0:
                issues = json.loads(result.stdout)
                return issues if issues else []

        except (subprocess.SubprocessError, OSError, json.JSONDecodeError):
            pass

        return None

    def get_open_prs(self, limit: int = 5) -> Optional[List[Dict]]:
        """
        Получить список открытых пулл-реквестов.

        Args:
            limit: Максимальное количество PR для возврата

        Returns:
            Список словарей PR или None, если недоступно
        """
        if not self.is_github_repo():
            return None

        try:
            result = subprocess.run(
                [
                    "gh",
                    "pr",
                    "list",
                    "--state",
                    "open",
                    "--limit",
                    str(limit),
                    "--json",
                    "number,title,author,updatedAt",
                ],
                capture_output=True,
                text=True,
                timeout=5,
                cwd=self.project_path,
            )

            if result.returncode == 0:
                prs = json.loads(result.stdout)
                return prs if prs else []

        except (subprocess.SubprocessError, OSError, json.JSONDecodeError):
            pass

        return None

    def format_issues_summary(self, issues: Optional[List[Dict]]) -> str:
        """
        Форматировать список задач в виде строки-сводки.

        Args:
            issues: Список словарей задач

        Returns:
            Отформатированная строка сводки
        """
        if not issues:
            return "Нет открытых задач"

        lines = []
        for issue in issues[:5]:  # Ограничить 5
            number = issue.get("number", "?")
            title = issue.get("title", "Без названия")
            # Обрезать длинные названия
            if len(title) > 60:
                title = title[:57] + "..."
            lines.append(f"  #{number}: {title}")

        return "\n".join(lines)

    def format_prs_summary(self, prs: Optional[List[Dict]]) -> str:
        """
        Форматировать список пулл-реквестов в виде строки-сводки.

        Args:
            prs: Список словарей PR

        Returns:
            Отформатированная строка сводки
        """
        if not prs:
            return "Нет открытых пулл-реквестов"

        lines = []
        for pr in prs[:5]:  # Ограничить 5
            number = pr.get("number", "?")
            title = pr.get("title", "Без названия")
            author = pr.get("author", {}).get("login", "неизвестно")
            # Обрезать длинные названия
            if len(title) > 50:
                title = title[:47] + "..."
            lines.append(f"  #{number}: {title} (@{author})")

        return "\n".join(lines)

    def get_repo_info(self) -> Optional[Dict]:
        """
        Получить информацию о репозитории.

        Returns:
            Словарь с информацией о репозитории или None, если недоступно
        """
        if not self.is_github_repo():
            return None

        try:
            result = subprocess.run(
                [
                    "gh",
                    "repo",
                    "view",
                    "--json",
                    "name,owner,description,url,isPrivate",
                ],
                capture_output=True,
                text=True,
                timeout=3,
                cwd=self.project_path,
            )

            if result.returncode == 0:
                return json.loads(result.stdout)

        except (subprocess.SubprocessError, OSError, json.JSONDecodeError):
            pass

        return None

    def get_github_info(self) -> Dict:
        """
        Получить всю информацию о GitHub за один вызов.

        Returns:
            Словарь с информацией о GitHub
        """
        if not self.is_gh_available():
            return {
                "available": False,
                "is_repo": False,
            }

        is_repo = self.is_github_repo()

        if not is_repo:
            return {
                "available": True,
                "is_repo": False,
            }

        return {
            "available": True,
            "is_repo": True,
            "open_issues": self.get_open_issues(limit=5),
            "assigned_issues": self.get_assigned_issues(limit=5),
            "open_prs": self.get_open_prs(limit=3),
            "repo_info": self.get_repo_info(),
        }
