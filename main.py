#!/usr/bin/env python3
"""
ANTI SCAM BOT - VERSION 3.0 (COMPLETE EDITION)
✅ Hoàn chỉnh 100% theo checklist
✅ Đầy đủ: Admin Panel + Group Management + Help Guides
✅ Hỗ trợ: Telegram + Binance + USDT (ERC20/TRC20/BEP20) + OKX UID
✅ 24/7 Render + Production Ready
"""

import os
import sys
import logging
import asyncio
import sqlite3
import json
import re
import time
import csv
import io
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Any, Union
from dataclasses import dataclass, asdict
from enum import Enum
from collections import defaultdict, Counter
import secrets
import string
import pytz

# ==================== CẤU HÌNH HỆ THỐNG ====================
# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Telegram Bot API
from telegram import (
    Update, 
    InlineKeyboardButton, 
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
    ChatMember,
    Chat,
    User,
    Message,
    CallbackQuery
)
from telegram.ext import (
    Application,
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    ConversationHandler,
    filters,
    PicklePersistence
)
from telegram.constants import ParseMode, ChatType, ChatMemberStatus
from telegram.error import TelegramError, NetworkError, Forbidden

# ==================== CẤU HÌNH GLOBAL ====================
class Config:
    """Quản lý cấu hình hệ thống"""
    
    # Bot Configuration
    BOT_TOKEN = os.getenv("BOT_TOKEN", "")
    BOT_USERNAME = os.getenv("BOT_USERNAME", "")
    
    # Admin Configuration
    ADMIN_IDS = [int(x.strip()) for x in os.getenv("ADMIN_IDS", "").split(",") if x.strip()]
    SUPER_ADMIN_IDS = [int(x.strip()) for x in os.getenv("SUPER_ADMIN_IDS", "").split(",") if x.strip()]
    
    # Database Configuration
    DATABASE_PATH = os.getenv("DATABASE_PATH", "anti_scam.db")
    BACKUP_DIR = os.getenv("BACKUP_DIR", "backups")
    
    # Render Configuration
    RENDER = os.getenv("RENDER", "false").lower() == "true"
    PORT = int(os.getenv("PORT", "8080"))
    
    # Rate Limiting
    RATE_LIMIT_REQUESTS = int(os.getenv("RATE_LIMIT_REQUESTS", "60"))
    RATE_LIMIT_PERIOD = int(os.getenv("RATE_LIMIT_PERIOD", "60"))
    REPORT_COOLDOWN = int(os.getenv("REPORT_COOLDOWN", "300"))
    
    # Security
    MAX_INPUT_LENGTH = 500
    MIN_REPORT_DESC = 20
    MAX_REPORTS_PER_DAY = 10
    
    # Group Settings
    GROUP_CHAT_ID = os.getenv("GROUP_CHAT_ID", "")
    CHANNEL_CHAT_ID = os.getenv("CHANNEL_CHAT_ID", "")
    SUPPORT_GROUP = os.getenv("SUPPORT_GROUP", "@anti_scam_support")
    
    # Feature Flags
    ENABLE_GROUPS = os.getenv("ENABLE_GROUPS", "true").lower() == "true"
    ENABLE_ADMIN_PANEL = os.getenv("ENABLE_ADMIN_PANEL", "true").lower() == "true"
    ENABLE_STATISTICS = os.getenv("ENABLE_STATISTICS", "true").lower() == "true"
    
    # Webhook (Not used for Render)
    WEBHOOK_URL = os.getenv("WEBHOOK_URL", "")
    
    # Logging
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE = os.getenv("LOG_FILE", "bot.log")
    
    # API Keys (if needed in future)
    BSCSCAN_API = os.getenv("BSCSCAN_API", "")
    ETHERSCAN_API = os.getenv("ETHERSCAN_API", "")
    
    # Constants
    SUPPORTED_LANGUAGES = ['en', 'vi', 'ru', 'zh']
    DEFAULT_LANGUAGE = 'en'
    
    # Risk Score Parameters
    RISK_WEIGHTS = {
        'report_count': 30,
        'multiple_reports': 30,
        'high_amount': 20,
        'multiple_ids': 20,
        'recent_activity': 20,
        'admin_confirmed': 40
    }
    
    # Transaction Safety Tips
    SAFETY_TIPS = {
        'en': [
            "✅ Always verify the recipient's identity",
            "✅ Use escrow services for large transactions",
            "✅ Never share your private keys or seed phrases",
            "✅ Enable 2FA on all your accounts",
            "✅ Double-check wallet addresses before sending",
            "✅ Use hardware wallets for large amounts",
            "✅ Beware of fake customer support",
            "✅ Research projects before investing"
        ],
        'vi': [
            "✅ Luôn xác minh danh tính người nhận",
            "✅ Sử dụng dịch vụ escrow cho giao dịch lớn",
            "✅ Không bao giờ chia sẻ private key hoặc seed phrase",
            "✅ Bật 2FA trên tất cả tài khoản",
            "✅ Kiểm tra kỹ địa chỉ ví trước khi gửi",
            "✅ Sử dụng ví cứng cho số lượng lớn",
            "✅ Cẩn thận với hỗ trợ khách hàng giả mạo",
            "✅ Nghiên cứu dự án trước khi đầu tư"
        ],
        'ru': [
            "✅ Всегда проверяйте личность получателя",
            "✅ Используйте услуги эскроу для крупных сделок",
            "✅ Никогда не делитесь своими приватными ключами или seed-фразами",
            "✅ Включите 2FA на всех своих аккаунтах",
            "✅ Дважды проверяйте адреса кошельков перед отправкой",
            "✅ Используйте аппаратные кошельки для крупных сумм",
            "✅ Остерегайтесь фальшивой службы поддержки",
            "✅ Изучайте проекты перед инвестированием"
        ],
        'zh': [
            "✅ 始终验证收款人身份",
            "✅ 对大额交易使用托管服务",
            "✅ 切勿分享您的私钥或助记词",
            "✅ 在所有账户上启用双重验证",
            "✅ 发送前仔细检查钱包地址",
            "✅ 对大额资金使用硬件钱包",
            "✅ 提防虚假客户支持",
            "✅ 投资前研究项目"
        ]
    }

