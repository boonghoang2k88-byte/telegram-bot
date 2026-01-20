from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes, ConversationHandler
from services.language_service import get_user_language, get_text
from services.report_service import create_report, check_report_limit
from db.database import save_report
import re

# Conversation states
NAME, USERNAME, LINK, ID, AMOUNT, CONFIRM = range(6)

async def report_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start the report process."""
    user = update.effective_user
    lang = get_user_language(user.id)
    
    # Check rate limit
    if check_report_limit(user.id):
        limit_message = get_text(lang, 'report_limit_exceeded')
        await update.message.reply_text(limit_message)
        return ConversationHandler.END
    
    instruction = get_text(lang, 'report_instruction')
    await update.message.reply_text(instruction)
    
    # Ask for Telegram display name
    ask_name = get_text(lang, 'ask_name')
    await update.message.reply_text(ask_name)
    
    return NAME

async def report_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Store scammer's Telegram display name."""
    user = update.effective_user
    lang = get_user_language(user.id)
    
    context.user_data['scammer_name'] = update.message.text
    
    ask_username = get_text(lang, 'ask_username')
    await update.message.reply_text(ask_username)
    
    return USERNAME

async def report_username(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Store scammer's Telegram username."""
    user = update.effective_user
    lang = get_user_language(user.id)
    
    username = update.message.text.strip()
    if not username.startswith('@'):
        username = '@' + username
    
    context.user_data['scammer_username'] = username
    
    ask_link = get_text(lang, 'ask_link')
    await update.message.reply_text(ask_link)
    
    return LINK

async def report_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Store scammer's Telegram link."""
    user = update.effective_user
    lang = get_user_language(user.id)
    
    link = update.message.text.strip()
    if not link.startswith('https://t.me/'):
        link = f'https://t.me/{link.replace("@", "")}'
    
    context.user_data['scammer_link'] = link
    
    ask_id = get_text(lang, 'ask_id')
    await update.message.reply_text(ask_id)
    
    return ID

async def report_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Store scammer's Binance ID or crypto wallet."""
    user = update.effective_user
    lang = get_user_language(user.id)
    
    context.user_data['scammer_id'] = update.message.text
    
    ask_amount = get_text(lang, 'ask_amount')
    await update.message.reply_text(ask_amount)
    
    return AMOUNT

async def report_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Store scam amount."""
    user = update.effective_user
    lang = get_user_language(user.id)
    
    amount_text = update.message.text
    # Extract numbers from the text
    numbers = re.findall(r'\d+\.?\d*', amount_text)
    amount = float(numbers[0]) if numbers else 0
    
    context.user_data['scam_amount'] = amount
    
    # Show summary and ask for confirmation
    summary = get_text(lang, 'report_summary').format(
        context.user_data['scammer_name'],
        context.user_data['scammer_username'],
        context.user_data['scammer_link'],
        context.user_data['scammer_id'],
        context.user_data['scam_amount']
    )
    
    keyboard = [
        [
            InlineKeyboardButton(get_text(lang, 'confirm_yes'), callback_data='yes_report'),
            InlineKeyboardButton(get_text(lang, 'confirm_no'), callback_data='no_report')
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(summary, reply_markup=reply_markup)
    
    return CONFIRM

async def report_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle report confirmation."""
    query = update.callback_query
    await query.answer()
    
    user = update.effective_user
    lang = get_user_language(user.id)
    
    if query.data == 'yes_report':
        # Save report to database
        report_data = {
            'reporter_id': user.id,
            'reporter_username': user.username,
            'scammer_name': context.user_data['scammer_name'],
            'scammer_username': context.user_data['scammer_username'],
            'scammer_link': context.user_data['scammer_link'],
            'scammer_id': context.user_data['scammer_id'],
            'amount': context.user_data['scam_amount'],
            'status': 'confirmed'
        }
        
        save_report(report_data)
        
        success_message = get_text(lang, 'report_success')
        await query.edit_message_text(success_message)
    else:
        cancel_message = get_text(lang, 'report_cancelled')
        warning = get_text(lang, 'report_warning')
        await query.edit_message_text(f"{cancel_message}\n\n{warning}")
    
    # Clear user data
    context.user_data.clear()
    
    return ConversationHandler.END

async def cancel_report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel the report process."""
    user = update.effective_user
    lang = get_user_language(user.id)
    
    cancel_message = get_text(lang, 'report_cancelled')
    warning = get_text(lang, 'report_warning')
    
    await update.message.reply_text(f"{cancel_message}\n\n{warning}")
    
    # Clear user data
    context.user_data.clear()
    
    return ConversationHandler.END
