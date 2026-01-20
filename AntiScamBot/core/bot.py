import asyncio
from telegram.ext import Application
from config.settings import TOKEN

class BotTele:
    def __init__(self):
        self.application = None
        
    async def start(self):
        """Start the bot."""
        self.application = Application.builder().token(TOKEN).build()
        
        # Setup handlers (imported from handlers module)
        from handlers import setup_handlers
        setup_handlers(self.application)
        
        # Start polling
        await self.application.initialize()
        await self.application.start()
        await self.application.updater.start_polling()
        
        logger.info("Bot is running...")
        
        # Keep running
        await asyncio.Event().wait()
        
    async def stop(self):
        """Stop the bot gracefully."""
        if self.application:
            await self.application.stop()
            await self.application.shutdown()
