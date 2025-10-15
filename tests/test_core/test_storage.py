"""
Tests for core/storage.py
"""

import pytest
import json
from pathlib import Path

from session_manager.core.storage import Storage, StorageError


class TestLoadJson:
    """Test JSON loading functionality"""
    
    def test_load_json_file_exists(self, tmp_path):
        """Test loading existing JSON file"""
        test_file = tmp_path / "test.json"
        test_data = {"key": "value", "number": 42}
        test_file.write_text(json.dumps(test_data))
        
        result = Storage.load_json(test_file)
        
        assert result == test_data
    
    def test_load_json_file_not_exists(self, tmp_path):
        """Test loading non-existent file returns default"""
        test_file = tmp_path / "missing.json"
        
        result = Storage.load_json(test_file)
        
        assert result == {}
    
    def test_load_json_custom_default(self, tmp_path):
        """Test loading with custom default value"""
        test_file = tmp_path / "missing.json"
        default = {"default": True}
        
        result = Storage.load_json(test_file, default=default)
        
        assert result == default
        # Ensure we get a copy, not the same object
        assert result is not default
    
    def test_load_json_invalid_format(self, tmp_path):
        """Test loading invalid JSON raises error"""
        test_file = tmp_path / "invalid.json"
        test_file.write_text("not valid json {")
        
        with pytest.raises(StorageError):
            Storage.load_json(test_file)
    
    def test_load_json_not_dict(self, tmp_path):
        """Test loading non-dict JSON raises error"""
        test_file = tmp_path / "array.json"
        test_file.write_text(json.dumps([1, 2, 3]))
        
        with pytest.raises(StorageError):
            Storage.load_json(test_file)
    
    def test_load_json_empty_file(self, tmp_path):
        """Test loading empty file raises error"""
        test_file = tmp_path / "empty.json"
        test_file.write_text("")
        
        with pytest.raises(StorageError):
            Storage.load_json(test_file)


class TestSaveJson:
    """Test JSON saving functionality"""
    
    def test_save_json_basic(self, tmp_path):
        """Test saving basic JSON data"""
        test_file = tmp_path / "test.json"
        test_data = {"key": "value", "number": 42}
        
        Storage.save_json(test_file, test_data)
        
        assert test_file.exists()
        loaded = json.loads(test_file.read_text())
        assert loaded == test_data
    
    def test_save_json_creates_directory(self, tmp_path):
        """Test saving creates parent directories"""
        test_file = tmp_path / "nested" / "deep" / "test.json"
        test_data = {"key": "value"}
        
        Storage.save_json(test_file, test_data)
        
        assert test_file.exists()
        assert test_file.parent.exists()
    
    def test_save_json_overwrites(self, tmp_path):
        """Test saving overwrites existing file"""
        test_file = tmp_path / "test.json"
        old_data = {"old": "data"}
        new_data = {"new": "data"}
        
        test_file.write_text(json.dumps(old_data))
        Storage.save_json(test_file, new_data)
        
        loaded = json.loads(test_file.read_text())
        assert loaded == new_data
        assert "old" not in loaded
    
    def test_save_json_custom_indent(self, tmp_path):
        """Test saving with custom indentation"""
        test_file = tmp_path / "test.json"
        test_data = {"key": "value"}
        
        Storage.save_json(test_file, test_data, indent=4)
        
        content = test_file.read_text()
        # Check that indentation is present
        assert "    " in content
    
    def test_save_json_non_dict_raises(self, tmp_path):
        """Test saving non-dict data raises error"""
        test_file = tmp_path / "test.json"
        
        with pytest.raises(StorageError):
            Storage.save_json(test_file, [1, 2, 3])
    
    def test_save_json_atomic_write(self, tmp_path):
        """Test that save uses atomic write (temp file)"""
        test_file = tmp_path / "test.json"
        test_data = {"key": "value"}
        
        Storage.save_json(test_file, test_data)
        
        # Temp file should be cleaned up
        temp_files = list(tmp_path.glob("*.tmp"))
        assert len(temp_files) == 0
    
    def test_save_json_unicode(self, tmp_path):
        """Test saving Unicode content"""
        test_file = tmp_path / "test.json"
        test_data = {"key": "значение", "emoji": "🚀"}
        
        Storage.save_json(test_file, test_data)
        
        loaded = json.loads(test_file.read_text(encoding='utf-8'))
        assert loaded == test_data


