from telegram import Update
from telegram.ext import ContextTypes
from services.language_service import get_user_language, get_text

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send help instructions."""
    user = update.effective_user
    lang = get_user_language(user.id)
    
    help_text = f"""**{get_text(lang, 'help_title')}**

**1. {get_text(lang, 'check_scam')}**
{get_text(lang, 'check_help')}

**2. {get_text(lang, 'report_scam')}**
{get_text(lang, 'report_help')}

**3. {get_text(lang, 'safety_tips')}**
{get_text(lang, 'safety_help')}

**4. {get_text(lang, 'general_info')}**
• {get_text(lang, 'rate_limit_info')}
• {get_text(lang, 'data_source_info')}
• {get_text(lang, 'disclaimer_info')}

**5. {get_text(lang, 'contact_support')}**
{get_text(lang, 'support_info')}
"""
    
    await update.message.reply_text(help_text, parse_mode='Markdown')
