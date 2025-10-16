"""
Управление глобальной конфигурацией для Session Manager

Управляет глобальным файлом конфигурации и реестром проектов.
"""

from datetime import datetime
from typing import Dict, Optional, List, Any

from ..utils.paths import (
    get_config_file,
    ensure_storage_structure,
    is_valid_project_path,
    normalize_project_path,
)
from .storage import Storage, StorageError


class ConfigError(Exception):
    """Базовое исключение для ошибок конфигурации"""
    pass


class ProjectInfo:
    """Информация о зарегистрированном проекте"""
    
    def __init__(
        self,
        name: str,
        path: str,
        alias: Optional[str] = None,
        created_at: Optional[str] = None,
        last_used: Optional[str] = None,
    ):
        self.name = name
        self.path = normalize_project_path(path)
        self.alias = alias
        self.created_at = created_at or datetime.now().isoformat()
        self.last_used = last_used or datetime.now().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """Конвертирует в словарь для сериализации"""
        return {
            "path": self.path,
            "alias": self.alias,
            "created_at": self.created_at,
            "last_used": self.last_used,
        }
    
    @classmethod
    def from_dict(cls, name: str, data: Dict[str, Any]) -> "ProjectInfo":
        """Создает ProjectInfo из словаря"""
        return cls(
            name=name,
            path=data.get("path", ""),
            alias=data.get("alias"),
            created_at=data.get("created_at"),
            last_used=data.get("last_used"),
        )
    
    def update_last_used(self) -> None:
        """Обновляет метку времени last_used на текущее время"""
        self.last_used = datetime.now().isoformat()


