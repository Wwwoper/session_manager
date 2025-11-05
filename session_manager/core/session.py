"""
Управление сеансами для Session Manager
Обрабатывает жизненный цикл сеанса: начало, завершение, отслеживание и историю.
"""

import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any
from .project import Project, ProjectError


class SessionError(Exception):
    """Базовое исключение для ошибок, связанных с сеансами"""

    pass


class SessionManager:
    """
    Управляет рабочими сеансами для проекта.
    Отслеживает время начала/окончания сеанса, продолжительность и метаданные.
    Интегрируется с управлением контекстом для сохранения состояния работы.
    """

    def __init__(self, project: Project):
        """
        Инициализировать менеджер сеансов для проекта.

        Args:
            project: Экземпляр проекта для управления сеансами
        """
        self.project = project
        self._ensure_sessions_file()

    def _ensure_sessions_file(self) -> None:
        """Убедиться, что файл сеансов существует с правильной структурой"""
        try:
            data = self.project.get_sessions_data()
            # Обеспечить правильную структуру
            if "sessions" not in data:
                data["sessions"] = []
            if "active_session" not in data:
                data["active_session"] = None
            self.project.save_sessions_data(data)
        except ProjectError as e:
            raise SessionError(f"Не удалось инициализировать файл сеансов: {e}")

    def start(self, description: str = "") -> Dict[str, Any]:
        """
        Начать новый сеанс.

        Args:
            description: Необязательное описание того, над чем вы работаете

        Returns:
            Словарь с информацией о сеансе

        Raises:
            SessionError: Если сеанс уже активен
        """
        # Проверить, есть ли уже активный сеанс
        active = self.get_active()
        if active:
            raise SessionError(
                f"Сеанс уже активен (начат в {active['start_time']}). "
                "Завершите его перед началом нового."
            )

        # Создать новый сеанс
        session = {
            "id": str(uuid.uuid4()),
            "start_time": datetime.now().isoformat(),
            "end_time": None,
            "description": description,
            "duration": None,
            "summary": None,
            "next_action": None,
            "branch": None,
            "last_commit": None,
            "snapshot_file": None,
        }

        # Загрузить и обновить данные сеансов
        try:
            data = self.project.get_sessions_data()
            data["sessions"].append(session)
            data["active_session"] = session["id"]
            self.project.save_sessions_data(data)
        except ProjectError as e:
            raise SessionError(f"Не удалось начать сеанс: {e}")

        return session

    def end(self, summary: str = "", next_action: str = "") -> Dict[str, Any]:
        """
        Завершить активный сеанс.

        Args:
            summary: Резюме проделанной работы
            next_action: Следующее действие при возобновлении работы

        Returns:
            Словарь с информацией о завершенном сеансе

        Raises:
            SessionError: Если активный сеанс не существует
        """
        active = self.get_active()
        if not active:
            raise SessionError("Нет активного сеанса для завершения")

        # Рассчитать продолжительность
        start_time = datetime.fromisoformat(active["start_time"])
        end_time = datetime.now()
        duration = int((end_time - start_time).total_seconds())

        # Обновить сеанс
        active["end_time"] = end_time.isoformat()
        active["duration"] = duration
        active["summary"] = summary
        active["next_action"] = next_action

        # Сохранить обновленный сеанс
        try:
            data = self.project.get_sessions_data()
            # Найти и обновить сеанс
            for i, session in enumerate(data["sessions"]):
                if session["id"] == active["id"]:
                    data["sessions"][i] = active
                    break

            # Очистить активный сеанс
            data["active_session"] = None
            self.project.save_sessions_data(data)
        except ProjectError as e:
            raise SessionError(f"Не удалось завершить сеанс: {e}")

        return active

    def get_active(self) -> Optional[Dict[str, Any]]:
        """
        Получить текущий активный сеанс.

        Returns:
            Словарь активного сеанса или None, если нет активного сеанса
        """
        try:
            data = self.project.get_sessions_data()
            active_id = data.get("active_session")

            if not active_id:
                return None

            # Найти активный сеанс
            for session in data["sessions"]:
                if session["id"] == active_id:
                    return session

            # ID активного сеанса существует, но сеанс не найден (повреждение данных)
            return None
        except ProjectError:
            return None

    def get_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Получить историю сеансов (самые последние первыми).

        Args:
            limit: Максимальное количество сеансов для возврата

        Returns:
            Список словарей сеансов
        """
        try:
            data = self.project.get_sessions_data()
            sessions = data.get("sessions", [])

            # Отфильтровать только завершенные сеансы
            completed = [s for s in sessions if s.get("end_time") is not None]

            # Сортировать по времени начала (самые последние первыми)
            sorted_sessions = sorted(
                completed, key=lambda s: s.get("start_time", ""), reverse=True
            )

            return sorted_sessions[:limit]
        except ProjectError:
            return []

    def get_all_sessions(self) -> List[Dict[str, Any]]:
        """
        Получить все сеансы (завершенные и активные).

        Returns:
            Список всех словарей сеансов
        """
        try:
            data = self.project.get_sessions_data()
            return data.get("sessions", [])
        except ProjectError:
            return []

    def get_stats(self) -> Dict[str, Any]:
        """
        Получить статистику о сеансах.

        Returns:
            Словарь со статистикой сеансов:
            - total_sessions: Общее количество завершенных сеансов
            - total_time: Общее время в секундах
            - average_duration: Средняя продолжительность сеанса в секундах
            - longest_session: Продолжительность самого длинного сеанса
            - shortest_session: Продолжительность самого короткого сеанса
        """
        try:
            data = self.project.get_sessions_data()
            sessions = data.get("sessions", [])

            # Отфильтровать завершенные сеансы с продолжительностью
            completed = [
                s
                for s in sessions
                if s.get("end_time") and s.get("duration") is not None
            ]

            if not completed:
                return {
                    "total_sessions": 0,
                    "total_time": 0,
                    "average_duration": 0,
                    "longest_session": 0,
                    "shortest_session": 0,
                }

            durations = [s["duration"] for s in completed]
            total_time = sum(durations)

            return {
                "total_sessions": len(completed),
                "total_time": total_time,
                "average_duration": total_time // len(completed) if completed else 0,
                "longest_session": max(durations),
                "shortest_session": min(durations),
            }
        except ProjectError:
            return {
                "total_sessions": 0,
                "total_time": 0,
                "average_duration": 0,
                "longest_session": 0,
                "shortest_session": 0,
            }

    def get_session_by_id(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Получить конкретный сеанс по ID.

        Args:
            session_id: UUID сеанса

        Returns:
            Словарь сеанса или None, если не найден
        """
        try:
            data = self.project.get_sessions_data()
            sessions = data.get("sessions", [])

            for session in sessions:
                if session.get("id") == session_id:
                    return session
            return None
        except ProjectError:
            return None

    def update_session_metadata(
        self,
        session_id: str,
        branch: Optional[str] = None,
        last_commit: Optional[str] = None,
        snapshot_file: Optional[str] = None,
    ) -> bool:
        """
        Обновить метаданные для сеанса.

        Args:
            session_id: UUID сеанса
            branch: Имя ветки Git
            last_commit: Последний коммит git
            snapshot_file: Путь к файлу снимка

        Returns:
            True, если успешно обновлено, False, если сеанс не найден
        """
        try:
            data = self.project.get_sessions_data()
            sessions = data.get("sessions", [])

            for session in sessions:
                if session.get("id") == session_id:
                    if branch is not None:
                        session["branch"] = branch
                    if last_commit is not None:
                        session["last_commit"] = last_commit
                    if snapshot_file is not None:
                        session["snapshot_file"] = snapshot_file
                    self.project.save_sessions_data(data)
                    return True
            return False
        except ProjectError:
            return False

    def delete_session(self, session_id: str) -> bool:
        """
        Удалить сеанс по ID.

        Args:
            session_id: UUID сеанса

        Returns:
            True, если удален, False, если не найден
        """
        try:
            data = self.project.get_sessions_data()
            sessions = data.get("sessions", [])

            # Найти и удалить сеанс
            for i, session in enumerate(sessions):
                if session.get("id") == session_id:
                    sessions.pop(i)
                    # Очистить активный сеанс, если это был удаленный
                    if data.get("active_session") == session_id:
                        data["active_session"] = None
                    self.project.save_sessions_data(data)
                    return True
            return False
        except ProjectError:
            return False

    def get_today_sessions(self) -> List[Dict[str, Any]]:
        """
        Получить все сеансы за сегодня.

        Returns:
            Список сеансов за сегодня
        """
        today = datetime.now().date()
        try:
            data = self.project.get_sessions_data()
            sessions = data.get("sessions", [])

            today_sessions = []
            for session in sessions:
                start_time_str = session.get("start_time")
                if start_time_str:
                    start_time = datetime.fromisoformat(start_time_str)
                    if start_time.date() == today:
                        today_sessions.append(session)

            return today_sessions
        except ProjectError:
            return []

    def get_total_time_today(self) -> int:
        """
        Получить общее время, проведенное в сеансах за сегодня.

        Returns:
            Общее количество секунд, проведенное в сеансах за сегодня
        """
        today_sessions = self.get_today_sessions()
        total = 0
        for session in today_sessions:
            if session.get("duration"):
                total += session["duration"]
        return total
