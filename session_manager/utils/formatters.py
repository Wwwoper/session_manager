"""
Утилиты форматирования для Session Manager

Предоставляет функции для форматирования вывода с эмодзи и цветами.
"""

from typing import List, Dict, Any
from datetime import datetime


def format_duration(seconds: int) -> str:
    """
    Форматировать продолжительность в удобочитаемом виде.

    Args:
        seconds: Продолжительность в секундах

    Returns:
        Отформатированная строка продолжительности (например, "1ч 30м", "45м", "30с")
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


def format_timestamp(iso_string: str, format_type: str = "datetime") -> str:
    """
    Форматировать временной штамп ISO в читаемом виде.

    Args:
        iso_string: Строка временного штампа ISO-8601
        format_type: Тип форматирования ("datetime", "date", "time")

    Returns:
        Отформатированная строка временного штампа
    """
    try:
        dt = datetime.fromisoformat(iso_string)

        if format_type == "date":
            return dt.strftime("%Y-%m-%d")
        elif format_type == "time":
            return dt.strftime("%H:%M:%S")
        else:  # datetime
            return dt.strftime("%Y-%m-%d %H:%M:%S")
    except (ValueError, AttributeError):
        return iso_string


def print_success(message: str) -> None:
    """Напечатать сообщение об успехе с эмодзи."""
    print(f"✅ {message}")


def print_warning(message: str) -> None:
    """Напечатать предупреждение с эмодзи."""
    print(f"⚠️  {message}")


def print_error(message: str) -> None:
    """Напечатать сообщение об ошибке с эмодзи."""
    print(f"❌ {message}")


def print_info(message: str) -> None:
    """Напечатать информационное сообщение с эмодзи."""
    print(f"ℹ️  {message}")


def print_section(title: str) -> None:
    """Напечатать заголовок раздела с эмодзи."""
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print(f"{'=' * 60}\n")


def print_subsection(title: str) -> None:
    """Напечатать заголовок подраздела."""
    print(f"\n{title}")
    print(f"{'-' * len(title)}")


def format_table(data: List[Dict[str, Any]], columns: List[str]) -> str:
    """
    Форматировать данные в виде простой текстовой таблицы.

    Args:
        data: Список словарей с данными
        columns: Список имен столбцов для отображения

    Returns:
        Отформатированная таблица в виде строки
    """
    if not data:
        return "Нет данных для отображения"

    # Вычислить ширину столбцов
    widths = {}
    for col in columns:
        # Начать с ширины названия столбца
        widths[col] = len(col)
        # Проверить ширину данных
        for row in data:
            value = str(row.get(col, ""))
            widths[col] = max(widths[col], len(value))

    # Построить таблицу
    lines = []

    # Заголовок
    header = " | ".join(col.ljust(widths[col]) for col in columns)
    lines.append(header)
    lines.append("-" * len(header))

    # Строки
    for row in data:
        line = " | ".join(str(row.get(col, "")).ljust(widths[col]) for col in columns)
        lines.append(line)

    return "\n".join(lines)


def format_list(items: List[str], bullet: str = "•") -> str:
    """
    Форматировать список элементов с маркерами.

    Args:
        items: Список строк
        bullet: Символ маркера

    Returns:
        Отформатированный список в виде строки
    """
    if not items:
        return "Нет элементов"

    return "\n".join(f"  {bullet} {item}" for item in items)


def format_key_value(data: Dict[str, Any], indent: int = 2) -> str:
    """
    Форматировать словарь в виде пар ключ-значение.

    Args:
        data: Словарь для форматирования
        indent: Количество пробелов для отступа

    Returns:
        Отформатированные пары ключ-значение в виде строки
    """
    if not data:
        return "Нет данных"

    # Найти самый длинный ключ для выравнивания
    max_key_len = max(len(str(k)) for k in data.keys())

    lines = []
    indent_str = " " * indent

    for key, value in data.items():
        key_str = str(key).ljust(max_key_len)
        lines.append(f"{indent_str}{key_str} : {value}")

    return "\n".join(lines)


def format_session_summary(session: Dict[str, Any]) -> str:
    """
    Форматировать информацию о сессии в виде резюме.

    Args:
        session: Словарь сессии

    Returns:
        Отформатированное резюме сессии
    """
    lines = []

    # Основная информация
    if session.get("description"):
        lines.append(f"Описание: {session['description']}")

    # Время
    if session.get("start_time"):
        lines.append(f"Начало: {format_timestamp(session['start_time'])}")

    if session.get("end_time"):
        lines.append(f"Конец: {format_timestamp(session['end_time'])}")

    if session.get("duration"):
        lines.append(f"Продолжительность: {format_duration(session['duration'])}")

    # Информация Git
    if session.get("branch"):
        lines.append(f"Ветка: {session['branch']}")

    if session.get("last_commit"):
        lines.append(f"Последний коммит: {session['last_commit']}")

    # Резюме
    if session.get("summary"):
        lines.append(f"\nРезюме: {session['summary']}")

    if session.get("next_action"):
        lines.append(f"Следующее действие: {session['next_action']}")

    return "\n".join(lines)


def format_project_list(projects: List[Dict[str, Any]]) -> str:
    """
    Форматировать список проектов.

    Args:
        projects: Список словарей информации о проектах

    Returns:
        Отформатированный список проектов
    """
    if not projects:
        return "Проекты не найдены"

    lines = []

    for project in projects:
        name = project.get("name", "Неизвестно")
        path = project.get("path", "Неизвестно")
        alias = project.get("alias")

        line = f"• {name}"
        if alias:
            line += f" ({alias})"
        line += f"\n  Путь: {path}"

        if project.get("last_used"):
            last_used = format_timestamp(project["last_used"])
            line += f"\n  Последнее использование: {last_used}"

        lines.append(line)

    return "\n\n".join(lines)


def truncate_string(s: str, max_length: int, suffix: str = "...") -> str:
    """
    Обрезать строку, если она превышает максимальную длину.

    Args:
        s: Строка для обрезки
        max_length: Максимальная длина
        suffix: Суффикс для добавления при обрезке

    Returns:
        Обрезанная строка
    """
    if len(s) <= max_length:
        return s
    return s[: max_length - len(suffix)] + suffix


def format_stats(stats: Dict[str, Any]) -> str:
    """
    Форматировать словарь статистики.

    Args:
        stats: Словарь статистики

    Returns:
        Отформатированная строка статистики
    """
    lines = []

    total_sessions = stats.get("total_sessions", 0)
    lines.append(f"Всего сессий: {total_sessions}")

    if total_sessions > 0:
        total_time = stats.get("total_time", 0)
        lines.append(f"Общее время: {format_duration(total_time)}")

        avg_duration = stats.get("average_duration", 0)
        lines.append(f"Средняя продолжительность: {format_duration(avg_duration)}")

        longest = stats.get("longest_session", 0)
        lines.append(f"Самая длинная сессия: {format_duration(longest)}")

        shortest = stats.get("shortest_session", 0)
        lines.append(f"Самая короткая сессия: {format_duration(shortest)}")

    return "\n".join(lines)


def wrap_text(text: str, width: int = 70) -> str:
    """
    Перенести текст на заданную ширину.

    Args:
        text: Текст для переноса
        width: Максимальная ширина строки

    Returns:
        Перенесенный текст
    """
    if len(text) <= width:
        return text

    words = text.split()
    lines = []
    current_line = []
    current_length = 0

    for word in words:
        word_len = len(word)

        if current_length + word_len + len(current_line) <= width:
            current_line.append(word)
            current_length += word_len
        else:
            if current_line:
                lines.append(" ".join(current_line))
            current_line = [word]
            current_length = word_len

    if current_line:
        lines.append(" ".join(current_line))

    return "\n".join(lines)


def print_header(text: str, char: str = "=") -> None:
    """
    Напечатать заголовок с декоративными символами.

    Args:
        text: Текст заголовка
        char: Символ для использования в декорации
    """
    width = max(len(text) + 4, 60)
    print(f"\n{char * width}")
    print(f"{text.center(width)}")
    print(f"{char * width}\n")
