async def language_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Change language setting."""
    keyboard = [
        [InlineKeyboardButton("🇺🇸 English", callback_data='lang_en')],
        [InlineKeyboardButton("🇻🇳 Tiếng Việt", callback_data='lang_vi')],
        [InlineKeyboardButton("🇨🇳 中文", callback_data='lang_zh')],
        [InlineKeyboardButton("🇷🇺 Русский", callback_data='lang_ru')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "🌐 Please select your language / Vui lòng chọn ngôn ngữ / 请选择语言 / Пожалуйста, выберите язык:",
        reply_markup=reply_markup
    )
