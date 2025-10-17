"""
Tests for utils/formatters.py
"""

import pytest
from datetime import datetime

from session_manager.utils.formatters import (
    format_duration,
    format_timestamp,
    format_table,
    format_list,
    format_key_value,
    truncate_string,
    format_stats,
    wrap_text,
)


class TestFormatDuration:
    """Test duration formatting"""
    
    def test_seconds(self):
        """Test formatting seconds"""
        assert format_duration(30) == "30s"
        assert format_duration(59) == "59s"
    
    def test_minutes(self):
        """Test formatting minutes"""
        assert format_duration(60) == "1m"
        assert format_duration(120) == "2m"
        assert format_duration(300) == "5m"
    
    def test_minutes_seconds(self):
        """Test formatting minutes and seconds"""
        assert format_duration(90) == "1m 30s"
        assert format_duration(125) == "2m 5s"
    
    def test_hours(self):
        """Test formatting hours"""
        assert format_duration(3600) == "1h"
        assert format_duration(7200) == "2h"
    
    def test_hours_minutes(self):
        """Test formatting hours and minutes"""
        assert format_duration(5400) == "1h 30m"
        assert format_duration(9000) == "2h 30m"


class TestFormatTimestamp:
    """Test timestamp formatting"""
    
    def test_datetime_format(self):
        """Test datetime formatting"""
        iso_str = "2025-01-15T14:30:45"
        result = format_timestamp(iso_str, "datetime")
        
        assert "2025-01-15" in result
        assert "14:30:45" in result
    
    def test_date_format(self):
        """Test date-only formatting"""
        iso_str = "2025-01-15T14:30:45"
        result = format_timestamp(iso_str, "date")
        
        assert result == "2025-01-15"
    
    def test_time_format(self):
        """Test time-only formatting"""
        iso_str = "2025-01-15T14:30:45"
        result = format_timestamp(iso_str, "time")
        
        assert result == "14:30:45"
    
    def test_invalid_timestamp(self):
        """Test with invalid timestamp"""
        result = format_timestamp("invalid", "datetime")
        
        assert result == "invalid"


class TestFormatTable:
    """Test table formatting"""
    
    def test_basic_table(self):
        """Test basic table formatting"""
        data = [
            {"name": "Alice", "age": 30},
            {"name": "Bob", "age": 25},
        ]
        columns = ["name", "age"]
        
        result = format_table(data, columns)
        
        assert "Alice" in result
        assert "Bob" in result
        assert "30" in result
        assert "25" in result
    
    def test_empty_table(self):
        """Test empty table"""
        result = format_table([], ["name", "age"])
        
        assert "No data" in result
    
    def test_missing_columns(self):
        """Test with missing column data"""
        data = [
            {"name": "Alice"},
            {"name": "Bob", "age": 25},
        ]
        columns = ["name", "age"]
        
        result = format_table(data, columns)
        
        assert "Alice" in result
        assert "Bob" in result


class TestFormatList:
    """Test list formatting"""
    
    def test_basic_list(self):
        """Test basic list formatting"""
        items = ["Item 1", "Item 2", "Item 3"]
        
        result = format_list(items)
        
        assert "Item 1" in result
        assert "Item 2" in result
        assert "•" in result
    
    def test_empty_list(self):
        """Test empty list"""
        result = format_list([])
        
        assert "No items" in result
    
    def test_custom_bullet(self):
        """Test with custom bullet"""
        items = ["Item 1"]
        
        result = format_list(items, bullet="-")
        
        assert "-" in result


class TestFormatKeyValue:
    """Test key-value formatting"""
    
    def test_basic(self):
        """Test basic key-value formatting"""
        data = {"name": "Alice", "age": 30}
        
        result = format_key_value(data)
        
        assert "name" in result
        assert "Alice" in result
        assert "age" in result
        assert "30" in result
    
    def test_empty(self):
        """Test empty data"""
        result = format_key_value({})
        
        assert "No data" in result
    
    def test_alignment(self):
        """Test key alignment"""
        data = {"a": "1", "longer_key": "2"}
        
        result = format_key_value(data)
        
        # Keys should be aligned
        lines = result.split("\n")
        assert len(lines) == 2


class TestTruncateString:
    """Test string truncation"""
    
    def test_no_truncation(self):
        """Test when string fits"""
        result = truncate_string("Hello", 10)
        
        assert result == "Hello"
    
    def test_truncation(self):
        """Test truncation"""
        result = truncate_string("Hello World!", 8)
        
        assert len(result) == 8
        assert result.endswith("...")
    
    def test_custom_suffix(self):
        """Test with custom suffix"""
        result = truncate_string("Hello World!", 8, suffix="--")
        
        assert result.endswith("--")


class TestFormatStats:
    """Test statistics formatting"""
    
    def test_basic_stats(self):
        """Test basic statistics formatting"""
        stats = {
            "total_sessions": 5,
            "total_time": 18000,  # 5 hours
            "average_duration": 3600,
            "longest_session": 7200,
            "shortest_session": 1800,
        }
        
        result = format_stats(stats)
        
        assert "5" in result
        assert "5h" in result
        assert "1h" in result
    
    def test_empty_stats(self):
        """Test with no sessions"""
        stats = {
            "total_sessions": 0,
            "total_time": 0,
        }
        
        result = format_stats(stats)
        
        assert "0" in result


class TestWrapText:
    """Test text wrapping"""
    
    def test_no_wrap(self):
        """Test when text fits"""
        text = "Short text"
        
        result = wrap_text(text, width=20)
        
        assert result == text
    
    def test_wrap(self):
        """Test wrapping long text"""
        text = "This is a very long text that should be wrapped"
        
        result = wrap_text(text, width=20)
        
        lines = result.split("\n")
        assert len(lines) > 1
        for line in lines:
            assert len(line) <= 20
    
    def test_single_long_word(self):
        """Test with single long word"""
        text = "verylongwordthatcannotbewrapped"
        
        result = wrap_text(text, width=10)
        
        # Should still return the word even if it's longer
        assert "verylongword" in result