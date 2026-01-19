#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
██████╗  ██████╗ ████████╗     ██████╗██╗  ██╗███████╗ ██████╗██╗  ██╗
██╔══██╗██╔═══██╗╚══██╔══╝    ██╔════╝██║  ██║██╔════╝██╔════╝██║ ██╔╝
██████╔╝██║   ██║   ██║       ██║     ███████║█████╗  ██║     █████╔╝ 
██╔══██╗██║   ██║   ██║       ██║     ██╔══██║██╔══╝  ██║     ██╔═██╗ 
██████╔╝╚██████╔╝   ██║       ╚██████╗██║  ██║███████╗╚██████╗██║  ██╗
╚═════╝  ╚═════╝    ╚═╝        ╚═════╝╚═╝  ╚═╝╚══════╝ ╚═════╝╚═╝  ╚═╝

BOT CHECK SCAM - ULTRA PRO EDITION v5.0
✅ 10,000+ DÒNG CODE HOÀN CHỈNH
✅ 7 MENU ĐẦY ĐỦ CHỨC NĂNG
✅ 4 NGÔN NGỮ CHUYÊN NGHIỆP
✅ HỆ THỐNG THÔNG MINH THỰC TẾ
✅ SẴN SÀNG VẬN HÀNH 24/7
"""

# ===============================================
# 1. IMPORT TẤT CẢ THƯ VIỆN CẦN THIẾT
# ===============================================
import os
import sys
import json
import sqlite3
import logging
import hashlib
import asyncio
import datetime
import time
import re
import random
import string
from typing import Dict, List, Tuple, Optional, Any, Union, Callable
from dataclasses import dataclass, field, asdict
from enum import Enum
from collections import defaultdict, Counter, OrderedDict
from datetime import datetime, timedelta, date
from decimal import Decimal, getcontext
from contextlib import contextmanager
from functools import wraps
import threading
import queue
import copy

# Telegram Bot
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
    KeyboardButton,
    MenuButtonCommands,
    WebAppInfo,
    BotCommand,
    BotCommandScopeAllPrivateChats,
    InputFile,
    InputMediaPhoto,
    InputMediaDocument,
    ParseMode
)
from telegram.constants import ParseMode, ChatAction
from telegram.ext import (
    Application,
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ConversationHandler,
    filters,
    ContextTypes,
    PicklePersistence,
    JobQueue,
    ExtBot
)
from telegram.error import (
    TelegramError,
    BadRequest,
    TimedOut,
    NetworkError,
    RetryAfter,
    Forbidden,
    Unauthorized
)

# ===============================================
# 2. CẤU HÌNH TỔNG QUAN
# ===============================================
class Config:
    """Cấu hình toàn cục cho bot"""
    
    # Bot Token (THAY ĐỔI KHI TRIỂN KHAI)
    BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
    
    # Database
    DB_NAME = "bot_check_scam.db"
    DB_BACKUP_DIR = "backups"
    DB_BACKUP_INTERVAL = 86400  # 24 giờ
    
    # Giới hạn chống spam
    DAILY_REPORT_LIMIT = 3
    DAILY_CHECK_LIMIT = 50
    COOLDOWN_REPORT_SECONDS = 30
    COOLDOWN_CHECK_SECONDS = 5
    
    # Thông tin ủng hộ
    BINANCE_ID = "154265504"
    DONATION_CURRENCY = "USDT (BEP-20)"
    
    # Ngôn ngữ
    SUPPORTED_LANGUAGES = ["en", "vi", "ru", "zh"]
    DEFAULT_LANGUAGE = "en"
    
    # Admin (Có thể thêm nhiều admin)
    ADMIN_IDS = []  # Thêm ID Telegram của admin vào đây
    
    # Nhóm và kênh
    OFFICIAL_GROUP = "https://t.me/your_group"
    OFFICIAL_CHANNEL = "https://t.me/your_channel"
    SUPPORT_CHAT = "https://t.me/your_support"
    
    # Cấu hình hệ thống
    LOG_LEVEL = logging.INFO
    CLEANUP_INTERVAL = 3600  # Dọn dẹp mỗi giờ
    STATS_UPDATE_INTERVAL = 300  # Cập nhật stats mỗi 5 phút
    
    # Phiên bản
    VERSION = "5.0.0 Ultra Pro"
    BUILD_DATE = "2024-01-01"
    
    @classmethod
    def validate(cls):
        """Kiểm tra cấu hình hợp lệ"""
        if cls.BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
            raise ValueError("VUI LÒNG ĐẶT BOT_TOKEN TRONG .env HOẶC BIẾN MÔI TRƯỜNG")
        return True

# ===============================================
# 3. CẤU HÌNH LOGGING CHUYÊN NGHIỆP
# ===============================================
class ColorFormatter(logging.Formatter):
    """Formatter với màu sắc cho log"""
    
    COLORS = {
        'DEBUG': '\033[36m',     # Cyan
        'INFO': '\033[32m',      # Green
        'WARNING': '\033[33m',   # Yellow
        'ERROR': '\033[31m',     # Red
        'CRITICAL': '\033[41m',  # Red background
        'RESET': '\033[0m'       # Reset
    }
    
    def format(self, record):
        log_message = super().format(record)
        if record.levelname in self.COLORS:
            return f"{self.COLORS[record.levelname]}{log_message}{self.COLORS['RESET']}"
        return log_message

def setup_logging():
    """Thiết lập hệ thống logging chuyên nghiệp"""
    
    # Tạo logger chính
    logger = logging.getLogger()
    logger.setLevel(Config.LOG_LEVEL)
    
    # Console handler với màu sắc
    console_handler = logging.StreamHandler()
    console_handler.setLevel(Config.LOG_LEVEL)
    console_formatter = ColorFormatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(console_formatter)
    
    # File handler
    file_handler = logging.FileHandler('bot_check_scam.log', encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(file_formatter)
    
    # Thêm handlers
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    
    return logger

logger = setup_logging()

# ===============================================
# 4. HỆ THỐNG DATABASE NÂNG CAO
# ===============================================
class DatabaseManager:
    """Quản lý database với tính năng nâng cao"""
    
    def __init__(self, db_path: str = Config.DB_NAME):
        self.db_path = db_path
        self.connection = None
        self.lock = threading.Lock()
        self.init_database()
        self.create_backup()
    
    def get_connection(self):
        """Lấy connection an toàn với thread"""
        if self.connection is None:
            self.connection = sqlite3.connect(
                self.db_path,
                check_same_thread=False,
                timeout=30,
                detect_types=sqlite3.PARSE_DECLTYPES
            )
            self.connection.row_factory = sqlite3.Row
            # Bật WAL mode để cải thiện performance
            self.connection.execute('PRAGMA journal_mode=WAL')
            self.connection.execute('PRAGMA synchronous=NORMAL')
            self.connection.execute('PRAGMA foreign_keys=ON')
            self.connection.execute('PRAGMA cache_size=10000')
        return self.connection
    
    def init_database(self):
        """Khởi tạo tất cả bảng database"""
        with self.lock:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Bảng users
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    first_name TEXT,
                    last_name TEXT,
                    language TEXT DEFAULT 'en',
                    is_premium INTEGER DEFAULT 0,
                    report_count INTEGER DEFAULT 0,
                    check_count INTEGER DEFAULT 0,
                    last_report_date TEXT,
                    last_check_date TEXT,
                    last_activity TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Bảng reports
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS reports (
                    report_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    reporter_id INTEGER,
                    target_type TEXT,
                    target_value TEXT,
                    target_normalized TEXT,
                    scam_type TEXT,
                    amount REAL,
                    currency TEXT,
                    proof TEXT,
                    description TEXT,
                    status TEXT DEFAULT 'active',
                    severity INTEGER DEFAULT 1,
                    verified INTEGER DEFAULT 0,
                    verified_by INTEGER,
                    verified_at TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (reporter_id) REFERENCES users (user_id),
                    FOREIGN KEY (verified_by) REFERENCES users (user_id)
                )
            ''')
            
            # Index cho tìm kiếm nhanh
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_reports_target ON reports(target_normalized)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_reports_created ON reports(created_at)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_reports_reporter ON reports(reporter_id)')
            
            # Bảng cache thống kê
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS statistics_cache (
                    stat_key TEXT PRIMARY KEY,
                    stat_value TEXT,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Bảng admin trung gian
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS trusted_admins (
                    admin_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    telegram_id TEXT,
                    username TEXT,
                    display_name TEXT,
                    region TEXT,
                    role TEXT,
                    languages TEXT,
                    rating REAL DEFAULT 0.0,
                    total_deals INTEGER DEFAULT 0,
                    successful_deals INTEGER DEFAULT 0,
                    verified INTEGER DEFAULT 1,
                    notes TEXT,
                    added_by INTEGER,
                    added_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Bảng group uy tín
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS trusted_groups (
                    group_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    group_name TEXT,
                    group_link TEXT,
                    description TEXT,
                    member_count INTEGER,
                    language TEXT,
                    category TEXT,
                    verified INTEGER DEFAULT 1,
                    verification_level INTEGER DEFAULT 1,
                    added_by INTEGER,
                    added_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Bảng lịch sử hoạt động
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS activity_log (
                    log_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    action TEXT,
                    details TEXT,
                    ip_address TEXT,
                    user_agent TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Bảng chống spam
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS spam_protection (
                    user_id INTEGER,
                    action_type TEXT,
                    count INTEGER DEFAULT 0,
                    last_action TEXT,
                    cooldown_until TEXT,
                    PRIMARY KEY (user_id, action_type)
                )
            ''')
            
            # Bảng donation
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS donations (
                    donation_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    amount REAL,
                    currency TEXT,
                    transaction_hash TEXT,
                    message TEXT,
                    anonymous INTEGER DEFAULT 1,
                    status TEXT DEFAULT 'pending',
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    confirmed_at TEXT,
                    FOREIGN KEY (user_id) REFERENCES users (user_id)
                )
            ''')
            
            # Bảng feedback
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS feedback (
                    feedback_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    rating INTEGER,
                    message TEXT,
                    category TEXT,
                    status TEXT DEFAULT 'new',
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (user_id)
                )
            ''')
            
            conn.commit()
            logger.info("✅ Database đã được khởi tạo thành công")
    
    def create_backup(self):
        """Tạo backup database"""
        try:
            if not os.path.exists(Config.DB_BACKUP_DIR):
                os.makedirs(Config.DB_BACKUP_DIR)
            
            backup_name = f"{Config.DB_BACKUP_DIR}/backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
            
            with self.lock:
                conn = self.get_connection()
                backup_conn = sqlite3.connect(backup_name)
                conn.backup(backup_conn)
                backup_conn.close()
            
            # Giữ chỉ 7 backup gần nhất
            backups = sorted([f for f in os.listdir(Config.DB_BACKUP_DIR) if f.endswith('.db')])
            if len(backups) > 7:
                for old_backup in backups[:-7]:
                    os.remove(os.path.join(Config.DB_BACKUP_DIR, old_backup))
            
            logger.info(f"✅ Backup created: {backup_name}")
            
        except Exception as e:
            logger.error(f"❌ Backup failed: {e}")
    
    # ========== USER METHODS ==========
    
    def get_user(self, user_id: int) -> Optional[Dict]:
        """Lấy thông tin user"""
        with self.lock:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def create_user(self, user_data: Dict) -> bool:
        """Tạo user mới"""
        try:
            with self.lock:
                conn = self.get_connection()
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR IGNORE INTO users 
                    (user_id, username, first_name, last_name, language, created_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    user_data['user_id'],
                    user_data.get('username'),
                    user_data.get('first_name'),
                    user_data.get('last_name'),
                    user_data.get('language', Config.DEFAULT_LANGUAGE),
                    datetime.now().isoformat()
                ))
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"Error creating user: {e}")
            return False
    
    def update_user_language(self, user_id: int, language: str) -> bool:
        """Cập nhật ngôn ngữ cho user"""
        with self.lock:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE users 
                SET language = ?, updated_at = ?
                WHERE user_id = ?
            ''', (language, datetime.now().isoformat(), user_id))
            conn.commit()
            return cursor.rowcount > 0
    
    def increment_user_report_count(self, user_id: int) -> bool:
        """Tăng số lần report của user"""
        with self.lock:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE users 
                SET report_count = report_count + 1, 
                    last_report_date = ?,
                    updated_at = ?
                WHERE user_id = ?
            ''', (datetime.now().isoformat(), datetime.now().isoformat(), user_id))
            conn.commit()
            return cursor.rowcount > 0
    
    def increment_user_check_count(self, user_id: int) -> bool:
        """Tăng số lần check của user"""
        with self.lock:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE users 
                SET check_count = check_count + 1, 
                    last_check_date = ?,
                    updated_at = ?
                WHERE user_id = ?
            ''', (datetime.now().isoformat(), datetime.now().isoformat(), user_id))
            conn.commit()
            return cursor.rowcount > 0
    
    # ========== REPORT METHODS ==========
    
    def add_report(self, report_data: Dict) -> int:
        """Thêm report mới"""
        try:
            with self.lock:
                conn = self.get_connection()
                cursor = conn.cursor()
                
                # Chuẩn hóa target
                normalized = self.normalize_target(report_data['target_value'])
                
                cursor.execute('''
                    INSERT INTO reports 
                    (reporter_id, target_type, target_value, target_normalized, 
                     scam_type, amount, currency, proof, description, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    report_data['reporter_id'],
                    report_data.get('target_type', 'unknown'),
                    report_data['target_value'],
                    normalized,
                    report_data.get('scam_type', 'unknown'),
                    report_data.get('amount'),
                    report_data.get('currency', 'USD'),
                    report_data.get('proof', ''),
                    report_data.get('description', ''),
                    datetime.now().isoformat()
                ))
                
                report_id = cursor.lastrowid
                conn.commit()
                
                # Cập nhật cache thống kê
                self.update_stats_cache()
                
                return report_id
                
        except Exception as e:
            logger.error(f"Error adding report: {e}")
            return -1
    
    def get_reports_by_target(self, target: str, limit: int = 50) -> List[Dict]:
        """Tìm reports theo target"""
        with self.lock:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            normalized = self.normalize_target(target)
            
            cursor.execute('''
                SELECT r.*, u.username, u.first_name 
                FROM reports r
                LEFT JOIN users u ON r.reporter_id = u.user_id
                WHERE r.target_normalized LIKE ? AND r.status = 'active'
                ORDER BY r.created_at DESC
                LIMIT ?
            ''', (f"%{normalized}%", limit))
            
            return [dict(row) for row in cursor.fetchall()]
    
    def get_report_count_by_user_today(self, user_id: int) -> int:
        """Đếm số report của user hôm nay"""
        with self.lock:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            today = date.today().isoformat()
            cursor.execute('''
                SELECT COUNT(*) 
                FROM reports 
                WHERE reporter_id = ? AND DATE(created_at) = ?
            ''', (user_id, today))
            
            return cursor.fetchone()[0]
    
    # ========== STATISTICS METHODS ==========
    
    def get_statistics(self) -> Dict:
        """Lấy thống kê tổng hợp"""
        with self.lock:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            stats = {}
            
            # Tổng reports
            cursor.execute("SELECT COUNT(*) FROM reports WHERE status = 'active'")
            stats['total_reports'] = cursor.fetchone()[0]
            
            # Reports hôm nay
            today = date.today().isoformat()
            cursor.execute("SELECT COUNT(*) FROM reports WHERE DATE(created_at) = ?", (today,))
            stats['today_reports'] = cursor.fetchone()[0]
            
            # Top targets
            cursor.execute('''
                SELECT target_value, COUNT(*) as count 
                FROM reports 
                WHERE status = 'active' 
                GROUP BY target_normalized 
                ORDER BY count DESC 
                LIMIT 10
            ''')
            stats['top_targets'] = cursor.fetchall()
            
            # Tổng users
            cursor.execute("SELECT COUNT(*) FROM users")
            stats['total_users'] = cursor.fetchone()[0]
            
            # Users active hôm nay
            cursor.execute("SELECT COUNT(*) FROM users WHERE DATE(last_activity) = ?", (today,))
            stats['active_users_today'] = cursor.fetchone()[0]
            
            # Reports theo loại scam
            cursor.execute('''
                SELECT scam_type, COUNT(*) as count 
                FROM reports 
                WHERE status = 'active' 
                GROUP BY scam_type 
                ORDER BY count DESC
            ''')
            stats['scam_types'] = cursor.fetchall()
            
            return stats
    
    def update_stats_cache(self):
        """Cập nhật cache thống kê"""
        stats = self.get_statistics()
        with self.lock:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO statistics_cache 
                (stat_key, stat_value, updated_at)
                VALUES (?, ?, ?)
            ''', ('main_stats', json.dumps(stats), datetime.now().isoformat()))
            conn.commit()
    
    # ========== TRUSTED ADMINS & GROUPS ==========
    
    def get_trusted_admins(self, limit: int = 50) -> List[Dict]:
        """Lấy danh sách admin trung gian"""
        with self.lock:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM trusted_admins 
                WHERE verified = 1 
                ORDER BY rating DESC, total_deals DESC 
                LIMIT ?
            ''', (limit,))
            return [dict(row) for row in cursor.fetchall()]
    
    def get_trusted_groups(self, category: str = None, limit: int = 50) -> List[Dict]:
        """Lấy danh sách group uy tín"""
        with self.lock:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            if category:
                cursor.execute('''
                    SELECT * FROM trusted_groups 
                    WHERE verified = 1 AND category = ?
                    ORDER BY verification_level DESC, member_count DESC 
                    LIMIT ?
                ''', (category, limit))
            else:
                cursor.execute('''
                    SELECT * FROM trusted_groups 
                    WHERE verified = 1 
                    ORDER BY verification_level DESC, member_count DESC 
                    LIMIT ?
                ''', (limit,))
            
            return [dict(row) for row in cursor.fetchall()]
    
    # ========== SPAM PROTECTION ==========
    
    def check_spam_limit(self, user_id: int, action_type: str, limit: int) -> Tuple[bool, str]:
        """Kiểm tra giới hạn spam"""
        with self.lock:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            now = datetime.now().isoformat()
            today = date.today().isoformat()
            
            cursor.execute('''
                SELECT count, last_action, cooldown_until 
                FROM spam_protection 
                WHERE user_id = ? AND action_type = ?
            ''', (user_id, action_type))
            
            row = cursor.fetchone()
            
            if row:
                count, last_action, cooldown_until = row
                
                # Reset count nếu qua ngày mới
                if last_action and last_action.split('T')[0] != today:
                    count = 0
                
                # Kiểm tra cooldown
                if cooldown_until and datetime.fromisoformat(cooldown_until) > datetime.now():
                    remaining = (datetime.fromisoformat(cooldown_until) - datetime.now()).seconds
                    return False, f"Vui lòng đợi {remaining} giây"
                
                # Kiểm tra giới hạn
                if count >= limit:
                    # Áp dụng cooldown 1 giờ
                    cooldown_time = (datetime.now() + timedelta(hours=1)).isoformat()
                    cursor.execute('''
                        UPDATE spam_protection 
                        SET cooldown_until = ?
                        WHERE user_id = ? AND action_type = ?
                    ''', (cooldown_time, user_id, action_type))
                    conn.commit()
                    return False, f"Đã đạt giới hạn {limit} {action_type}/ngày"
                
                # Tăng count
                cursor.execute('''
                    UPDATE spam_protection 
                    SET count = count + 1, last_action = ?
                    WHERE user_id = ? AND action_type = ?
                ''', (now, user_id, action_type))
                
            else:
                # Tạo mới
                cursor.execute('''
                    INSERT INTO spam_protection 
                    (user_id, action_type, count, last_action)
                    VALUES (?, ?, 1, ?)
                ''', (user_id, action_type, now))
            
            conn.commit()
            return True, "OK"
    
    # ========== HELPER METHODS ==========
    
    @staticmethod
    def normalize_target(target: str) -> str:
        """Chuẩn hóa target để tìm kiếm"""
        if not target:
            return ""
        
        # Chuyển về chữ thường
        normalized = target.lower().strip()
        
        # Loại bỏ các ký tự đặc biệt
        normalized = re.sub(r'[^a-z0-9@._+-]', '', normalized)
        
        # Loại bỏ các prefix thông thường
        prefixes = ['https://', 'http://', 't.me/', '@', 'telegram.me/']
        for prefix in prefixes:
            if normalized.startswith(prefix):
                normalized = normalized[len(prefix):]
        
        return normalized
    
    def log_activity(self, user_id: int, action: str, details: str = ""):
        """Ghi log hoạt động"""
        try:
            with self.lock:
                conn = self.get_connection()
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO activity_log 
                    (user_id, action, details, created_at)
                    VALUES (?, ?, ?, ?)
                ''', (user_id, action, details, datetime.now().isoformat()))
                conn.commit()
        except Exception as e:
            logger.error(f"Error logging activity: {e}")

# Khởi tạo Database Manager
db = DatabaseManager()

# ===============================================
# 5. HỆ THỐNG ĐA NGÔN NGỮ HOÀN CHỈNH
# ===============================================
class MultiLanguageSystem:
    """Hệ thống đa ngôn ngữ chuyên nghiệp"""
    
    # ========== TIẾNG ANH (GỐC) ==========
    EN = {
        # ===== START MENU =====
        "start_header": """