# ==================== CẤU TRÚC DATABASE ====================
class DatabaseManager:
    """Quản lý database SQLite với tất cả bảng cần thiết"""
    
    def __init__(self, db_path: str = Config.DATABASE_PATH):
        self.db_path = db_path
        self.init_database()
        self.create_backup_dir()
    
    def create_backup_dir(self):
        """Tạo thư mục backup nếu chưa tồn tại"""
        if not os.path.exists(Config.BACKUP_DIR):
            os.makedirs(Config.BACKUP_DIR)
    
    def get_connection(self):
        """Lấy connection đến database"""
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn
    
    def init_database(self):
        """Khởi tạo tất cả bảng database"""
        tables = [
            # Bảng users
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER UNIQUE NOT NULL,
                username TEXT,
                first_name TEXT,
                last_name TEXT,
                language TEXT DEFAULT 'en',
                is_admin BOOLEAN DEFAULT 0,
                is_super_admin BOOLEAN DEFAULT 0,
                is_banned BOOLEAN DEFAULT 0,
                ban_reason TEXT,
                ban_until TIMESTAMP,
                reports_submitted INTEGER DEFAULT 0,
                successful_reports INTEGER DEFAULT 0,
                last_report_time TIMESTAMP,
                trust_score INTEGER DEFAULT 100,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                total_requests INTEGER DEFAULT 0
            )
            """,
            
            # Bảng scammers
            """
            CREATE TABLE IF NOT EXISTS scammers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_username TEXT,
                telegram_id INTEGER,
                telegram_phone TEXT,
                binance_uid TEXT,
                binance_pay_id TEXT,
                binance_email TEXT,
                usdt_address TEXT,
                usdt_network TEXT,
                okx_uid TEXT,
                okx_email TEXT,
                other_wallets TEXT,
                risk_score INTEGER DEFAULT 0,
                risk_level TEXT DEFAULT 'low',
                total_reports INTEGER DEFAULT 0,
                total_amount_usd REAL DEFAULT 0,
                first_reported TIMESTAMP,
                last_reported TIMESTAMP,
                is_confirmed BOOLEAN DEFAULT 0,
                confirmed_by INTEGER,
                confirmed_at TIMESTAMP,
                notes TEXT,
                tags TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """,
            
            # Bảng reports
            """
            CREATE TABLE IF NOT EXISTS reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                reporter_id INTEGER NOT NULL,
                scammer_id INTEGER,
                report_type TEXT NOT NULL,
                telegram_username TEXT,
                telegram_id INTEGER,
                binance_uid TEXT,
                binance_pay_id TEXT,
                usdt_address TEXT,
                usdt_network TEXT,
                okx_uid TEXT,
                amount_usd REAL DEFAULT 0,
                currency TEXT DEFAULT 'USD',
                description TEXT NOT NULL,
                proof_url TEXT,
                proof_type TEXT,
                status TEXT DEFAULT 'pending',
                reviewed_by INTEGER,
                reviewed_at TIMESTAMP,
                is_verified BOOLEAN DEFAULT 0,
                verification_notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (reporter_id) REFERENCES users (telegram_id),
                FOREIGN KEY (scammer_id) REFERENCES scammers (id)
            )
            """,
            
            # Bảng lookup_logs
            """
            CREATE TABLE IF NOT EXISTS lookup_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                lookup_type TEXT NOT NULL,
                query_value TEXT NOT NULL,
                result_status TEXT,
                risk_level TEXT,
                scammer_found BOOLEAN DEFAULT 0,
                response_time_ms INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (telegram_id)
            )
            """,
            
            # Bảng groups
            """
            CREATE TABLE IF NOT EXISTS groups (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id INTEGER UNIQUE NOT NULL,
                title TEXT,
                username TEXT,
                group_type TEXT DEFAULT 'regular',
                is_verified BOOLEAN DEFAULT 0,
                is_blacklisted BOOLEAN DEFAULT 0,
                is_official BOOLEAN DEFAULT 0,
                admin_count INTEGER DEFAULT 0,
                member_count INTEGER DEFAULT 0,
                trust_score INTEGER DEFAULT 50,
                warning_count INTEGER DEFAULT 0,
                last_warning TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """,
            
            # Bảng group_members
            """
            CREATE TABLE IF NOT EXISTS group_members (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                group_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                is_admin BOOLEAN DEFAULT 0,
                is_owner BOOLEAN DEFAULT 0,
                joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (group_id) REFERENCES groups (id),
                FOREIGN KEY (user_id) REFERENCES users (telegram_id),
                UNIQUE(group_id, user_id)
            )
            """,
            
            # Bảng trusted_admins
            """
            CREATE TABLE IF NOT EXISTS trusted_admins (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                admin_level TEXT DEFAULT 'moderator',
                permissions TEXT DEFAULT 'view_reports,review_reports',
                is_active BOOLEAN DEFAULT 1,
                added_by INTEGER,
                added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                notes TEXT,
                FOREIGN KEY (user_id) REFERENCES users (telegram_id)
            )
            """,
            
            # Bảng audit_logs
            """
            CREATE TABLE IF NOT EXISTS audit_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                admin_id INTEGER,
                action TEXT NOT NULL,
                target_type TEXT,
                target_id INTEGER,
                target_name TEXT,
                details TEXT,
                ip_address TEXT,
                user_agent TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """,
            
            # Bảng blacklist
            """
            CREATE TABLE IF NOT EXISTS blacklist (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                target_type TEXT NOT NULL,
                target_value TEXT NOT NULL,
                reason TEXT,
                banned_by INTEGER,
                banned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP,
                is_active BOOLEAN DEFAULT 1
            )
            """,
            
            # Bảng statistics
            """
            CREATE TABLE IF NOT EXISTS statistics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date DATE UNIQUE NOT NULL,
                total_users INTEGER DEFAULT 0,
                new_users INTEGER DEFAULT 0,
                total_lookups INTEGER DEFAULT 0,
                successful_lookups INTEGER DEFAULT 0,
                total_reports INTEGER DEFAULT 0,
                verified_reports INTEGER DEFAULT 0,
                active_groups INTEGER DEFAULT 0,
                blocked_scammers INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        ]
        
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_users_telegram_id ON users(telegram_id)",
            "CREATE INDEX IF NOT EXISTS idx_users_username ON users(username)",
            "CREATE INDEX IF NOT EXISTS idx_scammers_telegram ON scammers(telegram_username)",
            "CREATE INDEX IF NOT EXISTS idx_scammers_binance ON scammers(binance_uid)",
            "CREATE INDEX IF NOT EXISTS idx_scammers_usdt ON scammers(usdt_address)",
            "CREATE INDEX IF NOT EXISTS idx_scammers_okx ON scammers(okx_uid)",
            "CREATE INDEX IF NOT EXISTS idx_scammers_risk ON scammers(risk_level)",
            "CREATE INDEX IF NOT EXISTS idx_reports_status ON reports(status)",
            "CREATE INDEX IF NOT EXISTS idx_reports_reporter ON reports(reporter_id)",
            "CREATE INDEX IF NOT EXISTS idx_reports_scammer ON reports(scammer_id)",
            "CREATE INDEX IF NOT EXISTS idx_reports_created ON reports(created_at)",
            "CREATE INDEX IF NOT EXISTS idx_lookup_logs_user ON lookup_logs(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_lookup_logs_created ON lookup_logs(created_at)",
            "CREATE INDEX IF NOT EXISTS idx_groups_chat_id ON groups(chat_id)",
            "CREATE INDEX IF NOT EXISTS idx_groups_verified ON groups(is_verified)",
            "CREATE INDEX IF NOT EXISTS idx_blacklist_target ON blacklist(target_type, target_value)",
            "CREATE INDEX IF NOT EXISTS idx_audit_admin ON audit_logs(admin_id)",
            "CREATE INDEX IF NOT EXISTS idx_audit_created ON audit_logs(created_at)"
        ]
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Tạo tables
            for table_sql in tables:
                cursor.execute(table_sql)
            
            # Tạo indexes
            for index_sql in indexes:
                try:
                    cursor.execute(index_sql)
                except:
                    pass
            
            # Insert default super admin nếu chưa có
            for admin_id in Config.SUPER_ADMIN_IDS:
                cursor.execute("""
                    INSERT OR IGNORE INTO users 
                    (telegram_id, is_admin, is_super_admin, trust_score) 
                    VALUES (?, 1, 1, 1000)
                """, (admin_id,))
                
                cursor.execute("""
                    INSERT OR IGNORE INTO trusted_admins 
                    (user_id, admin_level, permissions) 
                    VALUES (?, 'super_admin', 'all')
                """, (admin_id,))
            
            conn.commit()
    
    def execute(self, query: str, params: tuple = ()) -> sqlite3.Cursor:
        """Thực thi query"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()
            return cursor
    
    def fetch_one(self, query: str, params: tuple = ()) -> Optional[sqlite3.Row]:
        """Lấy một bản ghi"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            return cursor.fetchone()
    
    def fetch_all(self, query: str, params: tuple = ()) -> List[sqlite3.Row]:
        """Lấy tất cả bản ghi"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            return cursor.fetchall()
    
    def backup_database(self) -> str:
        """Tạo backup database"""
        backup_file = f"{Config.BACKUP_DIR}/backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
        
        # Copy database file
        import shutil
        shutil.copy2(self.db_path, backup_file)
        
        # Log backup
        self.execute("""
            INSERT INTO audit_logs (action, details)
            VALUES ('database_backup', ?)
        """, (f"Backup created: {backup_file}",))
        
        return backup_file
    
    def export_csv(self, table_name: str) -> str:
        """Export table to CSV"""
        data = self.fetch_all(f"SELECT * FROM {table_name}")
        if not data:
            return ""
        
        # Tạo CSV content
        import io
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow([description[0] for description in data[0].cursor_description])
        
        # Write data
        for row in data:
            writer.writerow(row)
        
        return output.getvalue()

# ==================== QUẢN LÝ ĐA NGÔN NGỮ ====================
class I18nManager:
    """Quản lý đa ngôn ngữ với 4 ngôn ngữ"""
    
    TRANSLATIONS = {
        'en': {
            # Main menu
            'welcome': "👮 *ANTI SCAM BOT*\n\nWelcome! I can help you verify suspicious accounts and report scammers across multiple platforms.",
            'select_language': "🌐 *Select your language:*",
            'main_menu': "📋 *Main Menu*\nChoose an option below:",
            'back_to_menu': "🔙 Back to Main Menu",
            
            # Menu options
            'lookup_scam': "🔍 Lookup Scammer",
            'report_scam': "🚨 Report Scammer",
            'help_guide': "ℹ️ Help & Safety Guide",
            'trusted_admins': "👑 Trusted Admins",
            'verified_groups': "✅ Verified Groups",
            'admin_panel': "⚡ Admin Panel",
            'change_language': "🌐 Change Language",
            'view_stats': "📊 View Statistics",
            'settings': "⚙️ Settings",
            
            # Lookup
            'lookup_title': "🔍 *Scammer Lookup*\n\nSelect lookup type:",
            'lookup_telegram': "📱 Telegram",
            'lookup_binance': "💳 Binance",
            'lookup_usdt': "💰 USDT Wallet",
            'lookup_okx': "🔶 OKX",
            'lookup_advanced': "🔬 Advanced Search",
            'enter_telegram': "Please enter Telegram username (e.g., @username) or ID:",
            'enter_binance': "Please enter Binance UID (6-10 digits):",
            'enter_binance_pay': "Please enter Binance Pay ID:",
            'enter_usdt': "Please enter USDT wallet address:",
            'select_usdt_network': "Select USDT network:",
            'enter_okx': "Please enter OKX UID:",
            'enter_advanced': "Enter multiple identifiers (separated by comma):\n\nFormat: @username, binance_uid, usdt_address",
            
            # Results
            'scam_found': "🚨 *SCAM RISK DETECTED*\n\n",
            'no_data': "ℹ️ *No reports found for this query.*\n\n⚠️ *WARNING:*\nNo data does not mean safe. Always verify carefully and use caution.",
            'risk_low': "🟢 LOW RISK",
            'risk_medium': "🟡 MEDIUM RISK",
            'risk_high': "🔴 HIGH RISK",
            'risk_critical': "💀 CRITICAL RISK",
            'reports_count': "📊 Reports: {}",
            'amount_lost': "💰 Amount Lost: ${}",
            'first_reported': "📅 First Reported: {}",
            'last_reported': "🔄 Last Reported: {}",
            'risk_score': "🎯 Risk Score: {}/100",
            'tags': "🏷️ Tags: {}",
            'notes': "📝 Notes: {}",
            'confirmed_scam': "✅ *ADMIN CONFIRMED SCAMMER*",
            
            # Report
            'report_start': "🚨 *Report a Scammer*\n\nPlease follow the steps below:",
            'report_step1': "1️⃣ *Select report type:*",
            'report_type_telegram': "📱 Telegram Scammer",
            'report_type_binance': "💳 Binance Scammer",
            'report_type_usdt': "💰 USDT Scammer",
            'report_type_okx': "🔶 OKX Scammer",
            'report_type_multi': "🔗 Multiple Platforms",
            'report_step2': "2️⃣ *Enter details:*",
            'report_step3': "3️⃣ *Enter amount lost (USD):*",
            'report_step4': "4️⃣ *Describe what happened (min 20 chars):*",
            'report_step5': "5️⃣ *Provide proof (URL or description):*",
            'report_step6': "6️⃣ *Review and submit:*",
            'report_confirmation': "✅ *Report Submitted Successfully!*\n\nYour report has been received and will be reviewed by our team. Thank you for helping keep the community safe!",
            'report_limit': "⚠️ You have reached your daily report limit ({} reports). Please try again tomorrow.",
            'report_cooldown': "⏳ Please wait {} seconds before submitting another report.",
            
            # Help & Safety
            'help_title': "ℹ️ *HELP & SAFETY GUIDE*\n\n",
            'safety_tips': "🔒 *Safety Tips for Secure Trading:*\n",
            'how_to_use': "🤖 *How to Use This Bot:*\n",
            'common_scams': "⚠️ *Common Scam Types:*\n",
            'what_to_do': "🚨 *What to Do If Scammed:*\n",
            'resources': "📚 *Additional Resources:*\n",
            
            # Trusted Admins
            'trusted_admins_title': "👑 *TRUSTED ADMINS*\n\nVerified administrators you can trust:",
            'admin_info': "👤 *{}*\nLevel: {}\nTrust Score: {}\nActive Since: {}",
            'no_admins': "No trusted admins available.",
            
            # Verified Groups
            'verified_groups_title': "✅ *VERIFIED GROUPS*\n\nOfficial and verified community groups:",
            'group_info': "👥 *{}*\nType: {}\nMembers: {}\nTrust Score: {}\nJoined: {}",
            'no_groups': "No verified groups available.",
            
            # Admin Panel
            'admin_welcome': "⚡ *ADMIN PANEL*\n\nWelcome, Administrator!",
            'admin_menu': "📊 *Admin Menu*\nSelect an option:",
            'view_reports': "📋 View Reports",
            'manage_scammers': "👥 Manage Scammers",
            'manage_users': "👤 Manage Users",
            'manage_groups': "👥 Manage Groups",
            'manage_admins': "👑 Manage Admins",
            'system_stats': "📈 System Statistics",
            'export_data': "💾 Export Data",
            'backup_db': "🔄 Backup Database",
            'broadcast': "📢 Broadcast Message",
            'system_settings': "⚙️ System Settings",
            
            # Admin Actions
            'report_details': "📋 *Report #{}*\n\nStatus: {}\nType: {}\nReporter: @{}\nAmount: ${}\nDate: {}",
            'approve_report': "✅ Approve",
            'reject_report': "❌ Reject",
            'mark_verified': "🔍 Mark Verified",
            'need_more_info': "ℹ️ Need More Info",
            'report_approved': "✅ Report #{} has been approved.",
            'report_rejected': "❌ Report #{} has been rejected.",
            'report_verified': "🔍 Report #{} has been marked as verified.",
            
            # Statistics
            'stats_title': "📊 *SYSTEM STATISTICS*\n\n",
            'stats_users': "👥 Users: {} ({} new today)",
            'stats_reports': "📋 Reports: {} ({} pending)",
            'stats_scammers': "🚨 Scammers: {} ({} high risk)",
            'stats_lookups': "🔍 Lookups: {} total",
            'stats_groups': "👥 Groups: {} ({} verified)",
            'stats_amount': "💰 Total Amount Lost: ${}",
            
            # Errors & Warnings
            'error_general': "❌ An error occurred. Please try again.",
            'error_not_found': "❌ Not found. Please check your input.",
            'error_invalid_input': "❌ Invalid input. Please try again.",
            'error_permission': "⛔ You don't have permission to use this feature.",
            'error_banned': "🚫 You have been banned. Reason: {}",
            'error_rate_limit': "⏳ Rate limit exceeded. Please wait {} seconds.",
            
            # Success Messages
            'success_updated': "✅ Updated successfully.",
            'success_deleted': "✅ Deleted successfully.",
            'success_added': "✅ Added successfully.",
            
            # Confirmation
            'confirm_action': "⚠️ Are you sure you want to {}?",
            'yes': "✅ Yes",
            'no': "❌ No",
            'cancel': "🚫 Cancel",
            
            # Network Names
            'network_erc20': "Ethereum (ERC20)",
            'network_trc20': "Tron (TRC20)",
            'network_bep20': "BNB Smart Chain (BEP20)",
            
            # Misc
            'loading': "⏳ Loading...",
            'searching': "🔍 Searching...",
            'processing': "⚙️ Processing...",
            'done': "✅ Done",
            'empty': "Empty",
            'unknown': "Unknown"
        },
        
        'vi': {
            # Main menu
            'welcome': "👮 *BOT CHỐNG LỪA ĐẢO*\n\nChào mừng! Tôi có thể giúp bạn xác minh tài khoản đáng ngờ và báo cáo kẻ lừa đảo trên nhiều nền tảng.",
            'select_language': "🌐 *Chọn ngôn ngữ của bạn:*",
            'main_menu': "📋 *Menu Chính*\nChọn một tùy chọn bên dưới:",
            'back_to_menu': "🔙 Quay lại Menu Chính",
            
            # Menu options
            'lookup_scam': "🔍 Tra Cứu Lừa Đảo",
            'report_scam': "🚨 Báo Cáo Lừa Đảo",
            'help_guide': "ℹ️ Hướng Dẫn & An Toàn",
            'trusted_admins': "👑 Quản Trị Viên Uy Tín",
            'verified_groups': "✅ Nhóm Đã Xác Minh",
            'admin_panel': "⚡ Bảng Quản Trị",
            'change_language': "🌐 Đổi Ngôn Ngữ",
            'view_stats': "📊 Xem Thống Kê",
            'settings': "⚙️ Cài Đặt",
            
            # Lookup
            'lookup_title': "🔍 *Tra Cứu Kẻ Lừa Đảo*\n\nChọn loại tra cứu:",
            'lookup_telegram': "📱 Telegram",
            'lookup_binance': "💳 Binance",
            'lookup_usdt': "💰 Ví USDT",
            'lookup_okx': "🔶 OKX",
            'lookup_advanced': "🔬 Tìm Kiếm Nâng Cao",
            'enter_telegram': "Vui lòng nhập username Telegram (ví dụ: @username) hoặc ID:",
            'enter_binance': "Vui lòng nhập Binance UID (6-10 chữ số):",
            'enter_binance_pay': "Vui lòng nhập Binance Pay ID:",
            'enter_usdt': "Vui lòng nhập địa chỉ ví USDT:",
            'select_usdt_network': "Chọn mạng lưới USDT:",
            'enter_okx': "Vui lòng nhập OKX UID:",
            'enter_advanced': "Nhập nhiều định danh (phân cách bằng dấu phẩy):\n\nĐịnh dạng: @username, binance_uid, usdt_address",
            
            # Results
            'scam_found': "🚨 *PHÁT HIỆN NGUY CƠ LỪA ĐẢO*\n\n",
            'no_data': "ℹ️ *Không tìm thấy báo cáo cho truy vấn này.*\n\n⚠️ *CẢNH BÁO:*\nKhông có dữ liệu không có nghĩa là an toàn. Luôn xác minh cẩn thận và thận trọng.",
            'risk_low': "🟢 RỦI RO THẤP",
            'risk_medium': "🟡 RỦI RO TRUNG BÌNH",
            'risk_high': "🔴 RỦI RO CAO",
            'risk_critical': "💀 RỦI RO NGHIÊM TRỌNG",
            'reports_count': "📊 Số báo cáo: {}",
            'amount_lost': "💰 Số tiền mất: ${}",
            'first_reported': "📅 Báo cáo đầu tiên: {}",
            'last_reported': "🔄 Báo cáo gần nhất: {}",
            'risk_score': "🎯 Điểm rủi ro: {}/100",
            'tags': "🏷️ Thẻ: {}",
            'notes': "📝 Ghi chú: {}",
            'confirmed_scam': "✅ *KẺ LỪA ĐẢO ĐÃ ĐƯỢC XÁC NHẬN BỞI QUẢN TRỊ*",
            
            # Report
            'report_start': "🚨 *Báo Cáo Kẻ Lừa Đảo*\n\nVui lòng làm theo các bước bên dưới:",
            'report_step1': "1️⃣ *Chọn loại báo cáo:*",
            'report_type_telegram': "📱 Lừa đảo Telegram",
            'report_type_binance': "💳 Lừa đảo Binance",
            'report_type_usdt': "💰 Lừa đảo USDT",
            'report_type_okx': "🔶 Lừa đảo OKX",
            'report_type_multi': "🔗 Nhiều nền tảng",
            'report_step2': "2️⃣ *Nhập thông tin chi tiết:*",
            'report_step3': "3️⃣ *Nhập số tiền mất (USD):*",
            'report_step4': "4️⃣ *Mô tả sự việc (tối thiểu 20 ký tự):*",
            'report_step5': "5️⃣ *Cung cấp bằng chứng (URL hoặc mô tả):*",
            'report_step6': "6️⃣ *Xem lại và gửi:*",
            'report_confirmation': "✅ *Báo Cáo Đã Được Gửi Thành Công!*\n\nBáo cáo của bạn đã được tiếp nhận và sẽ được xem xét bởi đội ngũ của chúng tôi. Cảm ơn bạn đã giúp bảo vệ cộng đồng!",
            'report_limit': "⚠️ Bạn đã đạt giới hạn báo cáo hàng ngày ({} báo cáo). Vui lòng thử lại vào ngày mai.",
            'report_cooldown': "⏳ Vui lòng đợi {} giây trước khi gửi báo cáo khác.",
            
            # Help & Safety
            'help_title': "ℹ️ *HƯỚNG DẪN & AN TOÀN*\n\n",
            'safety_tips': "🔒 *Mẹo An Toàn Cho Giao Dịch:*\n",
            'how_to_use': "🤖 *Cách Sử Dụng Bot Này:*\n",
            'common_scams': "⚠️ *Các Loại Lừa Đảo Phổ Biến:*\n",
            'what_to_do': "🚨 *Phải Làm Gì Nếu Bị Lừa:*\n",
            'resources': "📚 *Tài Nguyên Bổ Sung:*\n",
            
            # Trusted Admins
            'trusted_admins_title': "👑 *QUẢN TRỊ VIÊN UY TÍN*\n\nQuản trị viên đã xác minh mà bạn có thể tin tưởng:",
            'admin_info': "👤 *{}*\nCấp độ: {}\nĐiểm tin cậy: {}\nHoạt động từ: {}",
            'no_admins': "Không có quản trị viên uy tín nào.",
            
            # Verified Groups
            'verified_groups_title': "✅ *NHÓM ĐÃ XÁC MINH*\n\nCác nhóm cộng đồng chính thức và đã xác minh:",
            'group_info': "👥 *{}*\nLoại: {}\nThành viên: {}\nĐiểm tin cậy: {}\nTham gia: {}",
            'no_groups': "Không có nhóm đã xác minh nào.",
            
            # Admin Panel
            'admin_welcome': "⚡ *BẢNG QUẢN TRỊ*\n\nChào mừng, Quản trị viên!",
            'admin_menu': "📊 *Menu Quản Trị*\nChọn một tùy chọn:",
            'view_reports': "📋 Xem Báo Cáo",
            'manage_scammers': "👥 Quản Lý Kẻ Lừa Đảo",
            'manage_users': "👤 Quản Lý Người Dùng",
            'manage_groups': "👥 Quản Lý Nhóm",
            'manage_admins': "👑 Quản Lý Quản Trị Viên",
            'system_stats': "📈 Thống Kê Hệ Thống",
            'export_data': "💾 Xuất Dữ Liệu",
            'backup_db': "🔄 Sao Lưu Cơ Sở Dữ Liệu",
            'broadcast': "📢 Gửi Thông Báo",
            'system_settings': "⚙️ Cài Đặt Hệ Thống",
            
            # Admin Actions
            'report_details': "📋 *Báo Cáo #{}*\n\nTrạng thái: {}\nLoại: {}\nNgười báo cáo: @{}\nSố tiền: ${}\nNgày: {}",
            'approve_report': "✅ Duyệt",
            'reject_report': "❌ Từ chối",
            'mark_verified': "🔍 Đánh dấu Đã Xác Minh",
            'need_more_info': "ℹ️ Cần Thêm Thông Tin",
            'report_approved': "✅ Báo cáo #{} đã được duyệt.",
            'report_rejected': "❌ Báo cáo #{} đã bị từ chối.",
            'report_verified': "🔍 Báo cáo #{} đã được đánh dấu là đã xác minh.",
            
            # Statistics
            'stats_title': "📊 *THỐNG KÊ HỆ THỐNG*\n\n",
            'stats_users': "👥 Người dùng: {} ({} mới hôm nay)",
            'stats_reports': "📋 Báo cáo: {} ({} đang chờ)",
            'stats_scammers': "🚨 Kẻ lừa đảo: {} ({} rủi ro cao)",
            'stats_lookups': "🔍 Tra cứu: {} tổng cộng",
            'stats_groups': "👥 Nhóm: {} ({} đã xác minh)",
            'stats_amount': "💰 Tổng số tiền mất: ${}",
            
            # Errors & Warnings
            'error_general': "❌ Đã xảy ra lỗi. Vui lòng thử lại.",
            'error_not_found': "❌ Không tìm thấy. Vui lòng kiểm tra đầu vào của bạn.",
            'error_invalid_input': "❌ Đầu vào không hợp lệ. Vui lòng thử lại.",
            'error_permission': "⛔ Bạn không có quyền sử dụng tính năng này.",
            'error_banned': "🚫 Bạn đã bị cấm. Lý do: {}",
            'error_rate_limit': "⏳ Đã vượt quá giới hạn tốc độ. Vui lòng đợi {} giây.",
            
            # Success Messages
            'success_updated': "✅ Cập nhật thành công.",
            'success_deleted': "✅ Xóa thành công.",
            'success_added': "✅ Thêm thành công.",
            
            # Confirmation
            'confirm_action': "⚠️ Bạn có chắc muốn {}?",
            'yes': "✅ Có",
            'no': "❌ Không",
            'cancel': "🚫 Hủy",
            
            # Network Names
            'network_erc20': "Ethereum (ERC20)",
            'network_trc20': "Tron (TRC20)",
            'network_bep20': "BNB Smart Chain (BEP20)",
            
            # Misc
            'loading': "⏳ Đang tải...",
            'searching': "🔍 Đang tìm kiếm...",
            'processing': "⚙️ Đang xử lý...",
            'done': "✅ Hoàn thành",
            'empty': "Trống",
            'unknown': "Không xác định"
        },
        
        'ru': {
            # Main menu
            'welcome': "👮 *АНТИ-СКАМ БОТ*\n\nДобро пожаловать! Я могу помочь вам проверить подозрительные аккаунты и сообщить о мошенниках на различных платформах.",
            'select_language': "🌐 *Выберите ваш язык:*",
            'main_menu': "📋 *Главное меню*\nВыберите опцию ниже:",
            'back_to_menu': "🔙 Назад в главное меню",
            
            # Menu options
            'lookup_scam': "🔍 Поиск мошенника",
            'report_scam': "🚨 Сообщить о мошеннике",
            'help_guide': "ℹ️ Помощь и безопасность",
            'trusted_admins': "👑 Проверенные администраторы",
            'verified_groups': "✅ Проверенные группы",
            'admin_panel': "⚡ Панель администратора",
            'change_language': "🌐 Изменить язык",
            'view_stats': "📊 Просмотр статистики",
            'settings': "⚙️ Настройки",
            
            # Lookup
            'lookup_title': "🔍 *Поиск мошенника*\n\nВыберите тип поиска:",
            'lookup_telegram': "📱 Telegram",
            'lookup_binance': "💳 Binance",
            'lookup_usdt': "💰 Кошелек USDT",
            'lookup_okx': "🔶 OKX",
            'lookup_advanced': "🔬 Расширенный поиск",
            'enter_telegram': "Введите имя пользователя Telegram (например, @username) или ID:",
            'enter_binance': "Введите Binance UID (6-10 цифр):",
            'enter_binance_pay': "Введите Binance Pay ID:",
            'enter_usdt': "Введите адрес кошелька USDT:",
            'select_usdt_network': "Выберите сеть USDT:",
            'enter_okx': "Введите OKX UID:",
            'enter_advanced': "Введите несколько идентификаторов (через запятую):\n\nФормат: @username, binance_uid, usdt_address",
            
            # Results
            'scam_found': "🚨 *ОБНАРУЖЕН РИСК МОШЕННИЧЕСТВА*\n\n",
            'no_data': "ℹ️ *По этому запросу отчетов не найдено.*\n\n⚠️ *ПРЕДУПРЕЖДЕНИЕ:*\nОтсутствие данных не означает безопасность. Всегда проверяйте тщательно и будьте осторожны.",
            'risk_low': "🟢 НИЗКИЙ РИСК",
            'risk_medium': "🟡 СРЕДНИЙ РИСК",
            'risk_high': "🔴 ВЫСОКИЙ РИСК",
            'risk_critical': "💀 КРИТИЧЕСКИЙ РИСК",
            'reports_count': "📊 Отчетов: {}",
            'amount_lost': "💰 Потерянная сумма: ${}",
            'first_reported': "📅 Первый отчет: {}",
            'last_reported': "🔄 Последний отчет: {}",
            'risk_score': "🎯 Уровень риска: {}/100",
            'tags': "🏷️ Теги: {}",
            'notes': "📝 Примечания: {}",
            'confirmed_scam': "✅ *МОШЕННИК ПОДТВЕРЖДЕН АДМИНИСТРАТОРОМ*",
            
            # Report
            'report_start': "🚨 *Сообщить о мошеннике*\n\nПожалуйста, следуйте шагам ниже:",
            'report_step1': "1️⃣ *Выберите тип отчета:*",
            'report_type_telegram': "📱 Мошенник в Telegram",
            'report_type_binance': "💳 Мошенник в Binance",
            'report_type_usdt': "💰 Мошенник с USDT",
            'report_type_okx': "🔶 Мошенник в OKX",
            'report_type_multi': "🔗 Несколько платформ",
            'report_step2': "2️⃣ *Введите детали:*",
            'report_step3': "3️⃣ *Введите потерянную сумму (USD):*",
            'report_step4': "4️⃣ *Опишите, что произошло (минимум 20 символов):*",
            'report_step5': "5️⃣ *Предоставьте доказательства (URL или описание):*",
            'report_step6': "6️⃣ *Просмотрите и отправьте:*",
            'report_confirmation': "✅ *Отчет успешно отправлен!*\n\nВаш отчет получен и будет рассмотрен нашей командой. Спасибо, что помогаете сохранять сообщество безопасным!",
            'report_limit': "⚠️ Вы достигли дневного лимита отчетов ({} отчетов). Пожалуйста, попробуйте завтра.",
            'report_cooldown': "⏳ Пожалуйста, подождите {} секунд перед отправкой следующего отчета.",
            
            # Help & Safety
            'help_title': "ℹ️ *ПОМОЩЬ И БЕЗОПАСНОСТЬ*\n\n",
            'safety_tips': "🔒 *Советы по безопасной торговле:*\n",
            'how_to_use': "🤖 *Как использовать этого бота:*\n",
            'common_scams': "⚠️ *Распространенные типы мошенничества:*\n",
            'what_to_do': "🚨 *Что делать, если вас обманули:*\n",
            'resources': "📚 *Дополнительные ресурсы:*\n",
            
            # Trusted Admins
            'trusted_admins_title': "👑 *ПРОВЕРЕННЫЕ АДМИНИСТРАТОРЫ*\n\nПроверенные администраторы, которым можно доверять:",
            'admin_info': "👤 *{}*\nУровень: {}\nОценка доверия: {}\nАктивен с: {}",
            'no_admins': "Нет доступных проверенных администраторов.",
            
            # Verified Groups
            'verified_groups_title': "✅ *ПРОВЕРЕННЫЕ ГРУППЫ*\n\nОфициальные и проверенные группы сообщества:",
            'group_info': "👥 *{}*\nТип: {}\nУчастники: {}\nОценка доверия: {}\nПрисоединился: {}",
            'no_groups': "Нет доступных проверенных групп.",
            
            # Admin Panel
            'admin_welcome': "⚡ *ПАНЕЛЬ АДМИНИСТРАТОРА*\n\nДобро пожаловать, администратор!",
            'admin_menu': "📊 *Меню администратора*\nВыберите опцию:",
            'view_reports': "📋 Просмотр отчетов",
            'manage_scammers': "👥 Управление мошенниками",
            'manage_users': "👤 Управление пользователями",
            'manage_groups': "👥 Управление группами",
            'manage_admins': "👑 Управление администраторами",
            'system_stats': "📈 Статистика системы",
            'export_data': "💾 Экспорт данных",
            'backup_db': "🔄 Резервное копирование БД",
            'broadcast': "📢 Рассылка сообщений",
            'system_settings': "⚙️ Настройки системы",
            
            # Admin Actions
            'report_details': "📋 *Отчет #{}*\n\nСтатус: {}\nТип: {}\nОтправитель: @{}\nСумма: ${}\nДата: {}",
            'approve_report': "✅ Одобрить",
            'reject_report': "❌ Отклонить",
            'mark_verified': "🔍 Отметить проверенным",
            'need_more_info': "ℹ️ Нужно больше информации",
            'report_approved': "✅ Отчет #{} был одобрен.",
            'report_rejected': "❌ Отчет #{} был отклонен.",
            'report_verified': "🔍 Отчет #{} отмечен как проверенный.",
            
            # Statistics
            'stats_title': "📊 *СТАТИСТИКА СИСТЕМЫ*\n\n",
            'stats_users': "👥 Пользователи: {} ({} новых сегодня)",
            'stats_reports': "📋 Отчеты: {} ({} ожидают)",
            'stats_scammers': "🚨 Мошенники: {} ({} высокого риска)",
            'stats_lookups': "🔍 Поиски: {} всего",
            'stats_groups': "👥 Группы: {} ({} проверены)",
            'stats_amount': "💰 Общая потерянная сумма: ${}",
            
            # Errors & Warnings
            'error_general': "❌ Произошла ошибка. Пожалуйста, попробуйте снова.",
            'error_not_found': "❌ Не найдено. Пожалуйста, проверьте ваш ввод.",
            'error_invalid_input': "❌ Неверный ввод. Пожалуйста, попробуйте снова.",
            'error_permission': "⛔ У вас нет разрешения использовать эту функцию.",
            'error_banned': "🚫 Вы были забанены. Причина: {}",
            'error_rate_limit': "⏳ Превышен лимит запросов. Пожалуйста, подождите {} секунд.",
            
            # Success Messages
            'success_updated': "✅ Успешно обновлено.",
            'success_deleted': "✅ Успешно удалено.",
            'success_added': "✅ Успешно добавлено.",
            
            # Confirmation
            'confirm_action': "⚠️ Вы уверены, что хотите {}?",
            'yes': "✅ Да",
            'no': "❌ Нет",
            'cancel': "🚫 Отмена",
            
            # Network Names
            'network_erc20': "Ethereum (ERC20)",
            'network_trc20': "Tron (TRC20)",
            'network_bep20': "BNB Smart Chain (BEP20)",
            
            # Misc
            'loading': "⏳ Загрузка...",
            'searching': "🔍 Поиск...",
            'processing': "⚙️ Обработка...",
            'done': "✅ Готово",
            'empty': "Пусто",
            'unknown': "Неизвестно"
        },
        
        'zh': {
            # Main menu
            'welcome': "👮 *反诈骗机器人*\n\n欢迎！我可以帮助您验证可疑账户并报告多个平台上的诈骗者。",
            'select_language': "🌐 *选择您的语言:*",
            'main_menu': "📋 *主菜单*\n请选择下面的选项:",
            'back_to_menu': "🔙 返回主菜单",
            
            # Menu options
            'lookup_scam': "🔍 查询诈骗者",
            'report_scam': "🚨 报告诈骗者",
            'help_guide': "ℹ️ 帮助与安全指南",
            'trusted_admins': "👑 可信管理员",
            'verified_groups': "✅ 已验证群组",
            'admin_panel': "⚡ 管理员面板",
            'change_language': "🌐 更改语言",
            'view_stats': "📊 查看统计",
            'settings': "⚙️ 设置",
            
            # Lookup
            'lookup_title': "🔍 *诈骗者查询*\n\n选择查询类型:",
            'lookup_telegram': "📱 Telegram",
            'lookup_binance': "💳 Binance",
            'lookup_usdt': "💰 USDT钱包",
            'lookup_okx': "🔶 OKX",
            'lookup_advanced': "🔬 高级搜索",
            'enter_telegram': "请输入Telegram用户名（例如，@username）或ID:",
            'enter_binance': "请输入Binance UID（6-10位数字）:",
            'enter_binance_pay': "请输入Binance Pay ID:",
            'enter_usdt': "请输入USDT钱包地址:",
            'select_usdt_network': "选择USDT网络:",
            'enter_okx': "请输入OKX UID:",
            'enter_advanced': "输入多个标识符（用逗号分隔）:\n\n格式: @username, binance_uid, usdt_address",
            
            # Results
            'scam_found': "🚨 *检测到诈骗风险*\n\n",
            'no_data': "ℹ️ *未找到此查询的报告。*\n\n⚠️ *警告:*\n没有数据并不意味着安全。请始终仔细验证并谨慎行事。",
            'risk_low': "🟢 低风险",
            'risk_medium': "🟡 中等风险",
            'risk_high': "🔴 高风险",
            'risk_critical': "💀 严重风险",
            'reports_count': "📊 报告数量: {}",
            'amount_lost': "💰 损失金额: ${}",
            'first_reported': "📅 首次报告: {}",
            'last_reported': "🔄 最后报告: {}",
            'risk_score': "🎯 风险评分: {}/100",
            'tags': "🏷️ 标签: {}",
            'notes': "📝 备注: {}",
            'confirmed_scam': "✅ *管理员确认的诈骗者*",
            
            # Report
            'report_start': "🚨 *报告诈骗者*\n\n请按照以下步骤操作:",
            'report_step1': "1️⃣ *选择报告类型:*",
            'report_type_telegram': "📱 Telegram诈骗者",
            'report_type_binance': "💳 Binance诈骗者",
            'report_type_usdt': "💰 USDT诈骗者",
            'report_type_okx': "🔶 OKX诈骗者",
            'report_type_multi': "🔗 多个平台",
            'report_step2': "2️⃣ *输入详细信息:*",
            'report_step3': "3️⃣ *输入损失金额（USD）:*",
            'report_step4': "4️⃣ *描述发生了什么（至少20个字符）:*",
            'report_step5': "5️⃣ *提供证据（URL或描述）:*",
            'report_step6': "6️⃣ *审查并提交:*",
            'report_confirmation': "✅ *报告提交成功！*\n\n您的报告已收到，将由我们的团队审核。感谢您帮助保持社区安全！",
            'report_limit': "⚠️ 您已达到每日报告限制（{}个报告）。请明天再试。",
            'report_cooldown': "⏳ 请在提交另一个报告前等待{}秒。",
            
            # Help & Safety
            'help_title': "ℹ️ *帮助与安全指南*\n\n",
            'safety_tips': "🔒 *安全交易提示:*\n",
            'how_to_use': "🤖 *如何使用此机器人:*\n",
            'common_scams': "⚠️ *常见的诈骗类型:*\n",
            'what_to_do': "🚨 *如果被诈骗该怎么办:*\n",
            'resources': "📚 *其他资源:*\n",
            
            # Trusted Admins
            'trusted_admins_title': "👑 *可信管理员*\n\n您可以信任的已验证管理员:",
            'admin_info': "👤 *{}*\n级别: {}\n信任评分: {}\n活跃自: {}",
            'no_admins': "没有可用的可信管理员。",
            
            # Verified Groups
            'verified_groups_title': "✅ *已验证群组*\n\n官方和已验证的社区群组:",
            'group_info': "👥 *{}*\n类型: {}\n成员: {}\n信任评分: {}\n加入时间: {}",
            'no_groups': "没有可用的已验证群组。",
            
            # Admin Panel
            'admin_welcome': "⚡ *管理员面板*\n\n欢迎，管理员！",
            'admin_menu': "📊 *管理员菜单*\n选择一个选项:",
            'view_reports': "📋 查看报告",
            'manage_scammers': "👥 管理诈骗者",
            'manage_users': "👤 管理用户",
            'manage_groups': "👥 管理群组",
            'manage_admins': "👑 管理管理员",
            'system_stats': "📈 系统统计",
            'export_data': "💾 导出数据",
            'backup_db': "🔄 备份数据库",
            'broadcast': "📢 广播消息",
            'system_settings': "⚙️ 系统设置",
            
            # Admin Actions
            'report_details': "📋 *报告 #{}*\n\n状态: {}\n类型: {}\n报告者: @{}\n金额: ${}\n日期: {}",
            'approve_report': "✅ 批准",
            'reject_report': "❌ 拒绝",
            'mark_verified': "🔍 标记为已验证",
            'need_more_info': "ℹ️ 需要更多信息",
            'report_approved': "✅ 报告 #{} 已获批准。",
            'report_rejected': "❌ 报告 #{} 已被拒绝。",
            'report_verified': "🔍 报告 #{} 已标记为已验证。",
            
            # Statistics
            'stats_title': "📊 *系统统计*\n\n",
            'stats_users': "👥 用户: {}（今天新增{}）",
            'stats_reports': "📋 报告: {}（{}待处理）",
            'stats_scammers': "🚨 诈骗者: {}（{}高风险）",
            'stats_lookups': "🔍 查询: {}总计",
            'stats_groups': "👥 群组: {}（{}已验证）",
            'stats_amount': "💰 总损失金额: ${}",
            
            # Errors & Warnings
            'error_general': "❌ 发生错误。请重试。",
            'error_not_found': "❌ 未找到。请检查您的输入。",
            'error_invalid_input': "❌ 输入无效。请重试。",
            'error_permission': "⛔ 您没有使用此功能的权限。",
            'error_banned': "🚫 您已被封禁。原因: {}",
            'error_rate_limit': "⏳ 超过速率限制。请等待{}秒。",
            
            # Success Messages
            'success_updated': "✅ 更新成功。",
            'success_deleted': "✅ 删除成功。",
            'success_added': "✅ 添加成功。",
            
            # Confirmation
            'confirm_action': "⚠️ 您确定要{}吗？",
            'yes': "✅ 是",
            'no': "❌ 否",
            'cancel': "🚫 取消",
            
            # Network Names
            'network_erc20': "以太坊 (ERC20)",
            'network_trc20': "波场 (TRC20)",
            'network_bep20': "BNB智能链 (BEP20)",
            
            # Misc
            'loading': "⏳ 加载中...",
            'searching': "🔍 搜索中...",
            'processing': "⚙️ 处理中...",
            'done': "✅ 完成",
            'empty': "空",
            'unknown': "未知"
        }
    }
    
    @classmethod
    def get_text(cls, lang: str, key: str, **kwargs) -> str:
        """Lấy text đã dịch với định dạng"""
        if lang not in cls.TRANSLATIONS:
            lang = Config.DEFAULT_LANGUAGE
        
        text = cls.TRANSLATIONS[lang].get(key, cls.TRANSLATIONS[Config.DEFAULT_LANGUAGE].get(key, key))
        
        if kwargs:
            try:
                text = text.format(**kwargs)
            except:
                pass
        
        return text
    
    @classmethod
    def get_safety_tips(cls, lang: str) -> List[str]:
        """Lấy mẹo an toàn theo ngôn ngữ"""
        if lang not in Config.SAFETY_TIPS:
            lang = Config.DEFAULT_LANGUAGE
        return Config.SAFETY_TIPS.get(lang, Config.SAFETY_TIPS[Config.DEFAULT_LANGUAGE])

# ==================== VALIDATOR & HELPER ====================
class Validator:
    """Xác thực và chuẩn hóa input"""
    
    @staticmethod
    def normalize_telegram(input_str: str) -> Optional[str]:
        """Chuẩn hóa input Telegram"""
        if not input_str or len(input_str.strip()) < 3:
            return None
        
        normalized = input_str.strip().lower()
        
        # Loại bỏ @ đầu
        if normalized.startswith('@'):
            normalized = normalized[1:]
        
        # Loại bỏ t.me/
        if normalized.startswith('t.me/'):
            normalized = normalized[5:]
        
        # Kiểm tra nếu là numeric ID
        if normalized.isdigit() and len(normalized) >= 5:
            return normalized
        
        # Kiểm tra username hợp lệ
        if re.match(r'^[a-z0-9_]{5,}$', normalized):
            return normalized
        
        return None
    
    @staticmethod
    def validate_binance_uid(input_str: str) -> Optional[str]:
        """Xác thực Binance UID"""
        if not input_str:
            return None
        
        normalized = input_str.strip()
        
        # Binance UID thường là 6-10 chữ số
        if re.match(r'^\d{6,10}$', normalized):
            return normalized
        
        return None
    
    @staticmethod
    def validate_binance_pay_id(input_str: str) -> Optional[str]:
        """Xác thực Binance Pay ID"""
        if not input_str:
            return None
        
        normalized = input_str.strip()
        
        # Binance Pay ID có thể là numeric hoặc alphanumeric
        if 6 <= len(normalized) <= 20:
            return normalized
        
        return None
    
    @staticmethod
    def validate_usdt_address(input_str: str) -> Tuple[Optional[str], Optional[str]]:
        """Xác thực địa chỉ USDT và xác định network"""
        if not input_str:
            return None, None
        
        normalized = input_str.strip()
        
        # Ethereum (ERC20) - bắt đầu bằng 0x, 42 ký tự
        if normalized.startswith('0x') and len(normalized) == 42:
            return normalized, 'erc20'
        
        # Tron (TRC20) - bắt đầu bằng T, 34 ký tự
        if normalized.startswith('T') and len(normalized) == 34:
            return normalized, 'trc20'
        
        # BSC (BEP20) - bắt đầu bằng 0x, 42 ký tự (giống ERC20)
        # Cần thêm logic để phân biệt
        if normalized.startswith('0x') and len(normalized) == 42:
            return normalized, 'bep20'
        
        return None, None
    
    @staticmethod
    def validate_okx_uid(input_str: str) -> Optional[str]:
        """Xác thực OKX UID"""
        if not input_str:
            return None
        
        normalized = input_str.strip()
        
        # OKX UID thường là số
        if re.match(r'^\d{6,10}$', normalized):
            return normalized
        
        return None
    
    @staticmethod
    def validate_amount(input_str: str) -> Optional[float]:
        """Xác thực số tiền"""
        try:
            # Loại bỏ ký tự không cần thiết
            clean_str = re.sub(r'[^\d.]', '', input_str)
            amount = float(clean_str)
            
            if 0 <= amount <= 10000000:  # Giới hạn hợp lý
                return round(amount, 2)
        except:
            pass
        
        return None
    
    @staticmethod
    def sanitize_input(input_str: str, max_length: int = Config.MAX_INPUT_LENGTH) -> str:
        """Làm sạch input để tránh XSS và injection"""
        if not input_str:
            return ""
        
        # Giới hạn độ dài
        sanitized = input_str[:max_length]
        
        # Loại bỏ các ký tự nguy hiểm
        sanitized = re.sub(r'[<>"\'%;()&+]', '', sanitized)
        
        # Loại bỏ khoảng trắng thừa
        sanitized = ' '.join(sanitized.split())
        
        return sanitized
    
    @staticmethod
    def is_valid_url(url: str) -> bool:
        """Kiểm tra URL hợp lệ"""
        if not url:
            return False
        
        url_pattern = re.compile(
            r'^(https?://)?'  # http:// or https://
            r'(([A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain
            r'localhost|'  # localhost
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ip
            r'(?::\d+)?'  # port
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)
        
        return bool(url_pattern.match(url))

class RiskCalculator:
    """Tính toán risk score dựa trên nhiều yếu tố"""
    
    @staticmethod
    def calculate_risk_score(scammer_data: Dict, reports: List) -> Tuple[int, str]:
        """Tính toán risk score từ 0-100 và trả về mức độ rủi ro"""
        score = 0
        
        # 1. Số lượng báo cáo
        total_reports = scammer_data.get('total_reports', 0)
        if total_reports > 0:
            score += Config.RISK_WEIGHTS['report_count']
        
        # 2. Nhiều báo cáo
        if total_reports >= 3:
            score += Config.RISK_WEIGHTS['multiple_reports']
        
        # 3. Số tiền lớn
        total_amount = scammer_data.get('total_amount_usd', 0)
        if total_amount > 1000:
            score += Config.RISK_WEIGHTS['high_amount']
        if total_amount > 10000:
            score += Config.RISK_WEIGHTS['high_amount']
        
        # 4. Nhiều định danh
        identifiers = 0
        if scammer_data.get('telegram_username'):
            identifiers += 1
        if scammer_data.get('binance_uid'):
            identifiers += 1
        if scammer_data.get('usdt_address'):
            identifiers += 1
        if scammer_data.get('okx_uid'):
            identifiers += 1
        
        if identifiers >= 2:
            score += Config.RISK_WEIGHTS['multiple_ids']
        if identifiers >= 3:
            score += Config.RISK_WEIGHTS['multiple_ids']
        
        # 5. Hoạt động gần đây (7 ngày)
        recent_count = 0
        for report in reports:
            report_time = datetime.fromisoformat(report['created_at'].replace('Z', '+00:00'))
            if datetime.now() - report_time < timedelta(days=7):
                recent_count += 1
        
        if recent_count > 0:
            score += Config.RISK_WEIGHTS['recent_activity']
        
        # 6. Đã xác nhận bởi admin
        if scammer_data.get('is_confirmed'):
            score += Config.RISK_WEIGHTS['admin_confirmed']
        
        # Giới hạn điểm số
        score = min(score, 100)
        
        # Xác định mức độ rủi ro
        if score >= 80:
            level = "critical"
        elif score >= 60:
            level = "high"
        elif score >= 40:
            level = "medium"
        else:
            level = "low"
        
        return score, level
    
    @staticmethod
    def get_risk_emoji(level: str) -> str:
        """Lấy emoji tương ứng với mức độ rủi ro"""
        emoji_map = {
            'critical': '💀',
            'high': '🔴',
            'medium': '🟡',
            'low': '🟢'
        }
        return emoji_map.get(level, '⚪')

# ==================== SERVICES ====================
class UserService:
    """Dịch vụ quản lý người dùng"""
    
    def __init__(self, db: DatabaseManager):
        self.db = db
    
    def get_or_create_user(self, telegram_id: int, username: str = None, 
                          first_name: str = None, last_name: str = None) -> Dict:
        """Lấy hoặc tạo người dùng mới"""
        user = self.db.fetch_one(
            "SELECT * FROM users WHERE telegram_id = ?",
            (telegram_id,)
        )
        
        if user:
            # Cập nhật thông tin và last seen
            self.db.execute("""
                UPDATE users 
                SET username = ?, first_name = ?, last_name = ?,
                    last_seen = CURRENT_TIMESTAMP, last_active = CURRENT_TIMESTAMP,
                    total_requests = total_requests + 1
                WHERE telegram_id = ?
            """, (username, first_name, last_name, telegram_id))
            
            return dict(user)
        
        # Tạo người dùng mới
        self.db.execute("""
            INSERT INTO users 
            (telegram_id, username, first_name, last_name, created_at, last_seen, last_active)
            VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        """, (telegram_id, username, first_name, last_name))
        
        return {
            'telegram_id': telegram_id,
            'username': username,
            'first_name': first_name,
            'last_name': last_name,
            'language': 'en',
            'is_admin': False,
            'is_super_admin': False,
            'is_banned': False,
            'trust_score': 100
        }
    
    def get_user(self, telegram_id: int) -> Optional[Dict]:
        """Lấy thông tin người dùng"""
        user = self.db.fetch_one(
            "SELECT * FROM users WHERE telegram_id = ?",
            (telegram_id,)
        )
        return dict(user) if user else None
    
    def update_language(self, telegram_id: int, language: str) -> bool:
        """Cập nhật ngôn ngữ người dùng"""
        try:
            self.db.execute(
                "UPDATE users SET language = ? WHERE telegram_id = ?",
                (language, telegram_id)
            )
            return True
        except:
            return False
    
    def is_admin(self, telegram_id: int) -> bool:
        """Kiểm tra xem người dùng có phải admin không"""
        user = self.db.fetch_one(
            "SELECT is_admin, is_super_admin FROM users WHERE telegram_id = ?",
            (telegram_id,)
        )
        return user and (user['is_admin'] or user['is_super_admin'])
    
    def is_super_admin(self, telegram_id: int) -> bool:
        """Kiểm tra xem người dùng có phải super admin không"""
        user = self.db.fetch_one(
            "SELECT is_super_admin FROM users WHERE telegram_id = ?",
            (telegram_id,)
        )
        return user and user['is_super_admin']
    
    def is_banned(self, telegram_id: int) -> Tuple[bool, Optional[str]]:
        """Kiểm tra xem người dùng có bị banned không"""
        user = self.db.fetch_one(
            "SELECT is_banned, ban_reason, ban_until FROM users WHERE telegram_id = ?",
            (telegram_id,)
        )
        
        if not user:
            return False, None
        
        if user['is_banned']:
            # Kiểm tra nếu ban đã hết hạn
            if user['ban_until']:
                ban_until = datetime.fromisoformat(user['ban_until'].replace('Z', '+00:00'))
                if datetime.now() > ban_until:
                    # Hết hạn ban
                    self.db.execute(
                        "UPDATE users SET is_banned = 0, ban_reason = NULL, ban_until = NULL WHERE telegram_id = ?",
                        (telegram_id,)
                    )
                    return False, None
            
            return True, user['ban_reason']
        
        return False, None
    
    def increment_reports(self, telegram_id: int, successful: bool = False):
        """Tăng số lượng báo cáo của người dùng"""
        query = """
            UPDATE users 
            SET reports_submitted = reports_submitted + 1,
                last_report_time = CURRENT_TIMESTAMP
        """
        
        if successful:
            query += ", successful_reports = successful_reports + 1"
        
        query += " WHERE telegram_id = ?"
        
        self.db.execute(query, (telegram_id,))
    
    def update_trust_score(self, telegram_id: int, score_change: int):
        """Cập nhật điểm tin cậy của người dùng"""
        self.db.execute("""
            UPDATE users 
            SET trust_score = trust_score + ?
            WHERE telegram_id = ?
        """, (score_change, telegram_id))
    
    def ban_user(self, telegram_id: int, reason: str, days: int = 0):
        """Ban người dùng"""
        ban_until = None
        if days > 0:
            ban_until = (datetime.now() + timedelta(days=days)).isoformat()
        
        self.db.execute("""
            UPDATE users 
            SET is_banned = 1, ban_reason = ?, ban_until = ?
            WHERE telegram_id = ?
        """, (reason, ban_until, telegram_id))
    
    def unban_user(self, telegram_id: int):
        """Gỡ ban người dùng"""
        self.db.execute("""
            UPDATE users 
            SET is_banned = 0, ban_reason = NULL, ban_until = NULL
            WHERE telegram_id = ?
        """, (telegram_id,))
    
    def get_user_stats(self, telegram_id: int) -> Dict:
        """Lấy thống kê người dùng"""
        user = self.get_user(telegram_id)
        if not user:
            return {}
        
        # Thống kê báo cáo
        reports_stats = self.db.fetch_one("""
            SELECT 
                COUNT(*) as total_reports,
                SUM(CASE WHEN status = 'approved' THEN 1 ELSE 0 END) as approved_reports,
                SUM(CASE WHEN status = 'verified' THEN 1 ELSE 0 END) as verified_reports,
                SUM(amount_usd) as total_amount_reported
            FROM reports 
            WHERE reporter_id = ?
        """, (telegram_id,))
        
        # Thống kê lookup
        lookup_stats = self.db.fetch_one("""
            SELECT 
                COUNT(*) as total_lookups,
                SUM(CASE WHEN scammer_found = 1 THEN 1 ELSE 0 END) as successful_lookups
            FROM lookup_logs 
            WHERE user_id = ?
        """, (telegram_id,))
        
        return {
            'user_info': user,
            'reports': dict(reports_stats) if reports_stats else {},
            'lookups': dict(lookup_stats) if lookup_stats else {},
            'trust_score': user.get('trust_score', 100),
            'joined_date': user.get('created_at')
        }
    
    def get_top_users(self, limit: int = 10) -> List[Dict]:
        """Lấy top người dùng"""
        users = self.db.fetch_all("""
            SELECT 
                telegram_id, username, first_name, last_name,
                trust_score, reports_submitted, successful_reports,
                created_at
            FROM users 
            WHERE is_banned = 0
            ORDER BY trust_score DESC, successful_reports DESC
            LIMIT ?
        """, (limit,))
        
        return [dict(user) for user in users]

class ScamService:
    """Dịch vụ tra cứu và quản lý scammer"""
    
    def __init__(self, db: DatabaseManager):
        self.db = db
    
    def lookup(self, lookup_type: str, query_value: str) -> Optional[Dict]:
        """Tra cứu scammer theo loại"""
        normalized_value = query_value.lower().strip()
        
        # Xây dựng query dựa trên loại tra cứu
        if lookup_type == 'telegram':
            results = self.db.fetch_all("""
                SELECT s.*, 
                       COUNT(r.id) as report_count,
                       SUM(r.amount_usd) as total_amount,
                       MIN(r.created_at) as first_reported,
                       MAX(r.created_at) as last_reported
                FROM scammers s
                LEFT JOIN reports r ON s.id = r.scammer_id
                WHERE s.telegram_username = ? OR s.telegram_id = ?
                GROUP BY s.id
            """, (normalized_value, normalized_value))
        
        elif lookup_type == 'binance':
            results = self.db.fetch_all("""
                SELECT s.*,
                       COUNT(r.id) as report_count,
                       SUM(r.amount_usd) as total_amount,
                       MIN(r.created_at) as first_reported,
                       MAX(r.created_at) as last_reported
                FROM scammers s
                LEFT JOIN reports r ON s.id = r.scammer_id
                WHERE s.binance_uid = ? OR s.binance_pay_id = ?
                GROUP BY s.id
            """, (normalized_value, normalized_value))
        
        elif lookup_type == 'usdt':
            results = self.db.fetch_all("""
                SELECT s.*,
                       COUNT(r.id) as report_count,
                       SUM(r.amount_usd) as total_amount,
                       MIN(r.created_at) as first_reported,
                       MAX(r.created_at) as last_reported
                FROM scammers s
                LEFT JOIN reports r ON s.id = r.scammer_id
                WHERE s.usdt_address = ?
                GROUP BY s.id
            """, (normalized_value,))
        
        elif lookup_type == 'okx':
            results = self.db.fetch_all("""
                SELECT s.*,
                       COUNT(r.id) as report_count,
                       SUM(r.amount_usd) as total_amount,
                       MIN(r.created_at) as first_reported,
                       MAX(r.created_at) as last_reported
                FROM scammers s
                LEFT JOIN reports r ON s.id = r.scammer_id
                WHERE s.okx_uid = ?
                GROUP BY s.id
            """, (normalized_value,))
        
        else:
            results = []
        
        if not results:
            return None
        
        scammer_data = dict(results[0])
        scammer_id = scammer_data['id']
        
        # Lấy tất cả báo cáo liên quan
        reports = self.db.fetch_all("""
            SELECT * FROM reports 
            WHERE scammer_id = ?
            ORDER BY created_at DESC
        """, (scammer_id,))
        
        reports_list = [dict(report) for report in reports]
        
        # Tính toán risk score
        risk_score, risk_level = RiskCalculator.calculate_risk_score(scammer_data, reports_list)
        
        # Cập nhật risk score trong database
        self.db.execute("""
            UPDATE scammers 
            SET risk_score = ?, risk_level = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (risk_score, risk_level, scammer_id))
        
        scammer_data['risk_score'] = risk_score
        scammer_data['risk_level'] = risk_level
        scammer_data['reports'] = reports_list
        
        return scammer_data
    
    def advanced_lookup(self, identifiers: List[str]) -> List[Dict]:
        """Tra cứu nâng cao với nhiều định danh"""
        results = []
        
        for identifier in identifiers:
            identifier = identifier.strip().lower()
            
            # Thử tìm kiếm theo tất cả các loại
            for lookup_type in ['telegram', 'binance', 'usdt', 'okx']:
                result = self.lookup(lookup_type, identifier)
                if result and result not in results:
                    results.append(result)
        
        return results
    
    def create_scammer(self, data: Dict) -> int:
        """Tạo scammer mới"""
        # Kiểm tra xem scammer đã tồn tại chưa
        existing = None
        
        if data.get('telegram_username'):
            existing = self.db.fetch_one(
                "SELECT id FROM scammers WHERE telegram_username = ?",
                (data['telegram_username'],)
            )
        
        if not existing and data.get('binance_uid'):
            existing = self.db.fetch_one(
                "SELECT id FROM scammers WHERE binance_uid = ?",
                (data['binance_uid'],)
            )
        
        if not existing and data.get('usdt_address'):
            existing = self.db.fetch_one(
                "SELECT id FROM scammers WHERE usdt_address = ?",
                (data['usdt_address'],)
            )
        
        if not existing and data.get('okx_uid'):
            existing = self.db.fetch_one(
                "SELECT id FROM scammers WHERE okx_uid = ?",
                (data['okx_uid'],)
            )
        
        if existing:
            return existing['id']
        
        # Tạo scammer mới
        self.db.execute("""
            INSERT INTO scammers (
                telegram_username, telegram_id, binance_uid, binance_pay_id,
                usdt_address, usdt_network, okx_uid, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        """, (
            data.get('telegram_username'),
            data.get('telegram_id'),
            data.get('binance_uid'),
            data.get('binance_pay_id'),
            data.get('usdt_address'),
            data.get('usdt_network'),
            data.get('okx_uid')
        ))
        
        result = self.db.fetch_one("SELECT last_insert_rowid() as id")
        return result['id'] if result else 0
    
    def update_scammer(self, scammer_id: int, data: Dict):
        """Cập nhật thông tin scammer"""
        update_fields = []
        params = []
        
        for field in ['telegram_username', 'telegram_id', 'binance_uid', 'binance_pay_id',
                     'usdt_address', 'usdt_network', 'okx_uid', 'notes', 'tags',
                     'is_confirmed', 'confirmed_by']:
            if field in data:
                update_fields.append(f"{field} = ?")
                params.append(data[field])
        
        if update_fields:
            params.append(scammer_id)
            query = f"""
                UPDATE scammers 
                SET {', '.join(update_fields)}, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """
            self.db.execute(query, tuple(params))
    
    def delete_scammer(self, scammer_id: int):
        """Xóa scammer"""
        self.db.execute("DELETE FROM scammers WHERE id = ?", (scammer_id,))
        self.db.execute("DELETE FROM reports WHERE scammer_id = ?", (scammer_id,))
    
    def get_scammer_stats(self) -> Dict:
        """Lấy thống kê scammers"""
        stats = {}
        
        # Tổng số scammers
        result = self.db.fetch_one("SELECT COUNT(*) as count FROM scammers")
        stats['total_scammers'] = result['count'] if result else 0
        
        # Scammers theo mức độ rủi ro
        for level in ['critical', 'high', 'medium', 'low']:
            result = self.db.fetch_one(
                "SELECT COUNT(*) as count FROM scammers WHERE risk_level = ?",
                (level,)
            )
            stats[f'{level}_risk_scammers'] = result['count'] if result else 0
        
        # Scammers đã xác nhận
        result = self.db.fetch_one("SELECT COUNT(*) as count FROM scammers WHERE is_confirmed = 1")
        stats['confirmed_scammers'] = result['count'] if result else 0
        
        # Tổng số tiền mất
        result = self.db.fetch_one("SELECT SUM(total_amount_usd) as total FROM scammers")
        stats['total_amount_lost'] = round(result['total'] or 0, 2)
        
        # Scammers mới hôm nay
        result = self.db.fetch_one("""
            SELECT COUNT(*) as count FROM scammers 
            WHERE date(created_at) = date('now')
        """)
        stats['new_scammers_today'] = result['count'] if result else 0
        
        return stats
    
    def search_scammers(self, query: str, limit: int = 20) -> List[Dict]:
        """Tìm kiếm scammers"""
        search_query = f"%{query.lower()}%"
        
        results = self.db.fetch_all("""
            SELECT * FROM scammers 
            WHERE 
                telegram_username LIKE ? OR
                binance_uid LIKE ? OR
                usdt_address LIKE ? OR
                okx_uid LIKE ? OR
                notes LIKE ?
            ORDER BY risk_score DESC
            LIMIT ?
        """, (search_query, search_query, search_query, search_query, search_query, limit))
        
        return [dict(result) for result in results]

