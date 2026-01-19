#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BOT CHECK SCAM - Ultimate Anti-Scam Community Bot
Version: 4.0 (Ultra Professional)
Author: Community Driven
License: MIT
"""

import asyncio
import sqlite3
import json
import logging
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from collections import defaultdict
from dataclasses import dataclass, asdict

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
    MenuButtonCommands
)
from telegram.constants import ParseMode
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ConversationHandler,
    filters,
    ContextTypes
)
from telegram.error import TelegramError

# ====================== CONFIGURATION ======================
BOT_TOKEN = "YOUR_BOT_TOKEN_HERE"  # ← Thay bằng token thực tế
BINANCE_ID = "154265504"
SUPPORTED_LANGUAGES = ["en", "vi", "ru", "zh"]
DEFAULT_LANGUAGE = "en"

# Database setup
DB_FILE = "bot_check_scam.db"

# Anti-spam configuration
DAILY_REPORT_LIMIT = 3
REPORT_COOLDOWN_SECONDS = 30

# Admin and trusted groups (sample data)
TRUSTED_ADMINS = [
    {"telegram": "@admin1", "region": "Global", "role": "Senior Moderator", "note": "Verified since 2023"},
    {"telegram": "@admin2", "region": "Asia", "role": "Community Manager", "note": "Multilingual support"},
    {"telegram": "@admin3", "region": "Europe", "role": "Security Expert", "note": "24/7 availability"},
]

TRUSTED_GROUPS = [
    {"name": "Scam Alert Global", "description": "Main community for scam reports", "link": "https://t.me/scamalert", "verified": True},
    {"name": "Crypto Safety Hub", "description": "Cryptocurrency security discussions", "link": "https://t.me/cryptosafety", "verified": True},
    {"name": "Vietnamese Traders", "description": "Vietnamese trading community", "link": "https://t.me/vntraders", "verified": True},
]

# ====================== LOGGING SETUP ======================
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ====================== DATABASE MODELS ======================
@dataclass
class User:
    user_id: int
    language: str = DEFAULT_LANGUAGE
    report_count: int = 0
    last_report_date: str = ""
    last_activity: str = ""

@dataclass
class Report:
    id: int = 0
    reporter_id: int = 0
    target: str = ""
    scam_type: str = ""
    amount: str = ""
    proof: str = ""
    created_at: str = ""
    status: str = "active"

@dataclass
class Statistics:
    total_reports: int = 0
    today_reports: int = 0
    top_targets: List[Tuple[str, int]] = None

# ====================== DATABASE MANAGER ======================
class Database:
    def __init__(self, db_file: str):
        self.conn = sqlite3.connect(db_file, check_same_thread=False)
        self.create_tables()
    
    def create_tables(self):
        cursor = self.conn.cursor()
        
        # Users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                language TEXT DEFAULT 'en',
                report_count INTEGER DEFAULT 0,
                last_report_date TEXT,
                last_activity TEXT
            )
        ''')
        
        # Reports table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                reporter_id INTEGER,
                target TEXT,
                scam_type TEXT,
                amount TEXT,
                proof TEXT,
                created_at TEXT,
                status TEXT DEFAULT 'active',
                FOREIGN KEY (reporter_id) REFERENCES users (user_id)
            )
        ''')
        
        # Cache table for statistics
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS stats_cache (
                key TEXT PRIMARY KEY,
                value TEXT,
                updated_at TEXT
            )
        ''')
        
        self.conn.commit()
    
    def get_user(self, user_id: int) -> Optional[User]:
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()
        if row:
            return User(*row)
        return None
    
    def save_user(self, user: User):
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO users 
            (user_id, language, report_count, last_report_date, last_activity)
            VALUES (?, ?, ?, ?, ?)
        ''', (user.user_id, user.language, user.report_count, 
              user.last_report_date, user.last_activity))
        self.conn.commit()
    
    def add_report(self, report: Report) -> int:
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO reports 
            (reporter_id, target, scam_type, amount, proof, created_at, status)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (report.reporter_id, report.target, report.scam_type, 
              report.amount, report.proof, report.created_at, report.status))
        self.conn.commit()
        return cursor.lastrowid
    
    def get_reports_by_target(self, target: str) -> List[Report]:
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT * FROM reports 
            WHERE target LIKE ? AND status = 'active'
            ORDER BY created_at DESC
        ''', (f"%{target}%",))
        return [Report(*row) for row in cursor.fetchall()]
    
    def get_user_reports_today(self, user_id: int) -> int:
        today = datetime.now().strftime("%Y-%m-%d")
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT COUNT(*) FROM reports 
            WHERE reporter_id = ? AND DATE(created_at) = ?
        ''', (user_id, today))
        return cursor.fetchone()[0]
    
    def get_statistics(self) -> Statistics:
        cursor = self.conn.cursor()
        
        # Total reports
        cursor.execute("SELECT COUNT(*) FROM reports WHERE status = 'active'")
        total_reports = cursor.fetchone()[0]
        
        # Today's reports
        today = datetime.now().strftime("%Y-%m-%d")
        cursor.execute("SELECT COUNT(*) FROM reports WHERE DATE(created_at) = ?", (today,))
        today_reports = cursor.fetchone()[0]
        
        # Top targets
        cursor.execute('''
            SELECT target, COUNT(*) as count FROM reports 
            WHERE status = 'active' 
            GROUP BY target 
            ORDER BY count DESC 
            LIMIT 10
        ''')
        top_targets = cursor.fetchall()
        
        return Statistics(
            total_reports=total_reports,
            today_reports=today_reports,
            top_targets=top_targets
        )

db = Database(DB_FILE)

# ====================== MULTILANGUAGE SYSTEM ======================
TEXT = {
    "en": {
        "start_header": """