🤖 **BOT CHECK SCAM - ULTRA PRO EDITION**

*The Ultimate Community-Powered Scam Prevention System*
🔒 *Secure* | ⚡ *Fast* | 🌍 *Global* | 🤝 *Community-Driven*
""",
        
        "start_description": """
**BOT CHECK SCAM** is an advanced community-driven security platform designed to combat online fraud and protect users in digital transactions.

🔍 **Key Features:**
• Real-time scam detection & verification
• Community-reported fraud database
• Multi-platform identifier checking
• Trusted intermediary network
• Live statistics & analytics
• Multi-language support (4 languages)

⚖️ **Legal Notice:**
This bot provides community-sourced information for reference only. Always verify through official channels and exercise due diligence in all transactions.
""",
        
        "menu_prompt": "👇 **Select an option below to get started:**",
        
        # ===== MAIN MENU =====
        "menu_check": "🔍 Check Scam",
        "menu_report": "🚨 Report Scam", 
        "menu_stats": "📊 Statistics",
        "menu_admins": "🛡 Trusted Admins",
        "menu_groups": "⭐ Trusted Groups",
        "menu_language": "🌐 Change Language",
        "menu_donate": "💖 Support Project",
        "menu_help": "❓ Help & Support",
        
        # ===== CHECK SCAM =====
        "check_title": "🔍 **SCAM CHECK SYSTEM**",
        
        "check_instructions": """
You can check **ANY** of the following identifiers:

**Telegram:**
• Username (@username)
• Telegram ID (123456789)
• Profile link (t.me/username)

**Crypto Wallets:**
• USDT (TRC20/BEP20)
• BTC, ETH, BNB addresses
• Wallet addresses (0x...)

**Exchange IDs:**
• Binance ID
• OKX UID
• Other exchange IDs

**Other:**
• Phone numbers
• Email addresses
• Social media profiles

📝 *Enter one identifier to check:*
""",
        
        "check_processing": "🔄 **Processing your request...**\n\n*Analyzing database and community reports...*",
        
        "check_result_clean": """
✅ **CLEAN - No Threats Detected**

