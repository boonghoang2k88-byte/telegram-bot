# config/settings.py (phần cập nhật)
TRUSTED_GROUPS = {
    'vi': [
        {'name': 'OTC Crypto Việt Nam', 'link': 'https://t.me/otccryptovietnam'},
        {'name': 'Binance P2P Việt Nam', 'link': 'https://t.me/binancep2pvn'},
        {'name': 'Crypto Trading Vietnam', 'link': 'https://t.me/cryptotradingvietnam'},
    ],
    'en': [
        {'name': 'Global Crypto Trading', 'link': 'https://t.me/globalcrypto'},
        {'name': 'Binance P2P Official', 'link': 'https://t.me/binancep2p'},
    ],
    'zh': [
        {'name': '中文加密货币OTC', 'link': 'https://t.me/chinesecrypto'},
        {'name': '币安P2P中文群', 'link': 'https://t.me/binancep2pzh'},
        {'name': '中文加密交易社区', 'link': 'https://t.me/zhcryptocommunity'},
    ],
    'ru': [
        {'name': 'Русский Crypto OTC', 'link': 'https://t.me/russiancrypto'},
        {'name': 'Бинанс P2P Россия', 'link': 'https://t.me/binancep2pru'},
        {'name': 'Русское криптосообщество', 'link': 'https://t.me/ruscryptocommunity'},
    ]
}

TRUSTED_ADMINS = {
    'vi': [
        {'name': 'Admin OTC Việt Nam', 'username': '@otcadmin_vn'},
        {'name': 'Binance Support VN', 'username': '@binancesupport_vn'},
    ],
    'en': [
        {'name': 'Global Crypto Admin', 'username': '@globaladmin'},
        {'name': 'Binance Official Support', 'username': '@binancesupport'},
    ],
    'zh': [
        {'name': '中文社区管理员', 'username': '@zhcommunityadmin'},
        {'name': '币安中文支持', 'username': '@binancesupportzh'},
    ],
    'ru': [
        {'name': 'Русский администратор', 'username': '@rusadmin'},
        {'name': 'Поддержка Бинанс Россия', 'username': '@binancesupportru'},
    ]
}

# Cập nhật phần DONATION_INFO
DONATION_INFO = {
    'binance_id': '154265504',
    'message': {
        'vi': """Binance ID: 154265504

Mọi sự ủng hộ giúp BOT_TELE duy trì máy chủ,
nâng cấp bảo mật và phục vụ cộng đồng lâu dài.
Xin chân thành cảm ơn!""",
        'en': """Binance ID: 154265504

Every donation helps BOT_TELE maintain servers,
upgrade security and serve the community long-term.
Thank you sincerely!""",
        'zh': """Binance ID: 154265504

每笔捐赠都将帮助BOT_TELE维护服务器，
升级安全系统并长期服务社区。
衷心感谢！""",
        'ru': """Binance ID: 154265504

Каждое пожертвование помогает BOT_TELE поддерживать серверы,
обновлять безопасность и долгосрочно служить сообществу.
Искренне благодарим!"""
    }
}