class TestFileOperations:
    """Test file operation utilities"""
    
    def test_file_exists_true(self, tmp_path):
        """Test file_exists returns True for existing file"""
        test_file = tmp_path / "test.txt"
        test_file.touch()
        
        assert Storage.file_exists(test_file)
    
    def test_file_exists_false(self, tmp_path):
        """Test file_exists returns False for non-existent file"""
        test_file = tmp_path / "missing.txt"
        
        assert not Storage.file_exists(test_file)
    
    def test_file_exists_directory(self, tmp_path):
        """Test file_exists returns False for directory"""
        test_dir = tmp_path / "dir"
        test_dir.mkdir()
        
        assert not Storage.file_exists(test_dir)


class TestTextOperations:
    """Test text file operations"""
    
    def test_read_text_exists(self, tmp_path):
        """Test reading existing text file"""
        test_file = tmp_path / "test.txt"
        content = "Hello, World!"
        test_file.write_text(content)
        
        result = Storage.read_text(test_file)
        
        assert result == content
    
    def test_read_text_not_exists(self, tmp_path):
        """Test reading non-existent file returns default"""
        test_file = tmp_path / "missing.txt"
        
        result = Storage.read_text(test_file)
        
        assert result == ""
    
    def test_read_text_custom_default(self, tmp_path):
        """Test reading with custom default"""
        test_file = tmp_path / "missing.txt"
        default = "default content"
        
        result = Storage.read_text(test_file, default=default)
        
        assert result == default
    
    def test_read_text_unicode(self, tmp_path):
        """Test reading Unicode text"""
        test_file = tmp_path / "test.txt"
        content = "Привет, мир! 🚀"
        test_file.write_text(content, encoding='utf-8')
        
        result = Storage.read_text(test_file)
        
        assert result == content
    
    def test_write_text_basic(self, tmp_path):
        """Test writing basic text"""
        test_file = tmp_path / "test.txt"
        content = "Hello, World!"
        
        Storage.write_text(test_file, content)
        
        assert test_file.exists()
        assert test_file.read_text() == content
    
    def test_write_text_creates_directory(self, tmp_path):
        """Test writing creates parent directories"""
        test_file = tmp_path / "nested" / "test.txt"
        content = "Hello!"
        
        Storage.write_text(test_file, content)
        
        assert test_file.exists()
        assert test_file.read_text() == content
    
    def test_write_text_overwrites(self, tmp_path):
        """Test writing overwrites existing file"""
        test_file = tmp_path / "test.txt"
        test_file.write_text("old content")
        
        new_content = "new content"
        Storage.write_text(test_file, new_content)
        
        assert test_file.read_text() == new_content
    
    def test_write_text_unicode(self, tmp_path):
        """Test writing Unicode text"""
        test_file = tmp_path / "test.txt"
        content = "Привет, мир! 🚀"
        
        Storage.write_text(test_file, content)
        
        assert test_file.read_text(encoding='utf-8') == content


class TestDeleteOperations:
    """Test file deletion"""
    
    def test_delete_file_exists(self, tmp_path):
        """Test deleting existing file"""
        test_file = tmp_path / "test.txt"
        test_file.touch()
        
        result = Storage.delete_file(test_file)
        
        assert result is True
        assert not test_file.exists()
    
    def test_delete_file_not_exists(self, tmp_path):
        """Test deleting non-existent file"""
        test_file = tmp_path / "missing.txt"
        
        result = Storage.delete_file(test_file)
        
        assert result is False


class TestBackupOperations:
    """Test file backup functionality"""
    
    def test_backup_file_exists(self, tmp_path):
        """Test backing up existing file"""
        test_file = tmp_path / "test.txt"
        content = "important data"
        test_file.write_text(content)
        
        backup_path = Storage.backup_file(test_file)
        
        assert backup_path is not None
        assert backup_path.exists()
        assert backup_path.read_text() == content
        assert backup_path.name == "test.txt.backup"
    
    def test_backup_file_not_exists(self, tmp_path):
        """Test backing up non-existent file"""
        test_file = tmp_path / "missing.txt"
        
        result = Storage.backup_file(test_file)
        
        assert result is None
    
    def test_backup_file_custom_suffix(self, tmp_path):
        """Test backup with custom suffix"""
        test_file = tmp_path / "test.txt"
        test_file.write_text("data")
        
        backup_path = Storage.backup_file(test_file, suffix=".bak")
        
        assert backup_path is not None
        assert backup_path.name == "test.txt.bak"
    
    def test_backup_file_binary(self, tmp_path):
        """Test backing up binary file"""
        test_file = tmp_path / "test.bin"
        data = bytes([0, 1, 2, 3, 255])
        test_file.write_bytes(data)
        
        backup_path = Storage.backup_file(test_file)
        
        assert backup_path is not None
        assert backup_path.read_bytes() == data