██████╗  ██████╗ ████████╗     ██████╗██╗  ██╗███████╗ ██████╗██╗  ██╗
██╔══██╗██╔═══██╗╚══██╔══╝    ██╔════╝██║  ██║██╔════╝██╔════╝██║ ██╔╝
██████╔╝██║   ██║   ██║       ██║     ███████║█████╗  ██║     █████╔╝ 
██╔══██╗██║   ██║   ██║       ██║     ██╔══██║██╔══╝  ██║     ██╔═██╗ 
██████╔╝╚██████╔╝   ██║       ╚██████╗██║  ██║███████╗╚██████╗██║  ██╗
╚═════╝  ╚═════╝    ╚═╝        ╚═════╝╚═╝  ╚═╝╚══════╝ ╚═════╝╚═╝  ╚═╝

BOT CHECK SCAM
""",
        "start_description": """
BOT CHECK SCAM is a community-driven system
for checking, detecting, and warning about
fraudulent activities in online transactions.

The bot operates based on community data,
helping reduce risks before transactions,
not replacing law or official authorities.
""",
        "core_features": """
BOT CHECK SCAM supports:
• Checking suspicious targets
• Reporting scam activities
• Scam data statistics
• List of trusted intermediaries
• Verified community groups
• Multi-language support
""",
        "legal_warning": """
⚠️ IMPORTANT NOTE:
• Data is for community reference only
• Bot is not responsible for disputes
• Users are responsible for their transactions
""",
        "menu_prompt": "👇 Please select a function below",
        
        # Check Scam
        "check_prompt": """
🔍 CHECK FOR SCAM

You can enter *ANY OF THE FOLLOWING INFORMATION*:

• Name / Telegram username
• Telegram ID
• Telegram link (t.me/...)
• Binance ID
• Crypto wallet (USDT / BNB / ETH...)
• Phone number (if available)

👉 Just enter 1 piece of information
""",
        "check_found": "❌ *SCAM ALERT* - This target has been reported {count} time(s)",
        "check_suspicious": "⚠️ *SUSPICIOUS* - This target has few reports",
        "check_clean": "✅ *CLEAN* - No scam reports found for this target",
        "check_error": "❌ Error processing your request",
        
        # Report Scam
        "report_prompt": """
🚨 REPORT SCAM

You can report suspicious activity here.
*Daily limit: {limit} reports per user*

Please enter the target information
(username, ID, wallet, etc.):
""",
        "report_limit_reached": "You have reached your daily report limit ({limit}). Try again tomorrow.",
        "report_confirm": "Are you sure you want to report this target?",
        "report_type_prompt": "Select scam type:",
        "report_amount_prompt": "Enter amount (optional):",
        "report_proof_prompt": "Provide proof (text/links):",
        "report_success": "✅ Report submitted successfully!",
        "report_cancelled": "Report cancelled.",
        
        # Statistics
        "stats_header": "📊 *SCAM STATISTICS*",
        "stats_total": "• Total reports: `{total}`",
        "stats_today": "• Today's reports: `{today}`",
        "stats_top": "• Top reported targets:\n{targets}",
        
        # Trusted Admins
        "admins_header": "🛡 *TRUSTED INTERMEDIARIES*",
        "admin_format": "• {telegram} | {region} | {role}\n  Note: {note}",
        
        # Trusted Groups
        "groups_header": "⭐ *VERIFIED COMMUNITY GROUPS*",
        "group_format": "• [{name}]({link}) - {description}",
        
        # Language Selection
        "language_prompt": "🌐 *Select Language*",
        "language_changed": "Language changed to English 🇬🇧",
        
        # Donation
        "donation_header": """
💖 SUPPORT BOT CHECK SCAM MAINTENANCE

The bot is maintained for:
• 24/7 server operation
• Anti-scam data storage
• System maintenance and upgrades
• Free community service

Support is completely voluntary.
""",
        "donation_info": """
Binance ID: `{binance_id}`
Support via: USDT only
""",
        "donation_thanks": """
🙏 THANK YOU FOR YOUR CONTRIBUTION

Your support helps BOT CHECK SCAM
maintain operations and protect the community
from fraudulent activities.
""",
        
        # Common
        "back_button": "🔙 Back",
        "yes_button": "✅ Yes",
        "no_button": "❌ No",
        "cancel_button": "🚫 Cancel",
        "menu_button": "📋 Main Menu",
        "error_general": "❌ An error occurred. Please try again.",
        "spam_warning": "⚠️ Please wait before sending another request.",
    },
    
    "vi": {
        "start_header": """
██████╗  ██████╗ ████████╗     ██████╗██╗  ██╗███████╗ ██████╗██╗  ██╗
██╔══██╗██╔═══██╗╚══██╔══╝    ██╔════╝██║  ██║██╔════╝██╔════╝██║ ██╔╝
██████╔╝██║   ██║   ██║       ██║     ███████║█████╗  ██║     █████╔╝ 
██╔══██╗██║   ██║   ██║       ██║     ██╔══██║██╔══╝  ██║     ██╔═██╗ 
██████╔╝╚██████╔╝   ██║       ╚██████╗██║  ██║███████╗╚██████╗██║  ██╗
╚═════╝  ╚═════╝    ╚═╝        ╚═════╝╚═╝  ╚═╝╚══════╝ ╚═════╝╚═╝  ╚═╝

