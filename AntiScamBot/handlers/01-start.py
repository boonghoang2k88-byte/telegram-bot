from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
from services.language_service import get_user_language, get_text

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send welcome message when the command /start is issued."""
    user = update.effective_user
    lang = get_user_language(user.id)
    
    welcome_text = get_text(lang, 'welcome').format(user.first_name)
    
    # Create keyboard with all 10 menus
    keyboard = [
        [InlineKeyboardButton(get_text(lang, 'menu_language'), callback_data='menu_language')],
        [InlineKeyboardButton(get_text(lang, 'menu_check'), callback_data='menu_check')],
        [InlineKeyboardButton(get_text(lang, 'menu_report'), callback_data='menu_report')],
        [InlineKeyboardButton(get_text(lang, 'menu_help'), callback_data='menu_help')],
        [InlineKeyboardButton(get_text(lang, 'menu_safety'), callback_data='menu_safety')],
        [InlineKeyboardButton(get_text(lang, 'menu_donate'), callback_data='menu_donate')],
        [InlineKeyboardButton(get_text(lang, 'menu_groups'), callback_data='menu_groups')],
        [InlineKeyboardButton(get_text(lang, 'menu_admins'), callback_data='menu_admins')],
        [InlineKeyboardButton(get_text(lang, 'menu_stats'), callback_data='menu_stats')],
        [InlineKeyboardButton(get_text(lang, 'menu_about'), callback_data='menu_about')],
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.message:
        await update.message.reply_text(welcome_text, reply_markup=reply_markup)
    elif update.callback_query:
        await update.callback_query.edit_message_text(welcome_text, reply_markup=reply_markup)

async def about_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send information about the bot."""
    user = update.effective_user
    lang = get_user_language(user.id)
    
    # Get statistics from database
    from db.database import get_scam_statistics
    stats = get_scam_statistics()
    
    about_text = f"""**BOT_TELE** - {get_text(lang, 'about_title')}

{get_text(lang, 'about_description')}

🔎 **{get_text(lang, 'strengths_title')}**
• {get_text(lang, 'strength_1')}
• {get_text(lang, 'strength_2')}
• {get_text(lang, 'strength_3')}
• {get_text(lang, 'strength_4')}

📊 **{get_text(lang, 'community_stats')}**
• {get_text(lang, 'total_reports')}: {stats['total_reports']}
• {get_text(lang, 'unique_reporters')}: {stats['unique_reporters']}
• {get_text(lang, 'total_scammers')}: {stats['total_scammers']}

⚠️ **{get_text(lang, 'disclaimer')}**
{get_text(lang, 'disclaimer_text')}
"""
    
    await update.message.reply_text(about_text, parse_mode='Markdown')