class GlobalConfig:
    """
    Глобальная конфигурация для Session Manager.
    
    Управляет:
    - Текущим активным проектом
    - Реестром всех проектов
    - Глобальными настройками
    """
    
    def __init__(self):
        self.config_file = get_config_file()
        self.current_project: Optional[str] = None
        self.projects: Dict[str, ProjectInfo] = {}
        self._storage = Storage()
    
    def load(self) -> None:
        """
        Загружает конфигурацию с диска.
        
        Создает конфигурацию по умолчанию, если файл не существует.
        
        Raises:
            ConfigError: Если конфигурация невалидна или не может быть загружена
        """
        # Обеспечивает существование структуры хранения
        ensure_storage_structure()
        
        try:
            data = self._storage.load_json(self.config_file, default={})
            
            # Загружает текущий проект
            self.current_project = data.get("current_project")
            
            # Загружает проекты
            projects_data = data.get("projects", {})
            self.projects = {}
            
            for name, project_data in projects_data.items():
                try:
                    self.projects[name] = ProjectInfo.from_dict(name, project_data)
                except Exception as e:
                    # Логирует предупреждение, но продолжает загрузку других проектов
                    print(f"⚠️  Предупреждение: Не удалось загрузить проект '{name}': {e}")
            
        except StorageError as e:
            raise ConfigError(f"Не удалось загрузить конфигурацию: {e}")
    
    def save(self) -> None:
        """
        Сохраняет конфигурацию на диск.
        
        Raises:
            ConfigError: Если конфигурация не может быть сохранена
        """
        try:
            data = {
                "current_project": self.current_project,
                "projects": {
                    name: project.to_dict()
                    for name, project in self.projects.items()
                },
            }
            
            self._storage.save_json(self.config_file, data)
            
        except StorageError as e:
            raise ConfigError(f"Не удалось сохранить конфигурацию: {e}")
    
    def add_project(
        self,
        name: str,
        path: str,
        alias: Optional[str] = None,
    ) -> bool:
        """
        Добавляет новый проект в конфигурацию.
        
        Args:
            name: Уникальное имя проекта
            path: Путь к директории проекта
            alias: Опциональное короткое псевдоним для проекта
            
        Returns:
            True если проект был добавлен, False если уже существует
            
        Raises:
            ConfigError: Если путь проекта невалиден или имя невалидно
        """
        # Проверяет имя
        if not name or not name.strip():
            raise ConfigError("Имя проекта не может быть пустым")
        
        if not name.replace("-", "").replace("_", "").isalnum():
            raise ConfigError(
                "Имя проекта должно содержать только буквенно-цифровые символы, "
                "дефисы и подчеркивания"
            )
        
        # Проверяет, существует ли уже
        if name in self.projects:
            return False
        
        # Проверяет путь
        if not is_valid_project_path(path):
            raise ConfigError(f"Невалидный путь проекта: {path} (должен быть существующей директорией)")
        
        # Проверяет псевдоним, если предоставлен
        if alias and not alias.replace("-", "").replace("_", "").isalnum():
            raise ConfigError(
                "Псевдоним проекта должен содержать только буквенно-цифровые символы, "
                "дефисы и подчеркивания"
            )
        
        # Проверяет, используется ли псевдоним уже
        if alias:
            for existing_name, existing_project in self.projects.items():
                if existing_project.alias == alias:
                    raise ConfigError(
                        f"Псевдоним '{alias}' уже используется проектом '{existing_name}'"
                    )
        
        # Добавляет проект
        self.projects[name] = ProjectInfo(name, path, alias)
        self.save()
        
        return True
    
    def remove_project(self, name: str) -> bool:
        """
        Удаляет проект из конфигурации.
        
        Args:
            name: Имя проекта для удаления
            
        Returns:
            True если проект был удален, False если не существовал
        """
        if name not in self.projects:
            return False
        
        del self.projects[name]
        
        # Очищает current_project если это был этот проект
        if self.current_project == name:
            self.current_project = None
        
        self.save()
        return True
    
    def get_project_info(self, name: str) -> Optional[ProjectInfo]:
        """
        Получает информацию о проекте.
        
        Args:
            name: Имя проекта или псевдоним
            
        Returns:
            ProjectInfo если найден, иначе None
        """
        # Сначала пробует прямое совпадение по имени
        if name in self.projects:
            return self.projects[name]
        
        # Пробует совпадение по псевдониму
        for project in self.projects.values():
            if project.alias == name:
                return project
        
        return None
    
    def update_last_used(self, name: str) -> bool:
        """
        Обновляет метку времени last_used для проекта.
        
        Args:
            name: Имя проекта
            
        Returns:
            True если обновлено, False если проект не найден
        """
        if name not in self.projects:
            return False
        
        self.projects[name].update_last_used()
        self.save()
        return True
    
    def set_current_project(self, name: Optional[str]) -> bool:
        """
        Устанавливает текущий активный проект.
        
        Args:
            name: Имя проекта для установки как текущий (или None для очистки)
            
        Returns:
            True если установлено успешно, False если проект не существует
        """
        if name is not None and name not in self.projects:
            return False
        
        self.current_project = name
        
        if name is not None:
            self.update_last_used(name)
        
        self.save()
        return True
    
    def get_all_projects(self) -> List[ProjectInfo]:
        """
        Получает список всех проектов.
        
        Returns:
            Список объектов ProjectInfo
        """
        return list(self.projects.values())
    
    def get_projects_sorted_by_usage(self) -> List[ProjectInfo]:
        """
        Получает список всех проектов отсортированный по последнему использованию (сначала последние).
        
        Returns:
            Список объектов ProjectInfo отсортированный по last_used
        """
        return sorted(
            self.projects.values(),
            key=lambda p: p.last_used,
            reverse=True,
        )
    
    def project_exists(self, name: str) -> bool:
        """
        Проверяет, существует ли проект.
        
        Args:
            name: Имя проекта или псевдоним
            
        Returns:
            True если проект существует
        """
        return self.get_project_info(name) is not None
    
    def get_project_count(self) -> int:
        """
        Получает общее количество зарегистрированных проектов.
        
        Returns:
            Количество проектов
        """
        return len(self.projects)