BOT CHECK SCAM
""",
        "start_description": """
BOT CHECK SCAM là hệ thống hỗ trợ cộng đồng
trong việc kiểm tra, phát hiện và cảnh báo
các hành vi lừa đảo trong giao dịch trực tuyến.

Bot hoạt động dựa trên dữ liệu cộng đồng,
giúp giảm rủi ro trước khi giao dịch,
không thay thế pháp luật hay cơ quan chức năng.
""",
        "core_features": """
BOT CHECK SCAM hỗ trợ:
• Kiểm tra đối tượng nghi vấn
• Báo cáo hành vi lừa đảo
• Thống kê dữ liệu scam
• Danh sách trung gian uy tín
• Group cộng đồng đã xác minh
• Hỗ trợ đa ngôn ngữ
""",
        "legal_warning": """
⚠️ LƯU Ý QUAN TRỌNG:
• Dữ liệu mang tính tham khảo cộng đồng
• Bot không chịu trách nhiệm tranh chấp
• Người dùng tự chịu trách nhiệm giao dịch
""",
        "menu_prompt": "👇 Vui lòng chọn chức năng bên dưới",
        
        # Check Scam
        "check_prompt": """
🔍 KIỂM TRA LỪA ĐẢO

Bạn có thể nhập *MỘT TRONG CÁC THÔNG TIN SAU*:

• Tên / Username Telegram
• Telegram ID
• Link Telegram (t.me/...)
• Binance ID
• Ví Crypto (USDT / BNB / ETH…)
• Số điện thoại (nếu có)

👉 Chỉ cần nhập 1 thông tin bất kỳ
""",
        "check_found": "❌ *CẢNH BÁO LỪA ĐẢO* - Đối tượng này đã bị báo cáo {count} lần",
        "check_suspicious": "⚠️ *NGHI NGỜ* - Đối tượng này có ít báo cáo",
        "check_clean": "✅ *SẠCH* - Không tìm thấy báo cáo lừa đảo cho đối tượng này",
        "check_error": "❌ Lỗi xử lý yêu cầu của bạn",
        
        # Report Scam
        "report_prompt": """
🚨 BÁO CÁO LỪA ĐẢO

Bạn có thể báo cáo hành vi đáng ngờ tại đây.
*Giới hạn hàng ngày: {limit} báo cáo mỗi người*

Vui lòng nhập thông tin đối tượng
(username, ID, ví, v.v.):
""",
        "report_limit_reached": "Bạn đã đạt giới hạn báo cáo hàng ngày ({limit}). Thử lại vào ngày mai.",
        "report_confirm": "Bạn có chắc muốn báo cáo đối tượng này?",
        "report_type_prompt": "Chọn loại lừa đảo:",
        "report_amount_prompt": "Nhập số tiền (tùy chọn):",
        "report_proof_prompt": "Cung cấp bằng chứng (văn bản/liên kết):",
        "report_success": "✅ Báo cáo đã được gửi thành công!",
        "report_cancelled": "Đã hủy báo cáo.",
        
        # Statistics
        "stats_header": "📊 *THỐNG KÊ LỪA ĐẢO*",
        "stats_total": "• Tổng số báo cáo: `{total}`",
        "stats_today": "• Báo cáo hôm nay: `{today}`",
        "stats_top": "• Đối tượng bị báo cáo nhiều nhất:\n{targets}",
        
        # Trusted Admins
        "admins_header": "🛡 *TRUNG GIAN UY TÍN*",
        "admin_format": "• {telegram} | {region} | {role}\n  Ghi chú: {note}",
        
        # Trusted Groups
        "groups_header": "⭐ *NHÓM CỘNG ĐỒNG ĐÃ XÁC MINH*",
        "group_format": "• [{name}]({link}) - {description}",
        
        # Language Selection
        "language_prompt": "🌐 *Chọn Ngôn Ngữ*",
        "language_changed": "Đã đổi ngôn ngữ sang Tiếng Việt 🇻🇳",
        
        # Donation
        "donation_header": """
💖 ỦNG HỘ DUY TRÌ BOT CHECK SCAM

Bot được duy trì để:
• Vận hành máy chủ 24/7
• Lưu trữ dữ liệu chống lừa đảo
• Bảo trì và nâng cấp hệ thống
• Phục vụ cộng đồng miễn phí

Việc ủng hộ là hoàn toàn tự nguyện.
""",
        "donation_info": """
Binance ID: `{binance_id}`
Hỗ trợ: USDT
""",
        "donation_thanks": """
🙏 CẢM ƠN BẠN ĐÃ ĐÓNG GÓP

Sự ủng hộ của bạn giúp BOT CHECK SCAM
duy trì hoạt động và bảo vệ cộng đồng
trước các hành vi lừa đảo.
""",
        
        # Common
        "back_button": "🔙 Quay lại",
        "yes_button": "✅ Có",
        "no_button": "❌ Không",
        "cancel_button": "🚫 Hủy",
        "menu_button": "📋 Menu Chính",
        "error_general": "❌ Đã xảy ra lỗi. Vui lòng thử lại.",
        "spam_warning": "⚠️ Vui lòng đợi trước khi gửi yêu cầu khác.",
    },
    
    "ru": {
        "start_header": """
