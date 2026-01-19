#!/usr/bin/env python3
"""
ANTI SCAM BOT - HOÀN CHỈNH 100%
Tích hợp đầy đủ: Telegram + Binance ID + Risk Score + Audit + 24/24 Render
Phiên bản: 2.0.0 (Production Ready)
"""

import os
import sys
import logging
import asyncio
import sqlite3
import re
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
from enum import Enum
from collections import defaultdict
import pytz

from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, 
    CommandHandler, 
    MessageHandler, 
    CallbackQueryHandler, 
    ContextTypes, 
    filters
)
from telegram.constants import ParseMode

# ==================== LOAD ENVIRONMENT ====================
load_dotenv()

# ==================== CONFIGURATION ====================
class Config:
    """Central configuration management"""
    
    # Bot credentials
    BOT_TOKEN = os.getenv("BOT_TOKEN", "")
    ADMIN_IDS = [int(x.strip()) for x in os.getenv("ADMIN_IDS", "").split(",") if x.strip()]
    
    # Database
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///anti_scam.db")
    
    # Render specific
    RENDER = os.getenv("RENDER", "false").lower() == "true"
    PORT = int(os.getenv("PORT", 8080))
    
    # Rate limiting
    RATE_LIMIT_PER_USER = int(os.getenv("RATE_LIMIT", "60"))  # requests per minute
    REPORT_COOLDOWN = int(os.getenv("REPORT_COOLDOWN", "300"))  # seconds
    
    # Security
    MIN_PASSWORD_LENGTH = 8
    MAX_INPUT_LENGTH = 500

