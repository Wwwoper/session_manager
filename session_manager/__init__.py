"""
Session Manager - Smart session tracking with context preservation

A developer-focused tool that combines time tracking, context saving,
and deep integration with your development workflow.

Features:
- Track work sessions with automatic time calculation
- Save and restore project context (what you were doing, what's next)
- Git integration (branch, commits, uncommitted changes)
- Test status tracking (pytest integration)
- GitHub Issues integration (gh CLI)
- Works with or without git - graceful degradation everywhere
- Local storage for complete privacy

Usage:
    session project add myproject /path/to/project
    session start
    session end
    session status
"""

__version__ = "0.1.0"
__author__ = "Your Name"
__email__ = "your.email@example.com"
__license__ = "MIT"

# Core components will be imported here as they're developed
# from .core.session import SessionManager
# from .core.config import GlobalConfig
# from .core.project import Project