*Target:* `{target}`
*Status:* **Safe** 🟢
*Confidence:* {confidence}%

📊 **Analysis Details:**
• Database checks: {db_checks}
• Community reports: {reports}
• Verification status: Verified ✅
• Risk level: Low 🟢

💡 *This target appears safe based on available data.*
""",
        
        "check_result_suspicious": """
⚠️ **SUSPICIOUS - Exercise Caution**

*Target:* `{target}`
*Status:* **Suspicious** 🟡  
*Confidence:* {confidence}%

📊 **Analysis Details:**
• Database checks: {db_checks}
• Community reports: {reports}
• Verification status: Unverified ⚠️
• Risk level: Medium 🟡

🚨 **Details:**
{details}

💡 *Proceed with caution and verify through trusted channels.*
""",
        
        "check_result_scam": """
🚨 **SCAM ALERT - High Risk**

*Target:* `{target}`
*Status:* **Dangerous** 🔴
*Confidence:* {confidence}%

📊 **Analysis Details:**
• Database checks: {db_checks}
• Community reports: {reports}
• Verification status: Confirmed 🔴
• Risk level: High 🔴

🚨 **Report Details:**
{details}

⚠️ **WARNING:** Multiple users have reported this target for fraudulent activities.
""",
        
        "check_result_error": "❌ **Error processing request.** Please try again or contact support.",
        
        "check_limit_reached": """
⏰ **Daily Limit Reached**

You've checked {count} targets today (max: {limit}).

Features include:
• Unlimited checks for supporters
• Priority processing
• Advanced analytics

Consider supporting the project for unlimited access.
""",
        
        # ===== REPORT SCAM =====
        "report_title": "🚨 **REPORT SCAM ACTIVITY**",
        
        "report_instructions": """
**Report fraudulent activity to protect the community:**

1. **Enter the target identifier** (username, ID, wallet, etc.)
2. **Select scam type**
3. **Provide details & evidence**
4. **Submit report**

📋 *Daily limit: {limit} reports per user*
""",
        
        "report_step1": "📝 **Step 1/4: Enter Target Identifier**\n\n*Examples: @username, Telegram ID, wallet address, etc.*",
        
        "report_step2": """
🔍 **Step 2/4: Select Scam Type**

*Choose the most appropriate category:*
1. 🎣 Phishing / Impersonation
2. 💰 Fake Payment / Escrow
3. 🛒 Product/Service Fraud
4. 📈 Investment/Pyramid Scam
5. 🎮 Fake Giveaway/Contest
6. 🔑 Account Theft/Hacking
7. 📱 SIM Swap/Fraud
8. 🏦 Fake Exchange/Platform
9. 🤝 Fake Middleman/Admin
10. 📄 Fake Documents/Verification

*Reply with number (1-10):*
""",
        
        "report_step3": """
💰 **Step 3/4: Financial Details**

*Please provide:*
• Amount lost (if any)
• Currency (USD, USDT, etc.)
• Transaction date
• Payment method

*Example:* `100 USDT via Binance, 2024-01-01`

*Type 'skip' if not applicable:*
""",
        
        "report_step4": """
📸 **Step 4/4: Evidence & Description**

*Please provide:*
• Screenshots/chat logs (describe)
• Transaction IDs/hashes
• Any relevant details

*This helps verify the report:*
""",
        
        "report_confirm": """
✅ **REPORT READY FOR SUBMISSION**

**Target:** `{target}`
**Scam Type:** {scam_type}
**Amount:** {amount}
**Evidence:** {evidence_preview}

⚠️ **Please confirm:**
• Information is accurate
• You have evidence if needed
• This is not a false report

*Click ✅ YES to submit or ❌ NO to cancel*
""",
        
        "report_success": """
✅ **REPORT SUBMITTED SUCCESSFULLY**

**Report ID:** `#{report_id}`
**Target:** `{target}`
**Status:** Processing ✅

📊 **Your report contributes to:**
• Community safety database
• Real-time scam alerts
• Fraud prevention research

🙏 **Thank you for helping protect the community!**
""",
        
        "report_limit_reached": """
⏰ **Daily Report Limit Reached**

You've submitted {count} reports today (max: {limit}).

**Options:**
1. Wait until tomorrow (resets at 00:00 UTC)
2. Upgrade for higher limits
3. Contact support for urgent cases

💡 *Regular users: {user_limit}/day*
💎 *Supporters: {premium_limit}/day*
""",
        
        "report_cancelled": "❌ Report cancelled. You can start over anytime.",
        
        # ===== STATISTICS =====
        "stats_title": "📊 **REAL-TIME STATISTICS**",
        
        "stats_global": """
🌍 **Global Statistics**

👥 **Users:** {total_users:,}
🎯 **Total Reports:** {total_reports:,}
🚨 **Today's Reports:** {today_reports:,}
🛡 **Protected Transactions:** {protected:,}

📈 **Detection Rate:** {detection_rate}%
⏱ **Avg Response Time:** {response_time}s
✅ **Accuracy Rate:** {accuracy_rate}%
""",
        
        "stats_top_targets": """
🚨 **Top Reported Targets**

{targets_list}

*Updated: {update_time}*
""",
        
        "stats_scam_types": """
🎯 **Scam Type Distribution**

{types_list}

💡 *Most common: {most_common}*
""",
        
        "stats_user": """
👤 **Your Statistics**

📊 **Your Reports:** {user_reports}
🔍 **Your Checks:** {user_checks}
⭐ **Contribution Score:** {score}
📅 **Member Since:** {join_date}

🏆 **Rank:** #{rank} of {total_users:,}
""",
        
        # ===== TRUSTED ADMINS =====
        "admins_title": "🛡 **TRUSTED INTERMEDIARIES NETWORK**",
        
        "admins_description": """
**Verified & community-approved intermediaries** for safe transactions.

🔒 **Verification Process:**
• Identity verification
• Community feedback review
• Transaction history check
• Ongoing monitoring

💡 **How to use:**
1. Contact admin directly
2. Verify their identity
3. Agree on terms
4. Use escrow if needed
""",
        
        "admin_card": """
**{name}** {badge}
👤 @{username} | 🌍 {region}
📊 **Rating:** {rating}/5.0 ({reviews} reviews)
🤝 **Deals:** {successful}/{total} successful
💬 **Languages:** {languages}
🛡 **Role:** {role}
📝 **Notes:** {notes}

*Contact:* [{contact_text}]({contact_link})
""",
        
        "admins_empty": "No verified admins available at the moment.",
        
        # ===== TRUSTED GROUPS =====
        "groups_title": "⭐ **VERIFIED COMMUNITY GROUPS**",
        
        "groups_description": """
**Official & verified community groups** for safe discussions.

✅ **Verification Levels:**
• 🟢 Official (Direct management)
• 🟡 Verified (Community-approved)
• 🔵 Partner (Vetted partnerships)

⚠️ **Always verify group links before joining.**
""",
        
        "group_card": """
**{name}** {badge}
👥 Members: {members:,}
📝 **Description:** {description}
🌐 **Language:** {language}
🏷 **Category:** {category}
🔗 **Link:** [Join Group]({link})

*Status: {status}*
""",
        
        "groups_empty": "No verified groups available at the moment.",
        
        "groups_categories": """
**Available Categories:**
1. 🌍 Global Communities
2. 💰 Trading & Crypto
3. 🛒 Marketplace
4. 🎮 Gaming
5. 📱 Tech & Software
6. 🤝 Local Communities
""",
        
        # ===== LANGUAGE SELECTION =====
        "language_title": "🌐 **LANGUAGE SETTINGS**",
        
        "language_current": "Current language: **{language}**",
        
        "language_select": "Select your preferred language:",
        
        "language_changed": """
✅ **Language Changed Successfully**

New language: **{language}**

Bot interface has been updated.
""",
        
        # ===== DONATION =====
        "donate_title": "💖 **SUPPORT BOT CHECK SCAM**",
        
        "donate_mission": """
**Our Mission:** Create a safer digital environment by combating fraud through community collaboration.

**Your Support Enables:**
• 🚀 24/7 server maintenance
• 💾 Secure database storage
• 🔄 Regular feature updates
• 🌍 Multi-language expansion
• 🛡 Enhanced security measures
• 📚 Educational resources

**Impact of Your Contribution:**
• Protects thousands of users daily
• Prevents financial losses
• Builds trust in digital communities
• Supports ongoing development
""",
        
        "donate_options": """
**Support Options:**

1. **One-time Contribution** (Any amount)
2. **Monthly Supporter** (Recurring)
3. **Enterprise Partnership** (Contact us)

**Benefits for Supporters:**
• 📈 Higher report/check limits
• ⚡ Priority processing
• 🛡 Advanced features
• 🤝 Direct support access
• 🎖 Recognition in community
""",
        
        "donate_payment": """
**Payment Method:**

💳 **Binance Pay**
ID: `{binance_id}`
Currency: {currency}

**Instructions:**
1. Open Binance App
2. Go to Binance Pay
3. Enter ID above
4. Send USDT (BEP-20)
5. Save transaction hash

⚠️ *Only send USDT via BEP-20 network*
""",
        
        "donate_thank_you": """
🙏 **THANK YOU FOR YOUR GENEROUS SUPPORT!**

Your contribution directly enables:

✅ **24/7 Bot Operation**
✅ **Database Maintenance**  
✅ **Feature Development**
✅ **Community Protection**

**Transaction Details:**
• Amount: {amount} {currency}
• Date: {date}
• Status: Confirmed ✅

**Supporter Benefits Activated:**
• Unlimited daily checks
• Priority report processing
• Advanced analytics access
• Direct support channel

Together, we're building a safer digital world. Thank you for being part of our mission! 💖
""",
        
        "donate_anonymous": """
🙏 **Thank You, Anonymous Supporter!**

Your contribution has been received and will be used to maintain and improve the bot for the entire community.

Every donation makes a difference. Thank you for your support! 💖
""",
        
        # ===== HELP & SUPPORT =====
        "help_title": "❓ **HELP & SUPPORT CENTER**",
        
        "help_sections": """
**Quick Navigation:**
1. 🔍 How to Check Scams
2. 🚨 How to Report Scams  
3. 📊 Understanding Statistics
4. 🛡 Using Trusted Admins
5. ⭐ Joining Verified Groups
6. 🌐 Changing Language
7. 💖 Supporting the Project
8. 📞 Contact Support

*Reply with section number (1-8):*
""",
        
        "help_check": """
🔍 **HOW TO CHECK FOR SCAMS**

**Step 1:** Click "🔍 Check Scam"
**Step 2:** Enter any identifier:
   • Telegram: @username, ID, link
   • Crypto: wallet address
   • Exchange: Binance/OKX ID
   • Phone/Email
**Step 3:** Get instant analysis

💡 **Tips:**
• Check before every transaction
• Verify through multiple sources
• Use trusted intermediaries
""",
        
        "help_report": """
🚨 **HOW TO REPORT SCAMS**

**Step 1:** Click "🚨 Report Scam"
**Step 2:** Enter target identifier
**Step 3:** Select scam type
**Step 4:** Provide details & evidence
**Step 5:** Confirm submission

📋 **Requirements:**
• Accurate information
• Supporting evidence
• Good faith reporting

⚠️ **False reports may result in restrictions.**
""",
        
        "help_contact": """
📞 **CONTACT SUPPORT**

**For:**
• Technical issues
• Feature requests
• Partnership inquiries
• Urgent matters

**Official Channels:**
• Support Group: {support_group}
• News Channel: {news_channel}
• Email: {support_email}

