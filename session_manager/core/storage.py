"""
Слой хранения для Session Manager

Обрабатывает все операции ввода-вывода файлов с правильной обработкой ошибок.
"""

import json
from pathlib import Path
from typing import Any, Dict, Optional


class StorageError(Exception):
    """Базовое исключение для ошибок хранения данных"""
    pass


class Storage:
    """
    Обрабатывает операции файлового хранения для Session Manager.
    
    Обеспечивает безопасные операции чтения/записи для JSON и текстовых файлов
    с комплексной обработкой ошибок.
    """
    
    @staticmethod
    def load_json(path: Path, default: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Загружает данные из JSON файла.
        
        Args:
            path: Путь к JSON файлу
            default: Значение по умолчанию, если файл не существует
            
        Returns:
            Словарь с загруженными данными, или default если файл не существует
            
        Raises:
            StorageError: Если файл существует, но не может быть прочитан или распарсен
        """
        if default is None:
            default = {}
        
        if not path.exists():
            return default.copy()
        
        try:
            with path.open('r', encoding='utf-8') as f:
                data = json.load(f)
                
            if not isinstance(data, dict):
                raise StorageError(
                    f"Неверный формат JSON в {path}: ожидался объект, получен {type(data).__name__}"
                )
                
            return data
            
        except json.JSONDecodeError as e:
            raise StorageError(f"Не удалось распарсить JSON из {path}: {e}")
        except OSError as e:
            raise StorageError(f"Не удалось прочитать файл {path}: {e}")
    
    @staticmethod
    def save_json(path: Path, data: Dict[str, Any], indent: int = 2) -> None:
        """
        Сохраняет данные в JSON файл.
        
        Созет родительские директории, если они не существуют.
        Использует атомарную запись (запись во временный файл, затем переименование) для безопасности.
        
        Args:
            path: Путь к JSON файлу
            data: Словарь для сохранения
            indent: Уровень отступа JSON (по умолчанию: 2)
            
        Raises:
            StorageError: Если файл не может быть записан
        """
        if not isinstance(data, dict):
            raise StorageError(
                f"Нельзя сохранить не-словарь: ожидался dict, получен {type(data).__name__}"
            )
        
        try:
            # Обеспечивает существование родительской директории
            path.parent.mkdir(parents=True, exist_ok=True)
            
            # Сначала записывает во временный файл (атомарная запись)
            temp_path = path.with_suffix(path.suffix + '.tmp')
            
            with temp_path.open('w', encoding='utf-8') as f:
                json.dump(data, f, indent=indent, ensure_ascii=False)
                f.write('\n')  # Добавляет завершающий перенос строки
            
            # Переименовывает временный файл в целевой (атомарно на POSIX системах)
            temp_path.replace(path)
            
        except OSError as e:
            raise StorageError(f"Не удалось записать файл {path}: {e}")
        except (TypeError, ValueError) as e:
            raise StorageError(f"Не удалось сериализовать данные в JSON: {e}")
    
    @staticmethod
    def file_exists(path: Path) -> bool:
        """
        Проверяет, существует ли файл.
        
        Args:
            path: Путь для проверки
            
        Returns:
            True если файл существует, иначе False
        """
        return path.exists() and path.is_file()
    
    @staticmethod
    def read_text(path: Path, default: str = "") -> str:
        """
        Читает текст из файла.
        
        Args:
            path: Путь к текстовому файлу
            default: Значение по умолчанию, если файл не существует
            
        Returns:
            Содержимое файла как строка, или default если файл не существует
            
        Raises:
            StorageError: Если файл существует, но не может быть прочитан
        """
        if not path.exists():
            return default
        
        try:
            return path.read_text(encoding='utf-8')
        except OSError as e:
            raise StorageError(f"Не удалось прочитать файл {path}: {e}")
    
    @staticmethod
    def write_text(path: Path, content: str) -> None:
        """
        Записывает текст в файл.
        
        Создает родительские директории, если они не существуют.
        Использует атомарную запись для безопасности.
        
        Args:
            path: Путь к текстовому файлу
            content: Текстовое содержимое для записи
            
        Raises:
            StorageError: Если файл не может быть записан
        """
        try:
            # Обеспечивает существование родительской директории
            path.parent.mkdir(parents=True, exist_ok=True)
            
            # Сначала записывает во временный файл (атомарная запись)
            temp_path = path.with_suffix(path.suffix + '.tmp')
            temp_path.write_text(content, encoding='utf-8')
            
            # Переименовывает временный файл в целевой
            temp_path.replace(path)
            
        except OSError as e:
            raise StorageError(f"Не удалось записать файл {path}: {e}")
    
    @staticmethod
    def delete_file(path: Path) -> bool:
        """
        Удаляет файл, если он существует.
        
        Args:
            path: Путь к файлу для удаления
            
        Returns:
            True если файл был удален, False если он не существовал
            
        Raises:
            StorageError: Если файл существует, но не может быть удален
        """
        if not path.exists():
            return False
        
        try:
            path.unlink()
            return True
        except OSError as e:
            raise StorageError(f"Не удалось удалить файл {path}: {e}")
    
    @staticmethod
    def backup_file(path: Path, suffix: str = ".backup") -> Optional[Path]:
        """
        Создает резервную копию файла.
        
        Args:
            path: Путь к файлу для резервного копирования
            suffix: Суффикс для добавления к имени резервного файла
            
        Returns:
            Путь к резервному файлу, или None если оригинал не существует
            
        Raises:
            StorageError: Если резервная копия не может быть создана
        """
        if not path.exists():
            return None
        
        backup_path = path.with_suffix(path.suffix + suffix)
        
        try:
            # Читает оригинал и записывает в резервную копию
            content = path.read_bytes()
            backup_path.write_bytes(content)
            return backup_path
            
        except OSError as e:
            raise StorageError(f"Не удалось создать резервную копию {path}: {e}")