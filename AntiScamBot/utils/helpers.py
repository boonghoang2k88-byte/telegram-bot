import re
from typing import Optional, Dict, Any
from datetime import datetime, timedelta

def extract_username(text: str) -> Optional[str]:
    """Extract username from text."""
    patterns = [
        r'@([a-zA-Z0-9_]{5,32})',
        r't\.me/([a-zA-Z0-9_]{5,32})',
        r'telegram\.me/([a-zA-Z0-9_]{5,32})'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1)
    
    return None

def format_amount(amount: float) -> str:
    """Format amount for display."""
    if amount >= 1000000:
        return f"{amount/1000000:.2f}M"
    elif amount >= 1000:
        return f"{amount/1000:.1f}K"
    else:
        return f"{amount:.2f}"

def format_date(date: datetime) -> str:
    """Format date for display."""
    now = datetime.utcnow()
    diff = now - date
    
    if diff.days == 0:
        if diff.seconds < 60:
            return "just now"
        elif diff.seconds < 3600:
            return f"{diff.seconds // 60}m ago"
        else:
            return f"{diff.seconds // 3600}h ago"
    elif diff.days == 1:
        return "yesterday"
    elif diff.days < 7:
        return f"{diff.days}d ago"
    elif diff.days < 30:
        return f"{diff.days // 7}w ago"
    else:
        return date.strftime("%Y-%m-%d")

def sanitize_input(text: str) -> str:
    """Sanitize user input to prevent injection attacks."""
    if not text:
        return ""
    
    # Remove potentially dangerous characters
    dangerous_chars = ['<', '>', '&', '"', "'", ';', '=', '{', '}', '[', ']', '(', ')']
    
    for char in dangerous_chars:
        text = text.replace(char, '')
    
    # Limit length
    if len(text) > 1000:
        text = text[:1000] + "..."
    
    return text.strip()

def parse_duration(duration_str: str) -> Optional[timedelta]:
    """Parse duration string like '1d', '2h', '30m'."""
    if not duration_str:
        return None
    
    duration_str = duration_str.lower()
    
    # Parse days
    if 'd' in duration_str:
        days = int(re.search(r'(\d+)d', duration_str).group(1))
        return timedelta(days=days)
    
    # Parse hours
    elif 'h' in duration_str:
        hours = int(re.search(r'(\d+)h', duration_str).group(1))
        return timedelta(hours=hours)
    
    # Parse minutes
    elif 'm' in duration_str:
        minutes = int(re.search(r'(\d+)m', duration_str).group(1))
        return timedelta(minutes=minutes)
    
    return None

def create_keyboard_layout(buttons: list, columns: int = 2) -> list:
    """Create keyboard layout with specified number of columns."""
    keyboard = []
    row = []
    
    for i, button in enumerate(buttons):
        row.append(button)
        if (i + 1) % columns == 0:
            keyboard.append(row)
            row = []
    
    if row:
        keyboard.append(row)
    
    return keyboard
