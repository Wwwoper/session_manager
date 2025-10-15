"""
Project registry management

Provides high-level operations for managing multiple projects.
"""

from typing import Optional, List, Dict
from pathlib import Path

from .config import GlobalConfig, ProjectInfo, ConfigError
from .project import Project, ProjectError
from ..utils.paths import detect_current_project


class ProjectRegistry:
    """
    Registry for managing multiple projects.
    
    Provides CRUD operations and search functionality for projects.
    Integrates with GlobalConfig for persistence.
    """
    
    def __init__(self, config: GlobalConfig):
        """
        Initialize project registry.
        
        Args:
            config: GlobalConfig instance for persistence
        """
        self.config = config
    
    def add(
        self,
        name: str,
        path: str,
        alias: Optional[str] = None,
        set_as_current: bool = False,
    ) -> Project:
        """
        Add a new project to the registry.
        
        Args:
            name: Unique project name
            path: Path to project directory
            alias: Optional short alias
            set_as_current: If True, set as current project
            
        Returns:
            Created Project instance
            
        Raises:
            ConfigError: If project cannot be added (validation errors)
            ProjectError: If project structure cannot be created
        """
        # Add to config (handles validation)
        success = self.config.add_project(name, path, alias)
        
        if not success:
            raise ConfigError(f"Project '{name}' already exists")
        
        # Create project instance
        project = Project(name, path)
        
        # Ensure project structure exists
        try:
            project.ensure_structure()
        except Exception as e:
            # Rollback: remove from config
            self.config.remove_project(name)
            raise ProjectError(f"Failed to create project structure: {e}")
        
        # Set as current if requested
        if set_as_current:
            self.config.set_current_project(name)
        
        return project
    
    def remove(self, name: str, delete_data: bool = False) -> bool:
        """
        Remove a project from the registry.
        
        Args:
            name: Project name or alias
            delete_data: If True, also delete project data files
            
        Returns:
            True if project was removed, False if not found
            
        Raises:
            ProjectError: If data deletion fails
        """
        # Get project info to resolve alias
        project_info = self.config.get_project_info(name)
        if not project_info:
            return False
        
        actual_name = project_info.name
        
        # Delete data if requested
        if delete_data:
            project = Project(actual_name, project_info.path)
            try:
                # Delete sessions file
                if project.sessions_file.exists():
                    project.sessions_file.unlink()
                
                # Delete PROJECT.md
                if project.project_md_file.exists():
                    project.project_md_file.unlink()
                
                # Delete snapshots directory
                if project.snapshots_dir.exists():
                    import shutil
                    shutil.rmtree(project.snapshots_dir)
                
                # Delete project directory if empty
                if project._project_dir.exists():
                    try:
                        project._project_dir.rmdir()
                    except OSError:
                        # Directory not empty, leave it
                        pass
                        
            except Exception as e:
                raise ProjectError(f"Failed to delete project data: {e}")
        
        # Remove from config
        return self.config.remove_project(actual_name)
    
    def list(self, sort_by_usage: bool = True) -> List[ProjectInfo]:
        """
        List all registered projects.
        
        Args:
            sort_by_usage: If True, sort by last usage (most recent first)
            
        Returns:
            List of ProjectInfo objects
        """
        if sort_by_usage:
            return self.config.get_projects_sorted_by_usage()
        else:
            return self.config.get_all_projects()
    
    def get(self, name: str) -> Optional[Project]:
        """
        Get a project by name or alias.
        
        Args:
            name: Project name or alias
            
        Returns:
            Project instance, or None if not found
        """
        project_info = self.config.get_project_info(name)
        if not project_info:
            return None
        
        return Project(project_info.name, project_info.path)
    
    def find_by_path(self, path: str) -> Optional[str]:
        """
        Find project name by path.
        
        Args:
            path: Path to search for
            
        Returns:
            Project name if found, None otherwise
        """
        search_path = Path(path).resolve()
        
        for project_info in self.config.get_all_projects():
            project_path = Path(project_info.path).resolve()
            if project_path == search_path:
                return project_info.name
        
        return None
    
    def get_current(self) -> Optional[Project]:
        """
        Get the current active project.
        
        Returns:
            Current Project instance, or None if no current project
        """
        if not self.config.current_project:
            return None
        
        return self.get(self.config.current_project)
    
    def set_current(self, name: Optional[str]) -> bool:
        """
        Set the current active project.
        
        Args:
            name: Project name/alias to set as current (or None to clear)
            
        Returns:
            True if successful, False if project not found
        """
        if name is not None:
            # Resolve alias to actual name
            project_info = self.config.get_project_info(name)
            if not project_info:
                return False
            name = project_info.name
        
        return self.config.set_current_project(name)
    
    def detect_current(self) -> Optional[Project]:
        """
        Auto-detect current project based on current working directory.
        
        Returns:
            Detected Project instance, or None if not found
        """
        # Build projects dict for detection
        projects_dict = {
            name: {"path": info.path}
            for name, info in self.config.projects.items()
        }
        
        project_name = detect_current_project(projects_dict)
        
        if project_name:
            return self.get(project_name)
        
        return None
    
    def exists(self, name: str) -> bool:
        """
        Check if a project exists in the registry.
        
        Args:
            name: Project name or alias
            
        Returns:
            True if project exists
        """
        return self.config.project_exists(name)
    
    def get_count(self) -> int:
        """
        Get total number of registered projects.
        
        Returns:
            Number of projects
        """
        return self.config.get_project_count()
    
    def search(self, query: str) -> List[ProjectInfo]:
        """
        Search projects by name, alias, or path.
        
        Args:
            query: Search query (case-insensitive)
            
        Returns:
            List of matching ProjectInfo objects
        """
        query_lower = query.lower()
        results = []
        
        for project_info in self.config.get_all_projects():
            # Search in name
            if query_lower in project_info.name.lower():
                results.append(project_info)
                continue
            
            # Search in alias
            if project_info.alias and query_lower in project_info.alias.lower():
                results.append(project_info)
                continue
            
            # Search in path
            if query_lower in project_info.path.lower():
                results.append(project_info)
                continue
        
        return results
    
    def get_projects_summary(self) -> Dict[str, any]:
        """
        Get summary information about all projects.
        
        Returns:
            Dictionary with summary statistics
        """
        all_projects = self.config.get_all_projects()
        
        total_sessions = 0
        active_sessions = 0
        
        for project_info in all_projects:
            try:
                project = Project(project_info.name, project_info.path)
                sessions_data = project.get_sessions_data()
                total_sessions += len(sessions_data.get("sessions", []))
                if sessions_data.get("active_session"):
                    active_sessions += 1
            except ProjectError:
                # Skip projects with errors
                continue
        
        return {
            "total_projects": len(all_projects),
            "total_sessions": total_sessions,
            "active_sessions": active_sessions,
            "current_project": self.config.current_project,
        }
    
    def validate_all(self) -> Dict[str, List[str]]:
        """
        Validate all registered projects.
        
        Checks if project paths still exist.
        
        Returns:
            Dictionary with 'valid' and 'invalid' project names
        """
        valid = []
        invalid = []
        
        for project_info in self.config.get_all_projects():
            project_path = Path(project_info.path)
            if project_path.exists() and project_path.is_dir():
                valid.append(project_info.name)
            else:
                invalid.append(project_info.name)
        
        return {
            "valid": valid,
            "invalid": invalid,
        }