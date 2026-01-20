import time
from typing import Dict
from datetime import datetime, timedelta
from db.database import save_report, get_user_reports_today

def create_report(report_data: Dict) -> bool:
    """Create a new scam report."""
    # Add timestamp
    report_data['created_at'] = datetime.now().isoformat()
    
    # Save to database
    return save_report(report_data)

def check_report_limit(user_id: int) -> bool:
    """Check if user has exceeded report limit (3 per day)."""
    from config.settings import REPORT_LIMIT_PER_DAY
    
    reports_today = get_user_reports_today(user_id)
    
    return len(reports_today) >= REPORT_LIMIT_PER_DAY

def validate_report_data(data: Dict) -> tuple[bool, str]:
    """Validate report data."""
    required_fields = ['scammer_name', 'scammer_username', 'scammer_link', 'scammer_id']
    
    for field in required_fields:
        if not data.get(field):
            return False, f"Missing field: {field}"
    
    # Validate Telegram link
    if 't.me/' not in data['scammer_link']:
        return False, "Invalid Telegram link"
    
    # Validate amount (if provided)
    if 'amount' in data and data['amount'] < 0:
        return False, "Amount cannot be negative"
    
    return True, "Valid"

def generate_report_id() -> str:
    """Generate unique report ID."""
    timestamp = int(time.time() * 1000)
    return f"REPORT_{timestamp}"
