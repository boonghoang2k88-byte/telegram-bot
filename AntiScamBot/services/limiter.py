import time
from collections import defaultdict
from datetime import datetime, timedelta

class RateLimiter:
    """Rate limiter for user actions."""
    
    def __init__(self):
        self.user_actions = defaultdict(list)
    
    def check_limit(self, user_id: int, action: str, limit: int, window_seconds: int = 86400) -> bool:
        """Check if user has exceeded rate limit."""
        now = time.time()
        
        # Clean old actions
        self.user_actions[user_id] = [
            ts for ts in self.user_actions[user_id] 
            if now - ts < window_seconds
        ]
        
        # Check limit
        if len(self.user_actions[user_id]) >= limit:
            return False
        
        # Add current action
        self.user_actions[user_id].append(now)
        return True
    
    def get_remaining(self, user_id: int, limit: int, window_seconds: int = 86400) -> int:
        """Get remaining actions for user."""
        now = time.time()
        
        # Clean old actions
        self.user_actions[user_id] = [
            ts for ts in self.user_actions[user_id] 
            if now - ts < window_seconds
        ]
        
        return max(0, limit - len(self.user_actions[user_id]))

# Global rate limiter instance
rate_limiter = RateLimiter()

def check_rate_limit(user_id: int, action: str = 'report', limit: int = 3) -> bool:
    """Check rate limit for user."""
    return rate_limiter.check_limit(user_id, action, limit)

def get_remaining_reports(user_id: int) -> int:
    """Get remaining reports for today."""
    return rate_limiter.get_remaining(user_id, 'report', 3)
