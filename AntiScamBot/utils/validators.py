import re
from typing import Tuple

def validate_telegram_username(username: str) -> Tuple[bool, str]:
    """Validate Telegram username."""
    if not username:
        return False, "Username cannot be empty"
    
    # Remove @ if present
    username = username.lstrip('@')
    
    if len(username) < 5:
        return False, "Username too short (min 5 characters)"
    
    if len(username) > 32:
        return False, "Username too long (max 32 characters)"
    
    # Telegram username pattern
    pattern = r'^[a-zA-Z0-9_]{5,32}$'
    if not re.match(pattern, username):
        return False, "Invalid username format. Only letters, numbers and underscores allowed"
    
    return True, username

def validate_telegram_link(link: str) -> Tuple[bool, str]:
    """Validate Telegram link."""
    if not link:
        return False, "Link cannot be empty"
    
    # Add https:// if not present
    if not link.startswith('http'):
        link = f'https://{link}'
    
    # Telegram link pattern
    pattern = r'^https?://(?:t\.me|telegram\.me)/([a-zA-Z0-9_]{5,32})(?:/.*)?$'
    match = re.match(pattern, link)
    
    if not match:
        return False, "Invalid Telegram link format"
    
    username = match.group(1)
    return True, f'https://t.me/{username}'

def validate_binance_id(binance_id: str) -> Tuple[bool, str]:
    """Validate Binance ID."""
    if not binance_id:
        return False, "Binance ID cannot be empty"
    
    # Binance ID is usually numeric
    if not binance_id.isdigit():
        return False, "Binance ID should contain only numbers"
    
    if len(binance_id) < 6:
        return False, "Binance ID too short"
    
    if len(binance_id) > 20:
        return False, "Binance ID too long"
    
    return True, binance_id

def validate_amount(amount_str: str) -> Tuple[bool, float]:
    """Validate amount string."""
    try:
        # Remove currency symbols and commas
        cleaned = re.sub(r'[^\d.]', '', amount_str)
        amount = float(cleaned)
        
        if amount <= 0:
            return False, 0.0
        
        if amount > 1000000:  # 1 million limit
            return False, 0.0
        
        return True, amount
        
    except ValueError:
        return False, 0.0

def validate_crypto_wallet(wallet: str) -> Tuple[bool, str]:
    """Validate crypto wallet address."""
    if not wallet:
        return False, "Wallet address cannot be empty"
    
    wallet = wallet.strip()
    
    # Ethereum address pattern
    eth_pattern = r'^0x[a-fA-F0-9]{40}$'
    # Bitcoin address pattern (simplified)
    btc_pattern = r'^(bc1|[13])[a-zA-HJ-NP-Z0-9]{25,39}$'
    
    if re.match(eth_pattern, wallet) or re.match(btc_pattern, wallet):
        return True, wallet
    
    return False, "Invalid wallet address format"
