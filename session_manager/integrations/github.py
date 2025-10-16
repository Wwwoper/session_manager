"""
GitHub CLI integration for Session Manager

Provides GitHub Issues information via gh CLI with graceful degradation.
"""

import subprocess
import json
from pathlib import Path
from typing import Optional, List, Dict


class GitHubIntegration:
    """
    Integration with GitHub via gh CLI.
    
    Provides information about GitHub issues and pull requests.
    All methods gracefully handle missing gh CLI.
    """
    
    def __init__(self, project_path: Path):
        """
        Initialize GitHub integration for a project.
        
        Args:
            project_path: Path to the project directory
        """
        self.project_path = Path(project_path).resolve()
        self._gh_available = None
    
    def is_gh_available(self) -> bool:
        """
        Check if gh CLI is installed and accessible.
        
        Returns:
            True if gh CLI is available
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
        Check if project is a GitHub repository.
        
        Returns:
            True if project is connected to GitHub
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
        Get list of open issues.
        
        Args:
            limit: Maximum number of issues to return
            
        Returns:
            List of issue dictionaries, or None if not available
        """
        if not self.is_github_repo():
            return None
        
        try:
            result = subprocess.run(
                [
                    "gh", "issue", "list",
                    "--state", "open",
                    "--limit", str(limit),
                    "--json", "number,title,labels,updatedAt",
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
        Get issues assigned to current user.
        
        Args:
            limit: Maximum number of issues to return
            
        Returns:
            List of issue dictionaries, or None if not available
        """
        if not self.is_github_repo():
            return None
        
        try:
            result = subprocess.run(
                [
                    "gh", "issue", "list",
                    "--assignee", "@me",
                    "--state", "open",
                    "--limit", str(limit),
                    "--json", "number,title,labels",
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
        Get list of open pull requests.
        
        Args:
            limit: Maximum number of PRs to return
            
        Returns:
            List of PR dictionaries, or None if not available
        """
        if not self.is_github_repo():
            return None
        
        try:
            result = subprocess.run(
                [
                    "gh", "pr", "list",
                    "--state", "open",
                    "--limit", str(limit),
                    "--json", "number,title,author,updatedAt",
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
        Format issues list as a summary string.
        
        Args:
            issues: List of issue dictionaries
            
        Returns:
            Formatted summary string
        """
        if not issues:
            return "No open issues"
        
        lines = []
        for issue in issues[:5]:  # Limit to 5
            number = issue.get('number', '?')
            title = issue.get('title', 'No title')
            # Truncate long titles
            if len(title) > 60:
                title = title[:57] + "..."
            lines.append(f"  #{number}: {title}")
        
        return "\n".join(lines)
    
    def format_prs_summary(self, prs: Optional[List[Dict]]) -> str:
        """
        Format pull requests list as a summary string.
        
        Args:
            prs: List of PR dictionaries
            
        Returns:
            Formatted summary string
        """
        if not prs:
            return "No open pull requests"
        
        lines = []
        for pr in prs[:5]:  # Limit to 5
            number = pr.get('number', '?')
            title = pr.get('title', 'No title')
            author = pr.get('author', {}).get('login', 'unknown')
            # Truncate long titles
            if len(title) > 50:
                title = title[:47] + "..."
            lines.append(f"  #{number}: {title} (@{author})")
        
        return "\n".join(lines)
    
    def get_repo_info(self) -> Optional[Dict]:
        """
        Get repository information.
        
        Returns:
            Dictionary with repo info, or None if not available
        """
        if not self.is_github_repo():
            return None
        
        try:
            result = subprocess.run(
                [
                    "gh", "repo", "view",
                    "--json", "name,owner,description,url,isPrivate",
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
        Get all GitHub information in one call.
        
        Returns:
            Dictionary with GitHub information
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