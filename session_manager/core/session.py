"""
Управление сеансами для Session Manager
Обрабатывает жизненный цикл сеанса: начало, завершение, отслеживание и историю.
"""
import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any
from .project import Project, ProjectError

class SessionError(Exception):
    """Base exception for session-related errors"""
    pass

class SessionManager:
    """
    Manages work sessions for a project.
    Tracks session start/end times, duration, and metadata.
    Integrates with context management for saving work state.
    """

    def __init__(self, project: Project):
        """
        Initialize session manager for a project.

        Args:
            project: Project instance to manage sessions for
        """
        self.project = project
        self._ensure_sessions_file()

    def _ensure_sessions_file(self) -> None:
        """Ensure sessions file exists with proper structure"""
        try:
            data = self.project.get_sessions_data()
            # Ensure proper structure
            if "sessions" not in data:
                data["sessions"] = []
            if "active_session" not in data:
                data["active_session"] = None
            self.project.save_sessions_data(data)
        except ProjectError as e:
            raise SessionError(f"Failed to initialize sessions file: {e}")

    def start(self, description: str = "") -> Dict[str, Any]:
        """
        Start a new session.

        Args:
            description: Optional description of what you're working on

        Returns:
            Dictionary with session information

        Raises:
            SessionError: If a session is already active
        """
        # Check if there's already an active session
        active = self.get_active()
        if active:
            raise SessionError(
                f"Session already active (started at {active['start_time']}). "
                "End it before starting a new one."
            )

        # Create new session
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

        # Load and update sessions data
        try:
            data = self.project.get_sessions_data()
            data["sessions"].append(session)
            data["active_session"] = session["id"]
            self.project.save_sessions_data(data)
        except ProjectError as e:
            raise SessionError(f"Failed to start session: {e}")

        return session

    def end(self, summary: str = "", next_action: str = "") -> Dict[str, Any]:
        """
        End the active session.

        Args:
            summary: Summary of what was accomplished
            next_action: Next action to take when resuming work

        Returns:
            Dictionary with completed session information

        Raises:
            SessionError: If no active session exists
        """
        active = self.get_active()
        if not active:
            raise SessionError("No active session to end")

        # Calculate duration
        start_time = datetime.fromisoformat(active["start_time"])
        end_time = datetime.now()
        duration = int((end_time - start_time).total_seconds())

        # Update session
        active["end_time"] = end_time.isoformat()
        active["duration"] = duration
        active["summary"] = summary
        active["next_action"] = next_action

        # Save updated session
        try:
            data = self.project.get_sessions_data()
            # Find and update the session
            for i, session in enumerate(data["sessions"]):
                if session["id"] == active["id"]:
                    data["sessions"][i] = active
                    break

            # Clear active session
            data["active_session"] = None
            self.project.save_sessions_data(data)
        except ProjectError as e:
            raise SessionError(f"Failed to end session: {e}")

        return active

    def get_active(self) -> Optional[Dict[str, Any]]:
        """
        Get the currently active session.

        Returns:
            Active session dictionary, or None if no active session
        """
        try:
            data = self.project.get_sessions_data()
            active_id = data.get("active_session")

            if not active_id:
                return None

            # Find the active session
            for session in data["sessions"]:
                if session["id"] == active_id:
                    return session

            # Active session ID exists but session not found (data corruption)
            return None
        except ProjectError:
            return None

    def get_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get session history (most recent first).

        Args:
            limit: Maximum number of sessions to return

        Returns:
            List of session dictionaries
        """
        try:
            data = self.project.get_sessions_data()
            sessions = data.get("sessions", [])

            # Filter completed sessions only
            completed = [s for s in sessions if s.get("end_time") is not None]

            # Sort by start time (most recent first)
            sorted_sessions = sorted(
                completed, key=lambda s: s.get("start_time", ""), reverse=True
            )

            return sorted_sessions[:limit]
        except ProjectError:
            return []

    def get_all_sessions(self) -> List[Dict[str, Any]]:
        """
        Get all sessions (completed and active).

        Returns:
            List of all session dictionaries
        """
        try:
            data = self.project.get_sessions_data()
            return data.get("sessions", [])
        except ProjectError:
            return []

    def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics about sessions.

        Returns:
            Dictionary with session statistics:
            - total_sessions: Total number of completed sessions
            - total_time: Total time spent in seconds
            - average_duration: Average session duration in seconds
            - longest_session: Duration of longest session
            - shortest_session: Duration of shortest session
        """
        try:
            data = self.project.get_sessions_data()
            sessions = data.get("sessions", [])

            # Filter completed sessions with duration
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
        Get a specific session by ID.

        Args:
            session_id: Session UUID

        Returns:
            Session dictionary, or None if not found
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
        Update metadata for a session.

        Args:
            session_id: Session UUID
            branch: Git branch name
            last_commit: Last git commit
            snapshot_file: Path to snapshot file

        Returns:
            True if updated successfully, False if session not found
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
        Delete a session by ID.

        Args:
            session_id: Session UUID

        Returns:
            True if deleted, False if not found
        """
        try:
            data = self.project.get_sessions_data()
            sessions = data.get("sessions", [])

            # Find and remove session
            for i, session in enumerate(sessions):
                if session.get("id") == session_id:
                    sessions.pop(i)
                    # Clear active session if it was the deleted one
                    if data.get("active_session") == session_id:
                        data["active_session"] = None
                    self.project.save_sessions_data(data)
                    return True
            return False
        except ProjectError:
            return False

    def get_today_sessions(self) -> List[Dict[str, Any]]:
        """
        Get all sessions from today.

        Returns:
            List of today's sessions
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
        Get total time spent in sessions today.

        Returns:
            Total seconds spent in sessions today
        """
        today_sessions = self.get_today_sessions()
        total = 0
        for session in today_sessions:
            if session.get("duration"):
                total += session["duration"]
        return total