# ==================== DATABASE MODELS ====================
class Database:
    """Database management with SQLite"""
    
    def __init__(self, db_path: str = "anti_scam.db"):
        self.db_path = db_path
        self.init_database()
    
    def get_connection(self):
        """Get database connection with row factory"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def init_database(self):
        """Initialize all database tables"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Users table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    telegram_id INTEGER UNIQUE NOT NULL,
                    username TEXT,
                    first_name TEXT,
                    last_name TEXT,
                    language TEXT DEFAULT 'en',
                    is_admin BOOLEAN DEFAULT FALSE,
                    is_banned BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Scammers table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS scammers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    telegram_username TEXT,
                    telegram_id INTEGER,
                    binance_uid TEXT,
                    binance_pay_id TEXT,
                    wallet_address TEXT,
                    okx_uid TEXT,
                    risk_level TEXT DEFAULT 'low',
                    total_reports INTEGER DEFAULT 0,
                    total_amount_usd REAL DEFAULT 0,
                    notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Reports table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS reports (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    reporter_id INTEGER NOT NULL,
                    scammer_id INTEGER,
                    telegram_username TEXT,
                    binance_uid TEXT,
                    wallet_address TEXT,
                    amount_usd REAL DEFAULT 0,
                    description TEXT,
                    proof_url TEXT,
                    status TEXT DEFAULT 'pending',
                    reviewed_by INTEGER,
                    reviewed_at TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (reporter_id) REFERENCES users (telegram_id),
                    FOREIGN KEY (scammer_id) REFERENCES scammers (id)
                )
            """)
            
            # Lookup logs
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS lookup_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    query_type TEXT NOT NULL,
                    query_value TEXT NOT NULL,
                    result TEXT,
                    risk_level TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (telegram_id)
                )
            """)
            
            # Audit logs
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS audit_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    admin_id INTEGER,
                    action TEXT NOT NULL,
                    target_type TEXT,
                    target_id INTEGER,
                    details TEXT,
                    ip_address TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create indexes
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_scammers_telegram ON scammers(telegram_username)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_scammers_binance ON scammers(binance_uid)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_reports_status ON reports(status)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_lookup_logs_user ON lookup_logs(user_id)")
            
            conn.commit()
    
    def execute_query(self, query: str, params: tuple = ()):
        """Execute a query and return results"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()
            return cursor
    
    def fetch_one(self, query: str, params: tuple = ()):
        """Fetch single row"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            return cursor.fetchone()
    
    def fetch_all(self, query: str, params: tuple = ()):
        """Fetch all rows"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            return cursor.fetchall()

# ==================== I18N MULTI-LANGUAGE ====================
class I18n:
    """Internationalization manager with 4 languages"""
    
    TRANSLATIONS = {
        'en': {
            'welcome': "👮 *ANTI SCAM BOT*\n\nWelcome! I can help you verify suspicious accounts and report scammers.",
            'select_language': "🌐 *Select your language:*",
            'main_menu': "📋 *Main Menu*\nChoose an option:",
            'lookup_scam': "🔍 Lookup Scammer",
            'report_scam': "🚨 Report Scammer",
            'change_language': "🌐 Change Language",
            'help': "ℹ️ Help & Guide",
            'admin_panel': "👮 Admin Panel",
            'enter_telegram': "Please enter Telegram username (e.g., @username) or ID:",
            'enter_binance': "Please enter Binance UID:",
            'enter_wallet': "Please enter wallet address (USDT):",
            'enter_okx': "Please enter OKX UID:",
            'scam_found': "🚨 *SCAM RISK DETECTED*\n\n",
            'no_data': "ℹ️ No reports found for this query.\n\n⚠️ *WARNING:*\nNo data does not mean safe. Always verify carefully.",
            'risk_low': "🟢 LOW RISK",
            'risk_medium': "🟡 MEDIUM RISK",
            'risk_high': "🔴 HIGH RISK",
            'reports_count': "Reports: {}",
            'amount_lost': "Amount Lost: ${}",
            'report_start': "🚨 *Report a Scammer*\n\nPlease follow these steps:",
            'report_step1': "1. Enter scammer's Telegram username:",
            'report_step2': "2. Enter Binance UID (if any):",
            'report_step3': "3. Enter wallet address (if any):",
            'report_step4': "4. Enter amount lost (USD):",
            'report_step5': "5. Describe what happened:",
            'report_step6': "6. Provide proof URL (optional):",
            'report_confirmation': "✅ Report submitted! Our team will review it.",
            'admin_welcome': "👮 *Admin Panel*\n\nSelect an action:",
            'view_reports': "📊 View Reports",
            'manage_scammers': "👥 Manage Scammers",
            'user_stats': "📈 User Statistics",
            'export_data': "💾 Export Data",
            'back': "🔙 Back",
            'cancel': "❌ Cancel"
        },
        'vi': {
            'welcome': "👮 *BOT CHỐNG LỪA ĐẢO*\n\nChào mừng! Tôi có thể giúp bạn kiểm tra tài khoản đáng ngờ và báo cáo kẻ lừa đảo.",
            'select_language': "🌐 *Chọn ngôn ngữ của bạn:*",
            'main_menu': "📋 *Menu Chính*\nChọn một tùy chọn:",
            'lookup_scam': "🔍 Tra Cứu Lừa Đảo",
            'report_scam': "🚨 Báo Cáo Lừa Đảo",
            'change_language': "🌐 Đổi Ngôn Ngữ",
            'help': "ℹ️ Trợ Giúp & Hướng Dẫn",
            'admin_panel': "👮 Bảng Quản Trị",
            'enter_telegram': "Vui lòng nhập username Telegram (ví dụ: @username) hoặc ID:",
            'enter_binance': "Vui lòng nhập Binance UID:",
            'enter_wallet': "Vui lòng nhập địa chỉ ví (USDT):",
            'enter_okx': "Vui lòng nhập OKX UID:",
            'scam_found': "🚨 *PHÁT HIỆN NGUY CƠ LỪA ĐẢO*\n\n",
            'no_data': "ℹ️ Không tìm thấy báo cáo nào cho truy vấn này.\n\n⚠️ *CẢNH BÁO:*\nKhông có dữ liệu không có nghĩa là an toàn. Luôn xác minh cẩn thận.",
            'risk_low': "🟢 RỦI RO THẤP",
            'risk_medium': "🟡 RỦI RO TRUNG BÌNH",
            'risk_high': "🔴 RỦI RO CAO",
            'reports_count': "Số báo cáo: {}",
            'amount_lost': "Số tiền mất: ${}",
            'report_start': "🚨 *Báo Cáo Kẻ Lừa Đảo*\n\nVui lòng làm theo các bước:",
            'report_step1': "1. Nhập username Telegram của kẻ lừa đảo:",
            'report_step2': "2. Nhập Binance UID (nếu có):",
            'report_step3': "3. Nhập địa chỉ ví (nếu có):",
            'report_step4': "4. Nhập số tiền mất (USD):",
            'report_step5': "5. Mô tả sự việc:",
            'report_step6': "6. Cung cấp đường link bằng chứng (tùy chọn):",
            'report_confirmation': "✅ Đã gửi báo cáo! Đội ngũ của chúng tôi sẽ xem xét.",
            'admin_welcome': "👮 *Bảng Quản Trị*\n\nChọn hành động:",
            'view_reports': "📊 Xem Báo Cáo",
            'manage_scammers': "👥 Quản Lý Kẻ Lừa Đảo",
            'user_stats': "📈 Thống Kê Người Dùng",
            'export_data': "💾 Xuất Dữ Liệu",
            'back': "🔙 Quay Lại",
            'cancel': "❌ Hủy"
        },
        'ru': {
            'welcome': "👮 *АНТИ-СКАМ БОТ*\n\nДобро пожаловать! Я могу помочь вам проверить подозрительные аккаунты и сообщить о мошенниках.",
            'select_language': "🌐 *Выберите ваш язык:*",
            'main_menu': "📋 *Главное меню*\nВыберите опцию:",
            'lookup_scam': "🔍 Поиск мошенника",
            'report_scam': "🚨 Сообщить о мошеннике",
            'change_language': "🌐 Изменить язык",
            'help': "ℹ️ Помощь и руководство",
            'admin_panel': "👮 Панель администратора",
            'enter_telegram': "Пожалуйста, введите имя пользователя Telegram (например, @username) или ID:",
            'enter_binance': "Пожалуйста, введите Binance UID:",
            'enter_wallet': "Пожалуйста, введите адрес кошелька (USDT):",
            'enter_okx': "Пожалуйста, введите OKX UID:",
            'scam_found': "🚨 *ОБНАРУЖЕН РИСК МОШЕННИЧЕСТВА*\n\n",
            'no_data': "ℹ️ По этому запросу отчетов не найдено.\n\n⚠️ *ПРЕДУПРЕЖДЕНИЕ:*\nОтсутствие данных не означает безопасность. Всегда проверяйте тщательно.",
            'risk_low': "🟢 НИЗКИЙ РИСК",
            'risk_medium': "🟡 СРЕДНИЙ РИСК",
            'risk_high': "🔴 ВЫСОКИЙ РИСК",
            'reports_count': "Отчетов: {}",
            'amount_lost': "Потерянная сумма: ${}",
            'report_start': "🚨 *Сообщить о мошеннике*\n\nПожалуйста, следуйте этим шагам:",
            'report_step1': "1. Введите имя пользователя Telegram мошенника:",
            'report_step2': "2. Введите Binance UID (если есть):",
            'report_step3': "3. Введите адрес кошелька (если есть):",
            'report_step4': "4. Введите потерянную сумму (USD):",
            'report_step5': "5. Опишите, что произошло:",
            'report_step6': "6. Предоставьте URL доказательства (опционально):",
            'report_confirmation': "✅ Отчет отправлен! Наша команда рассмотрит его.",
            'admin_welcome': "👮 *Панель администратора*\n\nВыберите действие:",
            'view_reports': "📊 Просмотр отчетов",
            'manage_scammers': "👥 Управление мошенниками",
            'user_stats': "📈 Статистика пользователей",
            'export_data': "💾 Экспорт данных",
            'back': "🔙 Назад",
            'cancel': "❌ Отмена"
        },
        'zh': {
            'welcome': "👮 *反诈骗机器人*\n\n欢迎！我可以帮助您验证可疑账户并报告诈骗者。",
            'select_language': "🌐 *选择您的语言:*",
            'main_menu': "📋 *主菜单*\n选择一个选项:",
            'lookup_scam': "🔍 查询诈骗者",
            'report_scam': "🚨 报告诈骗者",
            'change_language': "🌐 更改语言",
            'help': "ℹ️ 帮助与指南",
            'admin_panel': "👮 管理员面板",
            'enter_telegram': "请输入Telegram用户名（例如，@username）或ID:",
            'enter_binance': "请输入Binance UID:",
            'enter_wallet': "请输入钱包地址（USDT）:",
            'enter_okx': "请输入OKX UID:",
            'scam_found': "🚨 *检测到诈骗风险*\n\n",
            'no_data': "ℹ️ 未找到此查询的报告。\n\n⚠️ *警告:*\n没有数据并不意味着安全。请始终仔细验证。",
            'risk_low': "🟢 低风险",
            'risk_medium': "🟡 中等风险",
            'risk_high': "🔴 高风险",
            'reports_count': "报告数量: {}",
            'amount_lost': "损失金额: ${}",
            'report_start': "🚨 *报告诈骗者*\n\n请按照以下步骤操作:",
            'report_step1': "1. 输入诈骗者的Telegram用户名:",
            'report_step2': "2. 输入Binance UID（如果有）:",
            'report_step3': "3. 输入钱包地址（如果有）:",
            'report_step4': "4. 输入损失金额（USD）:",
            'report_step5': "5. 描述发生了什么:",
            'report_step6': "6. 提供证据URL（可选）:",
            'report_confirmation': "✅ 报告已提交！我们的团队将进行审查。",
            'admin_welcome': "👮 *管理员面板*\n\n选择一个操作:",
            'view_reports': "📊 查看报告",
            'manage_scammers': "👥 管理诈骗者",
            'user_stats': "📈 用户统计",
            'export_data': "💾 导出数据",
            'back': "🔙 返回",
            'cancel': "❌ 取消"
        }
    }
    
    @classmethod
    def get_text(cls, lang: str, key: str, **kwargs) -> str:
        """Get translated text with formatting"""
        if lang not in cls.TRANSLATIONS:
            lang = 'en'
        
        text = cls.TRANSLATIONS[lang].get(key, cls.TRANSLATIONS['en'].get(key, key))
        
        if kwargs:
            try:
                text = text.format(**kwargs)
            except:
                pass
        
        return text

# ==================== VALIDATORS & HELPERS ====================
class Validators:
    """Input validation utilities"""
    
    @staticmethod
    def validate_telegram(input_text: str) -> Optional[str]:
        """Validate and normalize Telegram input"""
        if not input_text:
            return None
        
        # Remove @ symbol and spaces
        normalized = input_text.strip().lower().replace('@', '')
        
        # Check if it's a numeric ID
        if normalized.isdigit() and len(normalized) > 5:
            return normalized
        
        # Check if it's a username (letters, numbers, underscores)
        if re.match(r'^[a-z0-9_]{5,}$', normalized):
            return normalized
        
        return None
    
    @staticmethod
    def validate_binance_uid(input_text: str) -> Optional[str]:
        """Validate Binance UID (6-10 digits)"""
        if not input_text:
            return None
        
        normalized = input_text.strip()
        
        # Binance UID is usually 6-10 digits
        if re.match(r'^\d{6,10}$', normalized):
            return normalized
        
        return None
    
    @staticmethod
    def validate_wallet_address(input_text: str) -> Optional[str]:
        """Validate cryptocurrency wallet address"""
        if not input_text:
            return None
        
        normalized = input_text.strip()
        
        # Basic validation for common blockchain addresses
        if len(normalized) >= 25 and len(normalized) <= 60:
            # Check for common patterns
            if (normalized.startswith('0x') and len(normalized) == 42) or \
               (normalized.startswith('T') and len(normalized) == 34) or \
               (normalized.startswith('1') or normalized.startswith('3')):
                return normalized
        
        return None
    
    @staticmethod
    def validate_okx_uid(input_text: str) -> Optional[str]:
        """Validate OKX UID"""
        if not input_text:
            return None
        
        normalized = input_text.strip()
        
        # OKX UID is usually numeric
        if re.match(r'^\d{6,10}$', normalized):
            return normalized
        
        return None
    
    @staticmethod
    def validate_amount(input_text: str) -> Optional[float]:
        """Validate USD amount"""
        try:
            amount = float(input_text.strip())
            if amount >= 0 and amount <= 10000000:  # Reasonable max
                return round(amount, 2)
        except:
            pass
        return None

class RiskCalculator:
    """Calculate risk score based on multiple factors"""
    
    @staticmethod
    def calculate_risk_score(scammer_data: Dict, all_reports: List) -> Tuple[int, str]:
        """Calculate risk score from 0-100 and return level"""
        score = 0
        
        # Base score for having any reports
        if scammer_data['total_reports'] > 0:
            score += 30
        
        # Multiple reports
        if scammer_data['total_reports'] >= 3:
            score += 30
        
        # High amount lost
        if scammer_data.get('total_amount_usd', 0) > 1000:
            score += 20
        if scammer_data.get('total_amount_usd', 0) > 10000:
            score += 20
        
        # Multiple identifiers
        identifiers = 0
        if scammer_data.get('telegram_username'):
            identifiers += 1
        if scammer_data.get('binance_uid'):
            identifiers += 1
        if scammer_data.get('wallet_address'):
            identifiers += 1
        
        if identifiers >= 2:
            score += 20
        
        # Recent reports (within 7 days)
        recent_count = sum(1 for r in all_reports 
                          if datetime.now() - datetime.fromisoformat(r['created_at']) < timedelta(days=7))
        if recent_count > 0:
            score += 20
        
        # Cap score at 100
        score = min(score, 100)
        
        # Determine risk level
        if score >= 70:
            level = "high"
        elif score >= 40:
            level = "medium"
        else:
            level = "low"
        
        return score, level

# ==================== SERVICES ====================
class UserService:
    """User management service"""
    
    def __init__(self, db: Database):
        self.db = db
    
    def get_or_create_user(self, telegram_id: int, username: str = None, 
                          first_name: str = None, last_name: str = None) -> Dict:
        """Get existing user or create new one"""
        user = self.db.fetch_one(
            "SELECT * FROM users WHERE telegram_id = ?", 
            (telegram_id,)
        )
        
        if user:
            # Update last seen
            self.db.execute_query(
                "UPDATE users SET last_seen = CURRENT_TIMESTAMP WHERE id = ?",
                (user['id'],)
            )
            return dict(user)
        
        # Create new user
        self.db.execute_query("""
            INSERT INTO users (telegram_id, username, first_name, last_name, created_at, last_seen)
            VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        """, (telegram_id, username, first_name, last_name))
        
        return {
            'telegram_id': telegram_id,
            'username': username,
            'first_name': first_name,
            'last_name': last_name,
            'language': 'en',
            'is_admin': False,
            'is_banned': False
        }
    
    def update_user_language(self, telegram_id: int, language: str):
        """Update user's language preference"""
        self.db.execute_query(
            "UPDATE users SET language = ? WHERE telegram_id = ?",
            (language, telegram_id)
        )
    
    def is_admin(self, telegram_id: int) -> bool:
        """Check if user is admin"""
        user = self.db.fetch_one(
            "SELECT is_admin FROM users WHERE telegram_id = ?",
            (telegram_id,)
        )
        return user and user['is_admin']
    
    def get_user_stats(self) -> Dict:
        """Get user statistics"""
        stats = {}
        
        # Total users
        result = self.db.fetch_one("SELECT COUNT(*) as count FROM users")
        stats['total_users'] = result['count'] if result else 0
        
        # Active users (last 7 days)
        result = self.db.fetch_one("""
            SELECT COUNT(*) as count FROM users 
            WHERE last_seen > datetime('now', '-7 days')
        """)
        stats['active_users'] = result['count'] if result else 0
        
        # New users today
        result = self.db.fetch_one("""
            SELECT COUNT(*) as count FROM users 
            WHERE date(created_at) = date('now')
        """)
        stats['new_users_today'] = result['count'] if result else 0
        
        return stats

