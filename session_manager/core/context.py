"""
Управление контекстом для Session Manager

Обрабатывает снимки контекста и генерацию PROJECT.md.
"""

from datetime import datetime
from typing import Optional, Dict, Any
import re

from .project import Project, ProjectError


class ContextError(Exception):
    """Базовое исключение для ошибок, связанных с контекстом"""

    pass


class ContextManager:
    """
    Управляет контекстом проекта: снимки и PROJECT.md.

    Создает снимки рабочих сессий и генерирует PROJECT.md
    с последней информацией о контексте.
    """

    def __init__(self, project: Project):
        """
        Инициализировать менеджер контекста для проекта.

        Args:
            project: Экземпляр проекта для управления контекстом
        """
        self.project = project

    def save_snapshot(
        self,
        session_data: Dict[str, Any],
        summary: str,
        next_action: str,
        git_info: Optional[Dict] = None,
        test_info: Optional[Dict] = None,
    ) -> str:
        """
        Сохранить снимок контекста.

        Args:
            session_data: Информация о сессии
            summary: Резюме проделанной работы
            next_action: Следующее действие для выполнения
            git_info: Необязательная информация git
            test_info: Необязательная информация тестов

        Returns:
            Путь к файлу снимка

        Raises:
            ContextError: Если снимок не может быть сохранен
        """
        # Сгенерировать метку времени для имени файла
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        snapshot_path = self.project.get_snapshot_path(timestamp)

        # Форматировать содержимое снимка
        content = self._format_snapshot(
            session_data, summary, next_action, git_info, test_info
        )

        # Сохранить снимок
        try:
            snapshot_path.parent.mkdir(parents=True, exist_ok=True)
            snapshot_path.write_text(content, encoding="utf-8")
        except OSError as e:
            raise ContextError(f"Не удалось сохранить снимок: {e}")

        return str(snapshot_path)

    def load_last_snapshot(self) -> Optional[Dict[str, Any]]:
        """
        Загрузить самый последний снимок.

        Returns:
            Словарь с данными снимка или None, если снимков нет
        """
        latest = self.project.get_latest_snapshot()

        if not latest:
            return None

        try:
            content = latest.read_text(encoding="utf-8")
            return self._parse_snapshot(content)
        except OSError:
            return None

    def generate_project_md(
        self,
        session_data: Dict[str, Any],
        summary: str,
        next_action: str,
    ) -> None:
        """
        Сгенерировать или обновить PROJECT.md с последним контекстом.

        Args:
            session_data: Информация о сессии
            summary: Резюме последней сессии
            next_action: Следующее действие для выполнения

        Raises:
            ContextError: Если PROJECT.md не может быть обновлен
        """
        # Рассчитать продолжительность сессии
        duration_str = "N/A"
        if session_data.get("duration"):
            duration = session_data["duration"]
            hours = duration // 3600
            minutes = (duration % 3600) // 60
            if hours > 0:
                duration_str = f"{hours}ч {minutes}м"
            else:
                duration_str = f"{minutes}м"

        # Форматировать содержимое
        content = f"""# Контекст проекта

**Последнее обновление:** {datetime.now().strftime("%Y-%m-%d %H:%M")}  
**Продолжительность сессии:** {duration_str}

## 🎯 Следующее действие

{next_action}

## 📝 Резюме последней сессии

{summary}

---

## Информация о сессии

- **Начало:** {session_data.get("start_time", "N/A")}
- **Конец:** {session_data.get("end_time", "N/A")}
- **Ветка:** {session_data.get("branch", "N/A")}
- **Последний коммит:** {session_data.get("last_commit", "N/A")}

---

## Быстрые команды

```bash
# Начать новую сессию
session start

# Завершить текущую сессию
session end

# Проверить статус
session status

# Просмотр истории
session history
```

## Советы

- Просмотрите **Следующее действие** выше, чтобы быстро вернуться к работе
- Проверьте статус ветки и коммита git перед началом
- Запустите тесты, чтобы убедиться, что все работает
- Обновите этот файл в конце каждой сессии
"""

        try:
            self.project.update_project_md(content)
        except ProjectError as e:
            raise ContextError(f"Не удалось обновить PROJECT.md: {e}")

    def get_next_action_from_project_md(self) -> Optional[str]:
        """
        Извлечь "Следующее действие" из PROJECT.md.

        Returns:
            Текст следующего действия или None, если не найдено
        """
        if not self.project.has_project_md():
            return None

        try:
            content = self.project.get_project_md_content()

            # Искать раздел "Следующее действие"
            match = re.search(
                r"## 🎯 Следующее действие\s*\n\s*\n(.+?)(?:\n\n##|\Z)",
                content,
                re.DOTALL,
            )

            if match:
                return match.group(1).strip()

            return None

        except ProjectError:
            return None

    def _format_snapshot(
        self,
        session_data: Dict[str, Any],
        summary: str,
        next_action: str,
        git_info: Optional[Dict] = None,
        test_info: Optional[Dict] = None,
    ) -> str:
        """
        Форматировать содержимое снимка как Markdown.

        Args:
            session_data: Информация о сессии
            summary: Резюме сессии
            next_action: Следующее действие
            git_info: Необязательная информация git
            test_info: Необязательная информация тестов

        Returns:
            Отформатированное содержимое Markdown
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        content = f"""# Снимок контекста сессии

