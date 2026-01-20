from telegram import Update
from telegram.ext import ContextTypes
from services.language_service import get_user_language, get_text
from db.database import get_scam_statistics, get_top_scammers

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show scam statistics."""
    user = update.effective_user
    lang = get_user_language(user.id)
    
    stats = get_scam_statistics()
    top_scammers = get_top_scammers(limit=5)
    
    stats_text = f"""**📊 {get_text(lang, 'stats_title')}**

**{get_text(lang, 'overall_stats')}**
• {get_text(lang, 'total_reports')}: **{stats['total_reports']}**
• {get_text(lang, 'unique_reporters')}: **{stats['unique_reporters']}**
• {get_text(lang, 'total_scammers')}: **{stats['total_scammers']}**
• {get_text(lang, 'total_amount')}: **{stats['total_amount']} USDT**

**🏆 {get_text(lang, 'top_scammers')}**
"""
    
    for i, scammer in enumerate(top_scammers, 1):
        stats_text += f"\n**{i}. {scammer['username']}**"
        stats_text += f"\n   📈 {get_text(lang, 'reports')}: {scammer['report_count']}"
        stats_text += f"\n   👥 {get_text(lang, 'reporters')}: {scammer['reporter_count']}"
        stats_text += f"\n   💰 {get_text(lang, 'amount')}: {scammer['total_amount']} USDT"
    
    stats_text += f"\n\n**{get_text(lang, 'stats_note')}**"
    stats_text += f"\n{get_text(lang, 'stats_disclaimer')}"
    
    await update.message.reply_text(stats_text, parse_mode='Markdown')
