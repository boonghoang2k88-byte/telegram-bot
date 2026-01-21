# main.py - BOT CHECK SCAM
# Python 3.10.1 + python-telegram-bot 13.15 (synchronous)
# Hoạt động trên cả CMD và RENDER

import os
import json
import logging
from datetime import datetime, timedelta
from telegram import (
    Update, 
    InlineKeyboardButton, 
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
    ParseMode
)
from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    Filters,
    CallbackQueryHandler,
    CallbackContext,
    ConversationHandler
)
import pytz

# ========== CẤU HÌNH LOGGING ==========
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ========== CẤU TRÚC DỮ LIỆU ==========
DATA_FILE = 'data.json'
USERS_FILE = 'users.json'
STATS_FILE = 'stats.json'

# Khởi tạo file JSON nếu chưa tồn tại
def init_files():
    default_data = {
        "scammers": {},
        "user_reports": {},
        "daily_reports": {}
    }
    
    default_users = {
        "total_users": 0,
        "active_users": 0,
        "users": {}
    }
    
    default_stats = {
        "total_reports": 0,
        "unique_reporters": 0,
        "total_scammers": 0,
        "total_amount_scammed": 0
    }
    
    for file, default in [(DATA_FILE, default_data), 
                         (USERS_FILE, default_users), 
                         (STATS_FILE, default_stats)]:
        if not os.path.exists(file):
            with open(file, 'w', encoding='utf-8') as f:
                json.dump(default, f, ensure_ascii=False, indent=2)