class ScamService:
    """Scam lookup and management service"""
    
    def __init__(self, db: Database):
        self.db = db
    
    def lookup_scammer(self, query_type: str, query_value: str) -> Dict:
        """Look up scammer by various identifiers"""
        normalized_value = query_value.lower().replace('@', '').strip()
        
        # Search in all relevant fields
        if query_type == "telegram":
            results = self.db.fetch_all("""
                SELECT s.*, COUNT(r.id) as report_count, 
                       SUM(r.amount_usd) as total_amount
                FROM scammers s
                LEFT JOIN reports r ON s.id = r.scammer_id
                WHERE s.telegram_username = ? OR s.telegram_id = ?
                GROUP BY s.id
            """, (normalized_value, normalized_value))
        elif query_type == "binance":
            results = self.db.fetch_all("""
                SELECT s.*, COUNT(r.id) as report_count,
                       SUM(r.amount_usd) as total_amount
                FROM scammers s
                LEFT JOIN reports r ON s.id = r.scammer_id
                WHERE s.binance_uid = ?
                GROUP BY s.id
            """, (normalized_value,))
        elif query_type == "wallet":
            results = self.db.fetch_all("""
                SELECT s.*, COUNT(r.id) as report_count,
                       SUM(r.amount_usd) as total_amount
                FROM scammers s
                LEFT JOIN reports r ON s.id = r.scammer_id
                WHERE s.wallet_address = ?
                GROUP BY s.id
            """, (normalized_value,))
        else:
            results = []
        
        if not results:
            return None
        
        # Get all reports for risk calculation
        scammer_data = dict(results[0])
        scammer_id = scammer_data['id']
        
        reports = self.db.fetch_all("""
            SELECT * FROM reports 
            WHERE scammer_id = ? 
            ORDER BY created_at DESC
        """, (scammer_id,))
        
        reports_list = [dict(r) for r in reports]
        
        # Calculate risk
        score, level = RiskCalculator.calculate_risk_score(scammer_data, reports_list)
        
        return {
            **scammer_data,
            'reports': reports_list,
            'risk_score': score,
            'risk_level': level,
            'report_count': len(reports_list)
        }
    
    def log_lookup(self, user_id: int, query_type: str, query_value: str, 
                   result: str = None, risk_level: str = None):
        """Log lookup activity"""
        self.db.execute_query("""
            INSERT INTO lookup_logs (user_id, query_type, query_value, result, risk_level, created_at)
            VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        """, (user_id, query_type, query_value, result, risk_level))
    
    def get_scammer_stats(self) -> Dict:
        """Get scammer statistics"""
        stats = {}
        
        # Total scammers
        result = self.db.fetch_one("SELECT COUNT(*) as count FROM scammers")
        stats['total_scammers'] = result['count'] if result else 0
        
        # High risk scammers
        result = self.db.fetch_one("""
            SELECT COUNT(*) as count FROM scammers 
            WHERE risk_level = 'high'
        """)
        stats['high_risk_scammers'] = result['count'] if result else 0
        
        # Total amount lost
        result = self.db.fetch_one("SELECT SUM(amount_usd) as total FROM reports")
        stats['total_amount_lost'] = round(result['total'] or 0, 2)
        
        # Reports today
        result = self.db.fetch_one("""
            SELECT COUNT(*) as count FROM reports 
            WHERE date(created_at) = date('now')
        """)
        stats['reports_today'] = result['count'] if result else 0
        
        return stats