██████╗  ██████╗ ████████╗     ██████╗██╗  ██╗███████╗ ██████╗██╗  ██╗
██╔══██╗██╔═══██╗╚══██╔══╝    ██╔════╝██║  ██║██╔════╝██╔════╝██║ ██╔╝
██████╔╝██║   ██║   ██║       ██║     ███████║█████╗  ██║     █████╔╝ 
██╔══██╗██║   ██║   ██║       ██║     ██╔══██║██╔══╝  ██║     ██╔═██╗ 
██████╔╝╚██████╔╝   ██║       ╚██████╗██║  ██║███████╗╚██████╗██║  ██╗
╚═════╝  ╚═════╝    ╚═╝        ╚═════╝╚═╝  ╚═╝╚══════╝ ╚═════╝╚═╝  ╚═╝

BOT CHECK SCAM
""",
        "start_description": """
BOT CHECK SCAM — это система поддержки сообщества
в проверке, обнаружении и предупреждении
мошеннических действий в онлайн-транзакциях.

Бот работает на основе данных сообщества,
помогает снизить риски перед сделками,
не заменяет закон или официальные органы.
""",
        "core_features": """
BOT CHECK SCAM поддерживает:
• Проверку подозрительных объектов
• Сообщение о мошенничестве
• Статистику данных о скамах
• Список доверенных посредников
• Проверенные группы сообщества
• Многоязычную поддержку
""",
        "legal_warning": """
⚠️ ВАЖНОЕ ПРИМЕЧАНИЕ:
• Данные только для справки сообщества
• Бот не несет ответственности за споры
• Пользователи несут ответственность за свои транзакции
""",
        "menu_prompt": "👇 Пожалуйста, выберите функцию ниже",
        
        # Check Scam
        "check_prompt": """
🔍 ПРОВЕРКА НА МОШЕННИЧЕСТВО

Вы можете ввести *ЛЮБУЮ ИЗ СЛЕДУЮЩИХ ИНФОРМАЦИЙ*:

• Имя / Имя пользователя Telegram
• Telegram ID
• Ссылка Telegram (t.me/...)
• Binance ID
• Криптокошелек (USDT / BNB / ETH...)
• Номер телефона (если есть)

👉 Просто введите 1 информацию
""",
        "check_found": "❌ *МОШЕННИЧЕСТВО* - Этот объект был зарегистрирован {count} раз(а)",
        "check_suspicious": "⚠️ *ПОДОЗРИТЕЛЬНО* - У этого объекта мало сообщений",
        "check_clean": "✅ *ЧИСТО* - Сообщений о мошенничестве для этого объекта не найдено",
        "check_error": "❌ Ошибка обработки вашего запроса",
        
        # Report Scam
        "report_prompt": """
🚨 СООБЩИТЬ О МОШЕННИЧЕСТВЕ

Вы можете сообщить о подозрительной деятельности здесь.
*Дневной лимит: {limit} сообщений на пользователя*

Пожалуйста, введите информацию об объекте
(имя пользователя, ID, кошелек и т.д.):
""",
        "report_limit_reached": "Вы достигли дневного лимита сообщений ({limit}). Попробуйте завтра.",
        "report_confirm": "Вы уверены, что хотите сообщить об этом объекте?",
        "report_type_prompt": "Выберите тип мошенничества:",
        "report_amount_prompt": "Введите сумму (необязательно):",
        "report_proof_prompt": "Предоставьте доказательства (текст/ссылки):",
        "report_success": "✅ Сообщение успешно отправлено!",
        "report_cancelled": "Сообщение отменено.",
        
        # Statistics
        "stats_header": "📊 *СТАТИСТИКА МОШЕННИЧЕСТВА*",
        "stats_total": "• Всего сообщений: `{total}`",
        "stats_today": "• Сообщений сегодня: `{today}`",
        "stats_top": "• Наиболее часто сообщаемые объекты:\n{targets}",
        
        # Trusted Admins
        "admins_header": "🛡 *ДОВЕРЕННЫЕ ПОСРЕДНИКИ*",
        "admin_format": "• {telegram} | {region} | {role}\n  Примечание: {note}",
        
        # Trusted Groups
        "groups_header": "⭐ *ПРОВЕРЕННЫЕ ГРУППЫ СООБЩЕСТВА*",
        "group_format": "• [{name}]({link}) - {description}",
        
        # Language Selection
        "language_prompt": "🌐 *Выберите Язык*",
        "language_changed": "Язык изменен на Русский 🇷🇺",
        
        # Donation
        "donation_header": """
💖 ПОДДЕРЖАТЬ ПОДДЕРЖКУ BOT CHECK SCAM

Бот поддерживается для:
• Круглосуточной работы сервера
• Хранения данных о мошенничестве
• Технического обслуживания и обновлений системы
• Бесплатного обслуживания сообщества

Поддержка полностью добровольна.
""",
        "donation_info": """
Binance ID: `{binance_id}`
Поддержка через: USDT
""",
        "donation_thanks": """
🙏 СПАСИБО ЗА ВАШ ВКЛАД

Ваша поддержка помогает BOT CHECK SCAM
поддерживать операции и защищать сообщество
от мошеннических действий.
""",
        
        # Common
        "back_button": "🔙 Назад",
        "yes_button": "✅ Да",
        "no_button": "❌ Нет",
        "cancel_button": "🚫 Отмена",
        "menu_button": "📋 Главное Меню",
        "error_general": "❌ Произошла ошибка. Пожалуйста, попробуйте еще раз.",
        "spam_warning": "⚠️ Пожалуйста, подождите перед отправкой другого запроса.",
    },
    
    "zh": {
        "start_header": """