# ========== QUẢN LÝ DỮ LIỆU ==========
def load_data():
    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def load_users():
    with open(USERS_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_users(users):
    with open(USERS_FILE, 'w', encoding='utf-8') as f:
        json.dump(users, f, ensure_ascii=False, indent=2)

def load_stats():
    with open(STATS_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_stats(stats):
    with open(STATS_FILE, 'w', encoding='utf-8') as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)

# ========== NGÔN NGỮ ==========
LANGUAGES = {
    'en': {
        'menu': "📋 *CHECK-SCAM BOT MENU*",
        'language': "🌐 Language",
        'check': "🔍 Check Scammer",
        'report': "🚨 Report Scammer",
        'guide': "❓ How to Use",
        'safety': "⚠️ Safe Trading Tips",
        'donate': "💝 Support Developer",
        'group': "👥 Trusted Trading Group",
        'admin': "🛡 Trusted Admin/Mediator",
        'stats': "📊 Top Scammers",
        'help': "ℹ️ Help",
        'back': "🔙 Back",
        'cancel': "❌ Cancel",
        'choose_lang': "Please choose your language:",
        'lang_set': "✅ Language set to English",
        'welcome': "🛡️ *WELCOME TO CHECK-SCAM BOT* 🛡️\n\n",
        'bot_desc': [
            "CHECK-SCAM is a Telegram bot that helps the community ",
            "check, report, and warn about scams in software, goods, ",
            "game accounts, money transactions, and more.\n\n",
            "🔎 *Key Features & Credibility*\n",
            "• Data built from real community contributions\n",
            "• Each scammer shows:\n",
            "  • **Number of reports**\n",
            "  • **Number of unique reporters**\n",
            "  • More reporters → Higher warning reliability\n",
            "• System helps users:\n",
            "  • Assess risks before trading\n",
            "  • Avoid community-warned scammers\n\n",
            "📌 *Bot Statistics*\n",
            "• Total Bot Users: {total_users}\n",
            "• Active Reporters: {unique_reporters}\n",
            "• Total Scammers in DB: {total_scammers}\n\n",
            "⚠️ *Disclaimer*\n",
            "CHECK-SCAM does not provide legal conclusions, ",
            "only risk scores based on actual report data."
        ],
        'report_steps': [
            "Step 1/6: Enter scammer's Telegram @username (or 'skip' if none):",
            "Step 2/6: Enter scammer's Telegram link (or 'skip' if none):",
            "Step 3/6: Enter scammer's Binance ID/Crypto Wallet:",
            "Step 4/6: Enter amount scammed (in USDT or your currency):",
            "Step 5/6: What item/service was scammed? (software, game account, money, etc.):",
            "Step 6/6: Please confirm your report (YES/NO):"
        ],
        'check_prompt': "Enter @username, Telegram link, or Binance ID to check:",
        'scammer_info': """🚨 *TRANSACTION WARNING*

• Target: {username}
• Telegram: {telegram_link}
• Wallet/ID: {wallet_id}

📊 *COMMUNITY STATISTICS*
• Total Reports: {report_count}
• Unique Reporters: {reporter_count}
• Total Amount Involved: ~ {total_amount} USDT

⚠️ Risk Level: {risk_level}
Recommendation: {recommendation}""",
        'no_scammer': "No scammer found with that information.",
        'report_limit': "You have reached the daily report limit (3 reports per 24 hours).",
        'report_cancel': "Report cancelled. Remember: False reports harm the community.",
        'report_success': "✅ Report submitted successfully!",
        'invalid_amount': "Please enter a valid amount (numbers only).",
        'donation_text': """💝 *SUPPORT THE DEVELOPER*

Binance ID: `154265504`

Your support helps CHECK-SCAM maintain servers,
upgrade security, and serve the community long-term.
Thank you sincerely!

*Transparency Commitment:*
We pledge to use all donations transparently – 
strictly for bot operation and long-term development.

Thank you for your support! 🙏""",
        'group_text': """👥 *TRUSTED TRADING GROUP*

Join our verified trading community:
[👉 J5 Trading Community](https://t.me/j5FS6B_V9DM5ZmVl)

• Safe trading environment
• Community verified members
• Scam warnings and alerts""",
        'admin_text': """🛡 *TRUSTED ADMIN / MEDIATOR*

For trusted mediation services, contact:
[👉 Siculator98](https://t.me/siculator98)

• Experienced mediator
• Secure transaction handling
• Trusted by community""",
        'guide_text': """❓ *HOW TO USE CHECK-SCAM BOT*

1. *Check Scammer*: Use this before any transaction
2. *Report Scammer*: Report suspicious users (max 3/day)
3. *View Statistics*: See most reported scammers
4. *Safety Tips*: Learn safe trading practices

⚠️ Always verify before trading!""",
        'safety_text': """⚠️ *SAFE TRADING TIPS*

1. ✅ Always use trusted mediators
2. ✅ Check user history thoroughly
3. ✅ Avoid too-good-to-be-true deals
4. ✅ Use escrow services for large amounts
5. ✅ Report suspicious users immediately

Stay safe! 🔒""",
        'help_text': """ℹ️ *HELP & SUPPORT*

For issues or suggestions:
• Use /start to return to main menu
• Check guide for usage instructions
• Join group for community support

Bot Version: 2.0 | Updated: 2024""",
        'invalid_input': "Invalid input. Please try again.",
        'yes': "✅ YES",
        'no': "❌ NO",
        'skip': "⏭ Skip",
        'risk_high': "HIGH",
        'risk_medium': "MEDIUM", 
        'risk_low': "LOW",
        'recommend_avoid': "DO NOT TRANSACT",
        'recommend_caution': "Proceed with extreme caution",
        'recommend_monitor': "Monitor and verify carefully"
    },
    'vi': {
        'menu': "📋 *MENU BOT CHECK-SCAM*",
        'language': "🌐 Ngôn ngữ",
        'check': "🔍 Kiểm tra lừa đảo",
        'report': "🚨 Báo cáo scammer",
        'guide': "❓ Hướng dẫn sử dụng",
        'safety': "⚠️ Lưu ý giao dịch an toàn",
        'donate': "💝 Ủng hộ nhà phát triển",
        'group': "👥 Group giao dịch uy tín",
        'admin': "🛡 Admin/trung gian uy tín",
        'stats': "📊 Thống kê scammer lớn",
        'help': "ℹ️ Trợ giúp",
        'back': "🔙 Quay lại",
        'cancel': "❌ Hủy",
        'choose_lang': "Vui lòng chọn ngôn ngữ:",
        'lang_set': "✅ Đã đặt ngôn ngữ: Tiếng Việt",
        'welcome': "🛡️ *CHÀO MỪNG ĐẾN BOT CHECK-SCAM* 🛡️\n\n",
        'bot_desc': [
            "CHECK-SCAM là bot Telegram hỗ trợ cộng đồng ",
            "kiểm tra, báo cáo và cảnh báo lừa đảo trong giao dịch ",
            "phần mềm, hàng hóa, tài khoản game, tiền điện tử, v.v.\n\n",
            "🔎 *Điểm mạnh & Độ tin cậy*\n",
            "• Dữ liệu từ đóng góp thực tế của cộng đồng\n",
            "• Mỗi đối tượng lừa đảo hiển thị:\n",
            "  • **Số lượt báo cáo**\n",
            "  • **Số người báo cáo**\n",
            "  • Càng nhiều người báo cáo → Độ tin cậy càng cao\n",
            "• Hệ thống giúp người dùng:\n",
            "  • Đánh giá rủi ro trước khi giao dịch\n",
            "  • Tránh đối tượng đã bị cảnh báo\n\n",
            "📌 *Thống kê Bot*\n",
            "• Tổng người dùng: {total_users}\n",
            "• Người báo cáo: {unique_reporters}\n",
            "• Số scammer trong DB: {total_scammers}\n\n",
            "⚠️ *Lưu ý*\n",
            "CHECK-SCAM không kết luận pháp lý, ",
            "chỉ cung cấp điểm rủi ro dựa trên dữ liệu thực tế."
        ],
        'report_steps': [
            "Bước 1/6: Nhập @username Telegram của scammer (hoặc 'skip' nếu không có):",
            "Bước 2/6: Nhập link Telegram của scammer (hoặc 'skip' nếu không có):",
            "Bước 3/6: Nhập ID Binance/Ví Crypto của scammer:",
            "Bước 4/6: Nhập số tiền bị lừa (USDT hoặc tiền tệ của bạn):",
            "Bước 5/6: Mặt hàng bị lừa là gì? (phần mềm, acc game, tiền, v.v.):",
            "Bước 6/6: Xác nhận báo cáo (YES/NO):"
        ],
        'check_prompt': "Nhập @username, link Telegram hoặc Binance ID để kiểm tra:",
        'scammer_info': """🚨 *CẢNH BÁO GIAO DỊCH*

• Đối tượng: {username}
• Telegram: {telegram_link}
• Ví/ID: {wallet_id}

📊 *THỐNG KÊ CỘNG ĐỒNG*
• Số lượt báo cáo: {report_count}
• Số người báo cáo: {reporter_count}
• Tổng số tiền liên quan: ~ {total_amount} USDT

⚠️ Mức độ rủi ro: {risk_level}
Khuyến nghị: {recommendation}""",
        'no_scammer': "Không tìm thấy scammer với thông tin này.",
        'report_limit': "Bạn đã đạt giới hạn báo cáo (3 báo cáo/24 giờ).",
        'report_cancel': "Đã hủy báo cáo. Nhớ: Báo cáo sai gây hại cho cộng đồng.",
        'report_success': "✅ Báo cáo thành công!",
        'invalid_amount': "Vui lòng nhập số tiền hợp lệ (chỉ số).",
        'donation_text': """💝 *ỦNG HỘ NHÀ PHÁT TRIỂN*

Binance ID: `154265504`

Ủng hộ giúp CHECK-SCAM duy trì máy chủ,
nâng cấp bảo mật và phục vụ cộng đồng lâu dài.
Cảm ơn chân thành!

*Cam kết minh bạch:*
Chúng tôi cam kết sử dụng mọi khoản ủng hộ 
minh bạch - đúng mục đích vận hành và phát triển bot.

Trân trọng cảm ơn! 🙏""",
        'group_text': """👥 *GROUP GIAO DỊCH UY TÍN*

Tham gia cộng đồng giao dịch đã xác minh:
[👉 J5 Trading Community](https://t.me/j5FS6B_V9DM5ZmVl)

• Môi trường giao dịch an toàn
• Thành viên được xác minh
• Cảnh báo lừa đảo""",
        'admin_text': """🛡 *ADMIN/TRUNG GIAN UY TÍN*

Để sử dụng dịch vụ trung gian tin cậy:
[👉 Siculator98](https://t.me/siculator98)

• Trung gian có kinh nghiệm
• Xử lý giao dịch an toàn
• Được cộng đồng tin tưởng""",
        'guide_text': """❓ *HƯỚNG DẪN SỬ DỤNG BOT*

1. *Kiểm tra lừa đảo*: Dùng trước khi giao dịch
2. *Báo cáo scammer*: Báo cáo user đáng ngờ (tối đa 3/ngày)
3. *Xem thống kê*: Xem scammer bị báo cáo nhiều nhất
4. *Mẹo an toàn*: Học cách giao dịch an toàn

⚠️ Luôn xác minh trước khi giao dịch!""",
        'safety_text': """⚠️ *LƯU Ý GIAO DỊCH AN TOÀN*

1. ✅ Luôn dùng trung gian uy tín
2. ✅ Kiểm tra kỹ lịch sử người dùng
3. ✅ Tránh deal quá tốt để thành thật
4. ✅ Dùng dịch vụ escrow cho số tiền lớn
5. ✅ Báo cáo ngay user đáng ngờ

Giữ an toàn! 🔒""",
        'help_text': """ℹ️ *TRỢ GIÚP & HỖ TRỢ*

Gặp vấn đề hoặc đề xuất:
• Dùng /start để về menu chính
• Xem hướng dẫn sử dụng
• Vào group để được hỗ trợ

Phiên bản Bot: 2.0 | Cập nhật: 2024""",
        'invalid_input': "Nhập không hợp lệ. Vui lòng thử lại.",
        'yes': "✅ CÓ",
        'no': "❌ KHÔNG",
        'skip': "⏭ Bỏ qua",
        'risk_high': "CAO",
        'risk_medium': "TRUNG BÌNH",
        'risk_low': "THẤP",
        'recommend_avoid': "KHÔNG GIAO DỊCH",
        'recommend_caution': "Tiến hành với cực kỳ thận trọng",
        'recommend_monitor': "Theo dõi và xác minh cẩn thận"
    },
    'zh': {
        'menu': "📋 *CHECK-SCAM 机器人菜单*",
        'language': "🌐 语言",
        'check': "🔍 检查诈骗者",
        'report': "🚨 举报诈骗者",
        'guide': "❓ 使用指南",
        'safety': "⚠️ 安全交易提示",
        'donate': "💝 支持开发者",
        'group': "👥 可信交易群组",
        'admin': "🛡 可信管理员/中介",
        'stats': "📊 诈骗者统计",
        'help': "ℹ️ 帮助",
        'back': "🔙 返回",
        'cancel': "❌ 取消",
        'choose_lang': "请选择语言:",
        'lang_set': "✅ 语言设置为中文",
        'welcome': "🛡️ *欢迎使用 CHECK-SCAM 机器人* 🛡️\n\n",
        'bot_desc': [
            "CHECK-SCAM 是帮助社区检查、举报",
            "和警告软件、商品、游戏账号、",
            "加密货币交易等诈骗的Telegram机器人。\n\n",
            "🔎 *特点与可信度*\n",
            "• 数据来自社区真实贡献\n",
            "• 每个诈骗者显示：\n",
            "  • **举报次数**\n",
            "  • **举报人数**\n",
            "  • 举报人越多 → 警告可信度越高\n",
            "• 系统帮助用户：\n",
            "  • 交易前评估风险\n",
            "  • 避开社区警告的诈骗者\n\n",
            "📌 *机器人统计*\n",
            "• 总用户数: {total_users}\n",
            "• 活跃举报者: {unique_reporters}\n",
            "• 数据库诈骗者: {total_scammers}\n\n",
            "⚠️ *免责声明*\n",
            "CHECK-SCAM 不提供法律结论，",
            "仅基于实际数据提供风险评分。"
        ],
        'report_steps': [
            "第1/6步: 输入诈骗者Telegram @用户名 (如无请输入'skip'):",
            "第2/6步: 输入诈骗者Telegram链接 (如无请输入'skip'):",
            "第3/6步: 输入诈骗者Binance ID/加密货币钱包:",
            "第4/6步: 输入被骗金额 (USDT或您的货币):",
            "第5/6步: 被骗物品是什么? (软件、游戏账号、金钱等):",
            "第6/6步: 请确认您的举报 (是/否):"
        ],
        'check_prompt': "输入@用户名、Telegram链接或Binance ID检查:",
        'scammer_info': """🚨 *交易警告*

• 目标: {username}
• Telegram: {telegram_link}
• 钱包/ID: {wallet_id}

📊 *社区统计*
• 总举报: {report_count}
• 举报人数: {reporter_count}
• 涉及总金额: ~ {total_amount} USDT

⚠️ 风险等级: {risk_level}
建议: {recommendation}""",
        'no_scammer': "未找到该信息的诈骗者。",
        'report_limit': "您已达到每日举报限制 (24小时内3次)。",
        'report_cancel': "举报已取消。记住：虚假举报伤害社区。",
        'report_success': "✅ 举报提交成功！",
        'invalid_amount': "请输入有效金额 (仅数字)。",
        'donation_text': """💝 *支持开发者*

Binance ID: `154265504`

您的支持帮助CHECK-SCAM维护服务器、
升级安全并为社区长期服务。
衷心感谢！

*透明度承诺:*
我们承诺透明使用所有捐款 -
严格用于机器人运营和长期开发。

感谢您的支持！ 🙏""",
        'group_text': """👥 *可信交易群组*

加入我们验证的交易社区:
[👉 J5 Trading Community](https://t.me/j5FS6B_V9DM5ZmVl)

• 安全交易环境
• 社区验证成员
• 诈骗警告和提醒""",
        'admin_text': """🛡 *可信管理员/中介*

如需可信中介服务，请联系:
[👉 Siculator98](https://t.me/siculator98)

• 经验丰富的中介
• 安全交易处理
• 社区信任""",
        'guide_text': """❓ *如何使用CHECK-SCAM机器人*

1. *检查诈骗者*: 任何交易前使用
2. *举报诈骗者*: 举报可疑用户 (最多3次/天)
3. *查看统计*: 查看被举报最多的诈骗者
4. *安全提示*: 学习安全交易实践

⚠️ 交易前始终验证！""",
        'safety_text': """⚠️ *安全交易提示*

1. ✅ 始终使用可信中介
2. ✅ 彻底检查用户历史
3. ✅ 避开好得不真实的交易
4. ✅ 大额交易使用托管服务
5. ✅ 立即举报可疑用户

保持安全！ 🔒""",
        'help_text': """ℹ️ *帮助与支持*

问题或建议:
• 使用 /start 返回主菜单
• 查看使用指南
• 加群获取社区支持

机器人版本: 2.0 | 更新: 2024""",
        'invalid_input': "输入无效。请重试。",
        'yes': "✅ 是",
        'no': "❌ 否",
        'skip': "⏭ 跳过",
        'risk_high': "高",
        'risk_medium': "中",
        'risk_low': "低",
        'recommend_avoid': "不要交易",
        'recommend_caution': "极其谨慎进行",
        'recommend_monitor': "仔细监控和验证"
    },
    'ru': {
        'menu': "📋 *МЕНЮ БОТА CHECK-SCAM*",
        'language': "🌐 Язык",
        'check': "🔍 Проверить мошенника",
        'report': "🚨 Сообщить о мошеннике",
        'guide': "❓ Руководство по использованию",
        'safety': "⚠️ Советы по безопасным сделкам",
        'donate': "💝 Поддержать разработчика",
        'group': "👥 Проверенная группа для сделок",
        'admin': "🛡 Проверенный админ/посредник",
        'stats': "📊 Статистика мошенников",
        'help': "ℹ️ Помощь",
        'back': "🔙 Назад",
        'cancel': "❌ Отмена",
        'choose_lang': "Пожалуйста, выберите язык:",
        'lang_set': "✅ Язык установлен: Русский",
        'welcome': "🛡️ *ДОБРО ПОЖАЛОВАТЬ В БОТ CHECK-SCAM* 🛡️\n\n",
        'bot_desc': [
            "CHECK-SCAM - это Telegram-бот, помогающий сообществу ",
            "проверять, сообщать и предупреждать о мошенничествах ",
            "в сделках с ПО, товарами, игровыми аккаунтами, ",
            "криптовалютой и т.д.\n\n",
            "🔎 *Преимущества и надежность*\n",
            "• Данные из реальных отчетов сообщества\n",
            "• Каждый мошенник показывает:\n",
            "  • **Количество жалоб**\n",
            "  • **Количество жалобщиков**\n",
            "  • Больше жалобщиков → Выше надежность предупреждения\n",
            "• Система помогает пользователям:\n",
            "  • Оценить риски перед сделкой\n",
            "  • Избегать мошенников, о которых предупреждало сообщество\n\n",
            "📌 *Статистика бота*\n",
            "• Всего пользователей: {total_users}\n",
            "• Активных жалобщиков: {unique_reporters}\n",
            "• Мошенников в БД: {total_scammers}\n\n",
            "⚠️ *Отказ от ответственности*\n",
            "CHECK-SCAM не дает юридических заключений, ",
            "только оценки риска на основе фактических данных."
        ],
        'report_steps': [
            "Шаг 1/6: Введите @username Telegram мошенника (или 'skip' если нет):",
            "Шаг 2/6: Введите ссылку Telegram мошенника (или 'skip' если нет):",
            "Шаг 3/6: Введите Binance ID/криптокошелек мошенника:",
            "Шаг 4/6: Введите сумму мошенничества (в USDT или вашей валюте):",
            "Шаг 5/6: Какой товар/услуга была мошеннической? (ПО, игровой аккаунт, деньги и т.д.):",
            "Шаг 6/6: Подтвердите ваш отчет (ДА/НЕТ):"
        ],
        'check_prompt': "Введите @username, ссылку Telegram или Binance ID для проверки:",
        'scammer_info': """🚨 *ПРЕДУПРЕЖДЕНИЕ О СДЕЛКЕ*

• Цель: {username}
• Telegram: {telegram_link}
• Кошелек/ID: {wallet_id}

📊 *СТАТИСТИКА СООБЩЕСТВА*
• Всего жалоб: {report_count}
• Количество жалобщиков: {reporter_count}
• Общая сумма: ~ {total_amount} USDT

⚠️ Уровень риска: {risk_level}
Рекомендация: {recommendation}""",
        'no_scammer': "Мошенник с такой информацией не найден.",
        'report_limit': "Вы достигли дневного лимита жалоб (3 жалобы за 24 часа).",
        'report_cancel': "Жалоба отменена. Помните: Ложные жалобы вредят сообществу.",
        'report_success': "✅ Жалоба успешно отправлена!",
        'invalid_amount': "Пожалуйста, введите действительную сумму (только цифры).",
        'donation_text': """💝 *ПОДДЕРЖАТЬ РАЗРАБОТЧИКА*

Binance ID: `154265504`

Ваша поддержка помогает CHECK-SCAM поддерживать серверы,
улучшать безопасность и служить сообществу долгосрочно.
Искренне благодарим!

*Обязательство прозрачности:*
Мы обязуемся использовать все пожертвования прозрачно -
строго для работы и долгосрочного развития бота.

Спасибо за вашу поддержку! 🙏""",
        'group_text': """👥 *ПРОВЕРЕННАЯ ГРУППА ДЛЯ СДЕЛОК*

Присоединяйтесь к нашему проверенному сообществу:
[👉 J5 Trading Community](https://t.me/j5FS6B_V9DM5ZmVl)

• Безопасная среда для сделок
• Проверенные участники сообщества
• Предупреждения о мошенничествах""",
        'admin_text': """🛡 *ПРОВЕРЕННЫЙ АДМИН/ПОСРЕДНИК*

Для услуг доверенного посредника:
[👉 Siculator98](https://t.me/siculator98)

• Опытный посредник
• Безопасная обработка сделок
• Доверие сообщества""",
        'guide_text': """❓ *КАК ИСПОЛЬЗОВАТЬ БОТ CHECK-SCAM*

1. *Проверить мошенника*: Используйте перед любой сделкой
2. *Сообщить о мошеннике*: Сообщите о подозрительных пользователях (макс. 3/день)
3. *Просмотреть статистику*: Смотрите самых часто сообщаемых мошенников
4. *Советы по безопасности*: Изучите практики безопасных сделок

⚠️ Всегда проверяйте перед сделкой!""",
        'safety_text': """⚠️ *СОВЕТЫ ПО БЕЗОПАСНЫМ СДЕЛКАМ*

1. ✅ Всегда используйте проверенных посредников
2. ✅ Тщательно проверяйте историю пользователя
3. ✅ Избегайте слишком хороших предложений
4. ✅ Используйте услуги эскроу для крупных сумм
5. ✅ Немедленно сообщайте о подозрительных пользователях

Оставайтесь в безопасности! 🔒""",
        'help_text': """ℹ️ *ПОМОЩЬ И ПОДДЕРЖКА*

Проблемы или предложения:
• Используйте /start для возврата в главное меню
• Проверьте руководство по использованию
• Присоединяйтесь к группе для поддержки сообщества

Версия бота: 2.0 | Обновлено: 2024""",
        'invalid_input': "Неверный ввод. Пожалуйста, попробуйте снова.",
        'yes': "✅ ДА",
        'no': "❌ НЕТ",
        'skip': "⏭ Пропустить",
        'risk_high': "ВЫСОКИЙ",
        'risk_medium': "СРЕДНИЙ",
        'risk_low': "НИЗКИЙ",
        'recommend_avoid': "НЕ СОВЕРШАТЬ СДЕЛКУ",
        'recommend_caution': "Действовать с крайней осторожностью",
        'recommend_monitor': "Внимательно следить и проверять"
    }
}

# ========== STATE CHOICES ==========
USERNAME, LINK, WALLET, AMOUNT, ITEM, CONFIRM = range(6)

# ========== HÀM TRỢ GIÚP ==========
def get_user_language(user_id):
    """Lấy ngôn ngữ của user"""
    users = load_users()
    return users['users'].get(str(user_id), {}).get('language', 'en')

def get_text(user_id, key, **kwargs):
    """Lấy text theo ngôn ngữ"""
    lang = get_user_language(user_id)
    text = LANGUAGES[lang].get(key, LANGUAGES['en'].get(key, key))
    
    if isinstance(text, list):
        text = ''.join(text)
    
    if kwargs:
        try:
            text = text.format(**kwargs)
        except:
            pass
    
    return text

def update_user_count(user_id, username=None):
    """Cập nhật số người dùng"""
    users = load_users()
    user_id_str = str(user_id)
    
    if user_id_str not in users['users']:
        users['total_users'] += 1
        users['users'][user_id_str] = {
            'id': user_id,
            'username': username,
            'language': 'en',
            'first_seen': datetime.now().isoformat(),
            'last_active': datetime.now().isoformat(),
            'report_count': 0,
            'last_report_date': None
        }
    else:
        users['users'][user_id_str]['last_active'] = datetime.now().isoformat()
        if username and username != users['users'][user_id_str].get('username'):
            users['users'][user_id_str]['username'] = username
    
    save_users(users)
    return users['users'][user_id_str]

def can_user_report(user_id):
    """Kiểm tra user có thể report không"""
    users = load_users()
    user_data = users['users'].get(str(user_id), {})
    
    if not user_data.get('last_report_date'):
        return True, 3
    
    last_date = datetime.fromisoformat(user_data['last_report_date'])
    now = datetime.now()
    
    # Nếu quá 24h từ lần report cuối
    if (now - last_date).days >= 1:
        return True, 3
    
    # Kiểm tra số lần report trong ngày
    daily_reports = user_data.get('daily_reports', 0)
    remaining = max(0, 3 - daily_reports)
    
    return daily_reports < 3, remaining

def update_user_report_count(user_id):
    """Cập nhật số lần report của user"""
    users = load_users()
    user_id_str = str(user_id)
    
    if user_id_str in users['users']:
        now = datetime.now()
        today = now.date().isoformat()
        
        if users['users'][user_id_str].get('last_report_date') != today:
            users['users'][user_id_str]['daily_reports'] = 1
        else:
            users['users'][user_id_str]['daily_reports'] = users['users'][user_id_str].get('daily_reports', 0) + 1
        
        users['users'][user_id_str]['last_report_date'] = today
        users['users'][user_id_str]['report_count'] = users['users'][user_id_str].get('report_count', 0) + 1
        save_users(users)

def get_bot_stats():
    """Lấy thống kê bot"""
    data = load_data()
    stats = load_stats()
    users = load_users()
    
    # Tính số unique reporters
    unique_reporters = 0
    for user_data in users['users'].values():
        if user_data.get('report_count', 0) > 0:
            unique_reporters += 1
    
    stats['total_scammers'] = len(data['scammers'])
    stats['unique_reporters'] = unique_reporters
    stats['total_users'] = users['total_users']
    
    save_stats(stats)
    return stats

def format_scammer_info(scammer_data, lang='en'):
    """Định dạng thông tin scammer"""
    report_count = scammer_data.get('report_count', 0)
    reporter_count = scammer_data.get('reporter_count', 0)
    total_amount = scammer_data.get('total_amount', 0)
    
    # Xác định risk level
    if report_count >= 10 or reporter_count >= 8:
        risk_level = get_text_by_lang(lang, 'risk_high')
        recommendation = get_text_by_lang(lang, 'recommend_avoid')
    elif report_count >= 5 or reporter_count >= 4:
        risk_level = get_text_by_lang(lang, 'risk_medium')
        recommendation = get_text_by_lang(lang, 'recommend_caution')
    else:
        risk_level = get_text_by_lang(lang, 'risk_low')
        recommendation = get_text_by_lang(lang, 'recommend_monitor')
    
    return get_text_by_lang(lang, 'scammer_info').format(
        username=scammer_data.get('username', 'N/A'),
        telegram_link=scammer_data.get('telegram_link', 'N/A'),
        wallet_id=scammer_data.get('wallet_id', 'N/A'),
        report_count=report_count,
        reporter_count=reporter_count,
        total_amount=total_amount,
        risk_level=risk_level,
        recommendation=recommendation
    )

def get_text_by_lang(lang, key):
    """Lấy text theo ngôn ngữ trực tiếp"""
    return LANGUAGES[lang].get(key, LANGUAGES['en'].get(key, key))

# ========== MENU & KEYBOARDS ==========
def main_menu_keyboard(user_id):
    """Tạo keyboard menu chính"""
    lang = get_user_language(user_id)
    
    keyboard = [
        [get_text(user_id, 'language')],
        [get_text(user_id, 'check'), get_text(user_id, 'report')],
        [get_text(user_id, 'guide'), get_text(user_id, 'safety')],
        [get_text(user_id, 'donate')],
        [get_text(user_id, 'group'), get_text(user_id, 'admin')],
        [get_text(user_id, 'stats'), get_text(user_id, 'help')]
    ]
    
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def language_keyboard():
    """Tạo keyboard chọn ngôn ngữ"""
    keyboard = [
        [InlineKeyboardButton("🇺🇸 English", callback_data='lang_en')],
        [InlineKeyboardButton("🇻🇳 Tiếng Việt", callback_data='lang_vi')],
        [InlineKeyboardButton("🇨🇳 中文", callback_data='lang_zh')],
        [InlineKeyboardButton("🇷🇺 Русский", callback_data='lang_ru')]
    ]
    return InlineKeyboardMarkup(keyboard)

def confirm_keyboard(user_id):
    """Tạo keyboard xác nhận"""
    keyboard = [
        [
            InlineKeyboardButton(get_text(user_id, 'yes'), callback_data='confirm_yes'),
            InlineKeyboardButton(get_text(user_id, 'no'), callback_data='confirm_no')
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

# ========== COMMAND HANDLERS ==========
def start(update: Update, context: CallbackContext):
    """Xử lý lệnh /start"""
    user = update.effective_user
    user_id = user.id
    username = user.username
    
    # Cập nhật thông tin user
    update_user_count(user_id, username)
    
    # Lấy thống kê bot
    stats = get_bot_stats()
    
    # Tạo tin nhắn chào mừng với thiết kế đẹp
    welcome_text = get_text(user_id, 'welcome')
    desc_text = get_text(user_id, 'bot_desc').format(
        total_users=stats['total_users'],
        unique_reporters=stats['unique_reporters'],
        total_scammers=stats['total_scammers']
    )
    
    full_text = f"""
{welcome_text}
*┌──────────────────────────────┐*
*│       CHECK-SCAM BOT         │*
*│     Community Protection     │*
*└──────────────────────────────┘*

{desc_text}

*🔰 Trusted by {stats['unique_reporters']+stats['total_users']}+ users*
*🛡️  {stats['total_scammers']} scammers detected*
*✅ 100% Automated • No Admin Approval*

Select an option below:
"""
    
    # Gửi tin nhắn với menu
    update.message.reply_text(
        full_text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=main_menu_keyboard(user_id)
    )
    
    return ConversationHandler.END

def help_command(update: Update, context: CallbackContext):
    """Xử lý menu Help"""
    user_id = update.effective_user.id
    help_text = get_text(user_id, 'help_text')
    
    update.message.reply_text(
        help_text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=main_menu_keyboard(user_id)
    )

def guide_command(update: Update, context: CallbackContext):
    """Xử lý menu Hướng dẫn"""
    user_id = update.effective_user.id
    guide_text = get_text(user_id, 'guide_text')
    
    update.message.reply_text(
        guide_text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=main_menu_keyboard(user_id)
    )

def safety_command(update: Update, context: CallbackContext):
    """Xử lý menu An toàn"""
    user_id = update.effective_user.id
    safety_text = get_text(user_id, 'safety_text')
    
    update.message.reply_text(
        safety_text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=main_menu_keyboard(user_id)
    )

def donate_command(update: Update, context: CallbackContext):
    """Xử lý menu Ủng hộ"""
    user_id = update.effective_user.id
    donate_text = get_text(user_id, 'donation_text')
    
    update.message.reply_text(
        donate_text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=main_menu_keyboard(user_id)
    )

def group_command(update: Update, context: CallbackContext):
    """Xử lý menu Group"""
    user_id = update.effective_user.id
    group_text = get_text(user_id, 'group_text')
    
    update.message.reply_text(
        group_text,
        parse_mode=ParseMode.MARKDOWN,
        disable_web_page_preview=False,
        reply_markup=main_menu_keyboard(user_id)
    )

def admin_command(update: Update, context: CallbackContext):
    """Xử lý menu Admin"""
    user_id = update.effective_user.id
    admin_text = get_text(user_id, 'admin_text')
    
    update.message.reply_text(
        admin_text,
        parse_mode=ParseMode.MARKDOWN,
        disable_web_page_preview=False,
        reply_markup=main_menu_keyboard(user_id)
    )

def stats_command(update: Update, context: CallbackContext):
    """Hiển thị top scammers"""
    user_id = update.effective_user.id
    data = load_data()
    
    if not data['scammers']:
        update.message.reply_text(
            "No scammer data available yet.",
            reply_markup=main_menu_keyboard(user_id)
        )
        return
    
    # Sắp xếp scammers theo số report
    sorted_scammers = sorted(
        data['scammers'].items(),
        key=lambda x: x[1].get('report_count', 0),
        reverse=True
    )[:10]
    
    stats_text = "📊 *TOP 10 MOST REPORTED SCAMMERS*\n\n"
    
    for i, (scammer_id, scammer_data) in enumerate(sorted_scammers, 1):
        username = scammer_data.get('username', 'Unknown')
        reports = scammer_data.get('report_count', 0)
        reporters = scammer_data.get('reporter_count', 0)
        amount = scammer_data.get('total_amount', 0)
        
        stats_text += f"{i}. `{username}`\n"
        stats_text += f"   📌 Reports: {reports} | Reporters: {reporters}\n"
        stats_text += f"   💰 Amount: {amount} USDT\n\n"
    
    stats_text += f"\nTotal scammers in database: {len(data['scammers'])}"
    
    update.message.reply_text(
        stats_text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=main_menu_keyboard(user_id)
    )

# ========== LANGUAGE HANDLERS ==========
def language_callback(update: Update, context: CallbackContext):
    """Xử lý chọn ngôn ngữ"""
    query = update.callback_query
    query.answer()
    
    user_id = query.from_user.id
    lang_code = query.data.split('_')[1]
    
    # Cập nhật ngôn ngữ cho user
    users = load_users()
    user_id_str = str(user_id)
    
    if user_id_str in users['users']:
        users['users'][user_id_str]['language'] = lang_code
        save_users(users)
    
    # Cập nhật tin nhắn
    lang_text = get_text_by_lang(lang_code, 'lang_set')
    query.edit_message_text(
        f"✅ {lang_text}\n\nPlease use the main menu below:",
        reply_markup=main_menu_keyboard(user_id)
    )

def language_command(update: Update, context: CallbackContext):
    """Hiển thị menu chọn ngôn ngữ"""
    user_id = update.effective_user.id
    choose_text = get_text(user_id, 'choose_lang')
    
    update.message.reply_text(
        choose_text,
        reply_markup=language_keyboard()
    )

# ========== CHECK SCAMMER ==========
def check_scammer(update: Update, context: CallbackContext):
    """Bắt đầu quá trình kiểm tra scammer"""
    user_id = update.effective_user.id
    check_prompt = get_text(user_id, 'check_prompt')
    
    update.message.reply_text(
        check_prompt,
        reply_markup=ReplyKeyboardMarkup([[get_text(user_id, 'back')]], resize_keyboard=True)
    )
    
    return 'CHECKING'

def process_check(update: Update, context: CallbackContext):
    """Xử lý tìm kiếm scammer"""
    user_id = update.effective_user.id
    query = update.message.text.strip()
    
    if query == get_text(user_id, 'back'):
        update.message.reply_text(
            get_text(user_id, 'menu'),
            reply_markup=main_menu_keyboard(user_id)
        )
        return ConversationHandler.END
    
    data = load_data()
    found = False
    
    # Tìm trong database
    for scammer_id, scammer_data in data['scammers'].items():
        if (query.lower() in scammer_data.get('username', '').lower() or
            query.lower() in scammer_data.get('telegram_link', '').lower() or
            query.lower() in scammer_data.get('wallet_id', '').lower()):
            
            scammer_info = format_scammer_info(scammer_data, get_user_language(user_id))
            update.message.reply_text(
                scammer_info,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=main_menu_keyboard(user_id)
            )
            found = True
            break
    
    if not found:
        update.message.reply_text(
            get_text(user_id, 'no_scammer'),
            reply_markup=main_menu_keyboard(user_id)
        )
    
    return ConversationHandler.END

# ========== REPORT SCAMMER ==========
def report_scammer(update: Update, context: CallbackContext):
    """Bắt đầu quá trình báo cáo scammer"""
    user_id = update.effective_user.id
    
    # Kiểm tra giới hạn report
    can_report, remaining = can_user_report(user_id)
    if not can_report:
        update.message.reply_text(
            get_text(user_id, 'report_limit'),
            reply_markup=main_menu_keyboard(user_id)
        )
        return ConversationHandler.END
    
    context.user_data['report_data'] = {}
    
    # Bước 1: Username
    update.message.reply_text(
        get_text(user_id, 'report_steps')[0],
        reply_markup=ReplyKeyboardMarkup(
            [[get_text(user_id, 'skip'), get_text(user_id, 'cancel')]],
            resize_keyboard=True
        )
    )
    
    return USERNAME

def process_username(update: Update, context: CallbackContext):
    """Xử lý username"""
    user_id = update.effective_user.id
    text = update.message.text.strip()
    
    if text == get_text(user_id, 'cancel'):
        update.message.reply_text(
            get_text(user_id, 'report_cancel'),
            reply_markup=main_menu_keyboard(user_id)
        )
        return ConversationHandler.END
    
    context.user_data['report_data']['username'] = text if text.lower() != get_text(user_id, 'skip').lower() else 'N/A'
    
    # Bước 2: Link
    update.message.reply_text(
        get_text(user_id, 'report_steps')[1],
        reply_markup=ReplyKeyboardMarkup(
            [[get_text(user_id, 'skip')]],
            resize_keyboard=True
        )
    )
    
    return LINK

def process_link(update: Update, context: CallbackContext):
    """Xử lý link"""
    user_id = update.effective_user.id
    text = update.message.text.strip()
    
    context.user_data['report_data']['telegram_link'] = text if text.lower() != get_text(user_id, 'skip').lower() else 'N/A'
    
    # Bước 3: Wallet ID
    update.message.reply_text(
        get_text(user_id, 'report_steps')[2]
    )
    
    return WALLET

def process_wallet(update: Update, context: CallbackContext):
    """Xử lý wallet ID"""
    user_id = update.effective_user.id
    text = update.message.text.strip()
    
    context.user_data['report_data']['wallet_id'] = text
    
    # Bước 4: Amount
    update.message.reply_text(
        get_text(user_id, 'report_steps')[3]
    )
    
    return AMOUNT

def process_amount(update: Update, context: CallbackContext):
    """Xử lý số tiền"""
    user_id = update.effective_user.id
    text = update.message.text.strip()
    
    try:
        amount = float(text.replace(',', '').replace(' ', ''))
        context.user_data['report_data']['amount'] = amount
    except ValueError:
        update.message.reply_text(
            get_text(user_id, 'invalid_amount')
        )
        return AMOUNT
    
    # Bước 5: Item
    update.message.reply_text(
        get_text(user_id, 'report_steps')[4]
    )
    
    return ITEM

def process_item(update: Update, context: CallbackContext):
    """Xử lý mặt hàng"""
    user_id = update.effective_user.id
    text = update.message.text.strip()
    
    context.user_data['report_data']['item'] = text
    
    # Bước 6: Xác nhận
    report_data = context.user_data['report_data']
    confirm_text = f"""
📋 *REPORT SUMMARY*

• Username: {report_data.get('username', 'N/A')}
• Telegram Link: {report_data.get('telegram_link', 'N/A')}
• Wallet ID: {report_data.get('wallet_id', 'N/A')}
• Amount: {report_data.get('amount', 0)} USDT
• Item: {report_data.get('item', 'N/A')}

Please confirm your report:
"""
    
    update.message.reply_text(
        confirm_text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=confirm_keyboard(user_id)
    )
    
    return CONFIRM

def process_confirm(update: Update, context: CallbackContext):
    """Xử lý xác nhận report"""
    query = update.callback_query
    query.answer()
    
    user_id = query.from_user.id
    
    if query.data == 'confirm_yes':
        # Lưu report vào database
        data = load_data()
        report_data = context.user_data['report_data']
        
        # Tạo ID cho scammer dựa trên wallet_id hoặc username
        scammer_id = report_data.get('wallet_id', report_data.get('username', 'unknown')).lower()
        
        if scammer_id not in data['scammers']:
            data['scammers'][scammer_id] = {
                'username': report_data.get('username', 'N/A'),
                'telegram_link': report_data.get('telegram_link', 'N/A'),
                'wallet_id': report_data.get('wallet_id', 'N/A'),
                'report_count': 0,
                'reporter_count': 0,
                'total_amount': 0,
                'items': set(),
                'reporters': set()
            }
        
        # Cập nhật thống kê
        scammer = data['scammers'][scammer_id]
        scammer['report_count'] += 1
        
        # Kiểm tra nếu user đã report scammer này chưa
        user_id_str = str(user_id)
        if user_id_str not in scammer['reporters']:
            scammer['reporter_count'] += 1
            scammer['reporters'].add(user_id_str)
        
        scammer['total_amount'] += report_data.get('amount', 0)
        scammer['items'].add(report_data.get('item', 'Unknown'))
        
        # Chuyển set thành list để lưu JSON
        scammer['items'] = list(scammer['items'])
        scammer['reporters'] = list(scammer['reporters'])
        
        save_data(data)
        
        # Cập nhật thống kê user
        update_user_report_count(user_id)
        
        # Cập nhật thống kê tổng
        stats = load_stats()
        stats['total_reports'] += 1
        save_stats(stats)
        
        query.edit_message_text(
            get_text(user_id, 'report_success'),
            parse_mode=ParseMode.MARKDOWN
        )
        
        # Hiển thị menu chính
        context.bot.send_message(
            chat_id=user_id,
            text=get_text(user_id, 'menu'),
            reply_markup=main_menu_keyboard(user_id)
        )
        
    else:
        query.edit_message_text(
            get_text(user_id, 'report_cancel'),
            parse_mode=ParseMode.MARKDOWN
        )
        
        context.bot.send_message(
            chat_id=user_id,
            text=get_text(user_id, 'menu'),
            reply_markup=main_menu_keyboard(user_id)
        )
    
    return ConversationHandler.END

def cancel_report(update: Update, context: CallbackContext):
    """Hủy báo cáo"""
    user_id = update.effective_user.id
    
    update.message.reply_text(
        get_text(user_id, 'report_cancel'),
        reply_markup=main_menu_keyboard(user_id)
    )
    
    return ConversationHandler.END

# ========== MESSAGE HANDLER ==========
def handle_message(update: Update, context: CallbackContext):
    """Xử lý tin nhắn thông thường"""
    user_id = update.effective_user.id
    text = update.message.text
    
    # Kiểm tra nếu là lệnh menu
    if text == get_text(user_id, 'language'):
        language_command(update, context)
    elif text == get_text(user_id, 'check'):
        return check_scammer(update, context)
    elif text == get_text(user_id, 'report'):
        return report_scammer(update, context)
    elif text == get_text(user_id, 'guide'):
        guide_command(update, context)
    elif text == get_text(user_id, 'safety'):
        safety_command(update, context)
    elif text == get_text(user_id, 'donate'):
        donate_command(update, context)
    elif text == get_text(user_id, 'group'):
        group_command(update, context)
    elif text == get_text(user_id, 'admin'):
        admin_command(update, context)
    elif text == get_text(user_id, 'stats'):
        stats_command(update, context)
    elif text == get_text(user_id, 'help'):
        help_command(update, context)
    elif text == get_text(user_id, 'back'):
        update.message.reply_text(
            get_text(user_id, 'menu'),
            reply_markup=main_menu_keyboard(user_id)
        )
    else:
        update.message.reply_text(
            get_text(user_id, 'invalid_input'),
            reply_markup=main_menu_keyboard(user_id)
        )
    
    return ConversationHandler.END

# ========== MAIN FUNCTION ==========
def main():
    """Hàm chính khởi chạy bot"""
    # Khởi tạo file dữ liệu
    init_files()
    
    # Lấy token từ biến môi trường
    TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
    if not TOKEN:
        print("❌ Lỗi: Chưa đặt TELEGRAM_BOT_TOKEN trong biến môi trường!")
        print("👉 Trên CMD: set TELEGRAM_BOT_TOKEN=your_token")
        print("👉 Trên Render: Thêm trong Environment Variables")
        return
    
    # Tạo updater
    updater = Updater(TOKEN, use_context=True)
    dispatcher = updater.dispatcher
    
    # Conversation handler cho check scammer
    check_conv_handler = ConversationHandler(
        entry_points=[MessageHandler(Filters.regex(r'^(🔍|Check|Kiểm tra)'), check_scammer)],
        states={
            'CHECKING': [MessageHandler(Filters.text & ~Filters.command, process_check)]
        },
        fallbacks=[CommandHandler('start', start)]
    )
    
    # Conversation handler cho report scammer
    report_conv_handler = ConversationHandler(
        entry_points=[MessageHandler(Filters.regex(r'^(🚨|Report|Báo cáo)'), report_scammer)],
        states={
            USERNAME: [MessageHandler(Filters.text & ~Filters.command, process_username)],
            LINK: [MessageHandler(Filters.text & ~Filters.command, process_link)],
            WALLET: [MessageHandler(Filters.text & ~Filters.command, process_wallet)],
            AMOUNT: [MessageHandler(Filters.text & ~Filters.command, process_amount)],
            ITEM: [MessageHandler(Filters.text & ~Filters.command, process_item)],
            CONFIRM: [CallbackQueryHandler(process_confirm, pattern='^confirm_')]
        },
        fallbacks=[
            CommandHandler('start', start),
            MessageHandler(Filters.regex(r'^(Cancel|Hủy|Отмена|取消)'), cancel_report)
        ]
    )
    
    # Thêm các handler
    dispatcher.add_handler(CommandHandler('start', start))
    dispatcher.add_handler(CommandHandler('help', help_command))
    dispatcher.add_handler(CallbackQueryHandler(language_callback, pattern='^lang_'))
    dispatcher.add_handler(check_conv_handler)
    dispatcher.add_handler(report_conv_handler)
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))
    
    # Kiểm tra môi trường để chọn phương thức chạy
    PORT = int(os.environ.get('PORT', 8443))
    RENDER = os.environ.get('RENDER', False)
    
    if RENDER:
        # Chạy trên Render với Webhook
        APP_NAME = os.environ.get('APP_NAME', 'check-scam-bot')
        WEBHOOK_URL = f'https://{APP_NAME}.onrender.com/{TOKEN}'
        
        updater.start_webhook(
            listen="0.0.0.0",
            port=PORT,
            url_path=TOKEN,
            webhook_url=WEBHOOK_URL
        )
        updater.bot.set_webhook(WEBHOOK_URL)
        print(f"✅ Bot đang chạy trên Render với Webhook: {WEBHOOK_URL}")
    else:
        # Chạy trên CMD với Polling
        updater.start_polling()
        print("✅ Bot đang chạy trên CMD với Polling...")
    
    print("🤖 Bot CHECK-SCAM đã sẵn sàng!")
    print("📊 Phiên bản: 2.0 | Ngôn ngữ: Đa ngôn ngữ")
    print("🛡️ Tính năng: Check/Report Scammer, Không Admin Duyệt")
    
    updater.idle()

if __name__ == '__main__':
    main()