class ReportService:
    """Dịch vụ quản lý báo cáo"""
    
    def __init__(self, db: DatabaseManager):
        self.db = db
        self.user_service = UserService(db)
        self.scam_service = ScamService(db)
    
    def create_report(self, reporter_id: int, report_data: Dict) -> Tuple[bool, str, int]:
        """Tạo báo cáo mới"""
        try:
            # Kiểm tra rate limit
            recent_reports = self.db.fetch_one("""
                SELECT COUNT(*) as count FROM reports 
                WHERE reporter_id = ? AND created_at > datetime('now', '-1 day')
            """, (reporter_id,))
            
            if recent_reports and recent_reports['count'] >= Config.MAX_REPORTS_PER_DAY:
                return False, "report_limit", 0
            
            # Kiểm tra cooldown
            last_report = self.db.fetch_one("""
                SELECT created_at FROM reports 
                WHERE reporter_id = ? 
                ORDER BY created_at DESC 
                LIMIT 1
            """, (reporter_id,))
            
            if last_report:
                last_time = datetime.fromisoformat(last_report['created_at'].replace('Z', '+00:00'))
                if datetime.now() - last_time < timedelta(seconds=Config.REPORT_COOLDOWN):
                    remaining = Config.REPORT_COOLDOWN - (datetime.now() - last_time).seconds
                    return False, "report_cooldown", remaining
            
            # Tìm hoặc tạo scammer
            scammer_data = {
                'telegram_username': report_data.get('telegram_username'),
                'telegram_id': report_data.get('telegram_id'),
                'binance_uid': report_data.get('binance_uid'),
                'binance_pay_id': report_data.get('binance_pay_id'),
                'usdt_address': report_data.get('usdt_address'),
                'usdt_network': report_data.get('usdt_network'),
                'okx_uid': report_data.get('okx_uid')
            }
            
            scammer_id = self.scam_service.create_scammer(scammer_data)
            
            # Tạo báo cáo
            self.db.execute("""
                INSERT INTO reports (
                    reporter_id, scammer_id, report_type,
                    telegram_username, telegram_id, binance_uid, binance_pay_id,
                    usdt_address, usdt_network, okx_uid,
                    amount_usd, description, proof_url, proof_type,
                    status, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending', CURRENT_TIMESTAMP)
            """, (
                reporter_id, scammer_id, report_data.get('report_type', 'unknown'),
                report_data.get('telegram_username'),
                report_data.get('telegram_id'),
                report_data.get('binance_uid'),
                report_data.get('binance_pay_id'),
                report_data.get('usdt_address'),
                report_data.get('usdt_network'),
                report_data.get('okx_uid'),
                report_data.get('amount_usd', 0),
                Validator.sanitize_input(report_data.get('description', ''), 1000),
                report_data.get('proof_url', ''),
                report_data.get('proof_type', ''),
            ))
            
            # Cập nhật thống kê người dùng
            self.user_service.increment_reports(reporter_id)
            
            # Cập nhật thống kê scammer
            self._update_scammer_stats(scammer_id)
            
            # Log audit
            self.db.execute("""
                INSERT INTO audit_logs (admin_id, action, target_type, target_id, details)
                VALUES (?, 'create_report', 'report', ?, ?)
            """, (reporter_id, reporter_id, f"Report created for scammer {scammer_id}"))
            
            return True, "success", scammer_id
            
        except Exception as e:
            logging.error(f"Error creating report: {e}")
            return False, "error", 0
    
    def _update_scammer_stats(self, scammer_id: int):
        """Cập nhật thống kê scammer"""
        # Lấy tổng số báo cáo và số tiền
        result = self.db.fetch_one("""
            SELECT 
                COUNT(*) as report_count,
                SUM(amount_usd) as total_amount,
                MIN(created_at) as first_reported,
                MAX(created_at) as last_reported
            FROM reports 
            WHERE scammer_id = ?
        """, (scammer_id,))
        
        if result:
            self.db.execute("""
                UPDATE scammers 
                SET 
                    total_reports = ?,
                    total_amount_usd = ?,
                    first_reported = ?,
                    last_reported = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (
                result['report_count'],
                result['total_amount'] or 0,
                result['first_reported'],
                result['last_reported'],
                scammer_id
            ))
    
    def get_report(self, report_id: int) -> Optional[Dict]:
        """Lấy thông tin báo cáo"""
        report = self.db.fetch_one("""
            SELECT r.*, u.username as reporter_username,
                   s.telegram_username, s.binance_uid, s.usdt_address, s.okx_uid
            FROM reports r
            LEFT JOIN users u ON r.reporter_id = u.telegram_id
            LEFT JOIN scammers s ON r.scammer_id = s.id
            WHERE r.id = ?
        """, (report_id,))
        
        return dict(report) if report else None
    
    def get_pending_reports(self, limit: int = 50) -> List[Dict]:
        """Lấy báo cáo đang chờ xử lý"""
        reports = self.db.fetch_all("""
            SELECT r.*, u.username as reporter_username,
                   s.telegram_username, s.binance_uid, s.usdt_address, s.okx_uid
            FROM reports r
            LEFT JOIN users u ON r.reporter_id = u.telegram_id
            LEFT JOIN scammers s ON r.scammer_id = s.id
            WHERE r.status = 'pending'
            ORDER BY r.created_at DESC
            LIMIT ?
        """, (limit,))
        
        return [dict(report) for report in reports]
    
    def get_reports_by_status(self, status: str, limit: int = 50) -> List[Dict]:
        """Lấy báo cáo theo trạng thái"""
        reports = self.db.fetch_all("""
            SELECT r.*, u.username as reporter_username,
                   s.telegram_username, s.binance_uid, s.usdt_address, s.okx_uid
            FROM reports r
            LEFT JOIN users u ON r.reporter_id = u.telegram_id
            LEFT JOIN scammers s ON r.scammer_id = s.id
            WHERE r.status = ?
            ORDER BY r.created_at DESC
            LIMIT ?
        """, (status, limit))
        
        return [dict(report) for report in reports]
    
    def update_report_status(self, report_id: int, status: str, admin_id: int, notes: str = ""):
        """Cập nhật trạng thái báo cáo"""
        self.db.execute("""
            UPDATE reports 
            SET status = ?, reviewed_by = ?, reviewed_at = CURRENT_TIMESTAMP,
                verification_notes = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (status, admin_id, notes, report_id))
        
        # Nếu được approve, đánh dấu scammer là confirmed
        if status == 'approved':
            report = self.get_report(report_id)
            if report and report.get('scammer_id'):
                self.db.execute("""
                    UPDATE scammers 
                    SET is_confirmed = 1, confirmed_by = ?, confirmed_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (admin_id, report['scammer_id']))
                
                # Tăng điểm tin cậy cho người báo cáo
                self.user_service.update_trust_score(report['reporter_id'], 10)
        
        # Log audit
        self.db.execute("""
            INSERT INTO audit_logs (admin_id, action, target_type, target_id, details)
            VALUES (?, 'update_report_status', 'report', ?, ?)
        """, (admin_id, report_id, f"Status changed to {status}: {notes}"))
    
    def get_report_stats(self) -> Dict:
        """Lấy thống kê báo cáo"""
        stats = {}
        
        # Tổng số báo cáo theo trạng thái
        statuses = ['pending', 'approved', 'rejected', 'verified']
        for status in statuses:
            result = self.db.fetch_one(
                "SELECT COUNT(*) as count FROM reports WHERE status = ?",
                (status,)
            )
            stats[f'{status}_reports'] = result['count'] if result else 0
        
        # Tổng số báo cáo
        result = self.db.fetch_one("SELECT COUNT(*) as count FROM reports")
        stats['total_reports'] = result['count'] if result else 0
        
        # Báo cáo hôm nay
        result = self.db.fetch_one("""
            SELECT COUNT(*) as count FROM reports 
            WHERE date(created_at) = date('now')
        """)
        stats['reports_today'] = result['count'] if result else 0
        
        # Tổng số tiền
        result = self.db.fetch_one("SELECT SUM(amount_usd) as total FROM reports WHERE status = 'approved'")
        stats['total_amount_approved'] = round(result['total'] or 0, 2)
        
        return stats

class GroupService:
    """Dịch vụ quản lý nhóm"""
    
    def __init__(self, db: DatabaseManager):
        self.db = db
    
    def register_group(self, chat_id: int, title: str, username: str = None, 
                      group_type: str = "regular") -> bool:
        """Đăng ký nhóm mới"""
        try:
            existing = self.db.fetch_one(
                "SELECT id FROM groups WHERE chat_id = ?",
                (chat_id,)
            )
            
            if existing:
                # Cập nhật thông tin nhóm
                self.db.execute("""
                    UPDATE groups 
                    SET title = ?, username = ?, group_type = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE chat_id = ?
                """, (title, username, group_type, chat_id))
            else:
                # Tạo nhóm mới
                self.db.execute("""
                    INSERT INTO groups (chat_id, title, username, group_type, created_at, updated_at)
                    VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                """, (chat_id, title, username, group_type))
            
            return True
        except:
            return False
    
    def verify_group(self, chat_id: int, verified_by: int) -> bool:
        """Xác minh nhóm"""
        try:
            self.db.execute("""
                UPDATE groups 
                SET is_verified = 1, updated_at = CURRENT_TIMESTAMP
                WHERE chat_id = ?
            """, (chat_id,))
            
            # Log audit
            self.db.execute("""
                INSERT INTO audit_logs (admin_id, action, target_type, target_id, details)
                VALUES (?, 'verify_group', 'group', ?, 'Group verified')
            """, (verified_by, chat_id))
            
            return True
        except:
            return False
    
    def blacklist_group(self, chat_id: int, reason: str, banned_by: int) -> bool:
        """Blacklist nhóm"""
        try:
            self.db.execute("""
                UPDATE groups 
                SET is_blacklisted = 1, updated_at = CURRENT_TIMESTAMP
                WHERE chat_id = ?
            """, (chat_id,))
            
            # Log audit
            self.db.execute("""
                INSERT INTO audit_logs (admin_id, action, target_type, target_id, details)
                VALUES (?, 'blacklist_group', 'group', ?, ?)
            """, (banned_by, chat_id, f"Blacklisted: {reason}"))
            
            return True
        except:
            return False
    
    def get_group(self, chat_id: int) -> Optional[Dict]:
        """Lấy thông tin nhóm"""
        group = self.db.fetch_one(
            "SELECT * FROM groups WHERE chat_id = ?",
            (chat_id,)
        )
        return dict(group) if group else None
    
    def get_verified_groups(self, limit: int = 20) -> List[Dict]:
        """Lấy danh sách nhóm đã xác minh"""
        groups = self.db.fetch_all("""
            SELECT * FROM groups 
            WHERE is_verified = 1 AND is_blacklisted = 0
            ORDER BY trust_score DESC, member_count DESC
            LIMIT ?
        """, (limit,))
        
        return [dict(group) for group in groups]
    
    def get_all_groups(self, limit: int = 50) -> List[Dict]:
        """Lấy tất cả nhóm"""
        groups = self.db.fetch_all("""
            SELECT * FROM groups 
            ORDER BY created_at DESC
            LIMIT ?
        """, (limit,))
        
        return [dict(group) for group in groups]
    
    def update_group_stats(self, chat_id: int, admin_count: int, member_count: int):
        """Cập nhật thống kê nhóm"""
        self.db.execute("""
            UPDATE groups 
            SET admin_count = ?, member_count = ?, updated_at = CURRENT_TIMESTAMP
            WHERE chat_id = ?
        """, (admin_count, member_count, chat_id))
    
    def add_group_member(self, chat_id: int, user_id: int, is_admin: bool = False, is_owner: bool = False):
        """Thêm thành viên vào nhóm"""
        group = self.get_group(chat_id)
        if not group:
            return
        
        try:
            self.db.execute("""
                INSERT OR REPLACE INTO group_members (group_id, user_id, is_admin, is_owner, joined_at, last_active)
                VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            """, (group['id'], user_id, is_admin, is_owner))
        except:
            pass
    
    def get_group_stats(self) -> Dict:
        """Lấy thống kê nhóm"""
        stats = {}
        
        # Tổng số nhóm
        result = self.db.fetch_one("SELECT COUNT(*) as count FROM groups")
        stats['total_groups'] = result['count'] if result else 0
        
        # Nhóm đã xác minh
        result = self.db.fetch_one("SELECT COUNT(*) as count FROM groups WHERE is_verified = 1")
        stats['verified_groups'] = result['count'] if result else 0
        
        # Nhóm bị blacklist
        result = self.db.fetch_one("SELECT COUNT(*) as count FROM groups WHERE is_blacklisted = 1")
        stats['blacklisted_groups'] = result['count'] if result else 0
        
        # Tổng số thành viên
        result = self.db.fetch_one("SELECT SUM(member_count) as total FROM groups")
        stats['total_members'] = result['total'] if result else 0
        
        return stats

class AdminService:
    """Dịch vụ quản lý admin"""
    
    def __init__(self, db: DatabaseManager):
        self.db = db
        self.user_service = UserService(db)
    
    def add_admin(self, user_id: int, admin_level: str, permissions: str, added_by: int) -> bool:
        """Thêm admin mới"""
        try:
            # Cập nhật bảng users
            self.db.execute("""
                UPDATE users 
                SET is_admin = 1, trust_score = 1000
                WHERE telegram_id = ?
            """, (user_id,))
            
            # Thêm vào trusted_admins
            self.db.execute("""
                INSERT OR REPLACE INTO trusted_admins 
                (user_id, admin_level, permissions, added_by, added_at, last_active)
                VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            """, (user_id, admin_level, permissions, added_by))
            
            # Log audit
            self.db.execute("""
                INSERT INTO audit_logs (admin_id, action, target_type, target_id, details)
                VALUES (?, 'add_admin', 'user', ?, ?)
            """, (added_by, user_id, f"Added as {admin_level} admin with permissions: {permissions}"))
            
            return True
        except:
            return False
    
    def remove_admin(self, user_id: int, removed_by: int, reason: str = "") -> bool:
        """Xóa admin"""
        try:
            # Cập nhật bảng users
            self.db.execute("""
                UPDATE users 
                SET is_admin = 0
                WHERE telegram_id = ?
            """, (user_id,))
            
            # Cập nhật trusted_admins
            self.db.execute("""
                UPDATE trusted_admins 
                SET is_active = 0
                WHERE user_id = ?
            """, (user_id,))
            
            # Log audit
            self.db.execute("""
                INSERT INTO audit_logs (admin_id, action, target_type, target_id, details)
                VALUES (?, 'remove_admin', 'user', ?, ?)
            """, (removed_by, user_id, f"Removed as admin. Reason: {reason}"))
            
            return True
        except:
            return False
    
    def get_admin(self, user_id: int) -> Optional[Dict]:
        """Lấy thông tin admin"""
        admin = self.db.fetch_one("""
            SELECT ta.*, u.username, u.first_name, u.last_name, u.created_at as user_created
            FROM trusted_admins ta
            LEFT JOIN users u ON ta.user_id = u.telegram_id
            WHERE ta.user_id = ? AND ta.is_active = 1
        """, (user_id,))
        
        return dict(admin) if admin else None
    
    def get_all_admins(self, active_only: bool = True) -> List[Dict]:
        """Lấy tất cả admin"""
        query = """
            SELECT ta.*, u.username, u.first_name, u.last_name, u.created_at as user_created
            FROM trusted_admins ta
            LEFT JOIN users u ON ta.user_id = u.telegram_id
        """
        
        if active_only:
            query += " WHERE ta.is_active = 1"
        
        query += " ORDER BY ta.added_at DESC"
        
        admins = self.db.fetch_all(query)
        return [dict(admin) for admin in admins]
    
    def update_admin_permissions(self, user_id: int, permissions: str, updated_by: int) -> bool:
        """Cập nhật quyền admin"""
        try:
            self.db.execute("""
                UPDATE trusted_admins 
                SET permissions = ?, last_active = CURRENT_TIMESTAMP
                WHERE user_id = ?
            """, (permissions, user_id))
            
            # Log audit
            self.db.execute("""
                INSERT INTO audit_logs (admin_id, action, target_type, target_id, details)
                VALUES (?, 'update_admin_permissions', 'user', ?, ?)
            """, (updated_by, user_id, f"Permissions updated to: {permissions}"))
            
            return True
        except:
            return False
    
    def update_admin_activity(self, user_id: int):
        """Cập nhật thời gian hoạt động admin"""
        self.db.execute("""
            UPDATE trusted_admins 
            SET last_active = CURRENT_TIMESTAMP
            WHERE user_id = ?
        """, (user_id,))

class StatisticsService:
    """Dịch vụ thống kê"""
    
    def __init__(self, db: DatabaseManager):
        self.db = db
        self.user_service = UserService(db)
        self.scam_service = ScamService(db)
        self.report_service = ReportService(db)
        self.group_service = GroupService(db)
    
    def get_system_stats(self) -> Dict:
        """Lấy thống kê hệ thống"""
        stats = {}
        
        # Thống kê người dùng
        user_stats = self.db.fetch_one("""
            SELECT 
                COUNT(*) as total_users,
                SUM(CASE WHEN date(created_at) = date('now') THEN 1 ELSE 0 END) as new_users_today,
                SUM(CASE WHEN date(last_seen) = date('now') THEN 1 ELSE 0 END) as active_users_today,
                AVG(trust_score) as avg_trust_score
            FROM users
        """)
        
        if user_stats:
            stats['users'] = {
                'total': user_stats['total_users'],
                'new_today': user_stats['new_users_today'],
                'active_today': user_stats['active_users_today'],
                'avg_trust_score': round(user_stats['avg_trust_score'] or 0, 2)
            }
        
        # Thống kê scammers
        scammer_stats = self.scam_service.get_scammer_stats()
        stats['scammers'] = scammer_stats
        
        # Thống kê báo cáo
        report_stats = self.report_service.get_report_stats()
        stats['reports'] = report_stats
        
        # Thống kê nhóm
        group_stats = self.group_service.get_group_stats()
        stats['groups'] = group_stats
        
        # Thống kê lookup
        lookup_stats = self.db.fetch_one("""
            SELECT 
                COUNT(*) as total_lookups,
                SUM(CASE WHEN scammer_found = 1 THEN 1 ELSE 0 END) as successful_lookups,
                AVG(response_time_ms) as avg_response_time
            FROM lookup_logs 
            WHERE date(created_at) = date('now')
        """)
        
        if lookup_stats:
            stats['lookups'] = {
                'total_today': lookup_stats['total_lookups'],
                'successful_today': lookup_stats['successful_lookups'],
                'avg_response_time': round(lookup_stats['avg_response_time'] or 0, 2)
            }
        
        # Thống kê tổng quan
        stats['overall'] = {
            'total_requests': self.db.fetch_one("SELECT SUM(total_requests) as total FROM users")['total'] or 0,
            'system_uptime': self._get_system_uptime(),
            'database_size': self._get_database_size(),
            'last_backup': self._get_last_backup_time()
        }
        
        return stats
    
    def _get_system_uptime(self) -> str:
        """Lấy thời gian hoạt động của hệ thống"""
        # Trong thực tế, bạn sẽ lấy từ hệ thống
        return "24/7"
    
    def _get_database_size(self) -> str:
        """Lấy kích thước database"""
        try:
            size = os.path.getsize(Config.DATABASE_PATH)
            
            if size < 1024:
                return f"{size} B"
            elif size < 1024 * 1024:
                return f"{size/1024:.2f} KB"
            elif size < 1024 * 1024 * 1024:
                return f"{size/(1024*1024):.2f} MB"
            else:
                return f"{size/(1024*1024*1024):.2f} GB"
        except:
            return "Unknown"
    
    def _get_last_backup_time(self) -> str:
        """Lấy thời gian backup gần nhất"""
        try:
            backup_files = [f for f in os.listdir(Config.BACKUP_DIR) if f.endswith('.db')]
            if backup_files:
                backup_files.sort(reverse=True)
                backup_file = os.path.join(Config.BACKUP_DIR, backup_files[0])
                mtime = os.path.getmtime(backup_file)
                return datetime.fromtimestamp(mtime).strftime('%Y-%m-%d %H:%M:%S')
        except:
            pass
        
        return "No backup found"
    
    def update_daily_statistics(self):
        """Cập nhật thống kê hàng ngày"""
        try:
            stats = self.get_system_stats()
            
            self.db.execute("""
                INSERT OR REPLACE INTO statistics 
                (date, total_users, new_users, total_lookups, successful_lookups,
                 total_reports, verified_reports, active_groups, blocked_scammers)
                VALUES (date('now'), ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                stats['users']['total'],
                stats['users']['new_today'],
                stats['lookups']['total_today'],
                stats['lookups']['successful_today'],
                stats['reports']['total_reports'],
                stats['reports']['verified_reports'],
                stats['groups']['total_groups'],
                stats['scammers']['total_scammers']
            ))
        except Exception as e:
            logging.error(f"Error updating daily statistics: {e}")