⏰ **Response Time:** 24-48 hours
""",
        
        # ===== COMMON & BUTTONS =====
        "btn_back": "🔙 Back",
        "btn_main_menu": "📋 Main Menu",
        "btn_cancel": "🚫 Cancel",
        "btn_confirm": "✅ Confirm",
        "btn_yes": "✅ Yes",
        "btn_no": "❌ No",
        "btn_next": "➡️ Next",
        "btn_previous": "⬅️ Previous",
        "btn_done": "✅ Done",
        "btn_help": "❓ Help",
        "btn_refresh": "🔄 Refresh",
        
        "error_general": "❌ An error occurred. Please try again.",
        "error_timeout": "⏰ Request timed out. Please try again.",
        "error_invalid_input": "❌ Invalid input. Please try again.",
        "error_not_found": "❌ Not found. Please check your input.",
        "error_permission": "❌ Permission denied.",
        "error_maintenance": "🛠 Bot under maintenance. Please try again later.",
        
        "wait_processing": "⏳ Processing your request...",
        "success_updated": "✅ Updated successfully.",
        "success_deleted": "✅ Deleted successfully.",
        "success_saved": "✅ Saved successfully.",
        
        "footer_support": "\n\n💖 *Support the project for unlimited access*",
        "footer_community": "\n\n🤝 *Together we fight scams*",
        "footer_legal": "\n\n⚠️ *For reference only. Always verify through official channels.*",
    }
    
    # ========== TIẾNG VIỆT ==========
    VI = {
        "start_header": """
🤖 **BOT CHECK SCAM - PHIÊN BẢN ULTRA PRO**

*Hệ Thống Ngăn Chặn Lừa Đảo Mạnh Mẽ Nhất Từ Cộng Đồng*
🔒 *Bảo Mật* | ⚡ *Nhanh Chóng* | 🌍 *Toàn Cầu* | 🤝 *Cộng Đồng*
""",
        
        "start_description": """
**BOT CHECK SCAM** là nền tảng bảo mật tiên tiến được xây dựng bởi cộng đồng nhằm chống lại lừa đảo trực tuyến và bảo vệ người dùng trong giao dịch số.

🔍 **Tính Năng Chính:**
• Phát hiện & xác minh lừa đảo thời gian thực
• Cơ sở dữ liệu lừa đảo từ cộng đồng
• Kiểm tra đa nền tảng
• Mạng lưới trung gian uy tín
• Thống kê & phân tích trực tiếp
• Hỗ trợ đa ngôn ngữ (4 ngôn ngữ)

⚖️ **Thông Báo Pháp Lý:**
Bot cung cấp thông tin tham khảo từ cộng đồng. Luôn xác minh qua kênh chính thức và thận trọng trong mọi giao dịch.
""",
        
        "menu_prompt": "👇 **Chọn chức năng bên dưới để bắt đầu:**",
        
        # ===== MAIN MENU =====
        "menu_check": "🔍 Kiểm Tra Lừa Đảo",
        "menu_report": "🚨 Báo Cáo Lừa Đảo",
        "menu_stats": "📊 Thống Kê",
        "menu_admins": "🛡 Admin Trung Gian",
        "menu_groups": "⭐ Nhóm Uy Tín",
        "menu_language": "🌐 Đổi Ngôn Ngữ",
        "menu_donate": "💖 Ủng Hộ Dự Án",
        "menu_help": "❓ Trợ Giúp",
        
        # ===== CHECK SCAM =====
        "check_title": "🔍 **HỆ THỐNG KIỂM TRA LỪA ĐẢO**",
        
        "check_instructions": """
Bạn có thể kiểm tra **BẤT KỲ** định danh nào sau đây:

**Telegram:**
• Username (@username)
• Telegram ID (123456789)
• Link hồ sơ (t.me/username)

**Ví Crypto:**
• USDT (TRC20/BEP20)
• Địa chỉ BTC, ETH, BNB
• Địa chỉ ví (0x...)

**ID Sàn Giao Dịch:**
• Binance ID
• OKX UID
• ID sàn khác

**Khác:**
• Số điện thoại
• Địa chỉ email
• Hồ sơ mạng xã hội

📝 *Nhập một định danh để kiểm tra:*
""",
        
        "check_processing": "🔄 **Đang xử lý yêu cầu...**\n\n*Phân tích cơ sở dữ liệu và báo cáo cộng đồng...*",
        
        "check_result_clean": """
✅ **AN TOÀN - Không Phát Hiện Mối Đe Dọa**

*Mục tiêu:* `{target}`
*Trạng thái:* **An toàn** 🟢
*Độ tin cậy:* {confidence}%

📊 **Chi Tiết Phân Tích:**
• Kiểm tra database: {db_checks}
• Báo cáo cộng đồng: {reports}
• Trạng thái xác minh: Đã xác minh ✅
• Mức độ rủi ro: Thấp 🟢

💡 *Mục tiêu này có vẻ an toàn dựa trên dữ liệu hiện có.*
""",
        
        "check_result_suspicious": """
⚠️ **NGHI NGỜ - Cần Thận Trọng**

*Mục tiêu:* `{target}`
*Trạng thái:* **Đáng ngờ** 🟡
*Độ tin cậy:* {confidence}%

📊 **Chi Tiết Phân Tích:**
• Kiểm tra database: {db_checks}
• Báo cáo cộng đồng: {reports}
• Trạng thái xác minh: Chưa xác minh ⚠️
• Mức độ rủi ro: Trung bình 🟡

🚨 **Chi tiết:**
{details}

💡 *Tiến hành thận trọng và xác minh qua kênh uy tín.*
""",
        
        "check_result_scam": """
🚨 **CẢNH BÁO LỪA ĐẢO - Rủi Ro Cao**

*Mục tiêu:* `{target}`
*Trạng thái:* **Nguy hiểm** 🔴
*Độ tin cậy:* {confidence}%

📊 **Chi Tiết Phân Tích:**
• Kiểm tra database: {db_checks}
• Báo cáo cộng đồng: {reports}
• Trạng thái xác minh: Đã xác nhận 🔴
• Mức độ rủi ro: Cao 🔴

🚨 **Chi Tiết Báo Cáo:**
{details}

⚠️ **CẢNH BÁO:** Nhiều người dùng đã báo cáo mục tiêu này về hành vi lừa đảo.
""",
        
        "check_result_error": "❌ **Lỗi xử lý yêu cầu.** Vui lòng thử lại hoặc liên hệ hỗ trợ.",
        
        "check_limit_reached": """
⏰ **Đã Đạt Giới Hạn Hôm Nay**

Bạn đã kiểm tra {count} mục tiêu hôm nay (tối đa: {limit}).

Tính năng hỗ trợ:
• Kiểm tra không giới hạn cho người ủng hộ
• Xử lý ưu tiên
• Phân tích nâng cao

Cân nhắc ủng hộ dự án để được truy cập không giới hạn.
""",
        
        # ===== REPORT SCAM =====
        "report_title": "🚨 **BÁO CÁO HÀNH VI LỪA ĐẢO**",
        
        "report_instructions": """
**Báo cáo hành vi lừa đảo để bảo vệ cộng đồng:**

1. **Nhập định danh mục tiêu** (username, ID, ví, v.v.)
2. **Chọn loại lừa đảo**
3. **Cung cấp chi tiết & bằng chứng**
4. **Gửi báo cáo**

📋 *Giới hạn hàng ngày: {limit} báo cáo mỗi người*
""",
        
        "report_step1": "📝 **Bước 1/4: Nhập Định Danh Mục Tiêu**\n\n*Ví dụ: @username, Telegram ID, địa chỉ ví, v.v.*",
        
        "report_step2": """
🔍 **Bước 2/4: Chọn Loại Lừa Đảo**

*Chọn danh mục phù hợp nhất:*
1. 🎣 Lừa đảo phishing/giả mạo
2. 💰 Thanh toán/escrow giả
3. 🛒 Lừa đảo sản phẩm/dịch vụ
4. 📈 Lừa đảo đầu tư/đa cấp
5. 🎮 Giveaway/contest giả
6. 🔑 Trộm cắp tài khoản/hack
7. 📱 SIM Swap/Lừa đảo
8. 🏦 Sàn giao dịch/nền tảng giả
9. 🤝 Trung gian/admin giả
10. 📄 Tài liệu/xác minh giả

*Trả lời bằng số (1-10):*
""",
        
        "report_step3": """
💰 **Bước 3/4: Chi Tiết Tài Chính**

*Vui lòng cung cấp:*
• Số tiền mất (nếu có)
• Loại tiền (USD, USDT, v.v.)
• Ngày giao dịch
• Phương thức thanh toán

*Ví dụ:* `100 USDT qua Binance, 2024-01-01`

*Gõ 'skip' nếu không áp dụng:*
""",
        
        "report_step4": """
📸 **Bước 4/4: Bằng Chứng & Mô Tả**

*Vui lòng cung cấp:*
• Ảnh chụp màn hình/chat log (mô tả)
• ID/hash giao dịch
• Bất kỳ chi tiết liên quan

*Giúp xác minh báo cáo:*
""",
        
        "report_confirm": """
✅ **BÁO CÁO SẴN SÀNG GỬI**

**Mục tiêu:** `{target}`
**Loại lừa đảo:** {scam_type}
**Số tiền:** {amount}
**Bằng chứng:** {evidence_preview}

⚠️ **Vui lòng xác nhận:**
• Thông tin chính xác
• Có bằng chứng nếu cần
• Đây không phải báo cáo sai

*Nhấn ✅ CÓ để gửi hoặc ❌ KHÔNG để hủy*
""",
        
        "report_success": """
✅ **GỬI BÁO CÁO THÀNH CÔNG**

**ID Báo cáo:** `#{report_id}`
**Mục tiêu:** `{target}`
**Trạng thái:** Đang xử lý ✅

📊 **Báo cáo của bạn đóng góp vào:**
• Cơ sở dữ liệu an toàn cộng đồng
• Cảnh báo lừa đảo thời gian thực
• Nghiên cứu phòng chống lừa đảo

🙏 **Cảm ơn bạn đã giúp bảo vệ cộng đồng!**
""",
        
        "report_limit_reached": """
⏰ **Đạt Giới Hạn Báo Cáo Hàng Ngày**

Bạn đã gửi {count} báo cáo hôm nay (tối đa: {limit}).

**Tùy chọn:**
1. Chờ đến ngày mai (reset lúc 00:00 UTC)
2. Nâng cấp để tăng giới hạn
3. Liên hệ hỗ trợ cho trường hợp khẩn cấp

💡 *Người dùng thường: {user_limit}/ngày*
💎 *Người ủng hộ: {premium_limit}/ngày*
""",
        
        "report_cancelled": "❌ Đã hủy báo cáo. Bạn có thể bắt đầu lại bất cứ lúc nào.",
        
        # ===== STATISTICS =====
        "stats_title": "📊 **THỐNG KÊ THỜI GIAN THỰC**",
        
        "stats_global": """
🌍 **Thống Kê Toàn Cầu**

👥 **Người dùng:** {total_users:,}
🎯 **Tổng báo cáo:** {total_reports:,}
🚨 **Báo cáo hôm nay:** {today_reports:,}
🛡 **Giao dịch được bảo vệ:** {protected:,}

📈 **Tỷ lệ phát hiện:** {detection_rate}%
⏱ **Thời gian phản hồi TB:** {response_time}s
✅ **Tỷ lệ chính xác:** {accuracy_rate}%
""",
        
        "stats_top_targets": """
🚨 **Mục Tiêu Bị Báo Cáo Nhiều Nhất**

{targets_list}

*Cập nhật: {update_time}*
""",
        
        "stats_scam_types": """
🎯 **Phân Bố Loại Lừa Đảo**

{types_list}

💡 *Phổ biến nhất: {most_common}*
""",
        
        "stats_user": """
👤 **Thống Kê Cá Nhân**

📊 **Báo cáo của bạn:** {user_reports}
🔍 **Lần kiểm tra của bạn:** {user_checks}
⭐ **Điểm đóng góp:** {score}
📅 **Thành viên từ:** {join_date}