**Создан:** {timestamp}  
**ID сессии:** {session_data.get("id", "N/A")}

---

## 📋 Информация о сессии

- **Начало:** {session_data.get("start_time", "N/A")}
- **Конец:** {session_data.get("end_time", "N/A")}
- **Продолжительность:** {self._format_duration(session_data.get("duration", 0))}
- **Описание:** {session_data.get("description", "N/A")}

---

## 📝 Резюме

{summary if summary else "_Резюме не предоставлено_"}

---

## 🎯 Следующее действие

{next_action if next_action else "_Следующее действие не указано_"}


---
"""

        # Добавить информацию git, если доступна
        if git_info:
            content += """
## 🌿 Статус Git

"""
            if git_info.get("branch"):
                content += f"- **Ветка:** `{git_info['branch']}`\n"
            if git_info.get("last_commit"):
                content += f"- **Последний коммит:** `{git_info['last_commit']}`\n"
            if git_info.get("uncommitted_changes"):
                content += f"- **Незакоммиченные изменения:**\n```\n{git_info['uncommitted_changes']}\n```\n"
            elif git_info.get("has_changes") is False:
                content += "- **Статус:** Рабочий каталог чист ✅\n"

            content += "\n---\n"

        # Добавить информацию тестов, если доступна
        if test_info:
            content += """
## 🧪 Статус тестов

"""
            if test_info.get("summary"):
                content += f"{test_info['summary']}\n"

            content += "\n---\n"

        content += """
## 💡 Заметки

- Используйте этот снимок для быстрого восстановления контекста
- Просмотрите Следующее действие перед началом работы
- Проверьте статус git для любой незакоммиченной работы
"""

        return content

    def _parse_snapshot(self, content: str) -> Dict[str, Any]:
        """
        Разобрать содержимое снимка в структурированные данные.

        Args:
            content: Содержимое снимка Markdown

        Returns:
            Словарь с разобранными данными снимка
        """
        data = {}

        # Извлечь ID сессии
        session_id_match = re.search(r"\*\*ID сессии:\*\* (.+)", content)
        if session_id_match:
            data["session_id"] = session_id_match.group(1)

        # Извлечь резюме
        summary_match = re.search(
            r"## 📝 Резюме\s*\n\s*\n(.+?)(?:\n\n##|\Z)", content, re.DOTALL
        )
        if summary_match:
            data["summary"] = summary_match.group(1).strip()

        # Извлечь следующее действие
        next_action_match = re.search(
            r"## 🎯 Следующее действие\s*\n\s*\n(.+?)(?:\n\n##|\Z)", content, re.DOTALL
        )
        if next_action_match:
            data["next_action"] = next_action_match.group(1).strip()

        return data

    def _format_duration(self, seconds: int) -> str:
        """
        Форматировать продолжительность в удобочитаемом виде.

        Args:
            seconds: Продолжительность в секундах

        Returns:
            Отформатированная строка продолжительности
        """
        if seconds < 60:
            return f"{seconds}с"

        minutes = seconds // 60
        remaining_seconds = seconds % 60

        if minutes < 60:
            if remaining_seconds > 0:
                return f"{minutes}м {remaining_seconds}с"
            return f"{minutes}м"

        hours = minutes // 60
        remaining_minutes = minutes % 60

        if remaining_minutes > 0:
            return f"{hours}ч {remaining_minutes}м"
        return f"{hours}ч"
