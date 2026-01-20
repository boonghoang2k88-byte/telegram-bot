import hashlib
from typing import Optional

def hash_scammer_identifier(identifier: str, identifier_type: str) -> str:
    """Create hash for scammer identifier for privacy."""
    if not identifier:
        return ""
    
    # Create salt based on identifier type
    salt = f"BOT_TELE_{identifier_type}"
    
    # Create hash
    hash_object = hashlib.sha256(f"{salt}_{identifier}".encode())
    return hash_object.hexdigest()[:32]

def anonymize_user_id(user_id: int) -> str:
    """Anonymize user ID for public display."""
    hash_object = hashlib.md5(f"USER_{user_id}".encode())
    return f"USER_{hash_object.hexdigest()[:8]}"

def create_scammer_fingerprint(data: dict) -> str:
    """Create fingerprint for scammer based on multiple identifiers."""
    identifiers = []
    
    if data.get('username'):
        identifiers.append(f"USERNAME:{data['username']}")
    if data.get('binance_id'):
        identifiers.append(f"BINANCE:{data['binance_id']}")
    if data.get('crypto_wallet'):
        identifiers.append(f"WALLET:{data['crypto_wallet']}")
    if data.get('telegram_link'):
        identifiers.append(f"LINK:{data['telegram_link']}")
    
    if not identifiers:
        return ""
    
    # Sort for consistency
    identifiers.sort()
    fingerprint_string = "|".join(identifiers)
    
    hash_object = hashlib.sha256(fingerprint_string.encode())
    return hash_object.hexdigest()[:16]