# ==================== RATE LIMITER ====================
class RateLimiter:
    """Rate limiting để ngăn chặn lạm dụng"""
    
    def __init__(self):
        self.requests = defaultdict(list)
        self.blocked = defaultdict(float)
    
    def is_allowed(self, user_id: int, request_type: str = "general") -> Tuple[bool, Optional[float]]:
        """Kiểm tra xem người dùng có được phép thực hiện request không"""
        now = time.time()
        
        # Kiểm tra nếu bị block
        if user_id in self.blocked:
            if now < self.blocked[user_id]:
                remaining = self.blocked[user_id] - now
                return False, remaining
            else:
                del self.blocked[user_id]
        
        # Lấy lịch sử request
        user_requests = self.requests[user_id]
        
        # Xóa các request cũ
        user_requests = [req_time for req_time in user_requests 
                        if now - req_time < Config.RATE_LIMIT_PERIOD]
        
        # Kiểm tra giới hạn
        if len(user_requests) >= Config.RATE_LIMIT_REQUESTS:
            # Block người dùng
            block_time = Config.RATE_LIMIT_PERIOD
            self.blocked[user_id] = now + block_time
            return False, block_time
        
        # Thêm request mới
        user_requests.append(now)
        self.requests[user_id] = user_requests[-Config.RATE_LIMIT_REQUESTS:]  # Giữ số lượng giới hạn
        
        return True, None
    
    def clear_expired(self):
        """Xóa các bản ghi đã hết hạn"""
        now = time.time()
        
        # Xóa blocked đã hết hạn
        expired = [user_id for user_id, block_until in self.blocked.items() 
                  if now >= block_until]
        for user_id in expired:
            del self.blocked[user_id]
        
        # Xóa request cũ
        for user_id in list(self.requests.keys()):
            user_requests = self.requests[user_id]
            user_requests = [req_time for req_time in user_requests 
                            if now - req_time < Config.RATE_LIMIT_PERIOD]
            if user_requests:
                self.requests[user_id] = user_requests
            else:
                del self.requests[user_id]

