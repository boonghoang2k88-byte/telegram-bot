#!/usr/bin/env python3
import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler, ConversationHandler, ContextTypes
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import handlers
from handlers.start import start_command, about_command
from handlers.language import language_command, language_callback
from handlers.check import check_command, process_check
from handlers.report import (
    report_command, 
    cancel_report,
    report_name,
    report_username,
    report_link,
    report_id,
    report_amount,
    report_confirm,
    NAME, USERNAME, LINK, ID, AMOUNT, CONFIRM
)
from handlers.help import help_command
from handlers.safety import safety_command
from handlers.donate import donate_command
from handlers.trusted import trusted_groups_command, trusted_admins_command
from handlers.stats import stats_command

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

TOKEN = os.getenv('TOKEN')
if not TOKEN:
    logger.error("ERROR: Please set your bot token in the TOKEN variable!")
    logger.error("Get your token from BotFather on Telegram")
    exit(1)

def main():
    """Start the bot."""
    # Create the Application
    application = Application.builder().token(TOKEN).build()
    
    # Setup conversation handler for report
    report_conv_handler = ConversationHandler(
        entry_points=[CommandHandler('report', report_command)],
        states={
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, report_name)],
            USERNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, report_username)],
            LINK: [MessageHandler(filters.TEXT & ~filters.COMMAND, report_link)],
            ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, report_id)],
            AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, report_amount)],
            CONFIRM: [CallbackQueryHandler(report_confirm, pattern='^(yes|no)_report$')]
        },
        fallbacks=[CommandHandler('cancel', cancel_report)],
    )
    
    # Add command handlers
    application.add_handler(CommandHandler('start', start_command))
    application.add_handler(CommandHandler('about', about_command))
    application.add_handler(CommandHandler('language', language_command))
    application.add_handler(CommandHandler('check', check_command))
    application.add_handler(report_conv_handler)
    application.add_handler(CommandHandler('help', help_command))
    application.add_handler(CommandHandler('safety', safety_command))
    application.add_handler(CommandHandler('donate', donate_command))
    application.add_handler(CommandHandler('trusted_groups', trusted_groups_command))
    application.add_handler(CommandHandler('trusted_admins', trusted_admins_command))
    application.add_handler(CommandHandler('stats', stats_command))
    
    # Add callback query handlers
    application.add_handler(CallbackQueryHandler(language_callback, pattern='^lang_'))
    application.add_handler(CallbackQueryHandler(process_check, pattern='^check_'))
    
    # Start the Bot
    logger.info("Bot is starting...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