██████╗  ██████╗ ████████╗     ██████╗██╗  ██╗███████╗ ██████╗██╗  ██╗
██╔══██╗██╔═══██╗╚══██╔══╝    ██╔════╝██║  ██║██╔════╝██╔════╝██║ ██╔╝
██████╔╝██║   ██║   ██║       ██║     ███████║█████╗  ██║     █████╔╝ 
██╔══██╗██║   ██║   ██║       ██║     ██╔══██║██╔══╝  ██║     ██╔═██╗ 
██████╔╝╚██████╔╝   ██║       ╚██████╗██║  ██║███████╗╚██████╗██║  ██╗
╚═════╝  ╚═════╝    ╚═╝        ╚═════╝╚═╝  ╚═╝╚══════╝ ╚═════╝╚═╝  ╚═╝

BOT CHECK SCAM
""",
        "start_description": """
BOT CHECK SCAM 是一个社区驱动的系统
用于检查、检测和警告
在线交易中的欺诈行为。

该机器人基于社区数据运行，
帮助降低交易前的风险，
不能替代法律或官方机构。
""",
        "core_features": """
BOT CHECK SCAM 支持：
• 检查可疑目标
• 举报欺诈活动
• 欺诈数据统计
• 可信中介列表
• 已验证社区群组
• 多语言支持
""",
        "legal_warning": """
⚠️ 重要提示：
• 数据仅供参考社区使用
• 机器人不对争议负责
• 用户对自己的交易负责
""",
        "menu_prompt": "👇 请在下方选择功能",
        
        # Check Scam
        "check_prompt": """
🔍 检查欺诈

您可以输入*以下任何信息*：

• 姓名 / Telegram 用户名
• Telegram ID
• Telegram 链接 (t.me/...)
• Binance ID
• 加密货币钱包 (USDT / BNB / ETH...)
• 电话号码（如果有）

👉 只需输入1个信息
""",
        "check_found": "❌ *欺诈警告* - 此目标已被举报 {count} 次",
        "check_suspicious": "⚠️ *可疑* - 此目标举报较少",
        "check_clean": "✅ *安全* - 未找到此目标的欺诈举报",
        "check_error": "❌ 处理您的请求时出错",
        
        # Report Scam
        "report_prompt": """
🚨 举报欺诈

您可以在此举报可疑活动。
*每日限制：每位用户 {limit} 次举报*

请输入目标信息
（用户名、ID、钱包等）：
""",
        "report_limit_reached": "您已达到每日举报限制 ({limit})。请明天再试。",
        "report_confirm": "您确定要举报此目标吗？",
        "report_type_prompt": "选择欺诈类型：",
        "report_amount_prompt": "输入金额（可选）：",
        "report_proof_prompt": "提供证据（文本/链接）：",
        "report_success": "✅ 举报提交成功！",
        "report_cancelled": "举报已取消。",
        
        # Statistics
        "stats_header": "📊 *欺诈统计*",
        "stats_total": "• 总举报数：`{total}`",
        "stats_today": "• 今日举报：`{today}`",
        "stats_top": "• 被举报最多的目标：\n{targets}",
        
        # Trusted Admins
        "admins_header": "🛡 *可信中介*",
        "admin_format": "• {telegram} | {region} | {role}\n  备注：{note}",
        
        # Trusted Groups
        "groups_header": "⭐ *已验证社区群组*",
        "group_format": "• [{name}]({link}) - {description}",
        
        # Language Selection
        "language_prompt": "🌐 *选择语言*",
        "language_changed": "语言已更改为中文 🇨🇳",
        
        # Donation
        "donation_header": """
💖 支持 BOT CHECK SCAM 维护

机器人维护用于：
• 24/7 服务器运行
• 反欺诈数据存储
• 系统维护和升级
• 免费社区服务

支持完全自愿。
""",
        "donation_info": """
Binance ID：`{binance_id}`
支持方式：USDT
""",
        "donation_thanks": """
🙏 感谢您的贡献

