def get_user_language(user_id: int) -> str:
    """Get user's preferred language."""
    # In a real app, this would query the database
    # For now, return default 'en' or use Telegram's language_code
    return 'en'  # Default to English

def set_user_language(user_id: int, lang_code: str) -> None:
    """Set user's preferred language."""
    # Validate language code
    valid_languages = ['en', 'vi', 'zh', 'ru']
    if lang_code not in valid_languages:
        lang_code = 'en'
    
    # In a real app, save to database
    # For now, store in memory or user_data
    pass
