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
    """Base exception for project-related errors"""
    pass
class Project:
    """
    Represents a single project in Session Manager.
    
    Manages project-specific files and directories:
    - sessions.json: session history
    - PROJECT.md: context file
    - snapshots/: directory for context snapshots
    """
    
    def __init__(self, name: str, path: str):
        """
        Initialize a project.
        
        Args:
            name: Project name (unique identifier)
            path: Path to the project directory on disk
        """
        self.name = name
        self.path = Path(path).resolve()
        
        # Project data directory in ~/.session-manager/projects/{name}/
        self._project_dir = get_project_dir(name)
        
        # File paths
        self.sessions_file = get_sessions_file(name)
        self.project_md_file = get_project_md_file(name)
        self.snapshots_dir = get_snapshots_dir(name)
        
        self._storage = Storage()
    
    def ensure_structure(self) -> None:
        """
        Ensure project directory structure exists.
        
        Creates:
        - Project directory
        - Snapshots directory
        """
        ensure_project_structure(self.name)
    
    def exists(self) -> bool:
        """
        Check if project structure exists.
        
        Returns:
            True if project directory exists
        """
        return self._project_dir.exists()
    
    def get_project_md_content(self) -> str:
        """
        Read PROJECT.md content.
        
        Returns:
            Content of PROJECT.md file, or empty string if doesn't exist
        """
        try:
            return self._storage.read_text(self.project_md_file, default="")
        except StorageError as e:
            raise ProjectError(f"Failed to read PROJECT.md: {e}")
    
    def update_project_md(self, content: str) -> None:
        """
        Update PROJECT.md with new content.
        
        Args:
            content: New content for PROJECT.md
            
        Raises:
            ProjectError: If file cannot be written
        """
        try:
            self._storage.write_text(self.project_md_file, content)
        except StorageError as e:
            raise ProjectError(f"Failed to update PROJECT.md: {e}")
    
    def has_project_md(self) -> bool:
        """
        Check if PROJECT.md exists.
        
        Returns:
            True if PROJECT.md file exists
        """
        return self._storage.file_exists(self.project_md_file)
    
    def get_sessions_data(self) -> dict:
        """
        Load sessions data from sessions.json.
        
        Returns:
            Dictionary with sessions data, or empty dict if file doesn't exist
            
        Raises:
            ProjectError: If file exists but cannot be read
        """
        try:
            return self._storage.load_json(
                self.sessions_file,
                default={"sessions": [], "active_session": None}
            )
        except StorageError as e:
            raise ProjectError(f"Failed to load sessions: {e}")
    
    def save_sessions_data(self, data: dict) -> None:
        """
        Save sessions data to sessions.json.
        
        Args:
            data: Sessions data to save
            
        Raises:
            ProjectError: If data cannot be saved
        """
        try:
            self._storage.save_json(self.sessions_file, data)
        except StorageError as e:
            raise ProjectError(f"Failed to save sessions: {e}")
    
    def get_snapshot_path(self, timestamp: str) -> Path:
        """
        Get path for a snapshot file.
        
        Args:
            timestamp: Timestamp string (e.g., "20250115_1430")
            
        Returns:
            Path to snapshot file
        """
        return self.snapshots_dir / f"{timestamp}.md"
    
    def list_snapshots(self) -> list[Path]:
        """
        List all snapshot files.
        
        Returns:
            List of snapshot file paths, sorted by name (oldest first)
        """
        if not self.snapshots_dir.exists():
            return []
        
        snapshots = list(self.snapshots_dir.glob("*.md"))
        return sorted(snapshots)
    
    def get_latest_snapshot(self) -> Optional[Path]:
        """
        Get the most recent snapshot file.
        
        Returns:
            Path to latest snapshot, or None if no snapshots exist
        """
        snapshots = self.list_snapshots()
        return snapshots[-1] if snapshots else None
    
    def delete_old_snapshots(self, keep: int = 10) -> int:
        """
        Delete old snapshots, keeping only the most recent ones.
        
        Args:
            keep: Number of recent snapshots to keep
            
        Returns:
            Number of snapshots deleted
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
                # Continue deleting others even if one fails
                pass
        
        return deleted
    
    def backup_sessions(self) -> Optional[Path]:
        """
        Create a backup of sessions.json.
        
        Returns:
            Path to backup file, or None if sessions file doesn't exist
            
        Raises:
            ProjectError: If backup fails
        """
        try:
            return self._storage.backup_file(self.sessions_file)
        except StorageError as e:
            raise ProjectError(f"Failed to backup sessions: {e}")
    
    def get_project_info(self) -> dict:
        """
        Get information about the project.
        
        Returns:
            Dictionary with project information
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
