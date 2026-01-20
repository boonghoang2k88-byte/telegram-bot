from telegram import Update
from telegram.ext import ContextTypes
from services.language_service import get_user_language, get_text
from config.settings import DONATION_INFO

async def donate_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show donation information."""
    user = update.effective_user
    lang = get_user_language(user.id)
    
    donation_text = f"""**💝 {get_text(lang, 'donate_title')}**

{DONATION_INFO['message'][lang]}

**{get_text(lang, 'donation_usage')}**
• {get_text(lang, 'usage_1')}
• {get_text(lang, 'usage_2')}
• {get_text(lang, 'usage_3')}
• {get_text(lang, 'usage_4')}

**{get_text(lang, 'transparency_commitment')}**
{get_text(lang, 'transparency_text')}

**{get_text(lang, 'thank_you')}**
{get_text(lang, 'thank_you_text')}
"""
    
    await update.message.reply_text(donation_text, parse_mode='Markdown')
