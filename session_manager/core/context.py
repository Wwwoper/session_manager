"""
Context management for Session Manager

Handles context snapshots and PROJECT.md generation.
"""

from datetime import datetime
from typing import Optional, Dict, Any
import re

from .project import Project, ProjectError


class ContextError(Exception):
    """Base exception for context-related errors"""
    pass


class ContextManager:
    """
    Manages project context: snapshots and PROJECT.md.
    
    Creates snapshots of work sessions and generates PROJECT.md
    with the latest context information.
    """
    
    def __init__(self, project: Project):
        """
        Initialize context manager for a project.
        
        Args:
            project: Project instance to manage context for
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
        Save a context snapshot.
        
        Args:
            session_data: Session information
            summary: Summary of what was done
            next_action: Next action to take
            git_info: Optional git information
            test_info: Optional test information
            
        Returns:
            Path to the snapshot file
            
        Raises:
            ContextError: If snapshot cannot be saved
        """
        # Generate timestamp for filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        snapshot_path = self.project.get_snapshot_path(timestamp)
        
        # Format snapshot content
        content = self._format_snapshot(
            session_data,
            summary,
            next_action,
            git_info,
            test_info
        )
        
        # Save snapshot
        try:
            snapshot_path.parent.mkdir(parents=True, exist_ok=True)
            snapshot_path.write_text(content, encoding='utf-8')
        except OSError as e:
            raise ContextError(f"Failed to save snapshot: {e}")
        
        return str(snapshot_path)
    
    def load_last_snapshot(self) -> Optional[Dict[str, Any]]:
        """
        Load the most recent snapshot.
        
        Returns:
            Dictionary with snapshot data, or None if no snapshots exist
        """
        latest = self.project.get_latest_snapshot()
        
        if not latest:
            return None
        
        try:
            content = latest.read_text(encoding='utf-8')
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
        Generate or update PROJECT.md with latest context.
        
        Args:
            session_data: Session information
            summary: Summary of last session
            next_action: Next action to take
            
        Raises:
            ContextError: If PROJECT.md cannot be updated
        """
        # Calculate session duration
        duration_str = "N/A"
        if session_data.get("duration"):
            duration = session_data["duration"]
            hours = duration // 3600
            minutes = (duration % 3600) // 60
            if hours > 0:
                duration_str = f"{hours}h {minutes}m"
            else:
                duration_str = f"{minutes}m"
        
        # Format content
        content = f"""# Project Context

**Last Updated:** {datetime.now().strftime('%Y-%m-%d %H:%M')}  
**Session Duration:** {duration_str}

## 🎯 Next Action

{next_action}

## 📝 Last Session Summary

{summary}

---

## Session Information

- **Started:** {session_data.get('start_time', 'N/A')}
- **Ended:** {session_data.get('end_time', 'N/A')}
- **Branch:** {session_data.get('branch', 'N/A')}
- **Last Commit:** {session_data.get('last_commit', 'N/A')}

---

## Quick Commands

```bash
# Start a new session
session start

# End current session
session end

# Check status
session status

# View history
session history
```

## Tips

- Review the **Next Action** above to quickly resume work
- Check git branch and commit status before starting
- Run tests to ensure everything works
- Update this file at the end of each session
"""
        
        try:
            self.project.update_project_md(content)
        except ProjectError as e:
            raise ContextError(f"Failed to update PROJECT.md: {e}")
    
    def get_next_action_from_project_md(self) -> Optional[str]:
        """
        Extract the "Next Action" from PROJECT.md.
        
        Returns:
            Next action text, or None if not found
        """
        if not self.project.has_project_md():
            return None
        
        try:
            content = self.project.get_project_md_content()
            
            # Look for "Next Action" section
            match = re.search(
                r'## 🎯 Next Action\s*\n\s*\n(.+?)(?:\n\n##|\Z)',
                content,
                re.DOTALL
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
        Format snapshot content as Markdown.
        
        Args:
            session_data: Session information
            summary: Session summary
            next_action: Next action
            git_info: Optional git information
            test_info: Optional test information
            
        Returns:
            Formatted Markdown content
        """
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        content = f"""# Session Context Snapshot

**Created:** {timestamp}  
**Session ID:** {session_data.get('id', 'N/A')}

---

## 📋 Session Info

- **Started:** {session_data.get('start_time', 'N/A')}
- **Ended:** {session_data.get('end_time', 'N/A')}
- **Duration:** {self._format_duration(session_data.get('duration', 0))}
- **Description:** {session_data.get('description', 'N/A')}

---

## 📝 Summary

{summary if summary else '_No summary provided_'}

---

## 🎯 Next Action

{next_action if next_action else '_No next action specified_'}

---
"""
        
        # Add git information if available
        if git_info:
            content += """
## 🌿 Git Status

"""
            if git_info.get('branch'):
                content += f"- **Branch:** `{git_info['branch']}`\n"
            if git_info.get('last_commit'):
                content += f"- **Last Commit:** `{git_info['last_commit']}`\n"
            if git_info.get('uncommitted_changes'):
                content += f"- **Uncommitted Changes:**\n```\n{git_info['uncommitted_changes']}\n```\n"
            elif git_info.get('has_changes') is False:
                content += "- **Status:** Working directory clean ✅\n"
            
            content += "\n---\n"
        
        # Add test information if available
        if test_info:
            content += """
## 🧪 Test Status

"""
            if test_info.get('summary'):
                content += f"{test_info['summary']}\n"
            
            content += "\n---\n"
        
        content += """
## 💡 Notes

- Use this snapshot to quickly restore context
- Review Next Action before starting work
- Check git status for any uncommitted work
"""
        
        return content
    
    def _parse_snapshot(self, content: str) -> Dict[str, Any]:
        """
        Parse snapshot content into structured data.
        
        Args:
            content: Snapshot Markdown content
            
        Returns:
            Dictionary with parsed snapshot data
        """
        data = {}
        
        # Extract session ID
        session_id_match = re.search(r'\*\*Session ID:\*\* (.+)', content)
        if session_id_match:
            data['session_id'] = session_id_match.group(1)
        
        # Extract summary
        summary_match = re.search(
            r'## 📝 Summary\s*\n\s*\n(.+?)(?:\n\n##|\Z)',
            content,
            re.DOTALL
        )
        if summary_match:
            data['summary'] = summary_match.group(1).strip()
        
        # Extract next action
        next_action_match = re.search(
            r'## 🎯 Next Action\s*\n\s*\n(.+?)(?:\n\n##|\Z)',
            content,
            re.DOTALL
        )
        if next_action_match:
            data['next_action'] = next_action_match.group(1).strip()
        
        return data
    
    def _format_duration(self, seconds: int) -> str:
        """
        Format duration in a human-readable way.
        
        Args:
            seconds: Duration in seconds
            
        Returns:
            Formatted duration string
        """
        if seconds < 60:
            return f"{seconds}s"
        
        minutes = seconds // 60
        remaining_seconds = seconds % 60
        
        if minutes < 60:
            if remaining_seconds > 0:
                return f"{minutes}m {remaining_seconds}s"
            return f"{minutes}m"
        
        hours = minutes // 60
        remaining_minutes = minutes % 60
        
        if remaining_minutes > 0:
            return f"{hours}h {remaining_minutes}m"
        return f"{hours}h"