您的支持帮助 BOT CHECK SCAM
维持运营并保护社区
免受欺诈活动侵害。
""",
        
        # Common
        "back_button": "🔙 返回",
        "yes_button": "✅ 是",
        "no_button": "❌ 否",
        "cancel_button": "🚫 取消",
        "menu_button": "📋 主菜单",
        "error_general": "❌ 发生错误。请重试。",
        "spam_warning": "⚠️ 请在发送另一个请求前等待。",
    }
}

# ====================== HELPER FUNCTIONS ======================
def get_user_language(user_id: int) -> str:
    """Get user language from database or default"""
    user = db.get_user(user_id)
    if user and user.language in SUPPORTED_LANGUAGES:
        return user.language
    return DEFAULT_LANGUAGE

def get_text(user_id: int, key: str, **kwargs) -> str:
    """Get localized text for user"""
    lang = get_user_language(user_id)
    text = TEXT[lang].get(key, TEXT[DEFAULT_LANGUAGE].get(key, key))
    return text.format(**kwargs) if kwargs else text

def create_main_menu(user_id: int) -> InlineKeyboardMarkup:
    """Create main menu keyboard"""
    keyboard = [
        [InlineKeyboardButton("🔍 " + get_text(user_id, "check_button", check="Check Scam"), callback_data="check_scam")],
        [InlineKeyboardButton("🚨 " + get_text(user_id, "report_button", report="Report Scam"), callback_data="report_scam")],
        [InlineKeyboardButton("📊 " + get_text(user_id, "stats_button", stats="Statistics"), callback_data="statistics")],
        [InlineKeyboardButton("🛡 " + get_text(user_id, "admins_button", admins="Trusted Admins"), callback_data="trusted_admins")],
        [InlineKeyboardButton("⭐ " + get_text(user_id, "groups_button", groups="Trusted Groups"), callback_data="trusted_groups")],
        [InlineKeyboardButton("🌐 " + get_text(user_id, "language_button", language="Language"), callback_data="change_language")],
        [InlineKeyboardButton("💖 " + get_text(user_id, "donate_button", donate="Donate"), callback_data="donate")],
    ]
    return InlineKeyboardMarkup(keyboard)

def create_back_button(user_id: int) -> InlineKeyboardMarkup:
    """Create back button keyboard"""
    keyboard = [[InlineKeyboardButton(get_text(user_id, "back_button"), callback_data="main_menu")]]
    return InlineKeyboardMarkup(keyboard)

def create_yes_no_keyboard(user_id: int) -> InlineKeyboardMarkup:
    """Create yes/no keyboard"""
    keyboard = [
        [
            InlineKeyboardButton(get_text(user_id, "yes_button"), callback_data="yes"),
            InlineKeyboardButton(get_text(user_id, "no_button"), callback_data="no")
        ],
        [InlineKeyboardButton(get_text(user_id, "cancel_button"), callback_data="cancel")]
    ]
    return InlineKeyboardMarkup(keyboard)

def create_language_keyboard() -> InlineKeyboardMarkup:
    """Create language selection keyboard"""
    keyboard = [
        [
            InlineKeyboardButton("🇬🇧 English", callback_data="lang_en"),
            InlineKeyboardButton("🇻🇳 Tiếng Việt", callback_data="lang_vi")
        ],
        [
            InlineKeyboardButton("🇷🇺 Русский", callback_data="lang_ru"),
            InlineKeyboardButton("🇨🇳 中文", callback_data="lang_zh")
        ],
        [InlineKeyboardButton("🔙 Back", callback_data="main_menu")]
    ]
    return InlineKeyboardMarkup(keyboard)

def validate_input(target: str) -> Tuple[bool, str]:
    """Validate user input for checking/reporting"""
    if not target or len(target.strip()) < 3:
        return False, "Input too short"
    
    if len(target) > 500:
        return False, "Input too long"
    
    # Basic pattern checks
    patterns = {
        'telegram_link': r'^(https?://)?(t\.me/|telegram\.me/)',
        'username': r'^@[a-zA-Z0-9_]{5,32}$',
        'phone': r'^\+?[1-9]\d{7,14}$',
        'binance_id': r'^\d{6,10}$',
    }
    
    return True, "Valid"

def normalize_target(target: str) -> str:
    """Normalize target for consistent searching"""
    target = target.strip().lower()
    
    # Remove telegram link prefixes
    if target.startswith(('t.me/', 'telegram.me/', '@')):
        target = target.replace('t.me/', '').replace('telegram.me/', '').replace('@', '')
    
    return target

# ====================== COMMAND HANDLERS ======================
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /start command"""
    user_id = update.effective_user.id
    
    # Create or update user in database
    user = db.get_user(user_id)
    if not user:
        user = User(
            user_id=user_id,
            language=DEFAULT_LANGUAGE,
            last_activity=datetime.now().isoformat()
        )
        db.save_user(user)
    
    # Send welcome message
    welcome_text = (
        get_text(user_id, "start_header") + "\n\n" +
        get_text(user_id, "start_description") + "\n\n" +
        get_text(user_id, "core_features") + "\n\n" +
        get_text(user_id, "legal_warning") + "\n\n" +
        get_text(user_id, "menu_prompt")
    )
    
    await update.message.reply_text(
        welcome_text,
        reply_markup=create_main_menu(user_id),
        parse_mode=ParseMode.MARKDOWN,
        disable_web_page_preview=True
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /help command"""
    user_id = update.effective_user.id
    help_text = get_text(user_id, "core_features")
    await update.message.reply_text(help_text, parse_mode=ParseMode.MARKDOWN)

# ====================== CALLBACK HANDLERS ======================
async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle button callbacks"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    data = query.data
    
    if data == "main_menu":
        await show_main_menu(update, context)
    
    elif data == "check_scam":
        await check_scam_prompt(update, context)
    
    elif data == "report_scam":
        await report_scam_prompt(update, context)
    
    elif data == "statistics":
        await show_statistics(update, context)
    
    elif data == "trusted_admins":
        await show_trusted_admins(update, context)
    
    elif data == "trusted_groups":
        await show_trusted_groups(update, context)
    
    elif data == "change_language":
        await change_language_prompt(update, context)
    
    elif data == "donate":
        await show_donation_info(update, context)
    
    elif data.startswith("lang_"):
        lang_code = data.split("_")[1]
        await set_language(update, context, lang_code)
    
    elif data in ["yes", "no", "cancel"]:
        await handle_report_confirmation(update, context, data)

async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show main menu"""
    user_id = update.effective_user.id
    await update.callback_query.edit_message_text(
        get_text(user_id, "menu_prompt"),
        reply_markup=create_main_menu(user_id),
        parse_mode=ParseMode.MARKDOWN
    )

# ====================== CHECK SCAM HANDLERS ======================
async def check_scam_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Prompt user for target to check"""
    user_id = update.effective_user.id
    await update.callback_query.edit_message_text(
        get_text(user_id, "check_prompt"),
        reply_markup=create_back_button(user_id),
        parse_mode=ParseMode.MARKDOWN
    )
    context.user_data['awaiting_check'] = True

async def check_scam_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle check scam input"""
    if not context.user_data.get('awaiting_check'):
        return
    
    user_id = update.effective_user.id
    target = update.message.text.strip()
    
    # Validate input
    is_valid, message = validate_input(target)
    if not is_valid:
        await update.message.reply_text(
            f"❌ {message}\n\n" + get_text(user_id, "check_prompt"),
            reply_markup=create_back_button(user_id),
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    # Normalize and search
    normalized_target = normalize_target(target)
    reports = db.get_reports_by_target(normalized_target)
    
    if len(reports) >= 3:
        result_text = get_text(user_id, "check_found", count=len(reports))
    elif len(reports) >= 1:
        result_text = get_text(user_id, "check_suspicious")
    else:
        result_text = get_text(user_id, "check_clean")
    
    # Add details if available
    if reports:
        result_text += "\n\n*Recent reports:*"
        for i, report in enumerate(reports[:3], 1):
            result_text += f"\n{i}. {report.scam_type}"
            if report.amount:
                result_text += f" ({report.amount})"
            result_text += f" - {report.created_at[:10]}"
    
    await update.message.reply_text(
        result_text,
        reply_markup=create_back_button(user_id),
        parse_mode=ParseMode.MARKDOWN
    )
    
    context.user_data.pop('awaiting_check', None)

# ====================== REPORT SCAM HANDLERS ======================
async def report_scam_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Prompt user for report details"""
    user_id = update.effective_user.id
    
    # Check daily limit
    today_reports = db.get_user_reports_today(user_id)
    if today_reports >= DAILY_REPORT_LIMIT:
        await update.callback_query.edit_message_text(
            get_text(user_id, "report_limit_reached", limit=DAILY_REPORT_LIMIT),
            reply_markup=create_back_button(user_id),
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    await update.callback_query.edit_message_text(
        get_text(user_id, "report_prompt", limit=DAILY_REPORT_LIMIT),
        reply_markup=create_back_button(user_id),
        parse_mode=ParseMode.MARKDOWN
    )
    context.user_data['awaiting_report_target'] = True
    context.user_data['report_stage'] = 'target'

async def report_scam_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle multi-stage report process"""
    user_id = update.effective_user.id
    text = update.message.text.strip()
    
    if context.user_data.get('awaiting_report_target'):
        # Stage 1: Get target
        is_valid, message = validate_input(text)
        if not is_valid:
            await update.message.reply_text(
                f"❌ {message}\n\n" + get_text(user_id, "report_prompt", limit=DAILY_REPORT_LIMIT),
                reply_markup=create_back_button(user_id)
            )
            return
        
        context.user_data['report_target'] = text
        context.user_data['awaiting_report_target'] = False
        
        # Ask for confirmation
        await update.message.reply_text(
            f"*Target:* {text}\n\n" + get_text(user_id, "report_confirm"),
            reply_markup=create_yes_no_keyboard(user_id),
            parse_mode=ParseMode.MARKDOWN
        )
    
    elif context.user_data.get('awaiting_report_type'):
        # Stage 2: Get scam type
        context.user_data['report_type'] = text
        context.user_data['awaiting_report_type'] = False
        context.user_data['awaiting_report_amount'] = True
        
        await update.message.reply_text(
            get_text(user_id, "report_amount_prompt"),
            reply_markup=create_back_button(user_id)
        )
    
    elif context.user_data.get('awaiting_report_amount'):
        # Stage 3: Get amount (optional)
        if text.lower() not in ['skip', 'none', '']:
            context.user_data['report_amount'] = text
        
        context.user_data['awaiting_report_amount'] = False
        context.user_data['awaiting_report_proof'] = True
        
        await update.message.reply_text(
            get_text(user_id, "report_proof_prompt"),
            reply_markup=create_back_button(user_id)
        )
    
    elif context.user_data.get('awaiting_report_proof'):
        # Stage 4: Get proof
        context.user_data['report_proof'] = text
        
        # Save report
        report = Report(
            reporter_id=user_id,
            target=normalize_target(context.user_data['report_target']),
            scam_type=context.user_data.get('report_type', 'Unknown'),
            amount=context.user_data.get('report_amount', ''),
            proof=text,
            created_at=datetime.now().isoformat(),
            status='active'
        )
        
        db.add_report(report)
        
        # Clear context
        for key in ['report_target', 'report_type', 'report_amount', 'report_proof',
                   'awaiting_report_proof', 'report_stage']:
            context.user_data.pop(key, None)
        
        await update.message.reply_text(
            get_text(user_id, "report_success"),
            reply_markup=create_back_button(user_id)
        )

async def handle_report_confirmation(update: Update, context: ContextTypes.DEFAULT_TYPE, choice: str) -> None:
    """Handle yes/no/cancel for report confirmation"""
    user_id = update.effective_user.id
    
    if choice == "cancel":
        # Clear all report data
        for key in list(context.user_data.keys()):
            if key.startswith('report') or key.startswith('awaiting'):
                context.user_data.pop(key, None)
        
        await update.callback_query.edit_message_text(
            get_text(user_id, "report_cancelled"),
            reply_markup=create_back_button(user_id)
        )
    
    elif choice == "yes":
        # Proceed with report
        await update.callback_query.edit_message_text(
            get_text(user_id, "report_type_prompt"),
            reply_markup=create_back_button(user_id)
        )
        context.user_data['awaiting_report_type'] = True
    
    elif choice == "no":
        # Go back to report start
        await report_scam_prompt(update, context)

# ====================== STATISTICS HANDLER ======================
async def show_statistics(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show scam statistics"""
    user_id = update.effective_user.id
    stats = db.get_statistics()
    
    # Format top targets
    top_targets_text = ""
    if stats.top_targets:
        for target, count in stats.top_targets[:5]:
            top_targets_text += f"  ▪️ `{target[:30]}`: {count}\n"
    
    stats_text = (
        get_text(user_id, "stats_header") + "\n\n" +
        get_text(user_id, "stats_total", total=stats.total_reports) + "\n" +
        get_text(user_id, "stats_today", today=stats.today_reports) + "\n\n"
    )
    
    if top_targets_text:
        stats_text += get_text(user_id, "stats_top", targets=top_targets_text)
    
    await update.callback_query.edit_message_text(
        stats_text,
        reply_markup=create_back_button(user_id),
        parse_mode=ParseMode.MARKDOWN
    )

# ====================== TRUSTED ADMINS HANDLER ======================
async def show_trusted_admins(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show trusted admins list"""
    user_id = update.effective_user.id
    
    admins_text = get_text(user_id, "admins_header") + "\n\n"
    
    for admin in TRUSTED_ADMINS:
        admins_text += get_text(
            user_id, 
            "admin_format",
            telegram=admin['telegram'],
            region=admin['region'],
            role=admin['role'],
            note=admin['note']
        ) + "\n\n"
    
    await update.callback_query.edit_message_text(
        admins_text,
        reply_markup=create_back_button(user_id),
        parse_mode=ParseMode.MARKDOWN
    )

# ====================== TRUSTED GROUPS HANDLER ======================
async def show_trusted_groups(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show trusted groups list"""
    user_id = update.effective_user.id
    
    groups_text = get_text(user_id, "groups_header") + "\n\n"
    
    for group in TRUSTED_GROUPS:
        if group['verified']:
            groups_text += get_text(
                user_id,
                "group_format",
                name=group['name'],
                link=group['link'],
                description=group['description']
            ) + "\n\n"
    
    await update.callback_query.edit_message_text(
        groups_text,
        reply_markup=create_back_button(user_id),
        parse_mode=ParseMode.MARKDOWN,
        disable_web_page_preview=True
    )

# ====================== LANGUAGE HANDLERS ======================
async def change_language_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show language selection"""
    await update.callback_query.edit_message_text(
        "🌐 *Select Language / Chọn ngôn ngữ / Выберите язык / 选择语言*",
        reply_markup=create_language_keyboard(),
        parse_mode=ParseMode.MARKDOWN
    )

async def set_language(update: Update, context: ContextTypes.DEFAULT_TYPE, lang_code: str) -> None:
    """Set user language"""
    user_id = update.effective_user.id
    
    if lang_code in SUPPORTED_LANGUAGES:
        user = db.get_user(user_id)
        if not user:
            user = User(user_id=user_id)
        
        user.language = lang_code
        user.last_activity = datetime.now().isoformat()
        db.save_user(user)
        
        # Update message with selected language
        if lang_code == "en":
            lang_name = "English 🇬🇧"
        elif lang_code == "vi":
            lang_name = "Tiếng Việt 🇻🇳"
        elif lang_code == "ru":
            lang_name = "Русский 🇷🇺"
        elif lang_code == "zh":
            lang_name = "中文 🇨🇳"
        else:
            lang_name = "English 🇬🇧"
        
        await update.callback_query.edit_message_text(
            f"✅ Language set to {lang_name}",
            reply_markup=create_back_button(user_id)
        )

# ====================== DONATION HANDLER ======================
async def show_donation_info(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show donation information"""
    user_id = update.effective_user.id
    
    donation_text = (
        get_text(user_id, "donation_header") + "\n\n" +
        get_text(user_id, "donation_info", binance_id=BINANCE_ID) + "\n\n" +
        get_text(user_id, "donation_thanks")
    )
    
    await update.callback_query.edit_message_text(
        donation_text,
        reply_markup=create_back_button(user_id),
        parse_mode=ParseMode.MARKDOWN
    )

# ====================== MESSAGE HANDLER ======================
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle all text messages"""
    user_id = update.effective_user.id
    
    # Check if we're expecting input for check or report
    if context.user_data.get('awaiting_check'):
        await check_scam_handler(update, context)
    elif context.user_data.get('report_stage'):
        await report_scam_handler(update, context)
    else:
        # Default response
        await update.message.reply_text(
            get_text(user_id, "menu_prompt"),
            reply_markup=create_main_menu(user_id),
            parse_mode=ParseMode.MARKDOWN
        )

# ====================== ERROR HANDLER ======================
async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle errors"""
    logger.error(f"Exception while handling an update: {context.error}")
    
    if update and update.effective_user:
        user_id = update.effective_user.id
        try:
            await context.bot.send_message(
                chat_id=user_id,
                text=get_text(user_id, "error_general"),
                reply_markup=create_back_button(user_id)
            )
        except:
            pass

# ====================== MAIN FUNCTION ======================
def main() -> None:
    """Start the bot"""
    # Create application
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CallbackQueryHandler(button_callback))
    
    # Add message handler (must be last)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Add error handler
    application.add_error_handler(error_handler)
    
    # Start bot
    print("🤖 BOT CHECK SCAM is starting...")
    print(f"📊 Database: {DB_FILE}")
    print(f"🌐 Languages: {SUPPORTED_LANGUAGES}")
    print("🚀 Bot is now running. Press Ctrl+C to stop.")
    
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
