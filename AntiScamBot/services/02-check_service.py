import re
from typing import Optional, Dict
from db.database import search_scammer_in_db

def search_scammer(query: str) -> Optional[Dict]:
    """Search for scammer by various identifiers."""
    query = query.strip().lower()
    
    # Check if it's a Telegram username
    if query.startswith('@'):
        username = query[1:]
        return search_scammer_in_db('username', username)
    
    # Check if it's a Telegram link
    elif 't.me/' in query:
        username = query.split('t.me/')[-1].split('/')[0].split('?')[0]
        return search_scammer_in_db('telegram_link', f'https://t.me/{username}')
    
    # Check if it's a Binance ID (numeric)
    elif query.isdigit():
        return search_scammer_in_db('binance_id', query)
    
    # Check if it's a wallet address
    elif len(query) > 20 and (query.startswith('0x') or query.startswith('bc1')):
        return search_scammer_in_db('crypto_wallet', query)
    
    # Otherwise search by name
    else:
        return search_scammer_in_db('name', query)
    
    return None

def extract_username_from_text(text: str) -> Optional[str]:
    """Extract username from text."""
    patterns = [
        r'@(\w+)',
        r't\.me/(\w+)',
        r'https://t\.me/(\w+)'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1)
    
    return None

def calculate_risk_level(report_count: int, reporter_count: int) -> str:
    """Calculate risk level based on reports."""
    if report_count >= 10 or reporter_count >= 5:
        return "🔴 HIGH"
    elif report_count >= 5 or reporter_count >= 3:
        return "🟡 MEDIUM"
    elif report_count >= 2:
        return "🟠 LOW"
    else:
        return "🟢 MINIMAL"
