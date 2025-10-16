"""
Git integration for Session Manager

Provides git repository information with graceful degradation.
All methods return None if git is not available or not a git repository.
"""

import subprocess
from pathlib import Path
from typing import Optional


class GitIntegration:
    """
    Integration with Git version control.
    
    Provides information about git repository state.
    All methods gracefully handle missing git or non-git directories.
    """
    
    def __init__(self, project_path: Path):
        """
        Initialize git integration for a project.
        
        Args:
            project_path: Path to the project directory
        """
        self.project_path = Path(project_path).resolve()
        self._git_available = None
        self._is_repo = None
    
    def is_git_available(self) -> bool:
        """
        Check if git command is available.
        
        Returns:
            True if git is installed and accessible
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
        Check if project directory is a git repository.
        
        Returns:
            True if directory is inside a git repository
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
        Get the current git branch name.
        
        Returns:
            Branch name, or None if not available
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
        Get the last commit message (one line).
        
        Returns:
            Last commit in format "hash message", or None if not available
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
        Get uncommitted changes in short format.
        
        Returns:
            Git status output (short format), or None if not available
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
        Get git status in porcelain format.
        
        Returns:
            Git status output, or None if not available
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
        Check if there are uncommitted changes.
        
        Returns:
            True if there are uncommitted changes, False otherwise
        """
        changes = self.get_uncommitted_changes()
        return changes is not None and len(changes) > 0
    
    def add_all(self) -> bool:
        """
        Stage all changes (git add .).
        
        Returns:
            True if successful, False otherwise
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
        Create a commit with the given message.
        
        Args:
            message: Commit message
            
        Returns:
            True if commit was created, False otherwise
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
        Get the remote URL (origin).
        
        Returns:
            Remote URL, or None if not available
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
        Get all git information in one call.
        
        Returns:
            Dictionary with git information (all values may be None)
        """
        return {
            "is_repo": self.is_git_repo(),
            "branch": self.get_current_branch(),
            "last_commit": self.get_last_commit(),
            "uncommitted_changes": self.get_uncommitted_changes(),
            "has_changes": self.has_uncommitted_changes(),
            "remote_url": self.get_remote_url(),
        }