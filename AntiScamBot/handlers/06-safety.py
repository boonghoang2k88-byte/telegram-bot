from telegram import Update
from telegram.ext import ContextTypes
from services.language_service import get_user_language, get_text

async def safety_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send safety tips for trading."""
    user = update.effective_user
    lang = get_user_language(user.id)
    
    safety_text = f"""**⚠️ {get_text(lang, 'safety_title')}**

**1. {get_text(lang, 'verify_identity')}**
• {get_text(lang, 'tip_1_1')}
• {get_text(lang, 'tip_1_2')}
• {get_text(lang, 'tip_1_3')}

**2. {get_text(lang, 'secure_payment')}**
• {get_text(lang, 'tip_2_1')}
• {get_text(lang, 'tip_2_2')}
• {get_text(lang, 'tip_2_3')}

**3. {get_text(lang, 'avoid_common_scams')}**
• {get_text(lang, 'tip_3_1')}
• {get_text(lang, 'tip_3_2')}
• {get_text(lang, 'tip_3_3')}

**4. {get_text(lang, 'use_trusted_platforms')}**
• {get_text(lang, 'tip_4_1')}
• {get_text(lang, 'tip_4_2')}
• {get_text(lang, 'tip_4_3')}

**5. {get_text(lang, 'report_suspicious')}**
• {get_text(lang, 'tip_5_1')}
• {get_text(lang, 'tip_5_2')}

📢 **{get_text(lang, 'final_warning')}**: {get_text(lang, 'final_warning_text')}
"""
    
    await update.message.reply_text(safety_text, parse_mode='Markdown')
