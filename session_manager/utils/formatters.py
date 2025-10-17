"""
Formatting utilities for Session Manager

Provides functions for formatting output with emojis and colors.
"""

from typing import List, Dict, Any
from datetime import datetime


def format_duration(seconds: int) -> str:
    """
    Format duration in a human-readable way.
    
    Args:
        seconds: Duration in seconds
        
    Returns:
        Formatted duration string (e.g., "1h 30m", "45m", "30s")
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


def format_timestamp(iso_string: str, format_type: str = "datetime") -> str:
    """
    Format ISO timestamp in a readable way.
    
    Args:
        iso_string: ISO-8601 timestamp string
        format_type: Type of formatting ("datetime", "date", "time")
        
    Returns:
        Formatted timestamp string
    """
    try:
        dt = datetime.fromisoformat(iso_string)
        
        if format_type == "date":
            return dt.strftime("%Y-%m-%d")
        elif format_type == "time":
            return dt.strftime("%H:%M:%S")
        else:  # datetime
            return dt.strftime("%Y-%m-%d %H:%M:%S")
    except (ValueError, AttributeError):
        return iso_string


def print_success(message: str) -> None:
    """Print success message with emoji."""
    print(f"✅ {message}")


def print_warning(message: str) -> None:
    """Print warning message with emoji."""
    print(f"⚠️  {message}")


def print_error(message: str) -> None:
    """Print error message with emoji."""
    print(f"❌ {message}")


def print_info(message: str) -> None:
    """Print info message with emoji."""
    print(f"ℹ️  {message}")


def print_section(title: str) -> None:
    """Print section header with emoji."""
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print(f"{'=' * 60}\n")


def print_subsection(title: str) -> None:
    """Print subsection header."""
    print(f"\n{title}")
    print(f"{'-' * len(title)}")


def format_table(data: List[Dict[str, Any]], columns: List[str]) -> str:
    """
    Format data as a simple text table.
    
    Args:
        data: List of dictionaries with data
        columns: List of column names to display
        
    Returns:
        Formatted table as string
    """
    if not data:
        return "No data to display"
    
    # Calculate column widths
    widths = {}
    for col in columns:
        # Start with column name width
        widths[col] = len(col)
        # Check data widths
        for row in data:
            value = str(row.get(col, ""))
            widths[col] = max(widths[col], len(value))
    
    # Build table
    lines = []
    
    # Header
    header = " | ".join(col.ljust(widths[col]) for col in columns)
    lines.append(header)
    lines.append("-" * len(header))
    
    # Rows
    for row in data:
        line = " | ".join(
            str(row.get(col, "")).ljust(widths[col]) 
            for col in columns
        )
        lines.append(line)
    
    return "\n".join(lines)


def format_list(items: List[str], bullet: str = "•") -> str:
    """
    Format list of items with bullets.
    
    Args:
        items: List of strings
        bullet: Bullet character
        
    Returns:
        Formatted list as string
    """
    if not items:
        return "No items"
    
    return "\n".join(f"  {bullet} {item}" for item in items)


def format_key_value(data: Dict[str, Any], indent: int = 2) -> str:
    """
    Format dictionary as key-value pairs.
    
    Args:
        data: Dictionary to format
        indent: Number of spaces for indentation
        
    Returns:
        Formatted key-value pairs as string
    """
    if not data:
        return "No data"
    
    # Find longest key for alignment
    max_key_len = max(len(str(k)) for k in data.keys())
    
    lines = []
    indent_str = " " * indent
    
    for key, value in data.items():
        key_str = str(key).ljust(max_key_len)
        lines.append(f"{indent_str}{key_str} : {value}")
    
    return "\n".join(lines)


def format_session_summary(session: Dict[str, Any]) -> str:
    """
    Format session information as a summary.
    
    Args:
        session: Session dictionary
        
    Returns:
        Formatted session summary
    """
    lines = []
    
    # Basic info
    if session.get("description"):
        lines.append(f"Description: {session['description']}")
    
    # Timing
    if session.get("start_time"):
        lines.append(f"Started: {format_timestamp(session['start_time'])}")
    
    if session.get("end_time"):
        lines.append(f"Ended: {format_timestamp(session['end_time'])}")
    
    if session.get("duration"):
        lines.append(f"Duration: {format_duration(session['duration'])}")
    
    # Git info
    if session.get("branch"):
        lines.append(f"Branch: {session['branch']}")
    
    if session.get("last_commit"):
        lines.append(f"Last Commit: {session['last_commit']}")
    
    # Summary
    if session.get("summary"):
        lines.append(f"\nSummary: {session['summary']}")
    
    if session.get("next_action"):
        lines.append(f"Next Action: {session['next_action']}")
    
    return "\n".join(lines)


def format_project_list(projects: List[Dict[str, Any]]) -> str:
    """
    Format list of projects.
    
    Args:
        projects: List of project info dictionaries
        
    Returns:
        Formatted project list
    """
    if not projects:
        return "No projects found"
    
    lines = []
    
    for project in projects:
        name = project.get("name", "Unknown")
        path = project.get("path", "Unknown")
        alias = project.get("alias")
        
        line = f"• {name}"
        if alias:
            line += f" ({alias})"
        line += f"\n  Path: {path}"
        
        if project.get("last_used"):
            last_used = format_timestamp(project["last_used"])
            line += f"\n  Last used: {last_used}"
        
        lines.append(line)
    
    return "\n\n".join(lines)


def truncate_string(s: str, max_length: int, suffix: str = "...") -> str:
    """
    Truncate string if it exceeds max length.
    
    Args:
        s: String to truncate
        max_length: Maximum length
        suffix: Suffix to add when truncated
        
    Returns:
        Truncated string
    """
    if len(s) <= max_length:
        return s
    return s[:max_length - len(suffix)] + suffix


def format_stats(stats: Dict[str, Any]) -> str:
    """
    Format statistics dictionary.
    
    Args:
        stats: Statistics dictionary
        
    Returns:
        Formatted statistics string
    """
    lines = []
    
    total_sessions = stats.get("total_sessions", 0)
    lines.append(f"Total Sessions: {total_sessions}")
    
    if total_sessions > 0:
        total_time = stats.get("total_time", 0)
        lines.append(f"Total Time: {format_duration(total_time)}")
        
        avg_duration = stats.get("average_duration", 0)
        lines.append(f"Average Duration: {format_duration(avg_duration)}")
        
        longest = stats.get("longest_session", 0)
        lines.append(f"Longest Session: {format_duration(longest)}")
        
        shortest = stats.get("shortest_session", 0)
        lines.append(f"Shortest Session: {format_duration(shortest)}")
    
    return "\n".join(lines)


def wrap_text(text: str, width: int = 70) -> str:
    """
    Wrap text to specified width.
    
    Args:
        text: Text to wrap
        width: Maximum line width
        
    Returns:
        Wrapped text
    """
    if len(text) <= width:
        return text
    
    words = text.split()
    lines = []
    current_line = []
    current_length = 0
    
    for word in words:
        word_len = len(word)
        
        if current_length + word_len + len(current_line) <= width:
            current_line.append(word)
            current_length += word_len
        else:
            if current_line:
                lines.append(" ".join(current_line))
            current_line = [word]
            current_length = word_len
    
    if current_line:
        lines.append(" ".join(current_line))
    
    return "\n".join(lines)


def print_header(text: str, char: str = "=") -> None:
    """
    Print a header with decorative characters.
    
    Args:
        text: Header text
        char: Character to use for decoration
    """
    width = max(len(text) + 4, 60)
    print(f"\n{char * width}")
    print(f"{text.center(width)}")
    print(f"{char * width}\n")