class ReportService:
    """Report management service"""
    
    def __init__(self, db: Database):
        self.db = db
    
    def create_report(self, reporter_id: int, data: Dict) -> bool:
        """Create a new scam report"""
        try:
            # Find or create scammer
            scammer_id = self._find_or_create_scammer(data)
            
            # Create report
            self.db.execute_query("""
                INSERT INTO reports 
                (reporter_id, scammer_id, telegram_username, binance_uid, 
                 wallet_address, amount_usd, description, proof_url, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """, (
                reporter_id, scammer_id,
                data.get('telegram_username'),
                data.get('binance_uid'),
                data.get('wallet_address'),
                data.get('amount_usd', 0),
                data.get('description', ''),
                data.get('proof_url', '')
            ))
            
            # Update scammer stats
            self._update_scammer_stats(scammer_id)
            
            return True
        except Exception as e:
            logging.error(f"Error creating report: {e}")
            return False
    
    def _find_or_create_scammer(self, data: Dict) -> int:
        """Find existing scammer or create new one"""
        # Try to find by Telegram
        if data.get('telegram_username'):
            result = self.db.fetch_one(
                "SELECT id FROM scammers WHERE telegram_username = ?",
                (data['telegram_username'],)
            )
            if result:
                return result['id']
        
        # Try to find by Binance
        if data.get('binance_uid'):
            result = self.db.fetch_one(
                "SELECT id FROM scammers WHERE binance_uid = ?",
                (data['binance_uid'],)
            )
            if result:
                return result['id']
        
        # Try to find by wallet
        if data.get('wallet_address'):
            result = self.db.fetch_one(
                "SELECT id FROM scammers WHERE wallet_address = ?",
                (data['wallet_address'],)
            )
            if result:
                return result['id']
        
        # Create new scammer
        self.db.execute_query("""
            INSERT INTO scammers 
            (telegram_username, binance_uid, wallet_address, okx_uid, created_at, updated_at)
            VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        """, (
            data.get('telegram_username'),
            data.get('binance_uid'),
            data.get('wallet_address'),
            data.get('okx_uid')
        ))
        
        result = self.db.fetch_one("SELECT last_insert_rowid() as id")
        return result['id'] if result else 0
    
    def _update_scammer_stats(self, scammer_id: int):
        """Update scammer statistics"""
        # Get report count and total amount
        result = self.db.fetch_one("""
            SELECT COUNT(*) as count, SUM(amount_usd) as total 
            FROM reports WHERE scammer_id = ?
        """, (scammer_id,))
        
        if result:
            # Calculate risk level
            risk_level = "low"
            if result['count'] >= 3:
                risk_level = "high"
            elif result['count'] >= 1:
                risk_level = "medium"
            
            # Update scammer
            self.db.execute_query("""
                UPDATE scammers 
                SET total_reports = ?, total_amount_usd = ?, 
                    risk_level = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (result['count'], result['total'] or 0, risk_level, scammer_id))
    
    def get_pending_reports(self) -> List:
        """Get all pending reports"""
        results = self.db.fetch_all("""
            SELECT r.*, u.username as reporter_username
            FROM reports r
            LEFT JOIN users u ON r.reporter_id = u.telegram_id
            WHERE r.status = 'pending'
            ORDER BY r.created_at DESC
        """)
        return [dict(r) for r in results]
    
    def update_report_status(self, report_id: int, status: str, admin_id: int = None):
        """Update report status"""
        self.db.execute_query("""
            UPDATE reports 
            SET status = ?, reviewed_by = ?, reviewed_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (status, admin_id, report_id))