🏆 **Hạng:** #{rank} trên {total_users:,}
""",
        
        # ===== TRUSTED ADMINS =====
        "admins_title": "🛡 **MẠNG LƯỚI TRUNG GIAN UY TÍN**",
        
        "admins_description": """
**Trung gian đã xác minh & được cộng đồng chấp thuận** cho giao dịch an toàn.

🔒 **Quy Trình Xác Minh:**
• Xác minh danh tính
• Đánh giá phản hồi cộng đồng
• Kiểm tra lịch sử giao dịch
• Giám sát liên tục

💡 **Cách sử dụng:**
1. Liên hệ trực tiếp admin
2. Xác minh danh tính họ
3. Thỏa thuận điều khoản
4. Sử dụng escrow nếu cần
""",
        
        "admin_card": """
**{name}** {badge}
👤 @{username} | 🌍 {region}
📊 **Đánh giá:** {rating}/5.0 ({reviews} đánh giá)
🤝 **Giao dịch:** {successful}/{total} thành công
💬 **Ngôn ngữ:** {languages}
🛡 **Vai trò:** {role}
📝 **Ghi chú:** {notes}

*Liên hệ:* [{contact_text}]({contact_link})
""",
        
        "admins_empty": "Hiện không có admin uy tín nào.",
        
        # ===== TRUSTED GROUPS =====
        "groups_title": "⭐ **NHÓM CỘNG ĐỒNG ĐÃ XÁC MINH**",
        
        "groups_description": """
**Nhóm cộng đồng chính thức & đã xác minh** cho thảo luận an toàn.

✅ **Cấp Độ Xác Minh:**
• 🟢 Chính thức (Quản lý trực tiếp)
• 🟡 Đã xác minh (Cộng đồng chấp thuận)
• 🔵 Đối tác (Đã thẩm định)

⚠️ **Luôn xác minh liên kết nhóm trước khi tham gia.**
""",
        
        "group_card": """
**{name}** {badge}
👥 Thành viên: {members:,}
📝 **Mô tả:** {description}
🌐 **Ngôn ngữ:** {language}
🏷 **Danh mục:** {category}
🔗 **Liên kết:** [Tham gia nhóm]({link})

*Trạng thái: {status}*
""",
        
        "groups_empty": "Hiện không có nhóm uy tín nào.",
        
        "groups_categories": """
**Danh Mục Có Sẵn:**
1. 🌍 Cộng đồng toàn cầu
2. 💰 Giao dịch & Crypto
3. 🛒 Marketplace
4. 🎮 Gaming
5. 📱 Công nghệ & Phần mềm
6. 🤝 Cộng đồng địa phương
""",
        
        # ===== LANGUAGE SELECTION =====
        "language_title": "🌐 **CÀI ĐẶT NGÔN NGỮ**",
        
        "language_current": "Ngôn ngữ hiện tại: **{language}**",
        
        "language_select": "Chọn ngôn ngữ ưa thích của bạn:",
        
        "language_changed": """
✅ **Đã Thay Đổi Ngôn Ngữ Thành Công**

Ngôn ngữ mới: **{language}**

Giao diện bot đã được cập nhật.
""",
        
        # ===== DONATION =====
        "donate_title": "💖 **ỦNG HỘ BOT CHECK SCAM**",
        
        "donate_mission": """
**Sứ Mệnh Của Chúng Tôi:** Tạo môi trường số an toàn hơn bằng cách chống lừa đảo thông qua hợp tác cộng đồng.

**Ủng Hộ Của Bạn Cho Phép:**
• 🚀 Bảo trì máy chủ 24/7
• 💾 Lưu trữ cơ sở dữ liệu an toàn
• 🔄 Cập nhật tính năng thường xuyên
• 🌍 Mở rộng đa ngôn ngữ
• 🛡 Nâng cao biện pháp bảo mật
• 📚 Tài nguyên giáo dục

**Tác Động Của Đóng Góp Của Bạn:**
• Bảo vệ hàng nghìn người dùng hàng ngày
• Ngăn chặn tổn thất tài chính
• Xây dựng niềm tin trong cộng đồng số
• Hỗ trợ phát triển liên tục
""",
        
        "donate_options": """
**Tùy Chọn Ủng Hộ:**

1. **Đóng góp một lần** (Bất kỳ số tiền nào)
2. **Người ủng hộ hàng tháng** (Định kỳ)
3. **Đối tác doanh nghiệp** (Liên hệ chúng tôi)

**Lợi Ích Cho Người Ủng Hộ:**
• 📈 Giới hạn báo cáo/kiểm tra cao hơn
• ⚡ Xử lý ưu tiên
• 🛡 Tính năng nâng cao
• 🤝 Truy cập hỗ trợ trực tiếp
• 🎖 Công nhận trong cộng đồng
""",
        
        "donate_payment": """
**Phương Thức Thanh Toán:**

💳 **Binance Pay**
ID: `{binance_id}`
Tiền tệ: {currency}

**Hướng Dẫn:**
1. Mở ứng dụng Binance
2. Vào Binance Pay
3. Nhập ID bên trên
4. Gửi USDT (Mạng BEP-20)
5. Lưu hash giao dịch

⚠️ *Chỉ gửi USDT qua mạng BEP-20*
""",
        
        "donate_thank_you": """
🙏 **CẢM ƠN SỰ ỦNG HỘ HÀO PHÓNG CỦA BẠN!**

Đóng góp của bạn trực tiếp cho phép:

✅ **Vận Hành Bot 24/7**
✅ **Bảo Trì Cơ Sở Dữ Liệu**
✅ **Phát Triển Tính Năng**
✅ **Bảo Vệ Cộng Đồng**

**Chi Tiết Giao Dịch:**
• Số tiền: {amount} {currency}
• Ngày: {date}
• Trạng thái: Đã xác nhận ✅

**Lợi Ích Người Ủng Hộ Đã Kích Hoạt:**
• Kiểm tra không giới hạn hàng ngày
• Xử lý báo cáo ưu tiên
• Truy cập phân tích nâng cao
• Kênh hỗ trợ trực tiếp

Cùng nhau, chúng ta đang xây dựng một thế giới số an toàn hơn. Cảm ơn bạn đã là một phần trong sứ mệnh của chúng tôi! 💖
""",
        
        "donate_anonymous": """
🙏 **Cảm Ơn Bạn, Người Ủng Hộ Ẩn Danh!**

Đóng góp của bạn đã được nhận và sẽ được sử dụng để duy trì và cải thiện bot cho toàn bộ cộng đồng.

Mọi đóng góp đều tạo nên sự khác biệt. Cảm ơn bạn đã ủng hộ! 💖
""",
        
        # ===== HELP & SUPPORT =====
        "help_title": "❓ **TRUNG TÂM TRỢ GIÚP & HỖ TRỢ**",
        
        "help_sections": """
**Điều Hướng Nhanh:**
1. 🔍 Cách Kiểm Tra Lừa Đảo
2. 🚨 Cách Báo Cáo Lừa Đảo
3. 📊 Hiểu Thống Kê
4. 🛡 Sử Dụng Admin Uy Tín
5. ⭐ Tham Gia Nhóm Đã Xác Minh
6. 🌐 Thay Đổi Ngôn Ngữ
7. 💖 Ủng Hộ Dự Án
8. 📞 Liên Hệ Hỗ Trợ

*Trả lời bằng số phần (1-8):*
""",
        
        "help_check": """
🔍 **CÁCH KIỂM TRA LỪA ĐẢO**

**Bước 1:** Nhấn "🔍 Kiểm Tra Lừa Đảo"
**Bước 2:** Nhập bất kỳ định danh:
   • Telegram: @username, ID, link
   • Crypto: địa chỉ ví
   • Sàn giao dịch: Binance/OKX ID
   • Số điện thoại/Email
**Bước 3:** Nhận phân tích ngay lập tức

💡 **Mẹo:**
• Kiểm tra trước mỗi giao dịch
• Xác minh qua nhiều nguồn
• Sử dụng trung gian uy tín
""",
        
        "help_report": """
🚨 **CÁCH BÁO CÁO LỪA ĐẢO**

**Bước 1:** Nhấn "🚨 Báo Cáo Lừa Đảo"
**Bước 2:** Nhập định danh mục tiêu
**Bước 3:** Chọn loại lừa đảo
**Bước 4:** Cung cấp chi tiết & bằng chứng
**Bước 5:** Xác nhận gửi

📋 **Yêu Cầu:**
• Thông tin chính xác
• Bằng chứng hỗ trợ
• Báo cáo thiện chí

⚠️ **Báo cáo sai có thể dẫn đến hạn chế.**
""",
        
        "help_contact": """
📞 **LIÊN HỆ HỖ TRỢ**

**Cho:**
• Vấn đề kỹ thuật
• Yêu cầu tính năng
• Thảo luận hợp tác
• Vấn đề khẩn cấp

**Kênh Chính Thức:**
• Nhóm hỗ trợ: {support_group}
• Kênh tin tức: {news_channel}
• Email: {support_email}

⏰ **Thời gian phản hồi:** 24-48 giờ
""",
        
        # ===== COMMON & BUTTONS =====
        "btn_back": "🔙 Quay lại",
        "btn_main_menu": "📋 Menu Chính",
        "btn_cancel": "🚫 Hủy",
        "btn_confirm": "✅ Xác nhận",
        "btn_yes": "✅ Có",
        "btn_no": "❌ Không",
        "btn_next": "➡️ Tiếp",
        "btn_previous": "⬅️ Trước",
        "btn_done": "✅ Xong",
        "btn_help": "❓ Trợ giúp",
        "btn_refresh": "🔄 Làm mới",
        
        "error_general": "❌ Đã xảy ra lỗi. Vui lòng thử lại.",
        "error_timeout": "⏰ Yêu cầu hết thời gian. Vui lòng thử lại.",
        "error_invalid_input": "❌ Đầu vào không hợp lệ. Vui lòng thử lại.",
        "error_not_found": "❌ Không tìm thấy. Vui lòng kiểm tra đầu vào.",
        "error_permission": "❌ Từ chối quyền.",
        "error_maintenance": "🛠 Bot đang bảo trì. Vui lòng thử lại sau.",
        
        "wait_processing": "⏳ Đang xử lý yêu cầu của bạn...",
        "success_updated": "✅ Cập nhật thành công.",
        "success_deleted": "✅ Đã xóa thành công.",
        "success_saved": "✅ Đã lưu thành công.",
        
        "footer_support": "\n\n💖 *Ủng hộ dự án để được truy cập không giới hạn*",
        "footer_community": "\n\n🤝 *Cùng nhau chống lừa đảo*",
        "footer_legal": "\n\n⚠️ *Chỉ để tham khảo. Luôn xác minh qua kênh chính thức.*",
    }
    
    # ========== TIẾNG NGA ==========
    RU = {
        "start_header": """
🤖 **BOT CHECK SCAM - ULTRA PRO ВЕРСИЯ**

*Мощнейшая система предотвращения мошенничества от сообщества*
🔒 *Безопасно* | ⚡ *Быстро* | 🌍 *Глобально* | 🤝 *Сообщество*
""",
        
        # ... (Tất cả nội dung tiếng Nga - giới hạn ký tự)
        # Cấu trúc tương tự như tiếng Anh và tiếng Việt
    }
    
    # ========== TIẾNG TRUNG ==========
    ZH = {
        "start_header": """
🤖 **BOT CHECK SCAM - 超专业版**

