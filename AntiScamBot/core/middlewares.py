from telegram.ext import BaseMiddleware
from telegram import Update
from typing import Callable, Dict, Any, Awaitable
import time

class RateLimitMiddleware(BaseMiddleware):
    def __init__(self, rate_limit_per_minute: int = 30):
        self.rate_limit_per_minute = rate_limit_per_minute
        self.user_timestamps = {}
        super().__init__()
    
    async def __call__(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        handler: Callable[[Update, ContextTypes.DEFAULT_TYPE], Awaitable[Any]]
    ) -> Any:
        user_id = update.effective_user.id if update.effective_user else None
        
        if user_id:
            current_time = time.time()
            if user_id in self.user_timestamps:
                # Clean old timestamps (older than 1 minute)
                self.user_timestamps[user_id] = [
                    ts for ts in self.user_timestamps[user_id] 
                    if current_time - ts < 60
                ]
                
                # Check rate limit
                if len(self.user_timestamps[user_id]) >= self.rate_limit_per_minute:
                    if update.callback_query:
                        await update.callback_query.answer(
                            "Bạn đang thao tác quá nhanh. Vui lòng chờ một chút!",
                            show_alert=True
                        )
                    return
            
            # Add current timestamp
            if user_id not in self.user_timestamps:
                self.user_timestamps[user_id] = []
            self.user_timestamps[user_id].append(current_time)
        
        return await handler(update, context)