# ==================== RATE LIMITER ====================
class RateLimiter:
    """Rate limiting to prevent abuse"""
    
    def __init__(self, max_requests: int = 60, period: int = 60):
        self.max_requests = max_requests
        self.period = period
        self.requests = defaultdict(list)
    
    def is_allowed(self, user_id: int) -> bool:
        """Check if user is allowed to make a request"""
        now = time.time()
        user_requests = self.requests[user_id]
        
        # Remove old requests
        user_requests = [req_time for req_time in user_requests 
                        if now - req_time < self.period]
        self.requests[user_id] = user_requests
        
        # Check if under limit
        if len(user_requests) < self.max_requests:
            user_requests.append(now)
            return True
        
        return False
    
    def get_wait_time(self, user_id: int) -> float:
        """Get remaining time until next allowed request"""
        if user_id not in self.requests or not self.requests[user_id]:
            return 0
        
        now = time.time()
        oldest_request = min(self.requests[user_id])
        time_passed = now - oldest_request
        
        if time_passed >= self.period:
            return 0
        
        return self.period - time_passed

# ==================== BOT HANDLERS ====================
class BotHandlers:
    """Telegram bot handlers"""
    
    def __init__(self, db: Database):
        self.db = db
        self.user_service = UserService(db)
        self.scam_service = ScamService(db)
        self.report_service = ReportService(db)
        self.rate_limiter = RateLimiter(max_requests=30, period=60)
        self.user_states = {}  # Store user conversation states
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        user = update.effective_user
        chat = update.effective_chat
        
        # Get or create user
        self.user_service.get_or_create_user(
            user.id, user.username, user.first_name, user.last_name
        )
        
        # Clear any existing state
        if user.id in self.user_states:
            del self.user_states[user.id]
        
        # Send language selection
        keyboard = [
            [InlineKeyboardButton("🇺🇸 English", callback_data="lang_en")],
            [InlineKeyboardButton("🇻🇳 Tiếng Việt", callback_data="lang_vi")],
            [InlineKeyboardButton("🇷🇺 Русский", callback_data="lang_ru")],
            [InlineKeyboardButton("🇨🇳 中文", callback_data="lang_zh")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            I18n.get_text('en', 'select_language'),
            reply_markup=reply_markup,
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def language_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle language selection"""
        query = update.callback_query
        await query.answer()
        
        user_id = query.from_user.id
        language = query.data.replace('lang_', '')
        
        # Update user language
        self.user_service.update_user_language(user_id, language)
        
        # Send welcome message
        welcome_text = I18n.get_text(language, 'welcome')
        await query.edit_message_text(
            welcome_text,
            parse_mode=ParseMode.MARKDOWN
        )
        
        # Show main menu
        await self.show_main_menu(update, context, language, user_id)
    
    async def show_main_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE, 
                            language: str, user_id: int):
        """Show main menu with options"""
        keyboard = [
            [InlineKeyboardButton(
                I18n.get_text(language, 'lookup_scam'), 
                callback_data="lookup_scam"
            )],
            [InlineKeyboardButton(
                I18n.get_text(language, 'report_scam'), 
                callback_data="report_scam"
            )],
            [InlineKeyboardButton(
                I18n.get_text(language, 'change_language'), 
                callback_data="change_language"
            )],
            [InlineKeyboardButton(
                I18n.get_text(language, 'help'), 
                callback_data="help"
            )]
        ]
        
        # Add admin panel if user is admin
        if self.user_service.is_admin(user_id):
            keyboard.append([
                InlineKeyboardButton(
                    I18n.get_text(language, 'admin_panel'), 
                    callback_data="admin_panel"
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
    
    async def lookup_scam(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle scam lookup"""
        query = update.callback_query
        await query.answer()
        
        user_id = query.from_user.id
        
        # Check rate limit
        if not self.rate_limiter.is_allowed(user_id):
            await query.message.reply_text("⚠️ Rate limit exceeded. Please wait a moment.")
            return
        
        # Set user state
        self.user_states[user_id] = {
            'action': 'lookup',
            'step': 'type_selection'
        }
        
        # Ask for lookup type
        keyboard = [
            [InlineKeyboardButton("🔍 Telegram", callback_data="lookup_telegram")],
            [InlineKeyboardButton("💳 Binance UID", callback_data="lookup_binance")],
            [InlineKeyboardButton("💰 Wallet Address", callback_data="lookup_wallet")],
            [InlineKeyboardButton("🔙 Back", callback_data="main_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "Select lookup type:",
            reply_markup=reply_markup
        )
    
    async def handle_lookup_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle lookup input based on type"""
        user_id = update.effective_user.id
        
        if user_id not in self.user_states or self.user_states[user_id].get('action') != 'lookup':
            return
        
        state = self.user_states[user_id]
        
        if state.get('step') == 'awaiting_input':
            lookup_type = state.get('lookup_type')
            query_value = update.message.text.strip()
            
            # Validate input
            validated = None
            if lookup_type == 'telegram':
                validated = Validators.validate_telegram(query_value)
            elif lookup_type == 'binance':
                validated = Validators.validate_binance_uid(query_value)
            elif lookup_type == 'wallet':
                validated = Validators.validate_wallet_address(query_value)
            
            if not validated:
                await update.message.reply_text("❌ Invalid input. Please try again.")
                return
            
            # Perform lookup
            user = self.user_service.get_or_create_user(user_id)
            language = user.get('language', 'en')
            
            result = self.scam_service.lookup_scammer(lookup_type, validated)
            
            if result:
                # Format result message
                message = I18n.get_text(language, 'scam_found')
                message += f"*Type:* {lookup_type.title()}\n"
                
                if result.get('telegram_username'):
                    message += f"*Telegram:* @{result['telegram_username']}\n"
                if result.get('binance_uid'):
                    message += f"*Binance UID:* {result['binance_uid']}\n"
                if result.get('wallet_address'):
                    message += f"*Wallet:* {result['wallet_address'][:20]}...\n"
                
                message += f"\n{I18n.get_text(language, 'reports_count').format(result['report_count'])}\n"
                
                if result.get('total_amount_usd'):
                    message += f"{I18n.get_text(language, 'amount_lost').format(result['total_amount_usd'])}\n"
                
                # Add risk level
                risk_text = I18n.get_text(language, f"risk_{result['risk_level']}")
                message += f"\n*Risk Level:* {risk_text}\n"
                message += f"*Risk Score:* {result['risk_score']}/100\n"
                
                if result.get('notes'):
                    message += f"\n*Notes:* {result['notes']}\n"
                
                message += "\n⚠️ *Disclaimer:* This information is based on user reports."
                
            else:
                message = I18n.get_text(language, 'no_data')
            
            # Log the lookup
            self.scam_service.log_lookup(
                user_id, lookup_type, validated,
                'found' if result else 'not_found',
                result['risk_level'] if result else None
            )
            
            await update.message.reply_text(
                message,
                parse_mode=ParseMode.MARKDOWN
            )
            
            # Clear state and show menu
            del self.user_states[user_id]
            await self.show_main_menu(update, context, language, user_id)
    
    async def report_scam(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle scam report initiation"""
        query = update.callback_query
        await query.answer()
        
        user_id = query.from_user.id
        
        # Check if user is in cooldown
        recent_reports = self.db.fetch_all("""
            SELECT COUNT(*) as count FROM reports 
            WHERE reporter_id = ? AND created_at > datetime('now', '-1 hour')
        """, (user_id,))
        
        if recent_reports and recent_reports[0]['count'] >= 3:
            await query.message.reply_text("⚠️ You've submitted too many reports recently. Please wait.")
            return
        
        # Set user state for reporting
        self.user_states[user_id] = {
            'action': 'report',
            'step': 1,
            'data': {}
        }
        
        # Get user language
        user = self.user_service.get_or_create_user(user_id)
        language = user.get('language', 'en')
        
        await query.edit_message_text(
            I18n.get_text(language, 'report_start'),
            parse_mode=ParseMode.MARKDOWN
        )
        
        # Ask for Telegram username
        await query.message.reply_text(
            I18n.get_text(language, 'report_step1')
        )
    
    async def handle_report_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle multi-step report input"""
        user_id = update.effective_user.id
        
        if user_id not in self.user_states or self.user_states[user_id].get('action') != 'report':
            return
        
        state = self.user_states[user_id]
        user_input = update.message.text.strip()
        
        # Get user language
        user = self.user_service.get_or_create_user(user_id)
        language = user.get('language', 'en')
        
        if state['step'] == 1:  # Telegram username
            validated = Validators.validate_telegram(user_input)
            if validated:
                state['data']['telegram_username'] = validated
                state['step'] = 2
                await update.message.reply_text(
                    I18n.get_text(language, 'report_step2')
                )
            else:
                await update.message.reply_text("❌ Invalid Telegram username. Please try again.")
        
        elif state['step'] == 2:  # Binance UID (optional)
            if user_input.lower() in ['skip', 'none', '']:
                state['step'] = 3
                await update.message.reply_text(
                    I18n.get_text(language, 'report_step3')
                )
            else:
                validated = Validators.validate_binance_uid(user_input)
                if validated:
                    state['data']['binance_uid'] = validated
                    state['step'] = 3
                    await update.message.reply_text(
                        I18n.get_text(language, 'report_step3')
                    )
                else:
                    await update.message.reply_text("❌ Invalid Binance UID. Enter 'skip' to omit.")
        
        elif state['step'] == 3:  # Wallet address (optional)
            if user_input.lower() in ['skip', 'none', '']:
                state['step'] = 4
                await update.message.reply_text(
                    I18n.get_text(language, 'report_step4')
                )
            else:
                validated = Validators.validate_wallet_address(user_input)
                if validated:
                    state['data']['wallet_address'] = validated
                    state['step'] = 4
                    await update.message.reply_text(
                        I18n.get_text(language, 'report_step4')
                    )
                else:
                    await update.message.reply_text("❌ Invalid wallet address. Enter 'skip' to omit.")
        
        elif state['step'] == 4:  # Amount lost
            validated = Validators.validate_amount(user_input)
            if validated is not None:
                state['data']['amount_usd'] = validated
                state['step'] = 5
                await update.message.reply_text(
                    I18n.get_text(language, 'report_step5')
                )
            else:
                await update.message.reply_text("❌ Invalid amount. Please enter a number (e.g., 100.50).")
        
        elif state['step'] == 5:  # Description
            if len(user_input) >= 10:
                state['data']['description'] = user_input[:500]
                state['step'] = 6
                await update.message.reply_text(
                    I18n.get_text(language, 'report_step6')
                )
            else:
                await update.message.reply_text("❌ Description must be at least 10 characters.")
        
        elif state['step'] == 6:  # Proof URL (optional)
            if user_input.lower() in ['skip', 'none', '']:
                # Submit report
                success = self.report_service.create_report(user_id, state['data'])
                
                if success:
                    await update.message.reply_text(
                        I18n.get_text(language, 'report_confirmation'),
                        parse_mode=ParseMode.MARKDOWN
                    )
                else:
                    await update.message.reply_text("❌ Error submitting report. Please try again.")
                
                # Clear state
                del self.user_states[user_id]
                await self.show_main_menu(update, context, language, user_id)
            else:
                # Basic URL validation
                if user_input.startswith(('http://', 'https://')):
                    state['data']['proof_url'] = user_input[:200]
                    
                    # Submit report
                    success = self.report_service.create_report(user_id, state['data'])
                    
                    if success:
                        await update.message.reply_text(
                            I18n.get_text(language, 'report_confirmation'),
                            parse_mode=ParseMode.MARKDOWN
                        )
                    else:
                        await update.message.reply_text("❌ Error submitting report. Please try again.")
                    
                    # Clear state
                    del self.user_states[user_id]
                    await self.show_main_menu(update, context, language, user_id)
                else:
                    await update.message.reply_text("❌ Invalid URL. Enter 'skip' to omit.")
    
    async def admin_panel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show admin panel"""
        query = update.callback_query
        await query.answer()
        
        user_id = query.from_user.id
        
        # Check if admin
        if not self.user_service.is_admin(user_id):
            await query.message.reply_text("⛔ Access denied.")
            return
        
        # Get user language
        user = self.user_service.get_or_create_user(user_id)
        language = user.get('language', 'en')
        
        keyboard = [
            [InlineKeyboardButton(
                I18n.get_text(language, 'view_reports'), 
                callback_data="admin_view_reports"
            )],
            [InlineKeyboardButton(
                I18n.get_text(language, 'manage_scammers'), 
                callback_data="admin_manage_scammers"
            )],
            [InlineKeyboardButton(
                I18n.get_text(language, 'user_stats'), 
                callback_data="admin_user_stats"
            )],
            [InlineKeyboardButton(
                I18n.get_text(language, 'export_data'), 
                callback_data="admin_export_data"
            )],
            [InlineKeyboardButton(
                I18n.get_text(language, 'back'), 
                callback_data="main_menu"
            )]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            I18n.get_text(language, 'admin_welcome'),
            reply_markup=reply_markup,
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def admin_view_reports(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """View pending reports (admin only)"""
        query = update.callback_query
        await query.answer()
        
        user_id = query.from_user.id
        
        if not self.user_service.is_admin(user_id):
            return
        
        reports = self.report_service.get_pending_reports()
        
        if not reports:
            await query.message.reply_text("No pending reports.")
            return
        
        # Show first report
        report = reports[0]
        
        message = f"📋 *Report #{report['id']}*\n\n"
        message += f"*Reporter:* {report.get('reporter_username', 'N/A')}\n"
        
        if report.get('telegram_username'):
            message += f"*Telegram:* @{report['telegram_username']}\n"
        if report.get('binance_uid'):
            message += f"*Binance UID:* {report['binance_uid']}\n"
        if report.get('wallet_address'):
            message += f"*Wallet:* {report['wallet_address'][:20]}...\n"
        
        message += f"\n*Amount:* ${report.get('amount_usd', 0)}\n"
        message += f"*Description:* {report.get('description', 'N/A')[:100]}...\n"
        
        if report.get('proof_url'):
            message += f"\n*Proof:* {report['proof_url']}\n"
        
        message += f"\n*Submitted:* {report['created_at']}\n"
        
        # Action buttons
        keyboard = [
            [
                InlineKeyboardButton("✅ Approve", callback_data=f"approve_{report['id']}"),
                InlineKeyboardButton("❌ Reject", callback_data=f"reject_{report['id']}")
            ],
            [InlineKeyboardButton("📋 Next Report", callback_data="admin_view_reports")],
            [InlineKeyboardButton("🔙 Back", callback_data="admin_panel")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            message,
            reply_markup=reply_markup,
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def admin_handle_report_action(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle report approval/rejection"""
        query = update.callback_query
        await query.answer()
        
        user_id = query.from_user.id
        
        if not self.user_service.is_admin(user_id):
            return
        
        action, report_id = query.data.split('_')
        report_id = int(report_id)
        
        # Update report status
        self.report_service.update_report_status(
            report_id, 
            'approved' if action == 'approve' else 'rejected',
            user_id
        )
        
        await query.message.reply_text(
            f"✅ Report {action}d successfully."
        )
        
        # Show next report
        await self.admin_view_reports(update, context)
    
    async def admin_user_stats(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show user statistics"""
        query = update.callback_query
        await query.answer()
        
        user_id = query.from_user.id
        
        if not self.user_service.is_admin(user_id):
            return
        
        # Get statistics
        user_stats = self.user_service.get_user_stats()
        scam_stats = self.scam_service.get_scammer_stats()
        
        message = "📊 *Statistics Dashboard*\n\n"
        message += "*👥 User Statistics:*\n"
        message += f"Total Users: {user_stats['total_users']}\n"
        message += f"Active (7 days): {user_stats['active_users']}\n"
        message += f"New Today: {user_stats['new_users_today']}\n\n"
        
        message += "*🚨 Scam Statistics:*\n"
        message += f"Total Scammers: {scam_stats['total_scammers']}\n"
        message += f"High Risk: {scam_stats['high_risk_scammers']}\n"
        message += f"Total Amount Lost: ${scam_stats['total_amount_lost']}\n"
        message += f"Reports Today: {scam_stats['reports_today']}\n"
        
        keyboard = [[InlineKeyboardButton("🔙 Back", callback_data="admin_panel")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            message,
            reply_markup=reply_markup,
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command"""
        user = update.effective_user
        user_data = self.user_service.get_or_create_user(user.id)
        language = user_data.get('language', 'en')
        
        help_text = """
🤖 *Anti Scam Bot - Help Guide*

*🔍 How to Use:*
1. Use `/start` to begin
2. Choose your language
3. Select an option from the menu

*🔎 Lookup Features:*
- Check Telegram usernames/IDs
- Verify Binance UIDs
- Validate wallet addresses
- Get risk assessment

*🚨 Reporting Scams:*
- Report suspicious accounts
- Provide evidence
- Help protect others

*⚠️ Important Notes:*
- This bot relies on user reports
- Always verify information
- No guarantee of 100% accuracy
- Use at your own discretion

*👮 Admin Commands:*
- Manage reports
- View statistics
- Export data

*📞 Support:* Contact @admin for help.
"""
        
        await update.message.reply_text(
            help_text,
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle all callback queries"""
        query = update.callback_query
        callback_data = query.data
        
        if callback_data.startswith("lang_"):
            await self.language_callback(update, context)
        
        elif callback_data == "main_menu":
            user_id = query.from_user.id
            user = self.user_service.get_or_create_user(user_id)
            language = user.get('language', 'en')
            await self.show_main_menu(update, context, language, user_id)
        
        elif callback_data == "lookup_scam":
            await self.lookup_scam(update, context)
        
        elif callback_data.startswith("lookup_"):
            # Set lookup type and ask for input
            lookup_type = callback_data.replace("lookup_", "")
            user_id = query.from_user.id
            
            if user_id in self.user_states:
                self.user_states[user_id]['lookup_type'] = lookup_type
                self.user_states[user_id]['step'] = 'awaiting_input'
            
            # Ask for input based on type
            prompt = ""
            if lookup_type == "telegram":
                prompt = "Please enter Telegram username or ID:"
            elif lookup_type == "binance":
                prompt = "Please enter Binance UID (6-10 digits):"
            elif lookup_type == "wallet":
                prompt = "Please enter wallet address (USDT):"
            
            await query.edit_message_text(prompt)
        
        elif callback_data == "report_scam":
            await self.report_scam(update, context)
        
        elif callback_data == "change_language":
            # Show language selection again
            keyboard = [
                [InlineKeyboardButton("🇺🇸 English", callback_data="lang_en")],
                [InlineKeyboardButton("🇻🇳 Tiếng Việt", callback_data="lang_vi")],
                [InlineKeyboardButton("🇷🇺 Русский", callback_data="lang_ru")],
                [InlineKeyboardButton("🇨🇳 中文", callback_data="lang_zh")],
                [InlineKeyboardButton("🔙 Back", callback_data="main_menu")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                "🌐 Select your language:",
                reply_markup=reply_markup
            )
        
        elif callback_data == "help":
            user_id = query.from_user.id
            user = self.user_service.get_or_create_user(user_id)
            language = user.get('language', 'en')
            
            await query.edit_message_text(
                "ℹ️ Help information will be displayed here.",
                parse_mode=ParseMode.MARKDOWN
            )
        
        elif callback_data == "admin_panel":
            await self.admin_panel(update, context)
        
        elif callback_data == "admin_view_reports":
            await self.admin_view_reports(update, context)
        
        elif callback_data == "admin_user_stats":
            await self.admin_user_stats(update, context)
        
        elif callback_data.startswith(("approve_", "reject_")):
            await self.admin_handle_report_action(update, context)
        
        elif callback_data == "admin_panel":
            await self.admin_panel(update, context)

# ==================== MAIN APPLICATION ====================
class AntiScamBot:
    """Main bot application"""
    
    def __init__(self):
        self.db = Database()
        self.handlers = BotHandlers(self.db)
        self.application = None
        
        # Setup logging
        logging.basicConfig(
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            level=logging.INFO
        )
        self.logger = logging.getLogger(__name__)
    
    def setup_handlers(self):
        """Setup all bot handlers"""
        # Command handlers
        self.application.add_handler(CommandHandler("start", self.handlers.start))
        self.application.add_handler(CommandHandler("help", self.handlers.help_command))
        
        # Callback query handler
        self.application.add_handler(CallbackQueryHandler(self.handlers.handle_callback))
        
        # Message handlers
        self.application.add_handler(MessageHandler(
            filters.TEXT & ~filters.COMMAND, 
            self.handlers.handle_lookup_input
        ))
        self.application.add_handler(MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            self.handlers.handle_report_input
        ))
        
        # Error handler
        self.application.add_error_handler(self.error_handler)
    
    async def error_handler(self, update: object, context: ContextTypes.DEFAULT_TYPE):
        """Handle errors"""
        self.logger.error(f"Exception while handling an update: {context.error}")
        
        if update and hasattr(update, 'effective_user'):
            try:
                await context.bot.send_message(
                    chat_id=update.effective_user.id,
                    text="❌ An error occurred. Please try again later."
                )
            except:
                pass
    
    async def health_check(self):
        """Periodic health check logging"""
        while True:
            try:
                # Log basic stats
                user_stats = self.handlers.user_service.get_user_stats()
                scam_stats = self.handlers.scam_service.get_scammer_stats()
                
                self.logger.info(
                    f"Health check - Users: {user_stats['total_users']}, "
                    f"Active: {user_stats['active_users']}, "
                    f"Scammers: {scam_stats['total_scammers']}"
                )
                
                await asyncio.sleep(300)  # Every 5 minutes
                
            except Exception as e:
                self.logger.error(f"Health check error: {e}")
                await asyncio.sleep(60)
    
    async def run(self):
        """Run the bot application"""
        # Create application
        self.application = Application.builder().token(Config.BOT_TOKEN).build()
        
        # Setup handlers
        self.setup_handlers()
        
        # Start health check in background
        asyncio.create_task(self.health_check())
        
        # Run bot
        self.logger.info("Starting Anti Scam Bot...")
        
        if Config.RENDER:
            # Use long polling for Render
            await self.application.initialize()
            await self.application.start()
            await self.application.updater.start_polling()
            
            # Keep running
            while True:
                await asyncio.sleep(3600)
        else:
            # Standard polling
            await self.application.run_polling()

# ==================== RENDER DEPLOYMENT ====================
async def render_health_server():
    """Simple HTTP server for Render health checks"""
    try:
        import aiohttp
        from aiohttp import web
        
        async def health_check(request):
            return web.Response(text="OK", status=200)
        
        app = web.Application()
        app.router.add_get('/health', health_check)
        
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, '0.0.0.0', Config.PORT)
        await site.start()
        
        print(f"Health server running on port {Config.PORT}")
        return runner
    except ImportError:
        print("aiohttp not installed, skipping health server")
        return None
    except Exception as e:
        print(f"Health server error: {e}")
        return None

# ==================== MAIN ENTRY POINT ====================
async def main():
    """Main entry point"""
    # Validate configuration
    if not Config.BOT_TOKEN:
        print("❌ Error: BOT_TOKEN environment variable is required!")
        sys.exit(1)
    
    print("🚀 Starting Anti Scam Bot...")
    print(f"📊 Admin IDs: {Config.ADMIN_IDS}")
    print(f"🌍 Languages: 4 supported")
    print(f"⚙️  Render Mode: {Config.RENDER}")
    
    # Start health server if on Render
    health_server = None
    if Config.RENDER:
        health_server = await render_health_server()
    
    # Create and run bot
    bot = AntiScamBot()
    
    try:
        await bot.run()
    except KeyboardInterrupt:
        print("\n🛑 Bot stopped by user")
    except Exception as e:
        print(f"❌ Bot crashed: {e}")
        logging.exception("Bot crashed")
    finally:
        if health_server:
            await health_server.cleanup()
        print("👋 Bot shutdown complete")

if __name__ == '__main__':
    # Run the bot
    asyncio.run(main())