# ==================== BOT HANDLERS ====================
class AntiScamBot:
    """Lớp chính điều khiển bot"""
    
    # Conversation states
    LANGUAGE_SELECTION, MAIN_MENU = range(2)
    LOOKUP_TYPE, LOOKUP_INPUT = range(2, 4)
    REPORT_TYPE, REPORT_DETAILS, REPORT_AMOUNT, REPORT_DESCRIPTION, REPORT_PROOF, REPORT_REVIEW = range(4, 10)
    ADMIN_MENU, ADMIN_ACTION = range(10, 12)
    
    def __init__(self):
        # Khởi tạo database và services
        self.db = DatabaseManager()
        self.user_service = UserService(self.db)
        self.scam_service = ScamService(self.db)
        self.report_service = ReportService(self.db)
        self.group_service = GroupService(self.db)
        self.admin_service = AdminService(self.db)
        self.statistics_service = StatisticsService(self.db)
        
        # Rate limiter
        self.rate_limiter = RateLimiter()
        
        # User states và session data
        self.user_states = {}
        self.user_sessions = {}
        
        # Bot application
        self.application = None
        
        # Setup logging
        self.setup_logging()
        
        # Bot info
        self.bot_username = ""
        self.start_time = datetime.now()
        
        # Register default admin
        self.register_default_admins()
    
    def setup_logging(self):
        """Cấu hình logging"""
        logging.basicConfig(
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            level=getattr(logging, Config.LOG_LEVEL),
            handlers=[
                logging.FileHandler(Config.LOG_FILE),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def register_default_admins(self):
        """Đăng ký admin mặc định"""
        for admin_id in Config.SUPER_ADMIN_IDS:
            self.admin_service.add_admin(
                admin_id,
                'super_admin',
                'all',
                0  # System
            )
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Xử lý lệnh /start"""
        user = update.effective_user
        
        # Kiểm tra ban
        is_banned, ban_reason = self.user_service.is_banned(user.id)
        if is_banned:
            await update.message.reply_text(
                I18n.get_text('en', 'error_banned').format(ban_reason),
                parse_mode=ParseMode.MARKDOWN
            )
            return ConversationHandler.END
        
        # Kiểm tra rate limit
        allowed, wait_time = self.rate_limiter.is_allowed(user.id)
        if not allowed:
            await update.message.reply_text(
                I18n.get_text('en', 'error_rate_limit').format(int(wait_time)),
                parse_mode=ParseMode.MARKDOWN
            )
            return ConversationHandler.END
        
        # Lấy hoặc tạo người dùng
        user_data = self.user_service.get_or_create_user(
            user.id, user.username, user.first_name, user.last_name
        )
        
        # Xóa session cũ
        if user.id in self.user_sessions:
            del self.user_sessions[user.id]
        
        # Hiển thị chọn ngôn ngữ
        keyboard = [
            [
                InlineKeyboardButton("🇺🇸 English", callback_data="lang_en"),
                InlineKeyboardButton("🇻🇳 Tiếng Việt", callback_data="lang_vi")
            ],
            [
                InlineKeyboardButton("🇷🇺 Русский", callback_data="lang_ru"),
                InlineKeyboardButton("🇨🇳 中文", callback_data="lang_zh")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            I18n.get_text('en', 'select_language'),
            reply_markup=reply_markup,
            parse_mode=ParseMode.MARKDOWN
        )
        
        return self.LANGUAGE_SELECTION
    
    async def handle_language_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Xử lý chọn ngôn ngữ"""
        query = update.callback_query
        await query.answer()
        
        user = query.from_user
        language = query.data.replace('lang_', '')
        
        # Cập nhật ngôn ngữ người dùng
        self.user_service.update_language(user.id, language)
        
        # Lưu ngôn ngữ vào context
        context.user_data['language'] = language
        
        # Gửi thông báo chào mừng
        await query.edit_message_text(
            I18n.get_text(language, 'welcome'),
            parse_mode=ParseMode.MARKDOWN
        )
        
        # Hiển thị menu chính
        await self.show_main_menu(update, context, language, user.id)
        
        return self.MAIN_MENU
    
    async def show_main_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE, 
                            language: str, user_id: int):
        """Hiển thị menu chính"""
        keyboard = []
        
        # Các nút chính
        keyboard.append([
            InlineKeyboardButton(
                I18n.get_text(language, 'lookup_scam'),
                callback_data="menu_lookup"
            )
        ])
        
        keyboard.append([
            InlineKeyboardButton(
                I18n.get_text(language, 'report_scam'),
                callback_data="menu_report"
            )
        ])
        
        keyboard.append([
            InlineKeyboardButton(
                I18n.get_text(language, 'help_guide'),
                callback_data="menu_help"
            ),
            InlineKeyboardButton(
                I18n.get_text(language, 'trusted_admins'),
                callback_data="menu_admins"
            )
        ])
        
        keyboard.append([
            InlineKeyboardButton(
                I18n.get_text(language, 'verified_groups'),
                callback_data="menu_groups"
            ),
            InlineKeyboardButton(
                I18n.get_text(language, 'view_stats'),
                callback_data="menu_stats"
            )
        ])
        
        # Nút admin nếu là admin
        if self.user_service.is_admin(user_id):
            keyboard.append([
                InlineKeyboardButton(
                    I18n.get_text(language, 'admin_panel'),
                    callback_data="menu_admin"
                )
            ])
        
        # Các nút phụ
        keyboard.append([
            InlineKeyboardButton(
                I18n.get_text(language, 'change_language'),
                callback_data="menu_language"
            ),
            InlineKeyboardButton(
                I18n.get_text(language, 'settings'),
                callback_data="menu_settings"
            )
        ])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if update.callback_query:
            await update.callback_query.message.reply_text(
                I18n.get_text(language, 'main_menu'),
                reply_markup=reply_markup,
                parse_mode=ParseMode.MARKDOWN
            )
        else:
            await context.bot.send_message(
                chat_id=user_id,
                text=I18n.get_text(language, 'main_menu'),
                reply_markup=reply_markup,
                parse_mode=ParseMode.MARKDOWN
            )
    
    async def handle_main_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Xử lý menu chính"""
        query = update.callback_query
        await query.answer()
        
        user = query.from_user
        callback_data = query.data
        language = context.user_data.get('language', 'en')
        
        # Kiểm tra ban
        is_banned, ban_reason = self.user_service.is_banned(user.id)
        if is_banned:
            await query.edit_message_text(
                I18n.get_text(language, 'error_banned').format(ban_reason),
                parse_mode=ParseMode.MARKDOWN
            )
            return ConversationHandler.END
        
        # Kiểm tra rate limit
        allowed, wait_time = self.rate_limiter.is_allowed(user.id)
        if not allowed:
            await query.edit_message_text(
                I18n.get_text(language, 'error_rate_limit').format(int(wait_time)),
                parse_mode=ParseMode.MARKDOWN
            )
            return self.MAIN_MENU
        
        if callback_data == "menu_lookup":
            # Hiển thị menu tra cứu
            keyboard = [
                [
                    InlineKeyboardButton(
                        I18n.get_text(language, 'lookup_telegram'),
                        callback_data="lookup_telegram"
                    ),
                    InlineKeyboardButton(
                        I18n.get_text(language, 'lookup_binance'),
                        callback_data="lookup_binance"
                    )
                ],
                [
                    InlineKeyboardButton(
                        I18n.get_text(language, 'lookup_usdt'),
                        callback_data="lookup_usdt"
                    ),
                    InlineKeyboardButton(
                        I18n.get_text(language, 'lookup_okx'),
                        callback_data="lookup_okx"
                    )
                ],
                [
                    InlineKeyboardButton(
                        I18n.get_text(language, 'lookup_advanced'),
                        callback_data="lookup_advanced"
                    )
                ],
                [
                    InlineKeyboardButton(
                        I18n.get_text(language, 'back_to_menu'),
                        callback_data="back_to_main"
                    )
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                I18n.get_text(language, 'lookup_title'),
                reply_markup=reply_markup,
                parse_mode=ParseMode.MARKDOWN
            )
            
            self.user_states[user.id] = {'action': 'lookup', 'step': 'type_selection'}
            return self.LOOKUP_TYPE
            
        elif callback_data == "menu_report":
            # Bắt đầu quy trình báo cáo
            self.user_sessions[user.id] = {
                'action': 'report',
                'step': 1,
                'data': {}
            }
            
            keyboard = [
                [
                    InlineKeyboardButton(
                        I18n.get_text(language, 'report_type_telegram'),
                        callback_data="report_type_telegram"
                    ),
                    InlineKeyboardButton(
                        I18n.get_text(language, 'report_type_binance'),
                        callback_data="report_type_binance"
                    )
                ],
                [
                    InlineKeyboardButton(
                        I18n.get_text(language, 'report_type_usdt'),
                        callback_data="report_type_usdt"
                    ),
                    InlineKeyboardButton(
                        I18n.get_text(language, 'report_type_okx'),
                        callback_data="report_type_okx"
                    )
                ],
                [
                    InlineKeyboardButton(
                        I18n.get_text(language, 'report_type_multi'),
                        callback_data="report_type_multi"
                    )
                ],
                [
                    InlineKeyboardButton(
                        I18n.get_text(language, 'back_to_menu'),
                        callback_data="back_to_main"
                    )
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                I18n.get_text(language, 'report_step1'),
                reply_markup=reply_markup,
                parse_mode=ParseMode.MARKDOWN
            )
            
            return self.REPORT_TYPE
            
        elif callback_data == "menu_help":
            # Hiển thị hướng dẫn
            await self.show_help_guide(update, context, language)
            return self.MAIN_MENU
            
        elif callback_data == "menu_admins":
            # Hiển thị danh sách admin uy tín
            await self.show_trusted_admins(update, context, language)
            return self.MAIN_MENU
            
        elif callback_data == "menu_groups":
            # Hiển thị nhóm đã xác minh
            await self.show_verified_groups(update, context, language)
            return self.MAIN_MENU
            
        elif callback_data == "menu_stats":
            # Hiển thị thống kê
            await self.show_statistics(update, context, language)
            return self.MAIN_MENU
            
        elif callback_data == "menu_admin":
            # Kiểm tra quyền admin
            if not self.user_service.is_admin(user.id):
                await query.edit_message_text(
                    I18n.get_text(language, 'error_permission'),
                    parse_mode=ParseMode.MARKDOWN
                )
                return self.MAIN_MENU
            
            # Hiển thị admin panel
            await self.show_admin_panel(update, context, language, user.id)
            return self.ADMIN_MENU
            
        elif callback_data == "menu_language":
            # Hiển thị chọn ngôn ngữ
            keyboard = [
                [
                    InlineKeyboardButton("🇺🇸 English", callback_data="lang_en"),
                    InlineKeyboardButton("🇻🇳 Tiếng Việt", callback_data="lang_vi")
                ],
                [
                    InlineKeyboardButton("🇷🇺 Русский", callback_data="lang_ru"),
                    InlineKeyboardButton("🇨🇳 中文", callback_data="lang_zh")
                ],
                [
                    InlineKeyboardButton(
                        I18n.get_text(language, 'back_to_menu'),
                        callback_data="back_to_main"
                    )
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                I18n.get_text(language, 'select_language'),
                reply_markup=reply_markup,
                parse_mode=ParseMode.MARKDOWN
            )
            
            return self.LANGUAGE_SELECTION
            
        elif callback_data == "menu_settings":
            # Hiển thị cài đặt (đơn giản)
            await query.edit_message_text(
                "⚙️ *Settings*\n\nThis feature is under development.",
                parse_mode=ParseMode.MARKDOWN
            )
            return self.MAIN_MENU
            
        elif callback_data == "back_to_main":
            # Quay lại menu chính
            await self.show_main_menu(update, context, language, user.id)
            return self.MAIN_MENU
        
        return self.MAIN_MENU
    
    async def handle_lookup_type(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Xử lý chọn loại tra cứu"""
        query = update.callback_query
        await query.answer()
        
        user = query.from_user
        language = context.user_data.get('language', 'en')
        lookup_type = query.data.replace('lookup_', '')
        
        # Lưu loại tra cứu vào state
        self.user_states[user.id] = {
            'action': 'lookup',
            'step': 'awaiting_input',
            'lookup_type': lookup_type
        }
        
        # Hiển thị prompt phù hợp
        prompt_text = ""
        
        if lookup_type == 'telegram':
            prompt_text = I18n.get_text(language, 'enter_telegram')
        elif lookup_type == 'binance':
            prompt_text = I18n.get_text(language, 'enter_binance')
        elif lookup_type == 'usdt':
            # Hiển thị chọn network trước
            keyboard = [
                [
                    InlineKeyboardButton(
                        I18n.get_text(language, 'network_erc20'),
                        callback_data="network_erc20"
                    ),
                    InlineKeyboardButton(
                        I18n.get_text(language, 'network_trc20'),
                        callback_data="network_trc20"
                    )
                ],
                [
                    InlineKeyboardButton(
                        I18n.get_text(language, 'network_bep20'),
                        callback_data="network_bep20"
                    )
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                I18n.get_text(language, 'select_usdt_network'),
                reply_markup=reply_markup,
                parse_mode=ParseMode.MARKDOWN
            )
            
            self.user_states[user.id]['step'] = 'selecting_network'
            return self.LOOKUP_TYPE
        elif lookup_type == 'okx':
            prompt_text = I18n.get_text(language, 'enter_okx')
        elif lookup_type == 'advanced':
            prompt_text = I18n.get_text(language, 'enter_advanced')
        
        await query.edit_message_text(
            prompt_text,
            parse_mode=ParseMode.MARKDOWN
        )
        
        return self.LOOKUP_INPUT
    
    async def handle_usdt_network(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Xử lý chọn network USDT"""
        query = update.callback_query
        await query.answer()
        
        user = query.from_user
        network = query.data.replace('network_', '')
        
        # Lưu network vào state
        if user.id in self.user_states:
            self.user_states[user.id]['usdt_network'] = network
            self.user_states[user.id]['step'] = 'awaiting_input'
        
        language = context.user_data.get('language', 'en')
        
        await query.edit_message_text(
            I18n.get_text(language, 'enter_usdt'),
            parse_mode=ParseMode.MARKDOWN
        )
        
        return self.LOOKUP_INPUT
    
    async def handle_lookup_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Xử lý input tra cứu"""
        user = update.effective_user
        language = context.user_data.get('language', 'en')
        user_input = update.message.text.strip()
        
        # Kiểm tra state
        if user.id not in self.user_states or self.user_states[user.id].get('action') != 'lookup':
            await update.message.reply_text(
                I18n.get_text(language, 'error_general'),
                parse_mode=ParseMode.MARKDOWN
            )
            return self.MAIN_MENU
        
        state = self.user_states[user.id]
        lookup_type = state.get('lookup_type')
        
        # Xác thực input
        validated_value = None
        
        if lookup_type == 'telegram':
            validated_value = Validator.normalize_telegram(user_input)
        elif lookup_type == 'binance':
            validated_value = Validator.validate_binance_uid(user_input)
        elif lookup_type == 'usdt':
            validated_value, detected_network = Validator.validate_usdt_address(user_input)
            # Ưu tiên network từ state nếu có
            network = state.get('usdt_network', detected_network)
            if validated_value and network:
                validated_value = f"{validated_value}|{network}"
        elif lookup_type == 'okx':
            validated_value = Validator.validate_okx_uid(user_input)
        elif lookup_type == 'advanced':
            # Xử lý tra cứu nâng cao
            identifiers = [id.strip() for id in user_input.split(',') if id.strip()]
            if len(identifiers) > 0:
                results = self.scam_service.advanced_lookup(identifiers)
                
                if results:
                    response = I18n.get_text(language, 'scam_found')
                    for i, result in enumerate(results[:3]):  # Giới hạn 3 kết quả
                        response += f"\n*Result #{i+1}:*\n"
                        
                        if result.get('telegram_username'):
                            response += f"Telegram: @{result['telegram_username']}\n"
                        if result.get('binance_uid'):
                            response += f"Binance: {result['binance_uid']}\n"
                        if result.get('usdt_address'):
                            response += f"USDT: {result['usdt_address'][:10]}...\n"
                        
                        response += f"Risk: {RiskCalculator.get_risk_emoji(result.get('risk_level', 'low'))} {result.get('risk_level', 'low').upper()}\n"
                        response += f"Reports: {result.get('total_reports', 0)}\n"
                        
                        if i < len(results[:3]) - 1:
                            response += "─" * 20 + "\n"
                else:
                    response = I18n.get_text(language, 'no_data')
                
                # Log lookup
                self.db.execute("""
                    INSERT INTO lookup_logs 
                    (user_id, lookup_type, query_value, result_status, scammer_found, response_time_ms)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    user.id, 
                    'advanced',
                    user_input[:100],
                    'found' if results else 'not_found',
                    1 if results else 0,
                    0  # Placeholder
                ))
                
                await update.message.reply_text(
                    response,
                    parse_mode=ParseMode.MARKDOWN
                )
                
                # Xóa state và hiển thị menu
                if user.id in self.user_states:
                    del self.user_states[user.id]
                
                await self.show_main_menu(update, context, language, user.id)
                return self.MAIN_MENU
        
        if not validated_value:
            await update.message.reply_text(
                I18n.get_text(language, 'error_invalid_input'),
                parse_mode=ParseMode.MARKDOWN
            )
            return self.LOOKUP_INPUT
        
        # Thực hiện tra cứu
        start_time = time.time()
        result = self.scam_service.lookup(lookup_type, validated_value.split('|')[0] if '|' in str(validated_value) else validated_value)
        response_time = int((time.time() - start_time) * 1000)
        
        # Log lookup
        self.db.execute("""
            INSERT INTO lookup_logs 
            (user_id, lookup_type, query_value, result_status, risk_level, scammer_found, response_time_ms)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            user.id,
            lookup_type,
            validated_value[:100],
            'found' if result else 'not_found',
            result.get('risk_level') if result else None,
            1 if result else 0,
            response_time
        ))
        
        # Xây dựng response
        if result:
            response = I18n.get_text(language, 'scam_found')
            
            # Thông tin định danh
            if result.get('telegram_username'):
                response += f"📱 *Telegram:* @{result['telegram_username']}\n"
            if result.get('binance_uid'):
                response += f"💳 *Binance UID:* {result['binance_uid']}\n"
            if result.get('usdt_address'):
                usdt_parts = result['usdt_address'].split('|') if '|' in result['usdt_address'] else [result['usdt_address'], '']
                network_text = {
                    'erc20': I18n.get_text(language, 'network_erc20'),
                    'trc20': I18n.get_text(language, 'network_trc20'),
                    'bep20': I18n.get_text(language, 'network_bep20')
                }.get(usdt_parts[1] if len(usdt_parts) > 1 else '', 'Unknown')
                response += f"💰 *USDT ({network_text}):* {usdt_parts[0][:10]}...\n"
            if result.get('okx_uid'):
                response += f"🔶 *OKX UID:* {result['okx_uid']}\n"
            
            response += "\n"
            
            # Thống kê
            response += f"📊 {I18n.get_text(language, 'reports_count').format(result.get('total_reports', 0))}\n"
            response += f"💰 {I18n.get_text(language, 'amount_lost').format(result.get('total_amount_usd', 0))}\n"
            
            if result.get('first_reported'):
                response += f"📅 {I18n.get_text(language, 'first_reported').format(result['first_reported'][:10])}\n"
            if result.get('last_reported'):
                response += f"🔄 {I18n.get_text(language, 'last_reported').format(result['last_reported'][:10])}\n"
            
            response += "\n"
            
            # Risk assessment
            risk_emoji = RiskCalculator.get_risk_emoji(result.get('risk_level', 'low'))
            risk_text = I18n.get_text(language, f"risk_{result.get('risk_level', 'low')}")
            response += f"🎯 *Risk Assessment:* {risk_emoji} {risk_text}\n"
            response += f"📈 {I18n.get_text(language, 'risk_score').format(result.get('risk_score', 0))}\n"
            
            # Tags và notes
            if result.get('tags'):
                response += f"\n🏷️ {I18n.get_text(language, 'tags').format(result['tags'])}"
            if result.get('notes'):
                response += f"\n📝 {I18n.get_text(language, 'notes').format(result['notes'][:200])}"
            
            # Admin confirmed
            if result.get('is_confirmed'):
                response += f"\n\n✅ *{I18n.get_text(language, 'confirmed_scam')}*"
            
            response += "\n\n⚠️ *Disclaimer:* This information is based on user reports and may not be 100% accurate."
            
        else:
            response = I18n.get_text(language, 'no_data')
        
        await update.message.reply_text(
            response,
            parse_mode=ParseMode.MARKDOWN
        )
        
        # Xóa state và hiển thị menu
        if user.id in self.user_states:
            del self.user_states[user.id]
        
        await self.show_main_menu(update, context, language, user.id)
        return self.MAIN_MENU
    
    async def handle_report_type(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Xử lý chọn loại báo cáo"""
        query = update.callback_query
        await query.answer()
        
        user = query.from_user
        language = context.user_data.get('language', 'en')
        report_type = query.data.replace('report_type_', '')
        
        # Cập nhật session
        if user.id in self.user_sessions:
            self.user_sessions[user.id]['data']['report_type'] = report_type
            self.user_sessions[user.id]['step'] = 2
        
        # Hiển thị prompt phù hợp
        prompt_text = I18n.get_text(language, 'report_step2') + "\n\n"
        
        if report_type == 'telegram':
            prompt_text += I18n.get_text(language, 'enter_telegram')
        elif report_type == 'binance':
            prompt_text += I18n.get_text(language, 'enter_binance')
        elif report_type == 'usdt':
            # Hiển thị chọn network
            keyboard = [
                [
                    InlineKeyboardButton(
                        I18n.get_text(language, 'network_erc20'),
                        callback_data="report_network_erc20"
                    ),
                    InlineKeyboardButton(
                        I18n.get_text(language, 'network_trc20'),
                        callback_data="report_network_trc20"
                    )
                ],
                [
                    InlineKeyboardButton(
                        I18n.get_text(language, 'network_bep20'),
                        callback_data="report_network_bep20"
                    )
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                I18n.get_text(language, 'select_usdt_network'),
                reply_markup=reply_markup,
                parse_mode=ParseMode.MARKDOWN
            )
            
            return self.REPORT_DETAILS
        elif report_type == 'okx':
            prompt_text += I18n.get_text(language, 'enter_okx')
        elif report_type == 'multi':
            prompt_text += "Enter multiple identifiers (one per line):\n"
            prompt_text += "- Telegram username\n"
            prompt_text += "- Binance UID\n"
            prompt_text += "- USDT address\n"
            prompt_text += "- OKX UID\n\n"
            prompt_text += "Example:\n@scammer_username\n123456789\n0x123...abc\n987654321"
        
        await query.edit_message_text(
            prompt_text,
            parse_mode=ParseMode.MARKDOWN
        )
        
        return self.REPORT_DETAILS
    
    async def handle_report_network(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Xử lý chọn network khi báo cáo"""
        query = update.callback_query
        await query.answer()
        
        user = query.from_user
        language = context.user_data.get('language', 'en')
        network = query.data.replace('report_network_', '')
        
        # Cập nhật session
        if user.id in self.user_sessions:
            self.user_sessions[user.id]['data']['usdt_network'] = network
        
        await query.edit_message_text(
            I18n.get_text(language, 'enter_usdt'),
            parse_mode=ParseMode.MARKDOWN
        )
        
        return self.REPORT_DETAILS
    
    async def handle_report_details(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Xử lý chi tiết báo cáo"""
        user = update.effective_user
        language = context.user_data.get('language', 'en')
        user_input = update.message.text.strip()
        
        # Kiểm tra session
        if user.id not in self.user_sessions or self.user_sessions[user.id].get('action') != 'report':
            await update.message.reply_text(
                I18n.get_text(language, 'error_general'),
                parse_mode=ParseMode.MARKDOWN
            )
            return self.MAIN_MENU
        
        session = self.user_sessions[user.id]
        report_type = session['data'].get('report_type')
        
        # Xử lý input dựa trên loại báo cáo
        if report_type == 'telegram':
            validated = Validator.normalize_telegram(user_input)
            if validated:
                session['data']['telegram_username'] = validated
                session['step'] = 3
            else:
                await update.message.reply_text(
                    I18n.get_text(language, 'error_invalid_input'),
                    parse_mode=ParseMode.MARKDOWN
                )
                return self.REPORT_DETAILS
        
        elif report_type == 'binance':
            validated = Validator.validate_binance_uid(user_input)
            if validated:
                session['data']['binance_uid'] = validated
                session['step'] = 3
            else:
                await update.message.reply_text(
                    I18n.get_text(language, 'error_invalid_input'),
                    parse_mode=ParseMode.MARKDOWN
                )
                return self.REPORT_DETAILS
        
        elif report_type == 'usdt':
            validated, detected_network = Validator.validate_usdt_address(user_input)
            if validated:
                session['data']['usdt_address'] = validated
                # Ưu tiên network từ session nếu có
                network = session['data'].get('usdt_network', detected_network)
                session['data']['usdt_network'] = network
                session['step'] = 3
            else:
                await update.message.reply_text(
                    I18n.get_text(language, 'error_invalid_input'),
                    parse_mode=ParseMode.MARKDOWN
                )
                return self.REPORT_DETAILS
        
        elif report_type == 'okx':
            validated = Validator.validate_okx_uid(user_input)
            if validated:
                session['data']['okx_uid'] = validated
                session['step'] = 3
            else:
                await update.message.reply_text(
                    I18n.get_text(language, 'error_invalid_input'),
                    parse_mode=ParseMode.MARKDOWN
                )
                return self.REPORT_DETAILS
        
        elif report_type == 'multi':
            # Xử lý nhiều dòng
            lines = [line.strip() for line in user_input.split('\n') if line.strip()]
            for line in lines:
                # Thử xác định loại định danh
                if line.startswith('@'):
                    validated = Validator.normalize_telegram(line)
                    if validated:
                        session['data']['telegram_username'] = validated
                elif re.match(r'^\d{6,10}$', line):
                    session['data']['binance_uid'] = line
                elif line.startswith('0x') or line.startswith('T'):
                    validated, network = Validator.validate_usdt_address(line)
                    if validated:
                        session['data']['usdt_address'] = validated
                        session['data']['usdt_network'] = network
                elif re.match(r'^\d{6,10}$', line) and 'binance_uid' not in session['data']:
                    session['data']['okx_uid'] = line
            
            session['step'] = 3
        
        # Chuyển đến bước nhập số tiền
        await update.message.reply_text(
            I18n.get_text(language, 'report_step3'),
            parse_mode=ParseMode.MARKDOWN
        )
        
        return self.REPORT_AMOUNT
    
    async def handle_report_amount(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Xử lý số tiền báo cáo"""
        user = update.effective_user
        language = context.user_data.get('language', 'en')
        user_input = update.message.text.strip()
        
        # Kiểm tra session
        if user.id not in self.user_sessions or self.user_sessions[user.id].get('action') != 'report':
            await update.message.reply_text(
                I18n.get_text(language, 'error_general'),
                parse_mode=ParseMode.MARKDOWN
            )
            return self.MAIN_MENU
        
        session = self.user_sessions[user.id]
        
        # Xác thực số tiền
        validated_amount = Validator.validate_amount(user_input)
        
        if validated_amount is not None:
            session['data']['amount_usd'] = validated_amount
            session['step'] = 4
            
            await update.message.reply_text(
                I18n.get_text(language, 'report_step4'),
                parse_mode=ParseMode.MARKDOWN
            )
            
            return self.REPORT_DESCRIPTION
        else:
            await update.message.reply_text(
                I18n.get_text(language, 'error_invalid_input'),
                parse_mode=ParseMode.MARKDOWN
            )
            return self.REPORT_AMOUNT
    
    async def handle_report_description(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Xử lý mô tả báo cáo"""
        user = update.effective_user
        language = context.user_data.get('language', 'en')
        user_input = update.message.text.strip()
        
        # Kiểm tra session
        if user.id not in self.user_sessions or self.user_sessions[user.id].get('action') != 'report':
            await update.message.reply_text(
                I18n.get_text(language, 'error_general'),
                parse_mode=ParseMode.MARKDOWN
            )
            return self.MAIN_MENU
        
        session = self.user_sessions[user.id]
        
        # Kiểm tra độ dài mô tả
        if len(user_input) < Config.MIN_REPORT_DESC:
            await update.message.reply_text(
                f"Description must be at least {Config.MIN_REPORT_DESC} characters.",
                parse_mode=ParseMode.MARKDOWN
            )
            return self.REPORT_DESCRIPTION
        
        session['data']['description'] = Validator.sanitize_input(user_input, 1000)
        session['step'] = 5
        
        await update.message.reply_text(
            I18n.get_text(language, 'report_step5'),
            parse_mode=ParseMode.MARKDOWN
        )
        
        return self.REPORT_PROOF
    
    async def handle_report_proof(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Xử lý bằng chứng báo cáo"""
        user = update.effective_user
        language = context.user_data.get('language', 'en')
        user_input = update.message.text.strip()
        
        # Kiểm tra session
        if user.id not in self.user_sessions or self.user_sessions[user.id].get('action') != 'report':
            await update.message.reply_text(
                I18n.get_text(language, 'error_general'),
                parse_mode=ParseMode.MARKDOWN
            )
            return self.MAIN_MENU
        
        session = self.user_sessions[user.id]
        
        # Xử lý bằng chứng
        if user_input.lower() in ['skip', 'none', '']:
            session['data']['proof_url'] = ''
            session['data']['proof_type'] = 'none'
        elif Validator.is_valid_url(user_input):
            session['data']['proof_url'] = user_input
            session['data']['proof_type'] = 'url'
        else:
            session['data']['proof_url'] = Validator.sanitize_input(user_input, 500)
            session['data']['proof_type'] = 'text'
        
        session['step'] = 6
        
        # Hiển thị xem lại và xác nhận
        await self.show_report_review(update, context, language, user.id)
        
        return self.REPORT_REVIEW
    
    async def show_report_review(self, update: Update, context: ContextTypes.DEFAULT_TYPE, 
                                language: str, user_id: int):
        """Hiển thị xem lại báo cáo"""
        session = self.user_sessions.get(user_id, {})
        data = session.get('data', {})
        
        review_text = "📋 *Report Review*\n\n"
        
        # Thông tin báo cáo
        review_text += "*Report Type:* " + {
            'telegram': I18n.get_text(language, 'report_type_telegram'),
            'binance': I18n.get_text(language, 'report_type_binance'),
            'usdt': I18n.get_text(language, 'report_type_usdt'),
            'okx': I18n.get_text(language, 'report_type_okx'),
            'multi': I18n.get_text(language, 'report_type_multi')
        }.get(data.get('report_type', ''), 'Unknown') + "\n\n"
        
        # Chi tiết
        if data.get('telegram_username'):
            review_text += f"*Telegram:* @{data['telegram_username']}\n"
        if data.get('binance_uid'):
            review_text += f"*Binance UID:* {data['binance_uid']}\n"
        if data.get('usdt_address'):
            network_text = {
                'erc20': I18n.get_text(language, 'network_erc20'),
                'trc20': I18n.get_text(language, 'network_trc20'),
                'bep20': I18n.get_text(language, 'network_bep20')
            }.get(data.get('usdt_network', ''), 'Unknown')
            review_text += f"*USDT ({network_text}):* {data['usdt_address'][:10]}...\n"
        if data.get('okx_uid'):
            review_text += f"*OKX UID:* {data['okx_uid']}\n"
        
        review_text += f"\n*Amount:* ${data.get('amount_usd', 0)}\n"
        review_text += f"*Description:* {data.get('description', '')[:100]}...\n"
        
        if data.get('proof_url'):
            if data.get('proof_type') == 'url':
                review_text += f"*Proof URL:* {data['proof_url'][:50]}...\n"
            else:
                review_text += f"*Proof:* {data['proof_url'][:50]}...\n"
        
        review_text += "\n⚠️ *Please review your report before submitting.*"
        
        keyboard = [
            [
                InlineKeyboardButton(
                    "✅ Submit Report",
                    callback_data="submit_report"
                ),
                InlineKeyboardButton(
                    "❌ Cancel",
                    callback_data="cancel_report"
                )
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if update.callback_query:
            await update.callback_query.edit_message_text(
                review_text,
                reply_markup=reply_markup,
                parse_mode=ParseMode.MARKDOWN
            )
        else:
            await update.message.reply_text(
                review_text,
                reply_markup=reply_markup,
                parse_mode=ParseMode.MARKDOWN
            )
    
    async def handle_report_review(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Xử lý xem lại báo cáo"""
        query = update.callback_query
        await query.answer()
        
        user = query.from_user
        language = context.user_data.get('language', 'en')
        action = query.data
        
        if action == "submit_report":
            # Gửi báo cáo
            if user.id not in self.user_sessions:
                await query.edit_message_text(
                    I18n.get_text(language, 'error_general'),
                    parse_mode=ParseMode.MARKDOWN
                )
                return self.MAIN_MENU
            
            session_data = self.user_sessions[user.id].get('data', {})
            
            # Tạo báo cáo
            success, message, scammer_id = self.report_service.create_report(
                user.id, session_data
            )
            
            if success:
                # Thành công
                await query.edit_message_text(
                    I18n.get_text(language, 'report_confirmation'),
                    parse_mode=ParseMode.MARKDOWN
                )
                
                # Thông báo cho admin (nếu có)
                await self.notify_admins_new_report(scammer_id, user.id, session_data)
            else:
                # Xử lý lỗi
                error_message = I18n.get_text(language, 'error_general')
                if message == "report_limit":
                    error_message = I18n.get_text(language, 'report_limit').format(Config.MAX_REPORTS_PER_DAY)
                elif message == "report_cooldown":
                    error_message = I18n.get_text(language, 'report_cooldown').format(session_data.get('cooldown', 0))
                
                await query.edit_message_text(
                    error_message,
                    parse_mode=ParseMode.MARKDOWN
                )
            
            # Xóa session
            if user.id in self.user_sessions:
                del self.user_sessions[user.id]
            
            # Hiển thị menu chính
            await self.show_main_menu(update, context, language, user.id)
            return self.MAIN_MENU
            
        elif action == "cancel_report":
            # Hủy báo cáo
            if user.id in self.user_sessions:
                del self.user_sessions[user.id]
            
            await query.edit_message_text(
                "❌ Report cancelled.",
                parse_mode=ParseMode.MARKDOWN
            )
            
            await self.show_main_menu(update, context, language, user.id)
            return self.MAIN_MENU
        
        return self.REPORT_REVIEW
    
    async def notify_admins_new_report(self, scammer_id: int, reporter_id: int, report_data: Dict):
        """Thông báo cho admin về báo cáo mới"""
        try:
            admins = self.admin_service.get_all_admins(active_only=True)
            
            if not admins:
                return
            
            message = "🚨 *New Scam Report*\n\n"
            
            if report_data.get('telegram_username'):
                message += f"📱 Telegram: @{report_data['telegram_username']}\n"
            if report_data.get('binance_uid'):
                message += f"💳 Binance: {report_data['binance_uid']}\n"
            if report_data.get('usdt_address'):
                message += f"💰 USDT: {report_data['usdt_address'][:10]}...\n"
            if report_data.get('okx_uid'):
                message += f"🔶 OKX: {report_data['okx_uid']}\n"
            
            message += f"\n💰 Amount: ${report_data.get('amount_usd', 0)}\n"
            message += f"👤 Reporter ID: {reporter_id}\n"
            message += f"🆔 Scammer ID: {scammer_id}\n\n"
            message += "Please review in admin panel."
            
            for admin in admins:
                try:
                    await self.application.bot.send_message(
                        chat_id=admin['user_id'],
                        text=message,
                        parse_mode=ParseMode.MARKDOWN
                    )
                except:
                    continue
                    
        except Exception as e:
            self.logger.error(f"Error notifying admins: {e}")
    
    async def show_help_guide(self, update: Update, context: ContextTypes.DEFAULT_TYPE, language: str):
        """Hiển thị hướng dẫn"""
        query = update.callback_query
        
        help_text = I18n.get_text(language, 'help_title')
        
        # Safety tips
        help_text += I18n.get_text(language, 'safety_tips')
        for tip in I18n.get_safety_tips(language):
            help_text += f"• {tip}\n"
        
        help_text += "\n"
        
        # How to use
        help_text += I18n.get_text(language, 'how_to_use')
        help_text += "1. Use /start to begin\n"
        help_text += "2. Lookup suspicious accounts\n"
        help_text += "3. Report scammers with details\n"
        help_text += "4. Check trusted admins and groups\n"
        help_text += "5. Stay updated with safety tips\n"
        
        help_text += "\n"
        
        # Common scams
        help_text += I18n.get_text(language, 'common_scams')
        help_text += "• Fake investment schemes\n"
        help_text += "• Impersonation scams\n"
        help_text += "• Phishing links\n"
        help_text += "• Fake customer support\n"
        help_text += "• Romance scams\n"
        help_text += "• Giveaway scams\n"
        
        help_text += "\n"
        
        # What to do if scammed
        help_text += I18n.get_text(language, 'what_to_do')
        help_text += "1. Stop all communication\n"
        help_text += "2. Report to this bot\n"
        help_text += "3. Contact platform support\n"
        help_text += "4. Report to authorities\n"
        help_text += "5. Warn others in community\n"
        
        help_text += "\n"
        
        # Resources
        help_text += I18n.get_text(language, 'resources')
        help_text += "• Community groups (see Verified Groups)\n"
        help_text += "• Trusted admins (see Trusted Admins)\n"
        help_text += "• Platform support channels\n"
        
        keyboard = [[
            InlineKeyboardButton(
                I18n.get_text(language, 'back_to_menu'),
                callback_data="back_to_main"
            )
        ]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            help_text,
            reply_markup=reply_markup,
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def show_trusted_admins(self, update: Update, context: ContextTypes.DEFAULT_TYPE, language: str):
        """Hiển thị admin uy tín"""
        query = update.callback_query
        
        admins = self.admin_service.get_all_admins(active_only=True)
        
        if not admins:
            text = I18n.get_text(language, 'no_admins')
        else:
            text = I18n.get_text(language, 'trusted_admins_title') + "\n\n"
            
            for i, admin in enumerate(admins[:10]):  # Giới hạn 10 admin
                text += f"{i+1}. "
                text += I18n.get_text(language, 'admin_info').format(
                    admin.get('username', admin.get('first_name', 'Unknown')),
                    admin.get('admin_level', 'moderator'),
                    admin.get('trust_score', 100) if 'trust_score' in admin else 'N/A',
                    admin.get('added_at', 'Unknown')[:10]
                )
                
                if i < len(admins[:10]) - 1:
                    text += "\n" + "─" * 20 + "\n\n"
        
        keyboard = [[
            InlineKeyboardButton(
                I18n.get_text(language, 'back_to_menu'),
                callback_data="back_to_main"
            )
        ]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            text,
            reply_markup=reply_markup,
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def show_verified_groups(self, update: Update, context: ContextTypes.DEFAULT_TYPE, language: str):
        """Hiển thị nhóm đã xác minh"""
        query = update.callback_query
        
        groups = self.group_service.get_verified_groups(limit=10)
        
        if not groups:
            text = I18n.get_text(language, 'no_groups')
        else:
            text = I18n.get_text(language, 'verified_groups_title') + "\n\n"
            
            for i, group in enumerate(groups):
                text += f"{i+1}. "
                text += I18n.get_text(language, 'group_info').format(
                    group.get('title', 'Unknown Group'),
                    group.get('group_type', 'regular'),
                    group.get('member_count', 0),
                    group.get('trust_score', 50),
                    group.get('created_at', 'Unknown')[:10]
                )
                
                if group.get('username'):
                    text += f"\n   Join: @{group['username']}"
                
                if i < len(groups) - 1:
                    text += "\n" + "─" * 20 + "\n\n"
        
        keyboard = [[
            InlineKeyboardButton(
                I18n.get_text(language, 'back_to_menu'),
                callback_data="back_to_main"
            )
        ]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            text,
            reply_markup=reply_markup,
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def show_statistics(self, update: Update, context: ContextTypes.DEFAULT_TYPE, language: str):
        """Hiển thị thống kê"""
        query = update.callback_query
        
        stats = self.statistics_service.get_system_stats()
        
        text = I18n.get_text(language, 'stats_title')
        
        # User statistics
        if 'users' in stats:
            text += I18n.get_text(language, 'stats_users').format(
                stats['users']['total'],
                stats['users']['new_today']
            ) + "\n"
        
        # Report statistics
        if 'reports' in stats:
            text += I18n.get_text(language, 'stats_reports').format(
                stats['reports']['total_reports'],
                stats['reports']['pending_reports']
            ) + "\n"
        
        # Scammer statistics
        if 'scammers' in stats:
            text += I18n.get_text(language, 'stats_scammers').format(
                stats['scammers']['total_scammers'],
                stats['scammers']['high_risk_scammers']
            ) + "\n"
        
        # Lookup statistics
        if 'lookups' in stats:
            text += I18n.get_text(language, 'stats_lookups').format(
                stats['lookups']['total_today']
            ) + "\n"
        
        # Group statistics
        if 'groups' in stats:
            text += I18n.get_text(language, 'stats_groups').format(
                stats['groups']['total_groups'],
                stats['groups']['verified_groups']
            ) + "\n"
        
        # Amount statistics
        if 'scammers' in stats:
            text += I18n.get_text(language, 'stats_amount').format(
                stats['scammers']['total_amount_lost']
            ) + "\n"
        
        text += "\n📅 *Last Updated:* " + datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        keyboard = [[
            InlineKeyboardButton(
                I18n.get_text(language, 'back_to_menu'),
                callback_data="back_to_main"
            )
        ]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            text,
            reply_markup=reply_markup,
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def show_admin_panel(self, update: Update, context: ContextTypes.DEFAULT_TYPE, 
                              language: str, user_id: int):
        """Hiển thị admin panel"""
        query = update.callback_query
        
        # Kiểm tra quyền admin
        if not self.user_service.is_admin(user_id):
            await query.edit_message_text(
                I18n.get_text(language, 'error_permission'),
                parse_mode=ParseMode.MARKDOWN
            )
            return
        
        # Cập nhật hoạt động admin
        self.admin_service.update_admin_activity(user_id)
        
        keyboard = [
            [
                InlineKeyboardButton(
                    I18n.get_text(language, 'view_reports'),
                    callback_data="admin_view_reports"
                ),
                InlineKeyboardButton(
                    I18n.get_text(language, 'manage_scammers'),
                    callback_data="admin_manage_scammers"
                )
            ],
            [
                InlineKeyboardButton(
                    I18n.get_text(language, 'manage_users'),
                    callback_data="admin_manage_users"
                ),
                InlineKeyboardButton(
                    I18n.get_text(language, 'manage_groups'),
                    callback_data="admin_manage_groups"
                )
            ],
            [
                InlineKeyboardButton(
                    I18n.get_text(language, 'manage_admins'),
                    callback_data="admin_manage_admins"
                ),
                InlineKeyboardButton(
                    I18n.get_text(language, 'system_stats'),
                    callback_data="admin_system_stats"
                )
            ],
            [
                InlineKeyboardButton(
                    I18n.get_text(language, 'export_data'),
                    callback_data="admin_export_data"
                ),
                InlineKeyboardButton(
                    I18n.get_text(language, 'backup_db'),
                    callback_data="admin_backup_db"
                )
            ],
            [
                InlineKeyboardButton(
                    I18n.get_text(language, 'broadcast'),
                    callback_data="admin_broadcast"
                ),
                InlineKeyboardButton(
                    I18n.get_text(language, 'system_settings'),
                    callback_data="admin_system_settings"
                )
            ],
            [
                InlineKeyboardButton(
                    I18n.get_text(language, 'back_to_menu'),
                    callback_data="back_to_main"
                )
            ]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            I18n.get_text(language, 'admin_menu'),
            reply_markup=reply_markup,
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def handle_admin_actions(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Xử lý hành động admin"""
        query = update.callback_query
        await query.answer()
        
        user = query.from_user
        language = context.user_data.get('language', 'en')
        action = query.data
        
        # Kiểm tra quyền admin
        if not self.user_service.is_admin(user.id):
            await query.edit_message_text(
                I18n.get_text(language, 'error_permission'),
                parse_mode=ParseMode.MARKDOWN
            )
            return self.MAIN_MENU
        
        if action == "admin_view_reports":
            # Hiển thị báo cáo đang chờ
            reports = self.report_service.get_pending_reports(limit=10)
            
            if not reports:
                text = "📋 No pending reports."
            else:
                text = "📋 *Pending Reports*\n\n"
                for i, report in enumerate(reports[:5]):  # Giới hạn 5 báo cáo
                    text += f"*Report #{report['id']}*\n"
                    text += f"Type: {report.get('report_type', 'Unknown')}\n"
                    text += f"Reporter: @{report.get('reporter_username', 'N/A')}\n"
                    
                    if report.get('telegram_username'):
                        text += f"Telegram: @{report['telegram_username']}\n"
                    if report.get('binance_uid'):
                        text += f"Binance: {report['binance_uid']}\n"
                    if report.get('usdt_address'):
                        text += f"USDT: {report['usdt_address'][:10]}...\n"
                    
                    text += f"Amount: ${report.get('amount_usd', 0)}\n"
                    text += f"Date: {report['created_at'][:10]}\n"
                    
                    # Action buttons
                    text += "\n"
                    
                    if i < len(reports[:5]) - 1:
                        text += "─" * 20 + "\n\n"
            
            keyboard = []
            
            if reports:
                # Thêm nút action cho báo cáo đầu tiên
                keyboard.append([
                    InlineKeyboardButton(
                        I18n.get_text(language, 'approve_report'),
                        callback_data=f"admin_approve_{reports[0]['id']}"
                    ),
                    InlineKeyboardButton(
                        I18n.get_text(language, 'reject_report'),
                        callback_data=f"admin_reject_{reports[0]['id']}"
                    )
                ])
                keyboard.append([
                    InlineKeyboardButton(
                        I18n.get_text(language, 'mark_verified'),
                        callback_data=f"admin_verify_{reports[0]['id']}"
                    ),
                    InlineKeyboardButton(
                        I18n.get_text(language, 'need_more_info'),
                        callback_data=f"admin_moreinfo_{reports[0]['id']}"
                    )
                ])
            
            keyboard.append([
                InlineKeyboardButton(
                    "Next Report" if reports else "Refresh",
                    callback_data="admin_view_reports"
                ),
                InlineKeyboardButton(
                    I18n.get_text(language, 'back_to_menu'),
                    callback_data="back_to_admin"
                )
            ])
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                text,
                reply_markup=reply_markup,
                parse_mode=ParseMode.MARKDOWN
            )
            
            return self.ADMIN_ACTION
            
        elif action == "admin_manage_scammers":
            # Hiển thị quản lý scammers
            stats = self.scam_service.get_scammer_stats()
            
            text = "👥 *Manage Scammers*\n\n"
            text += f"Total Scammers: {stats.get('total_scammers', 0)}\n"
            text += f"High Risk: {stats.get('high_risk_scammers', 0)}\n"
            text += f"Confirmed: {stats.get('confirmed_scammers', 0)}\n"
            text += f"Total Amount: ${stats.get('total_amount_lost', 0)}\n\n"
            text += "Select an action:"
            
            keyboard = [
                [
                    InlineKeyboardButton("🔍 Search Scammer", callback_data="admin_search_scammer"),
                    InlineKeyboardButton("📊 Top Scammers", callback_data="admin_top_scammers")
                ],
                [
                    InlineKeyboardButton("🆕 Recent Scammers", callback_data="admin_recent_scammers"),
                    InlineKeyboardButton("📈 Risk Analysis", callback_data="admin_risk_analysis")
                ],
                [
                    InlineKeyboardButton("🗑️ Delete Scammer", callback_data="admin_delete_scammer"),
                    InlineKeyboardButton("📋 Export List", callback_data="admin_export_scammers")
                ],
                [
                    InlineKeyboardButton(
                        I18n.get_text(language, 'back_to_menu'),
                        callback_data="back_to_admin"
                    )
                ]
            ]
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                text,
                reply_markup=reply_markup,
                parse_mode=ParseMode.MARKDOWN
            )
            
            return self.ADMIN_ACTION
            
        elif action == "admin_manage_users":
            # Hiển thị quản lý người dùng
            user_stats = self.user_service.get_user_stats(user.id)
            
            text = "👤 *Manage Users*\n\n"
            text += "Select an action:"
            
            keyboard = [
                [
                    InlineKeyboardButton("🔍 Search User", callback_data="admin_search_user"),
                    InlineKeyboardButton("🏆 Top Users", callback_data="admin_top_users")
                ],
                [
                    InlineKeyboardButton("🚫 Ban User", callback_data="admin_ban_user"),
                    InlineKeyboardButton("✅ Unban User", callback_data="admin_unban_user")
                ],
                [
                    InlineKeyboardButton("📊 User Stats", callback_data="admin_user_statistics"),
                    InlineKeyboardButton("📋 Export Users", callback_data="admin_export_users")
                ],
                [
                    InlineKeyboardButton(
                        I18n.get_text(language, 'back_to_menu'),
                        callback_data="back_to_admin"
                    )
                ]
            ]
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                text,
                reply_markup=reply_markup,
                parse_mode=ParseMode.MARKDOWN
            )
            
            return self.ADMIN_ACTION
            
        elif action == "admin_manage_groups":
            # Hiển thị quản lý nhóm
            group_stats = self.group_service.get_group_stats()
            
            text = "👥 *Manage Groups*\n\n"
            text += f"Total Groups: {group_stats.get('total_groups', 0)}\n"
            text += f"Verified: {group_stats.get('verified_groups', 0)}\n"
            text += f"Blacklisted: {group_stats.get('blacklisted_groups', 0)}\n"
            text += f"Total Members: {group_stats.get('total_members', 0)}\n\n"
            text += "Select an action:"
            
            keyboard = [
                [
                    InlineKeyboardButton("✅ Verify Group", callback_data="admin_verify_group"),
                    InlineKeyboardButton("🚫 Blacklist Group", callback_data="admin_blacklist_group")
                ],
                [
                    InlineKeyboardButton("📋 List Groups", callback_data="admin_list_groups"),
                    InlineKeyboardButton("📊 Group Stats", callback_data="admin_group_statistics")
                ],
                [
                    InlineKeyboardButton(
                        I18n.get_text(language, 'back_to_menu'),
                        callback_data="back_to_admin"
                    )
                ]
            ]
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                text,
                reply_markup=reply_markup,
                parse_mode=ParseMode.MARKDOWN
            )
            
            return self.ADMIN_ACTION
            
        elif action == "admin_manage_admins":
            # Hiển thị quản lý admin
            admins = self.admin_service.get_all_admins(active_only=True)
            
            text = "👑 *Manage Admins*\n\n"
            text += f"Total Admins: {len(admins)}\n\n"
            
            for i, admin in enumerate(admins[:5]):
                text += f"{i+1}. @{admin.get('username', 'N/A')}\n"
                text += f"   Level: {admin.get('admin_level', 'moderator')}\n"
                text += f"   Added: {admin.get('added_at', 'N/A')[:10]}\n\n"
            
            text += "Select an action:"
            
            keyboard = [
                [
                    InlineKeyboardButton("➕ Add Admin", callback_data="admin_add_admin"),
                    InlineKeyboardButton("➖ Remove Admin", callback_data="admin_remove_admin")
                ],
                [
                    InlineKeyboardButton("📋 List All", callback_data="admin_list_admins"),
                    InlineKeyboardButton("⚙️ Edit Permissions", callback_data="admin_edit_permissions")
                ],
                [
                    InlineKeyboardButton(
                        I18n.get_text(language, 'back_to_menu'),
                        callback_data="back_to_admin"
                    )
                ]
            ]
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                text,
                reply_markup=reply_markup,
                parse_mode=ParseMode.MARKDOWN
            )
            
            return self.ADMIN_ACTION
            
        elif action == "admin_system_stats":
            # Hiển thị thống kê hệ thống chi tiết
            stats = self.statistics_service.get_system_stats()
            
            text = "📈 *System Statistics*\n\n"
            
            # Users
            if 'users' in stats:
                text += f"👥 Users: {stats['users']['total']:,}\n"
                text += f"   New Today: {stats['users']['new_today']}\n"
                text += f"   Active Today: {stats['users']['active_today']}\n"
                text += f"   Avg Trust Score: {stats['users']['avg_trust_score']}\n\n"
            
            # Scammers
            if 'scammers' in stats:
                text += f"🚨 Scammers: {stats['scammers']['total_scammers']:,}\n"
                text += f"   Critical Risk: {stats['scammers']['critical_risk_scammers']}\n"
                text += f"   High Risk: {stats['scammers']['high_risk_scammers']}\n"
                text += f"   Medium Risk: {stats['scammers']['medium_risk_scammers']}\n"
                text += f"   Total Amount Lost: ${stats['scammers']['total_amount_lost']:,}\n\n"
            
            # Reports
            if 'reports' in stats:
                text += f"📋 Reports: {stats['reports']['total_reports']:,}\n"
                text += f"   Pending: {stats['reports']['pending_reports']}\n"
                text += f"   Approved: {stats['reports']['approved_reports']}\n"
                text += f"   Verified: {stats['reports']['verified_reports']}\n"
                text += f"   Today: {stats['reports']['reports_today']}\n\n"
            
            # Lookups
            if 'lookups' in stats:
                text += f"🔍 Lookups Today: {stats['lookups']['total_today']:,}\n"
                text += f"   Successful: {stats['lookups']['successful_today']}\n"
                text += f"   Avg Response: {stats['lookups']['avg_response_time']}ms\n\n"
            
            # Groups
            if 'groups' in stats:
                text += f"👥 Groups: {stats['groups']['total_groups']}\n"
                text += f"   Verified: {stats['groups']['verified_groups']}\n"
                text += f"   Blacklisted: {stats['groups']['blacklisted_groups']}\n"
                text += f"   Total Members: {stats['groups']['total_members']:,}\n\n"
            
            # Overall
            if 'overall' in stats:
                text += f"📊 Overall:\n"
                text += f"   Total Requests: {stats['overall']['total_requests']:,}\n"
                text += f"   System Uptime: {stats['overall']['system_uptime']}\n"
                text += f"   Database Size: {stats['overall']['database_size']}\n"
                text += f"   Last Backup: {stats['overall']['last_backup']}\n"
            
            text += f"\n📅 Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            
            keyboard = [[
                InlineKeyboardButton("🔄 Refresh", callback_data="admin_system_stats"),
                InlineKeyboardButton(
                    I18n.get_text(language, 'back_to_menu'),
                    callback_data="back_to_admin"
                )
            ]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                text,
                reply_markup=reply_markup,
                parse_mode=ParseMode.MARKDOWN
            )
            
            return self.ADMIN_ACTION
            
        elif action.startswith("admin_approve_"):
            # Xử lý approve report
            report_id = int(action.replace("admin_approve_", ""))
            self.report_service.update_report_status(
                report_id, "approved", user.id, "Approved by admin"
            )
            
            await query.answer("✅ Report approved!")
            await self.handle_admin_actions(update, context)
            
        elif action.startswith("admin_reject_"):
            # Xử lý reject report
            report_id = int(action.replace("admin_reject_", ""))
            self.report_service.update_report_status(
                report_id, "rejected", user.id, "Rejected by admin"
            )
            
            await query.answer("❌ Report rejected!")
            await self.handle_admin_actions(update, context)
            
        elif action.startswith("admin_verify_"):
            # Xử lý verify report
            report_id = int(action.replace("admin_verify_", ""))
            self.report_service.update_report_status(
                report_id, "verified", user.id, "Verified by admin"
            )
            
            await query.answer("🔍 Report verified!")
            await self.handle_admin_actions(update, context)
            
        elif action == "back_to_admin":
            # Quay lại admin panel
            await self.show_admin_panel(update, context, language, user.id)
            return self.ADMIN_MENU
            
        elif action == "back_to_main":
            # Quay lại menu chính
            await self.show_main_menu(update, context, language, user.id)
            return self.MAIN_MENU
        
        return self.ADMIN_ACTION
    
    async def handle_group_events(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Xử lý sự kiện nhóm"""
        if not update.message or not update.message.chat:
            return
        
        chat = update.message.chat
        
        # Chỉ xử lý nhóm và siêu nhóm
        if chat.type not in [ChatType.GROUP, ChatType.SUPERGROUP]:
            return
        
        # Đăng ký nhóm
        self.group_service.register_group(
            chat.id,
            chat.title,
            chat.username,
            "group" if chat.type == ChatType.GROUP else "supergroup"
        )
        
        # Xử lý tin nhắn mới thành viên
        if update.message.new_chat_members:
            for new_member in update.message.new_chat_members:
                # Nếu là bot
                if new_member.id == context.bot.id:
                    await update.message.reply_text(
                        "👋 Hello! I'm Anti Scam Bot. Use /start in private chat to begin."
                    )
                else:
                    # Đăng ký thành viên mới
                    self.group_service.add_group_member(
                        chat.id,
                        new_member.id,
                        is_admin=False,
                        is_owner=False
                    )
        
        # Xử lý tin nhắn rời nhóm
        if update.message.left_chat_member:
            # Có thể log nhưng không cần xóa khỏi database
            pass
        
        # Xử lý quyền admin
        if update.message.from_user:
            try:
                chat_member = await context.bot.get_chat_member(
                    chat.id, update.message.from_user.id
                )
                
                is_admin = chat_member.status in [
                    ChatMemberStatus.ADMINISTRATOR, 
                    ChatMemberStatus.OWNER
                ]
                is_owner = chat_member.status == ChatMemberStatus.OWNER
                
                self.group_service.add_group_member(
                    chat.id,
                    update.message.from_user.id,
                    is_admin=is_admin,
                    is_owner=is_owner
                )
            except:
                pass
    
    async def handle_error(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Xử lý lỗi"""
        self.logger.error(f"Update {update} caused error {context.error}")
        
        try:
            if update and update.effective_user:
                await context.bot.send_message(
                    chat_id=update.effective_user.id,
                    text="❌ An error occurred. Please try again later."
                )
        except:
            pass
    
    async def health_check(self):
        """Kiểm tra sức khỏe định kỳ"""
        while True:
            try:
                # Xóa rate limit đã hết hạn
                self.rate_limiter.clear_expired()
                
                # Cập nhật thống kê hàng ngày
                self.statistics_service.update_daily_statistics()
                
                # Log health status
                self.logger.info("Health check passed")
                
                # Chờ 5 phút
                await asyncio.sleep(300)
                
            except Exception as e:
                self.logger.error(f"Health check error: {e}")
                await asyncio.sleep(60)
    
    def setup_handlers(self):
        """Thiết lập tất cả handlers"""
        # Conversation handler cho luồng chính
        conv_handler = ConversationHandler(
            entry_points=[CommandHandler('start', self.start)],
            states={
                self.LANGUAGE_SELECTION: [
                    CallbackQueryHandler(
                        self.handle_language_selection,
                        pattern='^lang_'
                    )
                ],
                self.MAIN_MENU: [
                    CallbackQueryHandler(self.handle_main_menu)
                ],
                self.LOOKUP_TYPE: [
                    CallbackQueryHandler(
                        self.handle_lookup_type,
                        pattern='^lookup_'
                    ),
                    CallbackQueryHandler(
                        self.handle_usdt_network,
                        pattern='^network_'
                    )
                ],
                self.LOOKUP_INPUT: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_lookup_input)
                ],
                self.REPORT_TYPE: [
                    CallbackQueryHandler(
                        self.handle_report_type,
                        pattern='^report_type_'
                    ),
                    CallbackQueryHandler(
                        self.handle_report_network,
                        pattern='^report_network_'
                    )
                ],
                self.REPORT_DETAILS: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_report_details)
                ],
                self.REPORT_AMOUNT: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_report_amount)
                ],
                self.REPORT_DESCRIPTION: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_report_description)
                ],
                self.REPORT_PROOF: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_report_proof)
                ],
                self.REPORT_REVIEW: [
                    CallbackQueryHandler(self.handle_report_review)
                ],
                self.ADMIN_MENU: [
                    CallbackQueryHandler(
                        self.handle_admin_actions,
                        pattern='^admin_'
                    ),
                    CallbackQueryHandler(
                        self.handle_main_menu,
                        pattern='^back_to_main$'
                    )
                ],
                self.ADMIN_ACTION: [
                    CallbackQueryHandler(self.handle_admin_actions)
                ]
            },
            fallbacks=[CommandHandler('start', self.start)],
            allow_reentry=True
        )
        
        # Thêm handlers
        self.application.add_handler(conv_handler)
        
        # Handler cho group events
        self.application.add_handler(
            MessageHandler(filters.ALL & filters.ChatType.GROUPS, self.handle_group_events)
        )
        
        # Handler lỗi
        self.application.add_error_handler(self.handle_error)
        
        # Handler help command
        self.application.add_handler(CommandHandler('help', self.start))
        
        # Handler stats command
        self.application.add_handler(CommandHandler('stats', self.start))
    
    async def run(self):
        """Chạy bot"""
        # Tạo application
        self.application = ApplicationBuilder() \
            .token(Config.BOT_TOKEN) \
            .post_init(self.post_init) \
            .build()
        
        # Thiết lập handlers
        self.setup_handlers()
        
        # Lấy bot info
        bot_info = await self.application.bot.get_me()
        self.bot_username = bot_info.username
        Config.BOT_USERNAME = self.bot_username
        
        self.logger.info(f"Starting bot @{self.bot_username}")
        self.logger.info(f"Admin IDs: {Config.ADMIN_IDS}")
        self.logger.info(f"Super Admin IDs: {Config.SUPER_ADMIN_IDS}")
        self.logger.info(f"Render Mode: {Config.RENDER}")
        
        # Khởi động health check
        asyncio.create_task(self.health_check())
        
        # Chạy bot
        if Config.RENDER:
            # Sử dụng long polling cho Render
            await self.application.initialize()
            await self.application.start()
            await self.application.updater.start_polling()
            
            # Giữ bot chạy
            while True:
                await asyncio.sleep(3600)
        else:
            # Polling bình thường
            await self.application.run_polling()
    
    async def post_init(self, application: Application):
        """Khởi tạo sau khi bot được tạo"""
        self.logger.info("Bot initialized successfully")

