from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
from services.language_service import get_user_language, get_text
from services.check_service import search_scammer
from db.database import get_scammer_details

async def check_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Initiate scammer check process."""
    user = update.effective_user
    lang = get_user_language(user.id)
    
    instruction = get_text(lang, 'check_instruction')
    
    await update.message.reply_text(instruction)
    
    # Store that user is in check mode
    context.user_data['mode'] = 'check'

async def process_check(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Process the check query."""
    query = update.callback_query
    await query.answer()
    
    # This would handle the check process
    # Implementation depends on your specific flow
    pass

async def check_scammer_details(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Check scammer by username or ID."""
    user_input = update.message.text.strip()
    user = update.effective_user
    lang = get_user_language(user.id)
    
    # Search for scammer
    result = search_scammer(user_input)
    
    if result:
        # Format warning message
        warning_text = format_scammer_warning(result, lang)
        await update.message.reply_text(warning_text, parse_mode='Markdown')
    else:
        not_found = get_text(lang, 'scammer_not_found')
        await update.message.reply_text(not_found)

def format_scammer_warning(scammer_data, lang):
    """Format scammer warning message."""
    risk_level = "🔴 HIGH" if scammer_data['report_count'] > 5 else "🟡 MEDIUM" if scammer_data['report_count'] > 2 else "🟢 LOW"
    
    return f"""🚨 **{get_text(lang, 'warning_title')}**

• **{get_text(lang, 'target')}**: {scammer_data['username']}
• **{get_text(lang, 'telegram_link')}**: {scammer_data['telegram_link']}
• **{get_text(lang, 'binance_id')}**: {scammer_data['binance_id']}

📊 **{get_text(lang, 'community_stats')}**
• {get_text(lang, 'report_count')}: {scammer_data['report_count']}
• {get_text(lang, 'reporter_count')}: {scammer_data['reporter_count']}
• {get_text(lang, 'total_amount')}: ~ {scammer_data['total_amount']} USDT

⚠️ **{get_text(lang, 'risk_assessment')}**: {risk_level}
📢 **{get_text(lang, 'recommendation')}**: {get_text(lang, 'do_not_trade')}
"""
