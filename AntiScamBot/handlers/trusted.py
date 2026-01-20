from telegram import Update
from telegram.ext import ContextTypes
from services.language_service import get_user_language, get_text
from config.settings import TRUSTED_GROUPS, TRUSTED_ADMINS

async def trusted_groups_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show trusted trading groups."""
    user = update.effective_user
    lang = get_user_language(user.id)
    
    groups_text = f"""**👥 {get_text(lang, 'trusted_groups_title')}**

{get_text(lang, 'groups_disclaimer')}
"""
    
    # Add groups for current language
    for group in TRUSTED_GROUPS.get(lang, TRUSTED_GROUPS['en']):
        groups_text += f"\n• **{group['name']}**: {group['link']}"
    
    groups_text += f"\n\n{get_text(lang, 'groups_warning')}"
    
    await update.message.reply_text(groups_text, parse_mode='Markdown', disable_web_page_preview=True)

async def trusted_admins_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show trusted admins/mediators."""
    user = update.effective_user
    lang = get_user_language(user.id)
    
    admins_text = f"""**🛡 {get_text(lang, 'trusted_admins_title')}**

{get_text(lang, 'admins_disclaimer')}
"""
    
    # Add admins for current language
    for admin in TRUSTED_ADMINS.get(lang, TRUSTED_ADMINS['en']):
        admins_text += f"\n• **{admin['name']}**: {admin['username']}"
    
    admins_text += f"\n\n{get_text(lang, 'admins_warning')}"
    
    await update.message.reply_text(admins_text, parse_mode='Markdown')