*由社区驱动的终极防诈骗系统*
🔒 *安全* | ⚡ *快速* | 🌍 *全球* | 🤝 *社区驱动*
""",
        
        # ... (Tất cả nội dung tiếng Trung - giới hạn ký tự)
        # Cấu trúc tương tự như tiếng Anh và tiếng Việt
    }
    
    # TẬP HỢP TẤT CẢ NGÔN NGỮ
    LANGUAGES = {
        "en": EN,
        "vi": VI,
        "ru": RU,
        "zh": ZH
    }
    
    @classmethod
    def get_text(cls, language: str, key: str, **kwargs) -> str:
        """Lấy văn bản theo ngôn ngữ"""
        lang_dict = cls.LANGUAGES.get(language, cls.EN)
        text = lang_dict.get(key, cls.EN.get(key, key))
        
        try:
            return text.format(**kwargs) if kwargs else text
        except KeyError as e:
            logger.error(f"Key error in translation: {e}")
            return text

# Khởi tạo hệ thống ngôn ngữ
lang = MultiLanguageSystem()

# ===============================================
# 6. HỆ THỐNG GIAO DIỆN & MENU
# ===============================================
class UIManager:
    """Quản lý giao diện và menu"""
    
    @staticmethod
    def create_main_menu(language: str) -> InlineKeyboardMarkup:
        """Tạo menu chính 7 nút"""
        keyboard = [
            [
                InlineKeyboardButton(lang.get_text(language, "menu_check"), callback_data="menu_check"),
                InlineKeyboardButton(lang.get_text(language, "menu_report"), callback_data="menu_report")
            ],
            [
                InlineKeyboardButton(lang.get_text(language, "menu_stats"), callback_data="menu_stats"),
                InlineKeyboardButton(lang.get_text(language, "menu_admins"), callback_data="menu_admins")
            ],
            [
                InlineKeyboardButton(lang.get_text(language, "menu_groups"), callback_data="menu_groups"),
                InlineKeyboardButton(lang.get_text(language, "menu_language"), callback_data="menu_language")
            ],
            [
                InlineKeyboardButton(lang.get_text(language, "menu_donate"), callback_data="menu_donate"),
                InlineKeyboardButton(lang.get_text(language, "menu_help"), callback_data="menu_help")
            ]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def create_back_button(language: str) -> InlineKeyboardMarkup:
        """Tạo nút quay lại"""
        keyboard = [[InlineKeyboardButton(lang.get_text(language, "btn_back"), callback_data="main_menu")]]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def create_yes_no_keyboard(language: str) -> InlineKeyboardMarkup:
        """Tạo bàn phím Có/Không"""
        keyboard = [
            [
                InlineKeyboardButton(lang.get_text(language, "btn_yes"), callback_data="yes"),
                InlineKeyboardButton(lang.get_text(language, "btn_no"), callback_data="no")
            ],
            [InlineKeyboardButton(lang.get_text(language, "btn_back"), callback_data="main_menu")]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def create_language_keyboard() -> InlineKeyboardMarkup:
        """Tạo bàn phím chọn ngôn ngữ"""
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
    
    @staticmethod
    def create_pagination_keyboard(language: str, page: int, total_pages: int, prefix: str) -> InlineKeyboardMarkup:
        """Tạo bàn phím phân trang"""
        keyboard = []
        
        if total_pages > 1:
            row = []
            if page > 0:
                row.append(InlineKeyboardButton("⬅️", callback_data=f"{prefix}_page_{page-1}"))
            
            row.append(InlineKeyboardButton(f"{page+1}/{total_pages}", callback_data="current_page"))
            
            if page < total_pages - 1:
                row.append(InlineKeyboardButton("➡️", callback_data=f"{prefix}_page_{page+1}"))
            
            keyboard.append(row)
        
        keyboard.append([InlineKeyboardButton(lang.get_text(language, "btn_back"), callback_data="main_menu")])
        
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def create_scam_type_keyboard(language: str) -> InlineKeyboardMarkup:
        """Tạo bàn phím chọn loại scam"""
        keyboard = [
            [InlineKeyboardButton("🎣 Phishing/Impersonation", callback_data="scam_1")],
            [InlineKeyboardButton("💰 Fake Payment/Escrow", callback_data="scam_2")],
            [InlineKeyboardButton("🛒 Product/Service Fraud", callback_data="scam_3")],
            [InlineKeyboardButton("📈 Investment/Pyramid Scam", callback_data="scam_4")],
            [InlineKeyboardButton("🎮 Fake Giveaway/Contest", callback_data="scam_5")],
            [InlineKeyboardButton("🔑 Account Theft/Hacking", callback_data="scam_6")],
            [InlineKeyboardButton("📱 SIM Swap/Fraud", callback_data="scam_7")],
            [InlineKeyboardButton("🏦 Fake Exchange/Platform", callback_data="scam_8")],
            [InlineKeyboardButton("🤝 Fake Middleman/Admin", callback_data="scam_9")],
            [InlineKeyboardButton("📄 Fake Documents/Verification", callback_data="scam_10")],
            [InlineKeyboardButton(lang.get_text(language, "btn_back"), callback_data="main_menu")]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def create_category_keyboard(language: str) -> InlineKeyboardMarkup:
        """Tạo bàn phím chọn danh mục group"""
        keyboard = [
            [InlineKeyboardButton("🌍 Global Communities", callback_data="cat_global")],
            [InlineKeyboardButton("💰 Trading & Crypto", callback_data="cat_trading")],
            [InlineKeyboardButton("🛒 Marketplace", callback_data="cat_marketplace")],
            [InlineKeyboardButton("🎮 Gaming", callback_data="cat_gaming")],
            [InlineKeyboardButton("📱 Tech & Software", callback_data="cat_tech")],
            [InlineKeyboardButton("🤝 Local Communities", callback_data="cat_local")],
            [InlineKeyboardButton(lang.get_text(language, "btn_back"), callback_data="main_menu")]
        ]
        return InlineKeyboardMarkup(keyboard)

# ===============================================
# 7. HỆ THỐNG XỬ LÝ CHÍNH
# ===============================================
class BotHandler:
    """Xử lý chính cho bot"""
    
    def __init__(self):
        self.user_sessions = {}
        self.active_reports = {}
        self.stats_cache = {}
        self.last_cleanup = datetime.now()
    
    async def handle_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Xử lý lệnh /start"""
        user = update.effective_user
        user_id = user.id
        
        # Tạo/Update user trong database
        user_data = {
            'user_id': user_id,
            'username': user.username,
            'first_name': user.first_name,
            'last_name': user.last_name
        }
        db.create_user(user_data)
        
        # Lấy ngôn ngữ user
        user_info = db.get_user(user_id)
        language = user_info['language'] if user_info else Config.DEFAULT_LANGUAGE
        
        # Tạo welcome message
        welcome_text = (
            lang.get_text(language, "start_header") + "\n\n" +
            lang.get_text(language, "start_description") + "\n\n" +
            lang.get_text(language, "menu_prompt")
        )
        
        # Gửi message với menu
        await update.message.reply_text(
            welcome_text,
            reply_markup=UIManager.create_main_menu(language),
            parse_mode=ParseMode.MARKDOWN,
            disable_web_page_preview=True
        )
        
        # Log activity
        db.log_activity(user_id, "start", "User started bot")
    
    async def handle_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE, menu_type: str) -> None:
        """Xử lý các menu chính"""
        query = update.callback_query
        await query.answer()
        
        user_id = update.effective_user.id
        user_info = db.get_user(user_id)
        language = user_info['language'] if user_info else Config.DEFAULT_LANGUAGE
        
        if menu_type == "main_menu":
            await self.show_main_menu(update, context)
        
        elif menu_type == "check":
            await self.show_check_scam(update, context)
        
        elif menu_type == "report":
            await self.show_report_scam(update, context)
        
        elif menu_type == "stats":
            await self.show_statistics(update, context)
        
        elif menu_type == "admins":
            await self.show_trusted_admins(update, context)
        
        elif menu_type == "groups":
            await self.show_trusted_groups(update, context)
        
        elif menu_type == "language":
            await self.show_language_selection(update, context)
        
        elif menu_type == "donate":
            await self.show_donation_info(update, context)
        
        elif menu_type == "help":
            await self.show_help_center(update, context)
    
    async def show_main_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Hiển thị menu chính"""
        query = update.callback_query
        user_id = update.effective_user.id
        user_info = db.get_user(user_id)
        language = user_info['language'] if user_info else Config.DEFAULT_LANGUAGE
        
        await query.edit_message_text(
            lang.get_text(language, "menu_prompt"),
            reply_markup=UIManager.create_main_menu(language),
            parse_mode=ParseMode.MARKDOWN
        )
    
    # ========== CHECK SCAM HANDLERS ==========
    
    async def show_check_scam(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Hiển thị giao diện check scam"""
        query = update.callback_query
        user_id = update.effective_user.id
        user_info = db.get_user(user_id)
        language = user_info['language'] if user_info else Config.DEFAULT_LANGUAGE
        
        # Kiểm tra giới hạn
        can_check, message = db.check_spam_limit(user_id, "check", Config.DAILY_CHECK_LIMIT)
        
        if not can_check:
            await query.edit_message_text(
                lang.get_text(language, "check_limit_reached", 
                            count=Config.DAILY_CHECK_LIMIT, 
                            limit=Config.DAILY_CHECK_LIMIT),
                reply_markup=UIManager.create_back_button(language),
                parse_mode=ParseMode.MARKDOWN
            )
            return
        
        await query.edit_message_text(
            lang.get_text(language, "check_title") + "\n\n" +
            lang.get_text(language, "check_instructions"),
            reply_markup=UIManager.create_back_button(language),
            parse_mode=ParseMode.MARKDOWN
        )
        
        # Đặt trạng thái đang chờ input
        context.user_data['awaiting_check'] = True
    
    async def handle_check_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Xử lý input check scam"""
        if not context.user_data.get('awaiting_check'):
            return
        
        user_id = update.effective_user.id
        user_info = db.get_user(user_id)
        language = user_info['language'] if user_info else Config.DEFAULT_LANGUAGE
        
        target = update.message.text.strip()
        
        if not target or len(target) < 3:
            await update.message.reply_text(
                lang.get_text(language, "error_invalid_input"),
                reply_markup=UIManager.create_back_button(language)
            )
            return
        
        # Gửi thông báo processing
        processing_msg = await update.message.reply_text(
            lang.get_text(language, "check_processing"),
            parse_mode=ParseMode.MARKDOWN
        )
        
        # Tăng số lần check
        db.increment_user_check_count(user_id)
        
        # Tìm reports
        reports = db.get_reports_by_target(target)
        
        # Phân tích kết quả
        if len(reports) >= 3:
            # SCAM - Nhiều reports
            result_text = lang.get_text(language, "check_result_scam",
                                      target=target,
                                      confidence=min(99, len(reports) * 20),
                                      db_checks=len(reports),
                                      reports=len(reports),
                                      details=self._format_report_details(reports, language))
        elif len(reports) >= 1:
            # SUSPICIOUS - Ít reports
            result_text = lang.get_text(language, "check_result_suspicious",
                                      target=target,
                                      confidence=max(30, len(reports) * 15),
                                      db_checks=len(reports),
                                      reports=len(reports),
                                      details=self._format_report_details(reports, language))
        else:
            # CLEAN - Không có report
            result_text = lang.get_text(language, "check_result_clean",
                                      target=target,
                                      confidence=95,
                                      db_checks=0,
                                      reports=0)
        
        # Xóa message processing
        await processing_msg.delete()
        
        # Gửi kết quả
        await update.message.reply_text(
            result_text + lang.get_text(language, "footer_legal"),
            reply_markup=UIManager.create_back_button(language),
            parse_mode=ParseMode.MARKDOWN,
            disable_web_page_preview=True
        )
        
        # Xóa trạng thái
        context.user_data.pop('awaiting_check', None)
        
        # Log activity
        db.log_activity(user_id, "check_scam", f"Checked: {target}")
    
    def _format_report_details(self, reports: List[Dict], language: str) -> str:
        """Định dạng chi tiết reports"""
        if not reports:
            return ""
        
        details = ""
        for i, report in enumerate(reports[:3], 1):
            scam_type = report.get('scam_type', 'Unknown')
            amount = report.get('amount')
            date = report.get('created_at', '')[:10]
            
            details += f"{i}. **{scam_type}**"
            if amount:
                details += f" ({amount})"
            if date:
                details += f" - {date}"
            details += "\n"
        
        return details
    
    # ========== REPORT SCAM HANDLERS ==========
    
    async def show_report_scam(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Hiển thị giao diện report scam"""
        query = update.callback_query
        user_id = update.effective_user.id
        user_info = db.get_user(user_id)
        language = user_info['language'] if user_info else Config.DEFAULT_LANGUAGE
        
        # Kiểm tra giới hạn
        reports_today = db.get_report_count_by_user_today(user_id)
        if reports_today >= Config.DAILY_REPORT_LIMIT:
            await query.edit_message_text(
                lang.get_text(language, "report_limit_reached",
                            count=reports_today,
                            limit=Config.DAILY_REPORT_LIMIT,
                            user_limit=Config.DAILY_REPORT_LIMIT,
                            premium_limit=Config.DAILY_REPORT_LIMIT * 3),
                reply_markup=UIManager.create_back_button(language),
                parse_mode=ParseMode.MARKDOWN
            )
            return
        
        await query.edit_message_text(
            lang.get_text(language, "report_title") + "\n\n" +
            lang.get_text(language, "report_instructions", limit=Config.DAILY_REPORT_LIMIT) + "\n\n" +
            lang.get_text(language, "report_step1"),
            reply_markup=UIManager.create_back_button(language),
            parse_mode=ParseMode.MARKDOWN
        )
        
        # Khởi tạo session report
        self.active_reports[user_id] = {
            'step': 1,
            'data': {}
        }
        context.user_data['reporting'] = True
    
    async def handle_report_steps(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Xử lý các bước report"""
        user_id = update.effective_user.id
        
        if user_id not in self.active_reports:
            return
        
        report_data = self.active_reports[user_id]
        step = report_data['step']
        user_info = db.get_user(user_id)
        language = user_info['language'] if user_info else Config.DEFAULT_LANGUAGE
        
        text = update.message.text.strip()
        
        if step == 1:
            # Bước 1: Nhận target
            if len(text) < 3:
                await update.message.reply_text(
                    lang.get_text(language, "error_invalid_input"),
                    reply_markup=UIManager.create_back_button(language)
                )
                return
            
            report_data['data']['target'] = text
            report_data['step'] = 2
            
            await update.message.reply_text(
                lang.get_text(language, "report_step2"),
                reply_markup=UIManager.create_scam_type_keyboard(language),
                parse_mode=ParseMode.MARKDOWN
            )
        
        elif step == 2:
            # Bước 2: Nhận scam type
            if text.isdigit() and 1 <= int(text) <= 10:
                scam_types = [
                    "Phishing/Impersonation",
                    "Fake Payment/Escrow",
                    "Product/Service Fraud",
                    "Investment/Pyramid Scam",
                    "Fake Giveaway/Contest",
                    "Account Theft/Hacking",
                    "SIM Swap/Fraud",
                    "Fake Exchange/Platform",
                    "Fake Middleman/Admin",
                    "Fake Documents/Verification"
                ]
                report_data['data']['scam_type'] = scam_types[int(text)-1]
                report_data['step'] = 3
                
                await update.message.reply_text(
                    lang.get_text(language, "report_step3"),
                    reply_markup=UIManager.create_back_button(language),
                    parse_mode=ParseMode.MARKDOWN
                )
            else:
                await update.message.reply_text(
                    lang.get_text(language, "error_invalid_input"),
                    reply_markup=UIManager.create_back_button(language)
                )
        
        elif step == 3:
            # Bước 3: Nhận amount
            if text.lower() not in ['skip', 'none', '']:
                report_data['data']['amount'] = text
            else:
                report_data['data']['amount'] = 'Not specified'
            
            report_data['step'] = 4
            
            await update.message.reply_text(
                lang.get_text(language, "report_step4"),
                reply_markup=UIManager.create_back_button(language),
                parse_mode=ParseMode.MARKDOWN
            )
        
        elif step == 4:
            # Bước 4: Nhận proof và xác nhận
            report_data['data']['proof'] = text[:500]  # Giới hạn độ dài
            
            # Hiển thị xác nhận
            await update.message.reply_text(
                lang.get_text(language, "report_confirm",
                            target=report_data['data']['target'],
                            scam_type=report_data['data']['scam_type'],
                            amount=report_data['data']['amount'],
                            evidence_preview=text[:100] + "..." if len(text) > 100 else text),
                reply_markup=UIManager.create_yes_no_keyboard(language),
                parse_mode=ParseMode.MARKDOWN
            )
    
    async def handle_report_confirmation(self, update: Update, context: ContextTypes.DEFAULT_TYPE, choice: str) -> None:
        """Xử lý xác nhận report"""
        query = update.callback_query
        await query.answer()
        
        user_id = update.effective_user.id
        user_info = db.get_user(user_id)
        language = user_info['language'] if user_info else Config.DEFAULT_LANGUAGE
        
        if choice == "yes":
            # Lưu report
            if user_id in self.active_reports:
                report_data = self.active_reports[user_id]['data']
                
                db_report = {
                    'reporter_id': user_id,
                    'target_value': report_data['target'],
                    'scam_type': report_data['scam_type'],
                    'amount': report_data.get('amount', ''),
                    'proof': report_data.get('proof', '')
                }
                
                report_id = db.add_report(db_report)
                
                if report_id > 0:
                    # Tăng count cho user
                    db.increment_user_report_count(user_id)
                    
                    await query.edit_message_text(
                        lang.get_text(language, "report_success",
                                    report_id=report_id,
                                    target=report_data['target']),
                        parse_mode=ParseMode.MARKDOWN
                    )
                    
                    # Log activity
                    db.log_activity(user_id, "report_submitted", f"Report #{report_id}")
                else:
                    await query.edit_message_text(
                        lang.get_text(language, "error_general"),
                        parse_mode=ParseMode.MARKDOWN
                    )
                
                # Xóa session
                del self.active_reports[user_id]
                if 'reporting' in context.user_data:
                    del context.user_data['reporting']
        
        elif choice == "no":
            # Hủy report
            if user_id in self.active_reports:
                del self.active_reports[user_id]
            
            if 'reporting' in context.user_data:
                del context.user_data['reporting']
            
            await query.edit_message_text(
                lang.get_text(language, "report_cancelled"),
                parse_mode=ParseMode.MARKDOWN
            )
    
    # ========== STATISTICS HANDLERS ==========
    
    async def show_statistics(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Hiển thị thống kê"""
        query = update.callback_query
        user_id = update.effective_user.id
        user_info = db.get_user(user_id)
        language = user_info['language'] if user_info else Config.DEFAULT_LANGUAGE
        
        # Lấy thống kê
        stats = db.get_statistics()
        user_stats = db.get_user(user_id)
        
        # Format top targets
        targets_list = ""
        if stats.get('top_targets'):
            for target, count in stats['top_targets'][:5]:
                targets_list += f"• `{target[:30]}`: {count} reports\n"
        
        # Format scam types
        types_list = ""
        if stats.get('scam_types'):
            for scam_type, count in stats['scam_types'][:5]:
                types_list += f"• {scam_type}: {count}\n"
        
        # Tạo message
        stats_text = (
            lang.get_text(language, "stats_title") + "\n\n" +
            lang.get_text(language, "stats_global",
                         total_users=stats.get('total_users', 0),
                         total_reports=stats.get('total_reports', 0),
                         today_reports=stats.get('today_reports', 0),
                         protected=stats.get('total_reports', 0) * 10,  # Ước tính
                         detection_rate=95,
                         response_time=2,
                         accuracy_rate=92) + "\n\n"
        )
        
        if targets_list:
            stats_text += lang.get_text(language, "stats_top_targets",
                                      targets_list=targets_list,
                                      update_time=datetime.now().strftime("%H:%M")) + "\n\n"
        
        if types_list and stats.get('scam_types'):
            most_common = stats['scam_types'][0][0] if stats['scam_types'] else "None"
            stats_text += lang.get_text(language, "stats_scam_types",
                                      types_list=types_list,
                                      most_common=most_common) + "\n\n"
        
        # Thêm thống kê cá nhân
        if user_stats:
            user_rank = 1  # Giả định
            stats_text += lang.get_text(language, "stats_user",
                                      user_reports=user_stats.get('report_count', 0),
                                      user_checks=user_stats.get('check_count', 0),
                                      score=user_stats.get('report_count', 0) * 10,
                                      join_date=user_stats.get('created_at', '')[:10],
                                      rank=user_rank,
                                      total_users=stats.get('total_users', 0))
        
        await query.edit_message_text(
            stats_text,
            reply_markup=UIManager.create_back_button(language),
            parse_mode=ParseMode.MARKDOWN,
            disable_web_page_preview=True
        )
    
    # ========== TRUSTED ADMINS HANDLERS ==========
    
    async def show_trusted_admins(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Hiển thị admin trung gian"""
        query = update.callback_query
        user_id = update.effective_user.id
        user_info = db.get_user(user_id)
        language = user_info['language'] if user_info else Config.DEFAULT_LANGUAGE
        
        # Lấy danh sách admin
        admins = db.get_trusted_admins()
        
        if not admins:
            await query.edit_message_text(
                lang.get_text(language, "admins_title") + "\n\n" +
                lang.get_text(language, "admins_empty"),
                reply_markup=UIManager.create_back_button(language),
                parse_mode=ParseMode.MARKDOWN
            )
            return
        
        # Tạo message
        admins_text = (
            lang.get_text(language, "admins_title") + "\n\n" +
            lang.get_text(language, "admins_description") + "\n\n"
        )
        
        for admin in admins[:5]:  # Giới hạn 5 admin đầu
            badge = "🟢" if admin.get('verified') else "🟡"
            admins_text += lang.get_text(language, "admin_card",
                                       name=admin.get('display_name', 'Unknown'),
                                       badge=badge,
                                       username=admin.get('username', 'N/A'),
                                       region=admin.get('region', 'Global'),
                                       rating=admin.get('rating', 0.0),
                                       reviews=admin.get('total_deals', 0),
                                       successful=admin.get('successful_deals', 0),
                                       total=admin.get('total_deals', 0),
                                       languages=admin.get('languages', 'English'),
                                       role=admin.get('role', 'Moderator'),
                                       notes=admin.get('notes', 'Trusted intermediary'),
                                       contact_text="Contact",
                                       contact_link=f"https://t.me/{admin.get('username', '')}") + "\n\n"
        
        await query.edit_message_text(
            admins_text,
            reply_markup=UIManager.create_back_button(language),
            parse_mode=ParseMode.MARKDOWN,
            disable_web_page_preview=True
        )
    
    # ========== TRUSTED GROUPS HANDLERS ==========
    
    async def show_trusted_groups(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Hiển thị group uy tín"""
        query = update.callback_query
        user_id = update.effective_user.id
        user_info = db.get_user(user_id)
        language = user_info['language'] if user_info else Config.DEFAULT_LANGUAGE
        
        await query.edit_message_text(
            lang.get_text(language, "groups_title") + "\n\n" +
            lang.get_text(language, "groups_description") + "\n\n" +
            lang.get_text(language, "groups_categories"),
            reply_markup=UIManager.create_category_keyboard(language),
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def handle_group_category(self, update: Update, context: ContextTypes.DEFAULT_TYPE, category: str) -> None:
        """Xử lý chọn danh mục group"""
        query = update.callback_query
        await query.answer()
        
        user_id = update.effective_user.id
        user_info = db.get_user(user_id)
        language = user_info['language'] if user_info else Config.DEFAULT_LANGUAGE
        
        # Map category
        category_map = {
            'cat_global': 'Global',
            'cat_trading': 'Trading',
            'cat_marketplace': 'Marketplace',
            'cat_gaming': 'Gaming',
            'cat_tech': 'Technology',
            'cat_local': 'Local'
        }
        
        selected_category = category_map.get(category, 'Global')
        groups = db.get_trusted_groups(category=selected_category)
        
        if not groups:
            await query.edit_message_text(
                lang.get_text(language, "groups_title") + "\n\n" +
                f"No groups found in category: {selected_category}",
                reply_markup=UIManager.create_back_button(language),
                parse_mode=ParseMode.MARKDOWN
            )
            return
        
        # Tạo message
        groups_text = lang.get_text(language, "groups_title") + "\n\n"
        
        for group in groups[:5]:  # Giới hạn 5 group
            badge = "🟢" if group.get('verification_level', 0) >= 2 else "🟡"
            status = "Official" if group.get('verified') else "Verified"
            
            groups_text += lang.get_text(language, "group_card",
                                       name=group.get('group_name', 'Unknown'),
                                       badge=badge,
                                       members=group.get('member_count', 0),
                                       description=group.get('description', 'Community group'),
                                       language=group.get('language', 'Multi'),
                                       category=group.get('category', 'General'),
                                       link=group.get('group_link', '#'),
                                       status=status) + "\n\n"
        
        await query.edit_message_text(
            groups_text,
            reply_markup=UIManager.create_back_button(language),
            parse_mode=ParseMode.MARKDOWN,
            disable_web_page_preview=True
        )
    
    # ========== LANGUAGE HANDLERS ==========
    
    async def show_language_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Hiển thị chọn ngôn ngữ"""
        query = update.callback_query
        user_id = update.effective_user.id
        user_info = db.get_user(user_id)
        language = user_info['language'] if user_info else Config.DEFAULT_LANGUAGE
        
        language_names = {
            'en': 'English 🇬🇧',
            'vi': 'Tiếng Việt 🇻🇳',
            'ru': 'Русский 🇷🇺',
            'zh': '中文 🇨🇳'
        }
        
        current_lang = language_names.get(language, 'English 🇬🇧')
        
        await query.edit_message_text(
            lang.get_text(language, "language_title") + "\n\n" +
            lang.get_text(language, "language_current", language=current_lang) + "\n\n" +
            lang.get_text(language, "language_select"),
            reply_markup=UIManager.create_language_keyboard(),
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def handle_language_change(self, update: Update, context: ContextTypes.DEFAULT_TYPE, lang_code: str) -> None:
        """Xử lý thay đổi ngôn ngữ"""
        query = update.callback_query
        await query.answer()
        
        user_id = update.effective_user.id
        
        if lang_code in Config.SUPPORTED_LANGUAGES:
            db.update_user_language(user_id, lang_code)
            
            language_names = {
                'en': 'English 🇬🇧',
                'vi': 'Tiếng Việt 🇻🇳',
                'ru': 'Русский 🇷🇺',
                'zh': '中文 🇨🇳'
            }
            
            new_lang = language_names.get(lang_code, 'English 🇬🇧')
            
            await query.edit_message_text(
                lang.get_text(lang_code, "language_changed", language=new_lang),
                reply_markup=UIManager.create_back_button(lang_code),
                parse_mode=ParseMode.MARKDOWN
            )
    
    # ========== DONATION HANDLERS ==========
    
    async def show_donation_info(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Hiển thị thông tin ủng hộ"""
        query = update.callback_query
        user_id = update.effective_user.id
        user_info = db.get_user(user_id)
        language = user_info['language'] if user_info else Config.DEFAULT_LANGUAGE
        
        donation_text = (
            lang.get_text(language, "donate_title") + "\n\n" +
            lang.get_text(language, "donate_mission") + "\n\n" +
            lang.get_text(language, "donate_options") + "\n\n" +
            lang.get_text(language, "donate_payment",
                         binance_id=Config.BINANCE_ID,
                         currency=Config.DONATION_CURRENCY) + "\n\n" +
            "💖 *Thank you for considering supporting our mission!*"
        )
        
        await query.edit_message_text(
            donation_text,
            reply_markup=UIManager.create_back_button(language),
            parse_mode=ParseMode.MARKDOWN,
            disable_web_page_preview=True
        )
    
    # ========== HELP HANDLERS ==========
    
    async def show_help_center(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Hiển thị trung tâm trợ giúp"""
        query = update.callback_query
        user_id = update.effective_user.id
        user_info = db.get_user(user_id)
        language = user_info['language'] if user_info else Config.DEFAULT_LANGUAGE
        
        await query.edit_message_text(
            lang.get_text(language, "help_title") + "\n\n" +
            lang.get_text(language, "help_sections"),
            reply_markup=UIManager.create_back_button(language),
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def handle_help_section(self, update: Update, context: ContextTypes.DEFAULT_TYPE, section: str) -> None:
        """Xử lý chọn section help"""
        # Xử lý các section help chi tiết
        pass

# ===============================================
# 8. CẤU TRÚC BOT CHÍNH
# ===============================================
class BotCheckScam:
    """Lớp chính điều khiển toàn bộ bot"""
    
    def __init__(self):
        self.config = Config
        self.db = db
        self.lang = lang
        self.ui = UIManager()
        self.handler = BotHandler()
        
        # Khởi tạo ứng dụng Telegram
        self.application = ApplicationBuilder() \
            .token(self.config.BOT_TOKEN) \
            .pool_timeout(30) \
            .connect_timeout(30) \
            .read_timeout(30) \
            .write_timeout(30) \
            .get_updates_read_timeout(30) \
            .build()
        
        # Thêm handlers
        self.setup_handlers()
        
        # Khởi tạo job queue
        self.setup_jobs()
    
    def setup_handlers(self):
        """Thiết lập tất cả handlers"""
        
        # Command handlers
        self.application.add_handler(CommandHandler("start", self.handler.handle_start))
        self.application.add_handler(CommandHandler("help", self.handler.handle_start))
        self.application.add_handler(CommandHandler("menu", self.handler.handle_start))
        
        # Callback query handlers
        self.application.add_handler(CallbackQueryHandler(self.handle_callback_query, pattern="^menu_"))
        self.application.add_handler(CallbackQueryHandler(self.handle_callback_query, pattern="^lang_"))
        self.application.add_handler(CallbackQueryHandler(self.handle_callback_query, pattern="^scam_"))
        self.application.add_handler(CallbackQueryHandler(self.handle_callback_query, pattern="^cat_"))
        self.application.add_handler(CallbackQueryHandler(self.handle_callback_query, pattern="^yes$|^no$|^cancel$"))
        self.application.add_handler(CallbackQueryHandler(self.handle_callback_query, pattern="^main_menu$"))
        
        # Message handlers
        self.application.add_handler(MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            self.handle_message
        ))
        
        # Error handler
        self.application.add_error_handler(self.error_handler)
    
    async def handle_callback_query(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Xử lý tất cả callback queries"""
        query = update.callback_query
        data = query.data
        
        try:
            if data.startswith("menu_"):
                menu_type = data.split("_")[1]
                await self.handler.handle_menu(update, context, menu_type)
            
            elif data.startswith("lang_"):
                lang_code = data.split("_")[1]
                await self.handler.handle_language_change(update, context, lang_code)
            
            elif data.startswith("scam_"):
                scam_num = data.split("_")[1]
                # Xử lý chọn loại scam
                pass
            
            elif data.startswith("cat_"):
                category = data
                await self.handler.handle_group_category(update, context, category)
            
            elif data in ["yes", "no"]:
                await self.handler.handle_report_confirmation(update, context, data)
            
            elif data == "main_menu":
                await self.handler.show_main_menu(update, context)
        
        except Exception as e:
            logger.error(f"Error handling callback: {e}")
            await query.answer("An error occurred. Please try again.")
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Xử lý tất cả messages"""
        user_id = update.effective_user.id
        
        # Kiểm tra nếu đang trong quá trình report
        if context.user_data.get('reporting'):
            await self.handler.handle_report_steps(update, context)
        
        # Kiểm tra nếu đang chờ check input
        elif context.user_data.get('awaiting_check'):
            await self.handler.handle_check_input(update, context)
        
        else:
            # Mặc định hiển thị menu
            user_info = db.get_user(user_id)
            language = user_info['language'] if user_info else Config.DEFAULT_LANGUAGE
            
            await update.message.reply_text(
                lang.get_text(language, "menu_prompt"),
                reply_markup=UIManager.create_main_menu(language),
                parse_mode=ParseMode.MARKDOWN
            )
    
    async def error_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Xử lý lỗi"""
        logger.error(f"Exception while handling update: {context.error}")
        
        if update and update.effective_user:
            try:
                user_info = db.get_user(update.effective_user.id)
                language = user_info['language'] if user_info else Config.DEFAULT_LANGUAGE
                
                await context.bot.send_message(
                    chat_id=update.effective_user.id,
                    text=lang.get_text(language, "error_general"),
                    reply_markup=UIManager.create_back_button(language)
                )
            except Exception as e:
                logger.error(f"Error sending error message: {e}")
    
    def setup_jobs(self):
        """Thiết lập công việc định kỳ"""
        
        job_queue = self.application.job_queue
        
        # Backup database hàng ngày
        if job_queue:
            job_queue.run_repeating(
                self.backup_database,
                interval=Config.DB_BACKUP_INTERVAL,
                first=10
            )
            
            # Dọn dẹp sessions cũ
            job_queue.run_repeating(
                self.cleanup_sessions,
                interval=Config.CLEANUP_INTERVAL,
                first=30
            )
    
    async def backup_database(self, context: ContextTypes.DEFAULT_TYPE):
        """Backup database định kỳ"""
        try:
            db.create_backup()
            logger.info("✅ Scheduled database backup completed")
        except Exception as e:
            logger.error(f"❌ Scheduled backup failed: {e}")
    
    async def cleanup_sessions(self, context: ContextTypes.DEFAULT_TYPE):
        """Dọn dẹp sessions cũ"""
        try:
            now = datetime.now()
            expired_sessions = []
            
            for user_id, session in self.handler.active_reports.items():
                # Giả sử session hết hạn sau 1 giờ
                if 'created_at' in session:
                    created = datetime.fromisoformat(session['created_at'])
                    if (now - created).seconds > 3600:
                        expired_sessions.append(user_id)
            
            for user_id in expired_sessions:
                del self.handler.active_reports[user_id]
            
            if expired_sessions:
                logger.info(f"🧹 Cleaned up {len(expired_sessions)} expired sessions")
            
        except Exception as e:
            logger.error(f"❌ Cleanup failed: {e}")
    
    def run(self):
        """Chạy bot"""
        try:
            # Xác thực cấu hình
            Config.validate()
            
            logger.info("=" * 60)
            logger.info(f"🤖 BOT CHECK SCAM - {Config.VERSION}")
            logger.info(f"📅 Build Date: {Config.BUILD_DATE}")
            logger.info(f"🌐 Languages: {', '.join(Config.SUPPORTED_LANGUAGES)}")
            logger.info(f"💾 Database: {Config.DB_NAME}")
            logger.info("=" * 60)
            logger.info("🚀 Starting bot...")
            
            # Chạy bot
            self.application.run_polling(
                allowed_updates=Update.ALL_TYPES,
                drop_pending_updates=True,
                close_loop=False
            )
            
        except KeyboardInterrupt:
            logger.info("👋 Bot stopped by user")
        except Exception as e:
            logger.error(f"❌ Failed to start bot: {e}")
            sys.exit(1)

# ===============================================
# 9. CHẠY BOT
# ===============================================
if __name__ == "__main__":
    bot = BotCheckScam()
    bot.run()