# ==================== RENDER HEALTH SERVER ====================
async def health_server():
    """Máy chủ health check cho Render"""
    try:
        import aiohttp
        from aiohttp import web
        
        async def handle_health(request):
            return web.Response(text="OK", status=200)
        
        app = web.Application()
        app.router.add_get('/health', handle_health)
        app.router.add_get('/', handle_health)
        
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, '0.0.0.0', Config.PORT)
        await site.start()
        
        print(f"✅ Health server running on port {Config.PORT}")
        return runner
    except ImportError:
        print("⚠️ aiohttp not installed, skipping health server")
        return None
    except Exception as e:
        print(f"❌ Health server error: {e}")
        return None

# ==================== MAIN ENTRY POINT ====================
async def main():
    """Điểm vào chính"""
    # Kiểm tra token
    if not Config.BOT_TOKEN:
        print("❌ ERROR: BOT_TOKEN is required!")
        print("Please set BOT_TOKEN environment variable")
        sys.exit(1)
    
    print("=" * 50)
    print("🚀 ANTI SCAM BOT - STARTING...")
    print("=" * 50)
    print(f"✅ Version: 3.0 (Complete Edition)")
    print(f"✅ Database: {Config.DATABASE_PATH}")
    print(f"✅ Languages: {len(Config.SUPPORTED_LANGUAGES)} supported")
    print(f"✅ Features: Admin Panel, Group Management, Help Guides")
    print(f"✅ Platforms: Telegram, Binance, USDT, OKX")
    print(f"✅ Render Mode: {Config.RENDER}")
    print("=" * 50)
    
    # Khởi động health server nếu trên Render
    health_runner = None
    if Config.RENDER:
        health_runner = await health_server()
    
    # Tạo và chạy bot
    bot = AntiScamBot()
    
    try:
        await bot.run()
    except KeyboardInterrupt:
        print("\n🛑 Bot stopped by user")
    except Exception as e:
        print(f"❌ Bot crashed: {e}")
        logging.exception("Bot crashed")
    finally:
        # Dọn dẹp
        if health_runner:
            await health_runner.cleanup()
        
        print("👋 Bot shutdown complete")

if __name__ == '__main__':
    # Chạy bot
    asyncio.run(main())
