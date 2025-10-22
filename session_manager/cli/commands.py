"""
CLI commands for Session Manager

Implements all command-line interface commands.
"""

from typing import List, Optional
from pathlib import Path

from ..core.config import GlobalConfig, ConfigError
from ..core.project_registry import ProjectRegistry
from ..core.project import Project, ProjectError
from ..core.session import SessionManager, SessionError
from ..core.context import ContextManager, ContextError
from ..integrations.git import GitIntegration
from ..integrations.tests import TestsIntegration
from ..integrations.github import GitHubIntegration
from ..utils.formatters import (
    print_success, print_error, print_warning, print_info,
    print_subsection, format_duration, format_timestamp,
    format_table, format_stats,
    print_header
)


class CLI:
    """
    Command-line interface for Session Manager.
    
    Handles all user commands and provides interactive experience.
    """
    
    def __init__(self, config: GlobalConfig, registry: ProjectRegistry):
        """
        Initialize CLI.
        
        Args:
            config: Global configuration instance
            registry: Project registry instance
        """
        self.config = config
        self.registry = registry
    
    def run(self, args: List[str]) -> int:
        """
        Run CLI command.
        
        Args:
            args: Command-line arguments
            
        Returns:
            Exit code (0 for success, non-zero for errors)
        """
        if not args:
            return self.show_help()
        
        command = args[0].lower()
        rest_args = args[1:]
        
        # Route commands
        commands = {
            "project": self.cmd_project,
            "start": self.cmd_start,
            "end": self.cmd_end,
            "status": self.cmd_status,
            "history": self.cmd_history,
            "stats": self.cmd_stats,
            "help": self.show_help,
            "version": self.show_version,
        }
        
        if command in commands:
            try:
                return commands[command](rest_args)
            except (ConfigError, ProjectError, SessionError, ContextError) as e:
                print_error(str(e))
                return 1
            except Exception as e:
                print_error(f"Unexpected error: {e}")
                return 1
        else:
            print_error(f"Unknown command: {command}")
            print_info("Run 'session help' for usage information")
            return 1
    
    # ==================== Project Commands ====================
    
    def cmd_project(self, args: List[str]) -> int:
        """Handle project subcommands."""
        if not args:
            print_error("Missing project subcommand")
            print_info("Available: add, list, remove, info")
            return 1
        
        subcommand = args[0].lower()
        sub_args = args[1:]
        
        if subcommand == "add":
            return self.project_add(sub_args)
        elif subcommand == "list":
            return self.project_list(sub_args)
        elif subcommand == "remove":
            return self.project_remove(sub_args)
        elif subcommand == "info":
            return self.project_info(sub_args)
        else:
            print_error(f"Unknown project subcommand: {subcommand}")
            return 1
    
    def project_add(self, args: List[str]) -> int:
        """Add a new project."""
        if len(args) < 2:
            print_error("Usage: session project add <name> <path> [--alias <alias>]")
            return 1
        
        name = args[0]
        path = args[1]
        alias = None
        
        # Parse optional alias
        if len(args) >= 4 and args[2] == "--alias":
            alias = args[3]
        
        try:
            project = self.registry.add(name, path, alias=alias, set_as_current=True)
            print_success(f"Added project '{name}'")
            print_info(f"Path: {project.path}")
            if alias:
                print_info(f"Alias: {alias}")
            print_info("Set as current project")
            return 0
        except (ConfigError, ProjectError) as e:
            print_error(f"Failed to add project: {e}")
            return 1
    
    def project_list(self, args: List[str]) -> int:
        """List all projects."""
        projects_info = self.registry.list(sort_by_usage=True)
        
        if not projects_info:
            print_info("No projects registered yet")
            print_info("Add a project with: session project add <name> <path>")
            return 0
        
        print_header("Registered Projects")
        
        # Prepare data for display
        projects_data = []
        for proj_info in projects_info:
            projects_data.append({
                "name": proj_info.name,
                "alias": proj_info.alias or "-",
                "path": str(proj_info.path)[:40] + "..." if len(str(proj_info.path)) > 40 else str(proj_info.path),
            })
        
        # Show current project
        if self.config.current_project:
            print(f"📌 Current: {self.config.current_project}\n")
        
        # Print table
        table = format_table(projects_data, ["name", "alias", "path"])
        print(table)
        
        print(f"\n Total: {len(projects_info)} projects")
        
        return 0
    
    def project_remove(self, args: List[str]) -> int:
        """Remove a project."""
        if len(args) < 1:
            print_error("Usage: session project remove <name>")
            return 1
        
        name = args[0]
        
        # Confirm deletion
        response = input(f"Remove project '{name}'? (y/N): ").strip().lower()
        if response != 'y':
            print_info("Cancelled")
            return 0
        
        try:
            success = self.registry.remove(name, delete_data=False)
            if success:
                print_success(f"Removed project '{name}'")
                print_info("Project data preserved in ~/.session-manager/")
                return 0
            else:
                print_error(f"Project '{name}' not found")
                return 1
        except ProjectError as e:
            print_error(f"Failed to remove project: {e}")
            return 1
    
    def project_info(self, args: List[str]) -> int:
        """Show project information."""
        if len(args) < 1:
            print_error("Usage: session project info <name>")
            return 1
        
        name = args[0]
        project = self.registry.get(name)
        
        if not project:
            print_error(f"Project '{name}' not found")
            return 1
        
        print_header(f"Project: {name}")
        
        info = project.get_project_info()
        
        print(f"Path: {info['path']}")
        print(f"Exists: {'✅' if info['exists'] else '❌'}")
        print(f"Has PROJECT.md: {'✅' if info['has_project_md'] else '❌'}")
        print(f"\nTotal Sessions: {info['total_sessions']}")
        print(f"Active Session: {info['active_session'] if info['active_session'] else 'None'}")
        print(f"Total Snapshots: {info['total_snapshots']}")
        
        if info['latest_snapshot']:
            print(f"Latest Snapshot: {info['latest_snapshot']}")
        
        return 0
    
    # ==================== Session Commands ====================
    
    def cmd_start(self, args: List[str]) -> int:
        """Start a new session."""
        # Get project
        project_name = args[0] if args else None
        project = self._resolve_project(project_name)
        
        if not project:
            return 1
        
        # Get description
        description = ""
        if len(args) > 1:
            description = " ".join(args[1:])
        
        try:
            sm = SessionManager(project)
            
            # Check for active session
            if sm.get_active():
                print_warning("Session already active!")
                print_info("End it with: session end")
                return 1
            
            print_header("🚀 Starting New Session")
            print(f"Project: {project.name}\n")
            
            # Show last context
            self._show_last_context(project)
            
            # Show git status
            self._show_git_status(project)
            
            # Show GitHub issues
            self._show_github_issues(project)
            
            # Run tests
            self._show_test_status(project)
            
            # Start session
            session = sm.start(description=description)
            
            # Update with git info
            git = GitIntegration(project.path)
            if git.is_git_repo():
                sm.update_session_metadata(
                    session["id"],
                    branch=git.get_current_branch(),
                    last_commit=git.get_last_commit()
                )
            
            print_success("Session started!")
            print_info(f"Session ID: {session['id'][:8]}...")
            
            return 0
            
        except SessionError as e:
            print_error(f"Failed to start session: {e}")
            return 1
    
    def cmd_end(self, args: List[str]) -> int:
        """End the active session."""
        # Get project
        project_name = args[0] if args else None
        project = self._resolve_project(project_name)
        
        if not project:
            return 1
        
        try:
            sm = SessionManager(project)
            
            active = sm.get_active()
            if not active:
                print_warning("No active session")
                return 1
            
            print_header("💾 Ending Session")
            
            # Get summary
            print("What was accomplished in this session?")
            summary = input("Summary: ").strip()
            
            print("\nWhat is the next concrete action?")
            print("(e.g., 'Add tests for parse_data function')")
            next_action = input("Next action: ").strip()
            
            # Check for uncommitted changes
            git = GitIntegration(project.path)
            if git.has_uncommitted_changes():
                print_warning("\nUncommitted changes detected!")
                changes = git.get_uncommitted_changes()
                print(changes[:200])  # Show first 200 chars
                
                response = input("\nCreate a commit? (y/N): ").strip().lower()
                if response == 'y':
                    commit_msg = input("Commit message: ").strip()
                    if commit_msg:
                        git.add_all()
                        if git.create_commit(commit_msg):
                            print_success("Commit created")
                        else:
                            print_error("Failed to create commit")
            
            # End session
            completed = sm.end(summary=summary, next_action=next_action)
            
            # Save context snapshot
            cm = ContextManager(project)
            git_info = git.get_git_info() if git.is_git_repo() else None
            tests = TestsIntegration(project.path)
            test_info = tests.get_test_info() if tests.is_pytest_available() else None
            
            snapshot_path = cm.save_snapshot(
                completed,
                summary,
                next_action,
                git_info=git_info,
                test_info=test_info
            )
            
            # Generate PROJECT.md
            cm.generate_project_md(completed, summary, next_action)
            
            print_success("\nSession ended!")
            print_info(f"Duration: {format_duration(completed['duration'])}")
            print_info(f"Snapshot saved: {Path(snapshot_path).name}")
            print_info("PROJECT.md updated")
            
            return 0
            
        except (SessionError, ContextError) as e:
            print_error(f"Failed to end session: {e}")
            return 1
    
    def cmd_status(self, args: List[str]) -> int:
        """Show project status."""
        # Get project
        project_name = args[0] if args else None
        project = self._resolve_project(project_name)
        
        if not project:
            return 1
        
        print_header(f"📊 Status: {project.name}")
        
        # Session info
        sm = SessionManager(project)
        active = sm.get_active()
        
        if active:
            print_subsection("Active Session")
            print(f"Started: {format_timestamp(active['start_time'])}")
            if active.get('description'):
                print(f"Description: {active['description']}")
            
            # Calculate current duration
            from datetime import datetime
            start = datetime.fromisoformat(active['start_time'])
            duration = int((datetime.now() - start).total_seconds())
            print(f"Duration: {format_duration(duration)}")
        else:
            print("No active session\n")
        
        # Last context
        self._show_last_context(project)
        
        # Git status
        self._show_git_status(project)
        
        # Test status
        self._show_test_status(project)
        
        return 0
    
    def cmd_history(self, args: List[str]) -> int:
        """Show session history."""
        # Get project
        project_name = args[0] if args and not args[0].startswith('--') else None
        project = self._resolve_project(project_name)
        
        if not project:
            return 1
        
        # Parse limit
        limit = 10
        for i, arg in enumerate(args):
            if arg == "--limit" and i + 1 < len(args):
                try:
                    limit = int(args[i + 1])
                except ValueError:
                    print_error("Invalid limit value")
                    return 1
        
        sm = SessionManager(project)
        history = sm.get_history(limit=limit)
        
        if not history:
            print_info("No completed sessions yet")
            return 0
        
        print_header(f"📜 Session History: {project.name}")
        
        for i, session in enumerate(history, 1):
            print(f"\n{i}. Session")
            print(f"   Started: {format_timestamp(session['start_time'])}")
            print(f"   Duration: {format_duration(session['duration'])}")
            
            if session.get('summary'):
                summary = session['summary'][:60]
                if len(session['summary']) > 60:
                    summary += "..."
                print(f"   Summary: {summary}")
        
        print(f"\nShowing {len(history)} most recent sessions")
        
        return 0
    
    def cmd_stats(self, args: List[str]) -> int:
        """Show session statistics."""
        # Get project
        project_name = args[0] if args else None
        project = self._resolve_project(project_name)
        
        if not project:
            return 1
        
        sm = SessionManager(project)
        stats = sm.get_stats()
        
        print_header(f"📊 Statistics: {project.name}")
        
        print(format_stats(stats))
        
        # Today's time
        today_time = sm.get_total_time_today()
        if today_time > 0:
            print(f"\nToday's Total: {format_duration(today_time)}")
        
        return 0
    
    # ==================== Helper Methods ====================
    
    def _resolve_project(self, project_name: Optional[str]) -> Optional[Project]:
        """Resolve project name to Project instance."""
        if project_name:
            project = self.registry.get(project_name)
            if not project:
                print_error(f"Project '{project_name}' not found")
                return None
            return project
        
        # Try current project
        if self.config.current_project:
            return self.registry.get(self.config.current_project)
        
        # Try auto-detect
        project = self.registry.detect_current()
        if project:
            print_info(f"Auto-detected project: {project.name}")
            return project
        
        print_error("No project specified and couldn't auto-detect")
        print_info("Specify project: session start <project-name>")
        print_info("Or add current directory: session project add <name> .")
        return None
    
    def _show_last_context(self, project: Project) -> None:
        """Show last saved context."""
        cm = ContextManager(project)
        next_action = cm.get_next_action_from_project_md()
        
        if next_action:
            print_subsection("📌 Next Action")
            print(f"   {next_action}\n")
    
    def _show_git_status(self, project: Project) -> None:
        """Show git status."""
        git = GitIntegration(project.path)
        
        if not git.is_git_repo():
            return
        
        print_subsection("🌿 Git Status")
        
        branch = git.get_current_branch()
        if branch:
            print(f"   Branch: {branch}")
        
        commit = git.get_last_commit()
        if commit:
            print(f"   Last Commit: {commit}")
        
        if git.has_uncommitted_changes():
            print("   ⚠️  Uncommitted changes detected")
        else:
            print("   ✅ Working directory clean")
        
        print()
    
    def _show_github_issues(self, project: Project) -> None:
        """Show GitHub issues."""
        gh = GitHubIntegration(project.path)
        
        if not gh.is_github_repo():
            return
        
        issues = gh.get_open_issues(limit=3)
        
        if issues:
            print_subsection("📋 Open Issues")
            summary = gh.format_issues_summary(issues)
            print(summary)
            print()
    
    def _show_test_status(self, project: Project) -> None:
        """Show test status."""
        tests = TestsIntegration(project.path)
        
        if not tests.is_pytest_available():
            return
        
        print_subsection("🧪 Running Tests...")
        
        result = tests.run_tests(timeout=15, verbose=False)
        
        if result["success"]:
            print(f"   ✅ {result['summary']}")
        else:
            print(f"   ❌ {result['summary']}")
        
        print()
    
    # ==================== Info Commands ====================
    
    def show_help(self, args: List[str] = None) -> int:
        """Show help information."""
        print_header("Session Manager - Help")
        
        print("USAGE:")
        print("  session <command> [options]\n")
        
        print("PROJECT COMMANDS:")
        print("  project add <name> <path> [--alias <alias>]")
        print("    Add a new project")
        print("  project list")
        print("    List all projects")
        print("  project remove <name>")
        print("    Remove a project")
        print("  project info <name>")
        print("    Show project information\n")
        
        print("SESSION COMMANDS:")
        print("  start [project] [description]")
        print("    Start a new session")
        print("  end [project]")
        print("    End active session")
        print("  status [project]")
        print("    Show current status")
        print("  history [project] [--limit N]")
        print("    Show session history")
        print("  stats [project]")
        print("    Show session statistics\n")
        
        print("OTHER COMMANDS:")
        print("  help")
        print("    Show this help")
        print("  version")
        print("    Show version\n")
        
        print("EXAMPLES:")
        print("  # Add a project")
        print("  session project add myapp /path/to/myapp --alias ma\n")
        
        print("  # Start working")
        print("  session start myapp\n")
        
        print("  # End session")
        print("  session end\n")
        
        print("  # Check status")
        print("  session status\n")
        
        return 0
    
    def show_version(self, args: List[str] = None) -> int:
        """Show version information."""
        from .. import __version__
        
        print(f"Session Manager v{__version__}")
        print("Smart session tracking for developers")
        
        return 0