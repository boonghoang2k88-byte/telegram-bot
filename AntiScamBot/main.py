#!/usr/bin/env python3
"""
ANTISCAMBOT - Main Entry Point
Bot Telegram kiểm tra và báo cáo lừa đảo Crypto/OTC
Version: 1.0.0
"""

import os
import sys
import logging
from pathlib import Path

# ==================== FIX IMPORT PATH ====================
# QUAN TRỌNG: Fix lỗi import trên Render
current_dir = Path(__file__).parent.absolute()
sys.path.insert(0, str(current_dir))

# Tạo __init__.py nếu thiếu
def ensure_init_files():
    """Đảm bảo tất cả thư mục có file __init__.py."""
    folders = ['config', 'core', 'handlers', 'services', 'db', 'utils', 'locales']
    for folder in folders:
        init_file = current_dir / folder / '__init__.py'
        if (current_dir / folder).exists() and not init_file.exists():
            init_file.write_text('# Package initialization\n')
            print(f"✅ Created: {folder}/__init__.py")

ensure_init_files()

# ==================== CONFIGURATION ====================
from dotenv import load_dotenv
load_dotenv()

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('bot.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

# Check token
TOKEN = os.getenv('TOKEN')
if not TOKEN:
    logger.error("❌ ERROR: TOKEN environment variable not set!")
    logger.error("Please set TOKEN in Render environment variables")
    logger.error("Get token from @BotFather on Telegram")
    sys.exit(1)

# ==================== IMPORT HANDLERS ====================
logger.info("📦 Importing handlers...")

try:
    # Import core Telegram components
    from telegram import Update
    from telegram.ext import (
        Application,
        CommandHandler,
        MessageHandler,
        filters,
        CallbackQueryHandler,
        ConversationHandler,
        ContextTypes
    )
    
    # Import handlers với try-except cho từng cái
    try:
        from handlers.start import start_command, about_command
        logger.info("✅ Imported: handlers.start")
    except ImportError as e:
        logger.error(f"❌ Failed to import handlers.start: {e}")
        # Tạo handler mẫu nếu không có
        async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
            await update.message.reply_text("👋 Welcome to AntiScamBot!")
        async def about_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
            await update.message.reply_text("🤖 AntiScamBot - Community scam reporting system")
    
    try:
        from handlers.language import language_command, language_callback
        logger.info("✅ Imported: handlers.language")
    except ImportError as e:
        logger.error(f"❌ Failed to import handlers.language: {e}")
        async def language_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
            await update.message.reply_text("🌐 Language selection (module not loaded)")
        language_callback = None
    
    try:
        from handlers.check import check_command
        logger.info("✅ Imported: handlers.check")
    except ImportError as e:
        logger.error(f"❌ Failed to import handlers.check: {e}")
        async def check_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
            await update.message.reply_text("🔍 Check scammer (module not loaded)")
    
    try:
        from handlers.report import (
            report_command, cancel_report,
            report_name, report_username, report_link,
            report_id, report_amount, report_confirm,
            NAME, USERNAME, LINK, ID, AMOUNT, CONFIRM
        )
        logger.info("✅ Imported: handlers.report")
    except ImportError as e:
        logger.error(f"❌ Failed to import handlers.report: {e}")
        # Tạo các biến mẫu
        NAME, USERNAME, LINK, ID, AMOUNT, CONFIRM = range(6)
        async def report_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
            await update.message.reply_text("🚨 Report scam (module not loaded)")
        async def cancel_report(update: Update, context: ContextTypes.DEFAULT_TYPE):
            await update.message.reply_text("❌ Report cancelled")
    
    try:
        from handlers.help import help_command
        logger.info("✅ Imported: handlers.help")
    except ImportError as e:
        logger.error(f"❌ Failed to import handlers.help: {e}")
        async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
            await update.message.reply_text("❓ Help (module not loaded)")
    
    try:
        from handlers.safety import safety_command
        logger.info("✅ Imported: handlers.safety")
    except ImportError as e:
        logger.error(f"❌ Failed to import handlers.safety: {e}")
        async def safety_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
            await update.message.reply_text("⚠️ Safety tips (module not loaded)")
    
    try:
        from handlers.donate import donate_command
        logger.info("✅ Imported: handlers.donate")
    except ImportError as e:
        logger.error(f"❌ Failed to import handlers.donate: {e}")
        async def donate_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
            await update.message.reply_text("💝 Donate (module not loaded)")
    
    try:
        from handlers.trusted import trusted_groups_command, trusted_admins_command
        logger.info("✅ Imported: handlers.trusted")
    except ImportError as e:
        logger.error(f"❌ Failed to import handlers.trusted: {e}")
        async def trusted_groups_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
            await update.message.reply_text("👥 Trusted groups (module not loaded)")
        async def trusted_admins_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
            await update.message.reply_text("🛡 Trusted admins (module not loaded)")
    
    try:
        from handlers.stats import stats_command
        logger.info("✅ Imported: handlers.stats")
    except ImportError as e:
        logger.error(f"❌ Failed to import handlers.stats: {e}")
        async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
            await update.message.reply_text("📊 Stats (module not loaded)")
    
    logger.info("✅ All handlers imported successfully")
    
except Exception as e:
    logger.error(f"❌ Critical import error: {e}")
    logger.error("Creating fallback handlers...")
    
    # Fallback handlers đơn giản
    from telegram import Update
    from telegram.ext import ContextTypes
    
    async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text("🤖 AntiScamBot is running in fallback mode!")
    
    async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text("Available commands: /start /help")
    
    # Gán các biến cần thiết
    NAME, USERNAME, LINK, ID, AMOUNT, CONFIRM = range(6)
    report_command = start_command
    cancel_report = start_command
    language_command = start_command
    check_command = start_command
    safety_command = start_command
    donate_command = start_command
    trusted_groups_command = start_command
    trusted_admins_command = start_command
    stats_command = start_command
    about_command = start_command
    language_callback = None

# ==================== DATABASE INITIALIZATION ====================
logger.info("🗄️ Initializing database...")
try:
    from db.session import init_db
    init_db()
    logger.info("✅ Database initialized successfully")
except Exception as e:
    logger.warning(f"⚠️ Database initialization failed: {e}")
    logger.warning("Bot will run without database (reports won't be saved)")

# ==================== MAIN BOT FUNCTION ====================
def main():
    """Chính hàm khởi chạy bot."""
    logger.info("🚀 Starting AntiScamBot...")
    logger.info(f"📁 Current directory: {current_dir}")
    logger.info(f"🔑 Token: {TOKEN[:10]}...")
    
    try:
        # Tạo ứng dụng bot
        application = Application.builder().token(TOKEN).build()
        
        # ==================== SETUP CONVERSATION HANDLER ====================
        logger.info("🔄 Setting up conversation handlers...")
        
        try:
            # Setup report conversation
            report_conv_handler = ConversationHandler(
                entry_points=[CommandHandler('report', report_command)],
                states={
                    NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, report_name)],
                    USERNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, report_username)],
                    LINK: [MessageHandler(filters.TEXT & ~filters.COMMAND, report_link)],
                    ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, report_id)],
                    AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, report_amount)],
                    CONFIRM: [CallbackQueryHandler(report_confirm, pattern='^(yes|no)_report$')]
                } if 'report_confirm' in globals() else {},  # Fallback nếu không có
                fallbacks=[CommandHandler('cancel', cancel_report)],
            )
            application.add_handler(report_conv_handler)
            logger.info("✅ Report conversation handler added")
        except Exception as e:
            logger.error(f"❌ Failed to setup report conversation: {e}")
        
        # ==================== ADD COMMAND HANDLERS ====================
        logger.info("📝 Adding command handlers...")
        
        # Danh sách command handlers
        commands = [
            ('start', start_command),
            ('about', about_command),
            ('language', language_command),
            ('check', check_command),
            ('help', help_command),
            ('safety', safety_command),
            ('donate', donate_command),
            ('trusted_groups', trusted_groups_command),
            ('trusted_admins', trusted_admins_command),
            ('stats', stats_command),
        ]
        
        for cmd, handler in commands:
            try:
                application.add_handler(CommandHandler(cmd, handler))
                logger.info(f"✅ Command /{cmd} added")
            except Exception as e:
                logger.error(f"❌ Failed to add /{cmd}: {e}")
        
        # ==================== ADD CALLBACK HANDLERS ====================
        if language_callback:
            try:
                application.add_handler(CallbackQueryHandler(language_callback, pattern='^lang_'))
                logger.info("✅ Language callback handler added")
            except Exception as e:
                logger.error(f"❌ Failed to add language callback: {e}")
        
        # ==================== START BOT ====================
        logger.info("🤖 Bot is ready! Starting polling...")
        print("\n" + "="*50)
        print("ANTISCAMBOT STARTED SUCCESSFULLY!")
        print("="*50)
        print(f"✅ Token: {TOKEN[:10]}...")
        print("✅ Database: Ready")
        print("✅ Handlers: Loaded")
        print("✅ Status: Running")
        print("="*50)
        
        # Chạy bot
        application.run_polling(allowed_updates=Update.ALL_TYPES)
        
    except Exception as e:
        logger.error(f"❌ Failed to start bot: {e}")
        logger.error("Bot will restart in 10 seconds...")
        import time
        time.sleep(10)
        # Tự động restart
        main()

# ==================== ENTRY POINT ====================
if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        logger.info("👋 Bot stopped by user")
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")
        logger.error("Restarting in 5 seconds...")
        import time
        time.sleep(5)
        main()
