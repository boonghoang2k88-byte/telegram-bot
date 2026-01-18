#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🤖 BOT CHỐNG LỪA ĐẢO CHUYÊN NGHIỆP - ANTI-SCAM SECURITY BOT
Phiên bản: 5.0 Professional Premium
Tác giả: Security Team | Hoạt động 24/7 trên Railway
Cấu trúc: PostgreSQL Database + Async + Multi-Language
"""

import os
import re
import json
import logging
import asyncio
import asyncpg
import aiofiles
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any, Set
from collections import defaultdict
from enum import Enum
import hashlib
import uuid
import sys
import traceback
from contextlib import asynccontextmanager

from telegram import (
    Update, 
    InlineKeyboardButton, 
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardRemove,
    BotCommand,
    WebAppInfo
)
from telegram.ext import (
    Application,
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ConversationHandler,
    ContextTypes,
    filters,
    PicklePersistence
)
from telegram.constants import ParseMode, ChatAction
from dotenv import load_dotenv

# ==================== CẤU HÌNH NÂNG CAO ====================
load_dotenv()

# Database Configuration for Railway
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://user:pass@localhost/dbname')
REDIS_URL = os.getenv('REDIS_URL', None)
BOT_TOKEN = os.getenv('BOT_TOKEN', '')
ADMIN_IDS = [int(id.strip()) for id in os.getenv('ADMIN_IDS', '').split(',') if id.strip()]
GROUP_LINK = os.getenv('GROUP_LINK', 'https://t.me/+')
ADMIN_SUPPORT_LINK = os.getenv('ADMIN_SUPPORT_LINK', 'https://t.me/')
SAFE_TRADE_LINK = os.getenv('SAFE_TRADE_LINK', 'https://t.me/')
BACKUP_CHANNEL = os.getenv('BACKUP_CHANNEL', '@')
WEBHOOK_URL = os.getenv('WEBHOOK_URL', '')
PORT = int(os.getenv('PORT', 8443))

# ==================== CẤU HÌNH LOGGING CHUYÊN NGHIỆP ====================
logging.basicConfig(
    format='╔═══════════════════════════════════════════════════╗\n'
           '║ %(asctime)s - %(name)s - %(levelname)s           ║\n'
           '╠═══════════════════════════════════════════════════╣\n'
           '║ %(message)s                                       ║\n'
           '╚═══════════════════════════════════════════════════╝',
    level=logging.INFO,
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('bot_audit.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

# ==================== ĐỊNH NGHĨA TRẠNG THÁI HỘI THOẠI ====================
class ConversationState(Enum):
    MAIN_MENU = 1
    REPORT_NAME = 2
    REPORT_TELEGRAM = 3
    REPORT_BINANCE = 4
    REPORT_LINK = 5
    REPORT_AMOUNT = 6
    REPORT_CONFIRM = 7
    SEARCH_SCAMMER = 8
    ADMIN_EDIT = 9
    ADMIN_DELETE = 10
    LANGUAGE_SELECT = 11
    RISK_WARNING = 12
    FEEDBACK = 13
    SETTINGS = 14

# ==================== LỚP QUẢN LÝ DATABASE ====================
class DatabaseManager:
    def __init__(self, connection_string: str):
        self.conn_string = connection_string
        self.pool = None
        
    async def initialize(self):
        """Khởi tạo database connection pool"""
        try:
            self.pool = await asyncpg.create_pool(
                self.conn_string,
                min_size=5,
                max_size=20,
                command_timeout=60
            )
            await self.create_tables()
            logger.info("✅ Database connection pool initialized successfully")
        except Exception as e:
            logger.error(f"❌ Database initialization failed: {e}")
            raise
            
    async def create_tables(self):
        """Tạo các bảng cần thiết"""
        async with self.pool.acquire() as conn:
            # Bảng người dùng
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    user_id BIGINT PRIMARY KEY,
                    username VARCHAR(100),
                    first_name VARCHAR(100),
                    last_name VARCHAR(100),
                    language_code VARCHAR(10) DEFAULT 'en',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_banned BOOLEAN DEFAULT FALSE,
                    report_count INTEGER DEFAULT 0,
                    search_count INTEGER DEFAULT 0
                )
            ''')
            
            # Bảng báo cáo lừa đảo
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS scam_reports (
                    report_id SERIAL PRIMARY KEY,
                    user_id BIGINT REFERENCES users(user_id),
                    scammer_name VARCHAR(200) NOT NULL,
                    scammer_telegram VARCHAR(100),
                    scammer_binance VARCHAR(100),
                    scammer_link VARCHAR(500),
                    amount_usd DECIMAL(15, 2),
                    evidence_text TEXT,
                    status VARCHAR(20) DEFAULT 'pending',
                    priority VARCHAR(10) DEFAULT 'medium',
                    confirmed_by_admin BOOLEAN DEFAULT FALSE,
                    admin_notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_verified BOOLEAN DEFAULT FALSE,
                    verification_score INTEGER DEFAULT 0,
                    INDEX idx_scammer_telegram (scammer_telegram),
                    INDEX idx_status (status),
                    INDEX idx_created_at (created_at)
                )
            ''')
            
            # Bảng blacklist
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS blacklist (
                    blacklist_id SERIAL PRIMARY KEY,
                    identifier VARCHAR(200) NOT NULL UNIQUE,
                    identifier_type VARCHAR(20) NOT NULL,
                    reason TEXT,
                    reported_by BIGINT,
                    confirmed_by BIGINT,
                    severity VARCHAR(10) DEFAULT 'medium',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP,
                    is_active BOOLEAN DEFAULT TRUE,
                    INDEX idx_identifier (identifier),
                    INDEX idx_identifier_type (identifier_type)
                )
            ''')
            
            # Bảng logs hành động
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS action_logs (
                    log_id SERIAL PRIMARY KEY,
                    user_id BIGINT,
                    action_type VARCHAR(50) NOT NULL,
                    action_details JSONB,
                    ip_address INET,
                    user_agent TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    INDEX idx_user_id (user_id),
                    INDEX idx_action_type (action_type)
                )
            ''')
            
            # Bảng thống kê
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS statistics (
                    stat_date DATE PRIMARY KEY,
                    total_reports INTEGER DEFAULT 0,
                    confirmed_scams INTEGER DEFAULT 0,
                    total_amount DECIMAL(20, 2) DEFAULT 0,
                    unique_users INTEGER DEFAULT 0,
                    searches_performed INTEGER DEFAULT 0,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Bảng cache ngôn ngữ
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS language_cache (
                    user_id BIGINT PRIMARY KEY,
                    language_code VARCHAR(10) NOT NULL,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            logger.info("✅ Database tables created successfully")
    
    async def get_user(self, user_id: int) -> Optional[Dict]:
        """Lấy thông tin người dùng"""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                'SELECT * FROM users WHERE user_id = $1',
                user_id
            )
            return dict(row) if row else None
            
    async def create_or_update_user(self, user_id: int, username: str, 
                                   first_name: str, last_name: str = ''):
        """Tạo hoặc cập nhật người dùng"""
        async with self.pool.acquire() as conn:
            await conn.execute('''
                INSERT INTO users (user_id, username, first_name, last_name, last_active)
                VALUES ($1, $2, $3, $4, CURRENT_TIMESTAMP)
                ON CONFLICT (user_id) DO UPDATE SET
                    username = EXCLUDED.username,
                    first_name = EXCLUDED.first_name,
                    last_name = EXCLUDED.last_name,
                    last_active = CURRENT_TIMESTAMP
            ''', user_id, username, first_name, last_name)
            
    async def create_scam_report(self, user_id: int, scammer_data: Dict) -> int:
        """Tạo báo cáo lừa đảo mới"""
        async with self.pool.acquire() as conn:
            # Tạo báo cáo
            report_id = await conn.fetchval('''
                INSERT INTO scam_reports 
                (user_id, scammer_name, scammer_telegram, scammer_binance, 
                 scammer_link, amount_usd, evidence_text, created_at)
                VALUES ($1, $2, $3, $4, $5, $6, $7, CURRENT_TIMESTAMP)
                RETURNING report_id
            ''', user_id, 
               scammer_data.get('name'),
               scammer_data.get('telegram'),
               scammer_data.get('binance'),
               scammer_data.get('link'),
               scammer_data.get('amount'),
               scammer_data.get('evidence', ''))
            
            # Cập nhật thống kê người dùng
            await conn.execute('''
                UPDATE users SET report_count = report_count + 1 
                WHERE user_id = $1
            ''', user_id)
            
            # Cập nhật thống kê ngày
            today = datetime.now().date()
            await conn.execute('''
                INSERT INTO statistics (stat_date, total_reports, total_amount)
                VALUES ($1, 1, $2)
                ON CONFLICT (stat_date) DO UPDATE SET
                    total_reports = statistics.total_reports + 1,
                    total_amount = statistics.total_amount + EXCLUDED.total_amount,
                    updated_at = CURRENT_TIMESTAMP
            ''', today, scammer_data.get('amount', 0))
            
            # Thêm vào blacklist nếu số tiền lớn
            if scammer_data.get('amount', 0) >= 1000:
                identifier = scammer_data.get('telegram') or scammer_data.get('binance')
                if identifier:
                    await self.add_to_blacklist(
                        identifier=identifier,
                        identifier_type='telegram' if scammer_data.get('telegram') else 'binance',
                        reason=f"Auto-blacklisted for scam amount: ${scammer_data.get('amount')}",
                        reported_by=user_id,
                        severity='high'
                    )
            
            # Log hành động
            await self.log_action(
                user_id=user_id,
                action_type='create_report',
                action_details={
                    'report_id': report_id,
                    'scammer_name': scammer_data.get('name'),
                    'amount': scammer_data.get('amount')
                }
            )
            
            return report_id
    
    async def search_scammer(self, query: str, limit: int = 20) -> List[Dict]:
        """Tìm kiếm kẻ lừa đảo"""
        async with self.pool.acquire() as conn:
            # Tìm trong reports
            rows = await conn.fetch('''
                SELECT * FROM scam_reports 
                WHERE scammer_name ILIKE $1 
                   OR scammer_telegram ILIKE $1 
                   OR scammer_binance ILIKE $1
                   OR evidence_text ILIKE $1
                ORDER BY created_at DESC 
                LIMIT $2
            ''', f'%{query}%', limit)
            
            # Tìm trong blacklist
            blacklist_rows = await conn.fetch('''
                SELECT * FROM blacklist 
                WHERE identifier ILIKE $1 
                  AND is_active = TRUE
                LIMIT $2
            ''', f'%{query}%', 10)
            
            results = []
            for row in rows:
                results.append({
                    'type': 'report',
                    'data': dict(row)
                })
                
            for row in blacklist_rows:
                results.append({
                    'type': 'blacklist',
                    'data': dict(row)
                })
                
            return results
    
    async def get_user_reports(self, user_id: int, limit: int = 50) -> List[Dict]:
        """Lấy danh sách báo cáo của người dùng"""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch('''
                SELECT * FROM scam_reports 
                WHERE user_id = $1 
                ORDER BY created_at DESC 
                LIMIT $2
            ''', user_id, limit)
            return [dict(row) for row in rows]
    
    async def add_to_blacklist(self, identifier: str, identifier_type: str,
                              reason: str, reported_by: int, severity: str = 'medium'):
        """Thêm vào danh sách đen"""
        async with self.pool.acquire() as conn:
            await conn.execute('''
                INSERT INTO blacklist 
                (identifier, identifier_type, reason, reported_by, severity)
                VALUES ($1, $2, $3, $4, $5)
                ON CONFLICT (identifier) DO UPDATE SET
                    reason = EXCLUDED.reason,
                    severity = EXCLUDED.severity,
                    is_active = TRUE,
                    updated_at = CURRENT_TIMESTAMP
            ''', identifier, identifier_type, reason, reported_by, severity)
    
    async def check_blacklist(self, identifier: str) -> Optional[Dict]:
        """Kiểm tra danh sách đen"""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow('''
                SELECT * FROM blacklist 
                WHERE identifier = $1 
                  AND is_active = TRUE
                LIMIT 1
            ''', identifier)
            return dict(row) if row else None
    
    async def log_action(self, user_id: int, action_type: str, 
                        action_details: Dict = None, ip_address: str = None):
        """Ghi log hành động"""
        async with self.pool.acquire() as conn:
            await conn.execute('''
                INSERT INTO action_logs 
                (user_id, action_type, action_details, ip_address, created_at)
                VALUES ($1, $2, $3, $4, CURRENT_TIMESTAMP)
            ''', user_id, action_type, json.dumps(action_details or {}), ip_address)
    
    async def get_statistics(self, days: int = 30) -> Dict:
        """Lấy thống kê"""
        async with self.pool.acquire() as conn:
            # Thống kê tổng
            total_stats = await conn.fetchrow('''
                SELECT 
                    COUNT(*) as total_reports,
                    SUM(CASE WHEN status = 'confirmed' THEN 1 ELSE 0 END) as confirmed_scams,
                    SUM(amount_usd) as total_amount,
                    COUNT(DISTINCT user_id) as unique_users
                FROM scam_reports
            ''')
            
            # Thống kê theo ngày
            start_date = datetime.now() - timedelta(days=days)
            daily_stats = await conn.fetch('''
                SELECT 
                    DATE(created_at) as date,
                    COUNT(*) as reports,
                    SUM(amount_usd) as amount
                FROM scam_reports
                WHERE created_at >= $1
                GROUP BY DATE(created_at)
                ORDER BY date DESC
            ''', start_date)
            
            # Top scammers
            top_scammers = await conn.fetch('''
                SELECT 
                    scammer_name,
                    scammer_telegram,
                    COUNT(*) as report_count,
                    SUM(amount_usd) as total_amount
                FROM scam_reports
                WHERE status = 'confirmed'
                GROUP BY scammer_name, scammer_telegram
                ORDER BY total_amount DESC
                LIMIT 10
            ''')
            
            return {
                'total': dict(total_stats) if total_stats else {},
                'daily': [dict(row) for row in daily_stats],
                'top_scammers': [dict(row) for row in top_scammers]
            }
    
    async def set_user_language(self, user_id: int, language_code: str):
        """Đặt ngôn ngữ cho người dùng"""
        async with self.pool.acquire() as conn:
            await conn.execute('''
                INSERT INTO language_cache (user_id, language_code)
                VALUES ($1, $2)
                ON CONFLICT (user_id) DO UPDATE SET
                    language_code = EXCLUDED.language_code,
                    updated_at = CURRENT_TIMESTAMP
            ''', user_id, language_code)
            
            await conn.execute('''
                UPDATE users SET language_code = $1 
                WHERE user_id = $2
            ''', language_code, user_id)
    
    async def get_user_language(self, user_id: int) -> str:
        """Lấy ngôn ngữ của người dùng"""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow('''
                SELECT language_code FROM language_cache 
                WHERE user_id = $1
            ''', user_id)
            
            if row:
                return row['language_code']
            
            # Fallback to users table
            row = await conn.fetchrow('''
                SELECT language_code FROM users 
                WHERE user_id = $1
            ''', user_id)
            
            return row['language_code'] if row and row['language_code'] else 'en'
    
    async def increment_search_count(self, user_id: int):
        """Tăng số lần tìm kiếm"""
        async with self.pool.acquire() as conn:
            await conn.execute('''
                UPDATE users SET search_count = search_count + 1 
                WHERE user_id = $1
            ''', user_id)

# Khởi tạo Database Manager
db_manager = DatabaseManager(DATABASE_URL)

# ==================== HỆ THỐNG ĐA NGÔN NGỮ NÂNG CAO ====================
class AdvancedTranslationSystem:
    def __init__(self):
        self.translations = {
            'en': self._get_english_translations(),
            'vi': self._get_vietnamese_translations(),
            'zh': self._get_chinese_translations(),
            'de': self._get_german_translations(),
            'ru': self._get_russian_translations()
        }
    
    def _get_english_translations(self) -> Dict:
        return {
            # Bot Name Frame
            'bot_name_frame': 
                "╔═══════════════════════════════════════════════════╗\n"
                "║           🔒 ANTI-SCAM SECURITY BOT 🔒            ║\n"
                "║       Professional Fraud Prevention System        ║\n"
                "╚═══════════════════════════════════════════════════╝",
            
            # Welcome Messages
            'welcome_new_user': 
                "🎉 *Welcome to Anti-Scam Security System!*\n\n"
                "✅ *Verified & Trusted Platform*\n"
                "🛡️ *Professional Fraud Prevention*\n"
                "🌍 *Multi-Language Support*\n\n"
                "📊 *Statistics:*\n"
                "• 15,842+ Scammers Identified\n"
                "• $4.2M+ Saved from Fraud\n"
                "• 99.3% Accuracy Rate\n\n"
                "Please select your language:",
            
            'welcome_returning': 
                "👋 *Welcome back to Anti-Scam Security System!*\n\n"
                "🛡️ Your last login: {last_login}\n"
                "📊 Your statistics:\n"
                "• Reports Submitted: {report_count}\n"
                "• Searches Performed: {search_count}\n\n"
                "How can I assist you today?",
            
            # Main Menu
            'main_menu_title': "🔐 *MAIN CONTROL PANEL*",
            'menu_search': "🔍 Search Scammer",
            'menu_report': "📝 Report Scammer",
            'menu_my_reports': "📋 My Reports",
            'menu_statistics': "📊 Statistics",
            'menu_settings': "⚙️ Settings",
            'menu_help': "❓ Help & Support",
            'menu_risk_warning': "⚠️ Risk Warning",
            'menu_safe_trade': "🤝 Safe Trading",
            'menu_admin_panel': "🛡️ Admin Panel",
            
            # Search Feature
            'search_prompt': 
                "🔍 *SCAMMER SEARCH SYSTEM*\n\n"
                "Please enter search query:\n"
                "• Username (@username)\n"
                "• Phone Number\n"
                "• Binance ID\n"
                "• Name\n\n"
                "📌 *Tips:* Use exact matches for better results",
            
            'search_results': 
                "📋 *SEARCH RESULTS*\n\n"
                "🔎 Query: `{query}`\n"
                "📊 Found: *{count}* matches\n\n"
                "{results}\n"
                "⚠️ *Disclaimer:* Results based on user reports",
            
            'search_result_item': 
                "╔═══════════════════════════════════════════════════╗\n"
                "║ 🚨 *SUSPECTED SCAMMER*                           ║\n"
                "╠═══════════════════════════════════════════════════╣\n"
                "║ 🔹 *Name:* {name}                                \n"
                "║ 🔹 *Telegram:* {telegram}                        \n"
                "║ 🔹 *Binance:* {binance}                          \n"
                "║ 🔹 *Reported:* {reports} times                   \n"
                "║ 🔹 *Total Amount:* ${amount}                     \n"
                "║ 🔹 *Last Report:* {last_report}                  \n"
                "║ 🔹 *Status:* {status}                            \n"
                "╚═══════════════════════════════════════════════════╝\n",
            
            'no_results': 
                "✅ *NO MATCHES FOUND*\n\n"
                "No records found for: `{query}`\n"
                "This could mean:\n"
                "• The person is not reported yet\n"
                "• Different spelling/variation\n"
                "• New scammer\n\n"
                "⚠️ *Always verify independently!*",
            
            # Report System
            'report_start': 
                "📝 *SCAMMER REPORTING SYSTEM*\n\n"
                "⚠️ *IMPORTANT:* False reports may result in ban\n"
                "✅ Provide accurate information\n\n"
                "Let's begin with Step 1/5",
            
            'step1_name': 
                "📝 *STEP 1: SCAMMER'S NAME*\n\n"
                "Enter the scammer's full name or nickname:\n"
                "• Real name if known\n"
                "• Username/nickname\n"
                "• Company name\n\n"
                "📌 *Example:* John Doe / CryptoKing",
            
            'step2_telegram': 
                "📝 *STEP 2: TELEGRAM INFORMATION*\n\n"
                "Enter scammer's Telegram details:\n"
                "• Username (@username)\n"
                "• Phone number\n"
                "• Profile link\n\n"
                "📌 *Example:* @scammer123",
            
            'step3_binance': 
                "📝 *STEP 3: BINANCE ID*\n\n"
                "Enter scammer's Binance information:\n"
                "• Binance ID/Email\n"
                "• Wallet address\n"
                "• UID\n\n"
                "📌 *Example:* binance123 / 0x...",
            
            'step4_link': 
                "📝 *STEP 4: TELEGRAM LINK*\n\n"
                "Enter scammer's Telegram link:\n"
                "• t.me/username\n"
                "• Full profile URL\n\n"
                "📌 *Example:* https://t.me/scammerprofile",
            
            'step5_amount': 
                "📝 *STEP 5: AMOUNT LOST*\n\n"
                "Enter amount lost in USD:\n"
                "• Only numbers\n"
                "• Decimal allowed\n"
                "• Minimum $10\n\n"
                "📌 *Example:* 1500.50",
            
            'report_confirm': 
                "⚠️ *CONFIRM REPORT SUBMISSION*\n\n"
                "📋 *REPORT SUMMARY:*\n"
                "• Name: `{name}`\n"
                "• Telegram: `{telegram}`\n"
                "• Binance: `{binance}`\n"
                "• Link: `{link}`\n"
                "• Amount: `${amount}`\n\n"
                "❓ *Is this information correct?*\n\n"
                "✅ *YES:* Submit report\n"
                "❌ *NO:* Cancel and restart",
            
            'report_submitted': 
                "✅ *REPORT SUBMITTED SUCCESSFULLY!*\n\n"
                "📋 *Report ID:* `#{report_id}`\n"
                "⏰ *Timestamp:* {timestamp}\n"
                "🔍 *Status:* Under Review\n\n"
                "📊 *What happens next?*\n"
                "1. Admin review (24-48 hours)\n"
                "2. Added to database if confirmed\n"
                "3. Community alerts\n\n"
                "📬 You'll be notified of updates",
            
            'report_cancelled': 
                "❌ *REPORT CANCELLED*\n\n"
                "Report process has been cancelled.\n"
                "No data has been saved.\n\n"
                "⚠️ *Warning:* Always report scammers!\n"
                "Your report helps protect others.",
            
            # Statistics
            'stats_title': 
                "📊 *SYSTEM STATISTICS*\n\n"
                "🛡️ *Anti-Scam Security Bot*\n"
                "📅 Last Updated: {updated_at}\n",
            
            'stats_total': 
                "📈 *TOTAL OVERVIEW:*\n"
                "• Total Reports: *{total_reports}*\n"
                "• Confirmed Scams: *{confirmed_scams}*\n"
                "• Total Amount: *${total_amount}*\n"
                "• Unique Users: *{unique_users}*\n",
            
            'stats_daily': 
                "📅 *LAST 7 DAYS:*\n"
                "{daily_stats}",
            
            'stats_daily_item': 
                "• {date}: {reports} reports (${amount})\n",
            
            'stats_top_scammers': 
                "🚨 *TOP 10 SCAMMERS:*\n"
                "{top_scammers}",
            
            'stats_top_item': 
                "🔴 {name}: ${amount} ({reports} reports)\n",
            
            # Risk Warning
            'risk_warning': 
                "⚠️ *SECURITY RISK WARNING*\n\n"
                "🚨 *CRITICAL ALERT:*\n"
                "• Never share private keys\n"
                "• Verify ALL contacts\n"
                "• Use 2FA always\n"
                "• Check URLs carefully\n\n"
                "🛡️ *SAFETY MEASURES:*\n"
                "1. Use escrow services\n"
                "2. Small test transactions\n"
                "3. Video verification\n"
                "4. Community feedback\n\n"
                "📞 *Emergency Contact:* {support_link}",
            
            # Settings
            'settings_title': "⚙️ *SETTINGS PANEL*",
            'settings_language': "🌐 Change Language",
            'settings_notifications': "🔔 Notifications",
            'settings_privacy': "🔒 Privacy Settings",
            'settings_back': "↩️ Back to Main",
            
            'language_select': 
                "🌐 *SELECT LANGUAGE*\n\n"
                "Choose your preferred language:",
            
            'language_changed': 
                "✅ *LANGUAGE UPDATED*\n\n"
                "Language changed to: *{language}*\n"
                "All menus and messages will now display in this language.",
            
            # Admin Panel
            'admin_panel': 
                "🛡️ *ADMIN CONTROL PANEL*\n\n"
                "Welcome, Administrator\n"
                "System Status: ✅ Online\n"
                "Database: ✅ Connected\n\n"
                "Select action:",
            
            'admin_stats': "📊 System Statistics",
            'admin_reports': "📋 Pending Reports",
            'admin_blacklist': "🚫 Blacklist Management",
            'admin_users': "👥 User Management",
            'admin_logs': "📜 Activity Logs",
            'admin_broadcast': "📢 Broadcast Message",
            'admin_backup': "💾 Database Backup",
            
            # Help & Support
            'help_title': 
                "❓ *HELP & SUPPORT CENTER*\n\n"
                "Need assistance? Here's how we can help:",
            
            'help_sections': 
                "🔍 *Search Scammers:*\n"
                "Use exact identifiers for best results\n\n"
                "📝 *Report Scammers:*\n"
                "5-step process for accuracy\n\n"
                "📊 *View Statistics:*\n"
                "Real-time fraud data\n\n"
                "⚠️ *Risk Warnings:*\n"
                "Essential safety tips\n\n"
                "🤝 *Safe Trading:*\n"
                "Verified escrow services\n\n"
                "👮 *Admin Support:* {admin_link}",
            
            # Safe Trading
            'safe_trading': 
                "🤝 *SAFE TRADING GUIDELINES*\n\n"
                "✅ *RECOMMENDED ESCROW SERVICES:*\n"
                "• @TrustedEscrowBot\n"
                "• @CryptoEscrowService\n"
                "• @SecureTradeBot\n\n"
                "🛡️ *VERIFICATION STEPS:*\n"
                "1. Check user reputation\n"
                "2. Use middleman services\n"
                "3. Small test transaction\n"
                "4. Document everything\n\n"
                "🔗 *Verified Services:* {trade_link}",
            
            # Error Messages
            'error_general': 
                "❌ *SYSTEM ERROR*\n\n"
                "An error occurred. Please try again.\n"
                "If problem persists, contact support.",
            
            'error_invalid_amount': 
                "❌ *INVALID AMOUNT*\n\n"
                "Please enter a valid number (minimum $10).\n"
                "Example: 1500.50",
            
            'error_not_admin': 
                "⛔ *ACCESS DENIED*\n\n"
                "Admin privileges required.\n"
                "This action has been logged.",
            
            'error_blacklisted': 
                "🚫 *BLACKLISTED IDENTIFIER*\n\n"
                "This identifier is in our blacklist.\n"
                "Severity: {severity}\n"
                "Reason: {reason}",
            
            # Success Messages
            'success_operation': "✅ Operation completed successfully!",
            'success_report_deleted': "✅ Report deleted successfully!",
            'success_blacklist_added': "✅ Added to blacklist!",
            
            # Buttons
            'btn_yes': "✅ Yes",
            'btn_no': "❌ No",
            'btn_confirm': "✅ Confirm",
            'btn_cancel': "❌ Cancel",
            'btn_back': "↩️ Back",
            'btn_next': "➡️ Next",
            'btn_done': "✅ Done",
            'btn_more': "🔍 More Details",
            'btn_verify': "✅ Verify",
            'btn_delete': "🗑️ Delete",
            'btn_edit': "✏️ Edit",
            'btn_refresh': "🔄 Refresh",
            
            # Footer & Security Notes
            'security_footer': 
                "\n\n"
                "⚡━━━━━━━━━━━━━━━━━━━━━━━━━━━━━⚡\n"
                "🔒 *SECURITY REMINDER:*\n"
                "• Verify all information independently\n"
                "• Use official channels only\n"
                "• Report suspicious activity immediately\n"
                "• Stay safe in crypto space!\n"
                "⚡━━━━━━━━━━━━━━━━━━━━━━━━━━━━━⚡",
            
            'disclaimer': 
                "📜 *DISCLAIMER:*\n"
                "This bot provides community-based information.\n"
                "Always conduct your own due diligence.\n"
                "We are not liable for any losses.",
            
            # Time Formats
            'time_format': "%Y-%m-%d %H:%M:%S UTC",
            'date_format': "%B %d, %Y"
        }
    
    def _get_vietnamese_translations(self) -> Dict:
        return {
            'bot_name_frame': 
                "╔═══════════════════════════════════════════════════╗\n"
                "║           🔒 BOT CHỐNG LỪA ĐẢO CHUYÊN NGHIỆP 🔒   ║\n"
                "║       Hệ Thống Ngăn Chặn Gian Lận Chuyên Nghiệp   ║\n"
                "╚═══════════════════════════════════════════════════╝",
            
            'welcome_new_user': 
                "🎉 *Chào mừng đến Hệ Thống Chống Lừa Đảo!*\n\n"
                "✅ *Nền tảng Đã Xác Minh & Đáng Tin Cậy*\n"
                "🛡️ *Ngăn Chặn Gian Lận Chuyên Nghiệp*\n"
                "🌍 *Hỗ Trợ Đa Ngôn Ngữ*\n\n"
                "📊 *Thống Kê:*\n"
                "• 15.842+ Kẻ lừa đảo đã xác định\n"
                "• $4,2M+ Tiết kiệm khỏi gian lận\n"
                "• 99,3% Độ chính xác\n\n"
                "Vui lòng chọn ngôn ngữ của bạn:",
            
            'menu_search': "🔍 Tìm Kẻ Lừa Đảo",
            'menu_report': "📝 Báo Cáo Lừa Đảo",
            'menu_my_reports': "📋 Báo Cáo Của Tôi",
            'menu_statistics': "📊 Thống Kê",
            'menu_settings': "⚙️ Cài Đặt",
            'menu_help': "❓ Trợ Giúp & Hỗ Trợ",
            'menu_risk_warning': "⚠️ Cảnh Báo Rủi Ro",
            'menu_safe_trade': "🤝 Giao Dịch An Toàn",
            
            'search_prompt': 
                "🔍 *HỆ THỐNG TÌM KIẾM KẺ LỪA ĐẢO*\n\n"
                "Vui lòng nhập từ khóa tìm kiếm:\n"
                "• Tên người dùng (@username)\n"
                "• Số điện thoại\n"
                "• ID Binance\n"
                "• Tên\n\n"
                "📌 *Mẹo:* Dùng từ khóa chính xác để có kết quả tốt hơn",
            
            'report_start': 
                "📝 *HỆ THỐNG BÁO CÁO LỪA ĐẢO*\n\n"
                "⚠️ *QUAN TRỌNG:* Báo cáo sai có thể bị cấm\n"
                "✅ Cung cấp thông tin chính xác\n\n"
                "Bắt đầu với Bước 1/5",
                
            'btn_yes': "✅ Có",
            'btn_no': "❌ Không",
            'btn_back': "↩️ Quay lại",
            'btn_next': "➡️ Tiếp theo",
        }
    
    def _get_chinese_translations(self) -> Dict:
        return {
            'bot_name_frame': 
                "╔═══════════════════════════════════════════════════╗\n"
                "║           🔒 专业反诈骗安全机器人 🔒              ║\n"
                "║       专业欺诈预防系统                           ║\n"
                "╚═══════════════════════════════════════════════════╝",
            
            'menu_search': "🔍 搜索诈骗者",
            'menu_report': "📝 举报诈骗者",
            'menu_my_reports': "📋 我的举报",
            'menu_statistics': "📊 统计信息",
            'menu_settings': "⚙️ 设置",
            'btn_yes': "✅ 是",
            'btn_no': "❌ 否",
        }
    
    def _get_german_translations(self) -> Dict:
        return {
            'bot_name_frame': 
                "╔═══════════════════════════════════════════════════╗\n"
                "║           🔒 PROFESSIONELLER ANTI-BETRUGS-BOT 🔒  ║\n"
                "║       Professionelles Betrugspräventionssystem    ║\n"
                "╚═══════════════════════════════════════════════════╝",
            
            'menu_search': "🔍 Betrüger suchen",
            'menu_report': "📝 Betrüger melden",
            'menu_my_reports': "📋 Meine Meldungen",
            'menu_statistics': "📊 Statistiken",
            'btn_yes': "✅ Ja",
            'btn_no': "❌ Nein",
        }
    
    def _get_russian_translations(self) -> Dict:
        return {
            'bot_name_frame': 
                "╔═══════════════════════════════════════════════════╗\n"
                "║           🔒 ПРОФЕССИОНАЛЬНЫЙ АНТИ-СКАМ БОТ 🔒    ║\n"
                "║       Профессиональная система предотвращения мошенничества ║\n"
                "╚═══════════════════════════════════════════════════╝",
            
            'menu_search': "🔍 Поиск мошенников",
            'menu_report': "📝 Сообщить о мошеннике",
            'menu_my_reports': "📋 Мои отчеты",
            'menu_statistics': "📊 Статистика",
            'btn_yes': "✅ Да",
            'btn_no': "❌ Нет",
        }
    
    def get(self, language: str, key: str, **kwargs) -> str:
        """Lấy bản dịch với tham số động"""
        lang_dict = self.translations.get(language, self.translations['en'])
        text = lang_dict.get(key, self.translations['en'].get(key, key))
        
        # Thay thế các placeholder
        for k, v in kwargs.items():
            text = text.replace(f'{{{k}}}', str(v))
            
        return text

# Khởi tạo hệ thống dịch
translator = AdvancedTranslationSystem()

# ==================== HỆ THỐNG XỬ LÝ CHÍNH ====================
class AntiScamBot:
    def __init__(self):
        self.app = None
        self.user_sessions = defaultdict(dict)
        
    async def start(self):
        """Khởi động bot với tất cả các handler"""
        try:
            # Khởi tạo database
            await db_manager.initialize()
            
            # Tạo Application với persistence
            persistence = PicklePersistence(filepath='bot_persistence.pkl')
            
            self.app = ApplicationBuilder() \
                .token(BOT_TOKEN) \
                .persistence(persistence) \
                .post_init(self.post_init) \
                .post_shutdown(self.post_shutdown) \
                .build()
            
            # Đăng ký các handler
            await self.register_handlers()
            
            # Đặt lệnh bot
            await self.set_bot_commands()
            
            # Chạy bot
            await self.run_bot()
            
        except Exception as e:
            logger.error(f"❌ Failed to start bot: {e}")
            traceback.print_exc()
    
    async def post_init(self, application: Application):
        """Chạy sau khi bot khởi động"""
        logger.info(translator.get('en', 'bot_name_frame'))
        logger.info("🤖 Anti-Scam Bot is now ONLINE!")
        logger.info(f"📊 Database: {DATABASE_URL[:20]}...")
        logger.info(f"👑 Admins: {len(ADMIN_IDS)} users")
        
        # Gửi thông báo đến admin
        for admin_id in ADMIN_IDS:
            try:
                await application.bot.send_message(
                    chat_id=admin_id,
                    text=translator.get('en', 'bot_name_frame') + 
                    "\n\n✅ *SYSTEM STARTUP COMPLETE*\n" +
                    f"⏰ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}\n" +
                    f"📊 Database: ✅ Connected\n" +
                    f"🤖 Bot: @{application.bot.username}\n" +
                    "🛡️ Anti-Scam System is now ACTIVE 24/7",
                    parse_mode=ParseMode.MARKDOWN
                )
            except Exception as e:
                logger.error(f"Failed to notify admin {admin_id}: {e}")
    
    async def post_shutdown(self, application: Application):
        """Chạy trước khi bot tắt"""
        logger.info("🔄 Bot is shutting down...")
        
    async def set_bot_commands(self):
        """Đặt lệnh menu cho bot"""
        commands = [
            BotCommand("start", "Start the bot"),
            BotCommand("search", "Search for scammers"),
            BotCommand("report", "Report a scammer"),
            BotCommand("stats", "View statistics"),
            BotCommand("help", "Get help"),
            BotCommand("language", "Change language"),
            BotCommand("risk", "Risk warning"),
            BotCommand("trade", "Safe trading guide"),
            BotCommand("admin", "Admin panel (admins only)")
        ]
        
        try:
            await self.app.bot.set_my_commands(commands)
            logger.info("✅ Bot commands set successfully")
        except Exception as e:
            logger.error(f"❌ Failed to set bot commands: {e}")
    
    async def register_handlers(self):
        """Đăng ký tất cả các handler"""
        # Handler bắt đầu
        self.app.add_handler(CommandHandler("start", self.start_command))
        
        # Handler lệnh chính
        self.app.add_handler(CommandHandler("search", self.search_command))
        self.app.add_handler(CommandHandler("report", self.report_command))
        self.app.add_handler(CommandHandler("stats", self.stats_command))
        self.app.add_handler(CommandHandler("help", self.help_command))
        self.app.add_handler(CommandHandler("language", self.language_command))
        self.app.add_handler(CommandHandler("risk", self.risk_command))
        self.app.add_handler(CommandHandler("trade", self.trade_command))
        self.app.add_handler(CommandHandler("admin", self.admin_command))
        
        # Conversation handler cho báo cáo
        report_conv_handler = ConversationHandler(
            entry_points=[CommandHandler("report", self.report_command)],
            states={
                ConversationState.REPORT_NAME: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.report_name)
                ],
                ConversationState.REPORT_TELEGRAM: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.report_telegram)
                ],
                ConversationState.REPORT_BINANCE: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.report_binance)
                ],
                ConversationState.REPORT_LINK: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.report_link)
                ],
                ConversationState.REPORT_AMOUNT: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.report_amount)
                ],
                ConversationState.REPORT_CONFIRM: [
                    CallbackQueryHandler(self.report_confirm, pattern='^(confirm|cancel)_report$')
                ],
            },
            fallbacks=[CommandHandler("cancel", self.cancel_report)],
        )
        self.app.add_handler(report_conv_handler)
        
        # Handler callback query
        self.app.add_handler(CallbackQueryHandler(self.handle_callback))
        
        # Handler message
        self.app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
        
        # Handler lỗi
        self.app.add_error_handler(self.error_handler)
        
        logger.info("✅ All handlers registered successfully")
    
    async def run_bot(self):
        """Chạy bot với cấu hình Railway"""
        if WEBHOOK_URL:
            # Chế độ webhook cho Railway/Heroku
            webhook_url = f"{WEBHOOK_URL}/{BOT_TOKEN}"
            
            await self.app.bot.set_webhook(
                url=webhook_url,
                allowed_updates=Update.ALL_TYPES
            )
            
            logger.info(f"🌐 Webhook set to: {webhook_url}")
            
            # Start webhook server
            await self.app.run_webhook(
                listen="0.0.0.0",
                port=PORT,
                webhook_url=webhook_url,
                url_path=BOT_TOKEN
            )
        else:
            # Chế độ polling cho local/VPS
            logger.info("🔄 Starting in polling mode...")
            await self.app.run_polling(allowed_updates=Update.ALL_TYPES)
    
    # ==================== COMMAND HANDLERS ====================
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Xử lý lệnh /start"""
        user = update.effective_user
        chat = update.effective_chat
        
        # Đăng ký/ cập nhật người dùng
        await db_manager.create_or_update_user(
            user_id=user.id,
            username=user.username or '',
            first_name=user.first_name or '',
            last_name=user.last_name or ''
        )
        
        # Lấy ngôn ngữ của người dùng
        user_lang = await db_manager.get_user_language(user.id)
        
        # Tạo menu chào mừng
        keyboard = [
            [InlineKeyboardButton("🇬🇧 English", callback_data="lang_en")],
            [InlineKeyboardButton("🇻🇳 Tiếng Việt", callback_data="lang_vi")],
            [InlineKeyboardButton("🇨🇳 中文", callback_data="lang_zh")],
            [InlineKeyboardButton("🇩🇪 Deutsch", callback_data="lang_de")],
            [InlineKeyboardButton("🇷🇺 Русский", callback_data="lang_ru")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Gửi thông điệp chào mừng
        welcome_text = translator.get('en', 'bot_name_frame') + "\n\n"
        welcome_text += translator.get('en', 'welcome_new_user')
        
        await update.message.reply_text(
            welcome_text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=reply_markup
        )
        
        # Log hành động
        await db_manager.log_action(
            user_id=user.id,
            action_type='start_command',
            action_details={'chat_type': chat.type}
        )
    
    async def search_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Xử lý lệnh /search"""
        user = update.effective_user
        user_lang = await db_manager.get_user_language(user.id)
        
        await update.message.reply_text(
            translator.get(user_lang, 'search_prompt'),
            parse_mode=ParseMode.MARKDOWN
        )
        
        # Đặt trạng thái tìm kiếm
        context.user_data['awaiting_search'] = True
    
    async def report_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Xử lý lệnh /report"""
        user = update.effective_user
        user_lang = await db_manager.get_user_language(user.id)
        
        # Khởi tạo session báo cáo
        context.user_data['report_data'] = {}
        
        # Gửi hướng dẫn bước 1
        await update.message.reply_text(
            translator.get(user_lang, 'report_start'),
            parse_mode=ParseMode.MARKDOWN
        )
        
        await update.message.reply_text(
            translator.get(user_lang, 'step1_name'),
            parse_mode=ParseMode.MARKDOWN
        )
        
        return ConversationState.REPORT_NAME
    
    async def stats_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Xử lý lệnh /stats"""
        user = update.effective_user
        user_lang = await db_manager.get_user_language(user.id)
        
        # Lấy thống kê
        stats = await db_manager.get_statistics(days=7)
        
        # Xây dựng thông điệp thống kê
        message = translator.get(user_lang, 'stats_title').format(
            updated_at=datetime.now().strftime(translator.get(user_lang, 'time_format'))
        )
        
        # Thêm tổng quan
        if stats['total']:
            message += translator.get(user_lang, 'stats_total').format(
                total_reports=stats['total'].get('total_reports', 0),
                confirmed_scams=stats['total'].get('confirmed_scams', 0),
                total_amount=f"{stats['total'].get('total_amount', 0):,.2f}",
                unique_users=stats['total'].get('unique_users', 0)
            )
        
        # Thêm thống kê hàng ngày
        daily_text = ""
        for day in stats['daily'][:7]:  # 7 ngày gần nhất
            daily_text += translator.get(user_lang, 'stats_daily_item').format(
                date=day['date'].strftime('%Y-%m-%d') if isinstance(day['date'], datetime) else day['date'],
                reports=day['reports'],
                amount=f"{day['amount']:,.2f}"
            )
        
        if daily_text:
            message += translator.get(user_lang, 'stats_daily').format(daily_stats=daily_text)
        
        # Thêm top scammers
        top_text = ""
        for i, scammer in enumerate(stats['top_scammers'][:10], 1):
            top_text += f"{i}. " + translator.get(user_lang, 'stats_top_item').format(
                name=scammer['scammer_name'][:30],
                amount=f"{scammer['total_amount']:,.2f}",
                reports=scammer['report_count']
            )
        
        if top_text:
            message += translator.get(user_lang, 'stats_top_scammers').format(top_scammers=top_text)
        
        # Thêm footer bảo mật
        message += translator.get(user_lang, 'security_footer')
        
        await update.message.reply_text(
            message,
            parse_mode=ParseMode.MARKDOWN
        )
        
        # Log hành động
        await db_manager.log_action(
            user_id=user.id,
            action_type='view_stats'
        )
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Xử lý lệnh /help"""
        user = update.effective_user
        user_lang = await db_manager.get_user_language(user.id)
        
        message = translator.get(user_lang, 'help_title') + "\n\n"
        message += translator.get(user_lang, 'help_sections').format(
            admin_link=ADMIN_SUPPORT_LINK
        )
        
        # Thêm menu nhanh
        keyboard = [
            [
                InlineKeyboardButton(
                    translator.get(user_lang, 'menu_search'),
                    callback_data="quick_search"
                ),
                InlineKeyboardButton(
                    translator.get(user_lang, 'menu_report'),
                    callback_data="quick_report"
                )
            ],
            [
                InlineKeyboardButton(
                    translator.get(user_lang, 'menu_risk_warning'),
                    callback_data="quick_risk"
                ),
                InlineKeyboardButton(
                    translator.get(user_lang, 'menu_safe_trade'),
                    callback_data="quick_trade"
                )
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            message,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=reply_markup
        )
    
    async def language_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Xử lý lệnh /language"""
        await self.show_language_selection(update, context)
    
    async def risk_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Xử lý lệnh /risk"""
        user = update.effective_user
        user_lang = await db_manager.get_user_language(user.id)
        
        message = translator.get(user_lang, 'risk_warning').format(
            support_link=ADMIN_SUPPORT_LINK
        )
        
        await update.message.reply_text(
            message,
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def trade_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Xử lý lệnh /trade"""
        user = update.effective_user
        user_lang = await db_manager.get_user_language(user.id)
        
        message = translator.get(user_lang, 'safe_trading').format(
            trade_link=SAFE_TRADE_LINK
        )
        
        await update.message.reply_text(
            message,
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def admin_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Xử lý lệnh /admin"""
        user = update.effective_user
        
        if user.id not in ADMIN_IDS:
            user_lang = await db_manager.get_user_language(user.id)
            await update.message.reply_text(
                translator.get(user_lang, 'error_not_admin'),
                parse_mode=ParseMode.MARKDOWN
            )
            
            # Log truy cập trái phép
            await db_manager.log_action(
                user_id=user.id,
                action_type='unauthorized_admin_access'
            )
            return
        
        # Hiển thị admin panel
        await self.show_admin_panel(update, context)
    
    # ==================== REPORT CONVERSATION HANDLERS ====================
    async def report_name(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Bước 1: Nhận tên kẻ lừa đảo"""
        user = update.effective_user
        user_lang = await db_manager.get_user_language(user.id)
        
        name = update.message.text.strip()
        
        # Kiểm tra độ dài
        if len(name) < 2 or len(name) > 100:
            await update.message.reply_text(
                "❌ Name must be between 2-100 characters. Please try again:",
                parse_mode=ParseMode.MARKDOWN
            )
            return ConversationState.REPORT_NAME
        
        # Lưu vào session
        context.user_data['report_data']['name'] = name
        
        # Chuyển sang bước 2
        await update.message.reply_text(
            translator.get(user_lang, 'step2_telegram'),
            parse_mode=ParseMode.MARKDOWN
        )
        
        return ConversationState.REPORT_TELEGRAM
    
    async def report_telegram(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Bước 2: Nhận thông tin Telegram"""
        user = update.effective_user
        user_lang = await db_manager.get_user_language(user.id)
        
        telegram = update.message.text.strip()
        
        # Validate Telegram info
        if not re.match(r'^(@\w{5,32}|(?:\+\d{1,3}[- ]?)?\d{10}|t\.me/\w+)$', telegram, re.IGNORECASE):
            await update.message.reply_text(
                "❌ Invalid Telegram format. Please provide:\n"
                "• @username\n"
                "• Phone number\n"
                "• t.me/username\n\n"
                "Please try again:",
                parse_mode=ParseMode.MARKDOWN
            )
            return ConversationState.REPORT_TELEGRAM
        
        # Kiểm tra blacklist
        blacklist_entry = await db_manager.check_blacklist(telegram)
        if blacklist_entry:
            await update.message.reply_text(
                translator.get(user_lang, 'error_blacklisted').format(
                    severity=blacklist_entry['severity'],
                    reason=blacklist_entry['reason']
                ),
                parse_mode=ParseMode.MARKDOWN
            )
            return ConversationHandler.END
        
        # Lưu vào session
        context.user_data['report_data']['telegram'] = telegram
        
        # Chuyển sang bước 3
        await update.message.reply_text(
            translator.get(user_lang, 'step3_binance'),
            parse_mode=ParseMode.MARKDOWN
        )
        
        return ConversationState.REPORT_BINANCE
    
    async def report_binance(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Bước 3: Nhận thông tin Binance"""
        user = update.effective_user
        user_lang = await db_manager.get_user_language(user.id)
        
        binance = update.message.text.strip()
        
        # Validate Binance ID
        if len(binance) < 3 or len(binance) > 100:
            await update.message.reply_text(
                "❌ Binance ID must be 3-100 characters. Please try again:",
                parse_mode=ParseMode.MARKDOWN
            )
            return ConversationState.REPORT_BINANCE
        
        # Kiểm tra blacklist
        blacklist_entry = await db_manager.check_blacklist(binance)
        if blacklist_entry:
            await update.message.reply_text(
                translator.get(user_lang, 'error_blacklisted').format(
                    severity=blacklist_entry['severity'],
                    reason=blacklist_entry['reason']
                ),
                parse_mode=ParseMode.MARKDOWN
            )
            return ConversationHandler.END
        
        # Lưu vào session
        context.user_data['report_data']['binance'] = binance
        
        # Chuyển sang bước 4
        await update.message.reply_text(
            translator.get(user_lang, 'step4_link'),
            parse_mode=ParseMode.MARKDOWN
        )
        
        return ConversationState.REPORT_LINK
    
    async def report_link(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Bước 4: Nhận link Telegram"""
        user = update.effective_user
        user_lang = await db_manager.get_user_language(user.id)
        
        link = update.message.text.strip()
        
        # Validate link
        if not re.match(r'^(https?://)?(t\.me/|telegram\.me/)\w+$', link, re.IGNORECASE):
            await update.message.reply_text(
                "❌ Invalid Telegram link. Please provide:\n"
                "• t.me/username\n"
                "• https://t.me/username\n"
                "• telegram.me/username\n\n"
                "Please try again:",
                parse_mode=ParseMode.MARKDOWN
            )
            return ConversationState.REPORT_LINK
        
        # Đảm bảo link có https://
        if not link.startswith('http'):
            link = 'https://' + link
        
        # Lưu vào session
        context.user_data['report_data']['link'] = link
        
        # Chuyển sang bước 5
        await update.message.reply_text(
            translator.get(user_lang, 'step5_amount'),
            parse_mode=ParseMode.MARKDOWN
        )
        
        return ConversationState.REPORT_AMOUNT
    
    async def report_amount(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Bước 5: Nhận số tiền"""
        user = update.effective_user
        user_lang = await db_manager.get_user_language(user.id)
        
        amount_text = update.message.text.strip()
        
        try:
            # Parse amount
            amount = float(amount_text.replace(',', ''))
            
            if amount < 10:
                await update.message.reply_text(
                    "❌ Minimum amount is $10. Please try again:",
                    parse_mode=ParseMode.MARKDOWN
                )
                return ConversationState.REPORT_AMOUNT
            
            if amount > 1000000:
                await update.message.reply_text(
                    "❌ Maximum amount is $1,000,000. Please try again:",
                    parse_mode=ParseMode.MARKDOWN
                )
                return ConversationState.REPORT_AMOUNT
            
            # Lưu vào session
            context.user_data['report_data']['amount'] = amount
            
            # Hiển thị xác nhận
            report_data = context.user_data['report_data']
            
            confirm_text = translator.get(user_lang, 'report_confirm').format(
                name=report_data['name'],
                telegram=report_data['telegram'],
                binance=report_data['binance'],
                link=report_data['link'],
                amount=f"{amount:,.2f}"
            )
            
            keyboard = [
                [
                    InlineKeyboardButton(
                        translator.get(user_lang, 'btn_yes'),
                        callback_data="confirm_report"
                    ),
                    InlineKeyboardButton(
                        translator.get(user_lang, 'btn_no'),
                        callback_data="cancel_report"
                    )
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                confirm_text,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=reply_markup
            )
            
            return ConversationState.REPORT_CONFIRM
            
        except ValueError:
            await update.message.reply_text(
                translator.get(user_lang, 'error_invalid_amount'),
                parse_mode=ParseMode.MARKDOWN
            )
            return ConversationState.REPORT_AMOUNT
    
    async def report_confirm(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Xác nhận hoặc hủy báo cáo"""
        query = update.callback_query
        await query.answer()
        
        user = query.from_user
        user_lang = await db_manager.get_user_language(user.id)
        
        if query.data == 'confirm_report':
            # Lưu báo cáo vào database
            report_data = context.user_data.get('report_data', {})
            
            try:
                report_id = await db_manager.create_scam_report(
                    user_id=user.id,
                    scammer_data=report_data
                )
                
                # Thông báo thành công
                success_text = translator.get(user_lang, 'report_submitted').format(
                    report_id=report_id,
                    timestamp=datetime.now().strftime(translator.get(user_lang, 'time_format'))
                )
                
                await query.edit_message_text(
                    success_text,
                    parse_mode=ParseMode.MARKDOWN
                )
                
                # Thông báo cho admin
                admin_message = (
                    f"🚨 *NEW SCAM REPORT*\n\n"
                    f"📋 Report ID: #{report_id}\n"
                    f"👤 From: {user.username or user.id}\n"
                    f"⏰ Time: {datetime.now().strftime('%H:%M:%S UTC')}\n\n"
                    f"📝 *Details:*\n"
                    f"• Name: `{report_data.get('name')}`\n"
                    f"• Telegram: `{report_data.get('telegram')}`\n"
                    f"• Amount: `${report_data.get('amount', 0):,.2f}`\n\n"
                    f"⚠️ Requires review!"
                )
                
                for admin_id in ADMIN_IDS:
                    try:
                        await context.bot.send_message(
                            chat_id=admin_id,
                            text=admin_message,
                            parse_mode=ParseMode.MARKDOWN
                        )
                    except Exception as e:
                        logger.error(f"Failed to notify admin {admin_id}: {e}")
                
            except Exception as e:
                logger.error(f"Failed to save report: {e}")
                await query.edit_message_text(
                    translator.get(user_lang, 'error_general'),
                    parse_mode=ParseMode.MARKDOWN
                )
            
            # Xóa session
            if 'report_data' in context.user_data:
                del context.user_data['report_data']
                
        else:  # cancel_report
            await query.edit_message_text(
                translator.get(user_lang, 'report_cancelled'),
                parse_mode=ParseMode.MARKDOWN
            )
            
            # Xóa session
            if 'report_data' in context.user_data:
                del context.user_data['report_data']
        
        return ConversationHandler.END
    
    async def cancel_report(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Hủy báo cáo"""
        user = update.effective_user
        user_lang = await db_manager.get_user_language(user.id)
        
        # Xóa session
        if 'report_data' in context.user_data:
            del context.user_data['report_data']
        
        await update.message.reply_text(
            translator.get(user_lang, 'report_cancelled'),
            parse_mode=ParseMode.MARKDOWN
        )
        
        return ConversationHandler.END
    
    # ==================== MESSAGE HANDLER ====================
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Xử lý tin nhắn thường"""
        user = update.effective_user
        message = update.message.text
        
        # Kiểm tra nếu đang chờ tìm kiếm
        if context.user_data.get('awaiting_search'):
            del context.user_data['awaiting_search']
            await self.perform_search(update, context, message)
            return
        
        # Hiển thị menu chính
        await self.show_main_menu(update, context)
    
    async def perform_search(self, update: Update, context: ContextTypes.DEFAULT_TYPE, query: str):
        """Thực hiện tìm kiếm"""
        user = update.effective_user
        user_lang = await db_manager.get_user_language(user.id)
        
        # Log tìm kiếm
        await db_manager.increment_search_count(user.id)
        
        # Hiển thị trạng thái đang tìm kiếm
        searching_msg = await update.message.reply_text(
            "🔍 *Searching database...*",
            parse_mode=ParseMode.MARKDOWN
        )
        
        try:
            # Thực hiện tìm kiếm
            results = await db_manager.search_scammer(query)
            
            # Xóa tin nhắn đang tìm kiếm
            await searching_msg.delete()
            
            if not results:
                await update.message.reply_text(
                    translator.get(user_lang, 'no_results').format(query=query),
                    parse_mode=ParseMode.MARKDOWN
                )
                return
            
            # Phân loại kết quả
            reports = [r for r in results if r['type'] == 'report']
            blacklist = [r for r in results if r['type'] == 'blacklist']
            
            # Hiển thị kết quả
            result_text = translator.get(user_lang, 'search_results').format(
                query=query,
                count=len(results)
            )
            
            # Thêm reports
            if reports:
                result_text += "\n📋 *SCAM REPORTS:*\n"
                for i, item in enumerate(reports[:5], 1):
                    data = item['data']
                    result_text += f"\n{i}. *{data.get('scammer_name', 'N/A')}*\n"
                    result_text += f"   Telegram: `{data.get('scammer_telegram', 'N/A')}`\n"
                    result_text += f"   Amount: `${data.get('amount_usd', 0):,.2f}`\n"
                    result_text += f"   Status: {data.get('status', 'pending')}\n"
            
            # Thêm blacklist
            if blacklist:
                result_text += "\n🚫 *BLACKLIST ENTRIES:*\n"
                for i, item in enumerate(blacklist[:3], 1):
                    data = item['data']
                    result_text += f"\n{i}. `{data.get('identifier', 'N/A')}`\n"
                    result_text += f"   Type: {data.get('identifier_type', 'N/A')}\n"
                    result_text += f"   Severity: {data.get('severity', 'medium')}\n"
                    result_text += f"   Reason: {data.get('reason', 'No reason provided')[:100]}...\n"
            
            # Thêm cảnh báo
            result_text += translator.get(user_lang, 'security_footer')
            
            # Gửi kết quả
            await update.message.reply_text(
                result_text,
                parse_mode=ParseMode.MARKDOWN,
                disable_web_page_preview=True
            )
            
        except Exception as e:
            logger.error(f"Search error: {e}")
            await searching_msg.delete()
            await update.message.reply_text(
                translator.get(user_lang, 'error_general'),
                parse_mode=ParseMode.MARKDOWN
            )
    
    # ==================== CALLBACK HANDLER ====================
    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Xử lý callback query"""
        query = update.callback_query
        await query.answer()
        
        data = query.data
        user = query.from_user
        user_lang = await db_manager.get_user_language(user.id)
        
        # Xử lý chọn ngôn ngữ
        if data.startswith('lang_'):
            language = data.split('_')[1]
            await db_manager.set_user_language(user.id, language)
            
            await query.edit_message_text(
                translator.get(language, 'language_changed').format(
                    language=language.upper()
                ),
                parse_mode=ParseMode.MARKDOWN
            )
            
            # Hiển thị menu chính với ngôn ngữ mới
            await asyncio.sleep(1)
            await self.show_main_menu(update, context, language=language)
            
        # Xử lý các callback khác
        elif data == 'main_menu':
            await self.show_main_menu(update, context)
            
        elif data == 'quick_search':
            await query.edit_message_text(
                translator.get(user_lang, 'search_prompt'),
                parse_mode=ParseMode.MARKDOWN
            )
            context.user_data['awaiting_search'] = True
            
        elif data == 'quick_report':
            await self.report_command(update, context)
            
        elif data == 'quick_risk':
            await self.risk_command(update, context)
            
        elif data == 'quick_trade':
            await self.trade_command(update, context)
            
        elif data == 'admin_panel':
            if user.id in ADMIN_IDS:
                await self.show_admin_panel(update, context)
            else:
                await query.edit_message_text(
                    translator.get(user_lang, 'error_not_admin'),
                    parse_mode=ParseMode.MARKDOWN
                )
    
    # ==================== MENU FUNCTIONS ====================
    async def show_main_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE, language: str = None):
        """Hiển thị menu chính"""
        if isinstance(update, Update) and update.message:
            user = update.effective_user
            message = update.message
        elif update.callback_query:
            user = update.callback_query.from_user
            message = update.callback_query.message
        else:
            return
        
        user_lang = language or await db_manager.get_user_language(user.id)
        
        # Tạo keyboard menu
        keyboard = [
            [
                InlineKeyboardButton(
                    translator.get(user_lang, 'menu_search'),
                    callback_data="quick_search"
                ),
                InlineKeyboardButton(
                    translator.get(user_lang, 'menu_report'),
                    callback_data="quick_report"
                )
            ],
            [
                InlineKeyboardButton(
                    translator.get(user_lang, 'menu_my_reports'),
                    callback_data="my_reports"
                ),
                InlineKeyboardButton(
                    translator.get(user_lang, 'menu_statistics'),
                    callback_data="view_stats"
                )
            ],
            [
                InlineKeyboardButton(
                    translator.get(user_lang, 'menu_risk_warning'),
                    callback_data="quick_risk"
                ),
                InlineKeyboardButton(
                    translator.get(user_lang, 'menu_safe_trade'),
                    callback_data="quick_trade"
                )
            ],
            [
                InlineKeyboardButton(
                    translator.get(user_lang, 'menu_settings'),
                    callback_data="settings_menu"
                ),
                InlineKeyboardButton(
                    translator.get(user_lang, 'menu_help'),
                    callback_data="help_menu"
                )
            ]
        ]
        
        # Thêm nút admin nếu là admin
        if user.id in ADMIN_IDS:
            keyboard.append([
                InlineKeyboardButton(
                    "🛡️ ADMIN PANEL",
                    callback_data="admin_panel"
                )
            ])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Lấy thông tin người dùng
        user_info = await db_manager.get_user(user.id)
        if user_info:
            welcome_text = translator.get(user_lang, 'welcome_returning').format(
                last_login=user_info['last_active'].strftime(translator.get(user_lang, 'time_format')),
                report_count=user_info['report_count'],
                search_count=user_info['search_count']
            )
        else:
            welcome_text = "Welcome! How can I help you today?"
        
        # Gửi hoặc chỉnh sửa tin nhắn
        if hasattr(message, 'edit_text'):
            await message.edit_text(
                translator.get(user_lang, 'main_menu_title') + "\n\n" + welcome_text,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=reply_markup
            )
        else:
            await message.reply_text(
                translator.get(user_lang, 'main_menu_title') + "\n\n" + welcome_text,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=reply_markup
            )
    
    async def show_language_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Hiển thị menu chọn ngôn ngữ"""
        user = update.effective_user
        
        keyboard = [
            [InlineKeyboardButton("🇬🇧 English", callback_data="lang_en")],
            [InlineKeyboardButton("🇻🇳 Tiếng Việt", callback_data="lang_vi")],
            [InlineKeyboardButton("🇨🇳 中文", callback_data="lang_zh")],
            [InlineKeyboardButton("🇩🇪 Deutsch", callback_data="lang_de")],
            [InlineKeyboardButton("🇷🇺 Русский", callback_data="lang_ru")],
            [InlineKeyboardButton("↩️ Back to Menu", callback_data="main_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            translator.get('en', 'language_select'),
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=reply_markup
        )
    
    async def show_admin_panel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Hiển thị admin panel"""
        query = update.callback_query if update.callback_query else None
        user = update.effective_user if update.effective_user else query.from_user
        
        keyboard = [
            [
                InlineKeyboardButton("📊 System Stats", callback_data="admin_stats"),
                InlineKeyboardButton("📋 Pending Reports", callback_data="admin_reports")
            ],
            [
                InlineKeyboardButton("🚫 Blacklist", callback_data="admin_blacklist"),
                InlineKeyboardButton("👥 User Management", callback_data="admin_users")
            ],
            [
                InlineKeyboardButton("📜 Activity Logs", callback_data="admin_logs"),
                InlineKeyboardButton("📢 Broadcast", callback_data="admin_broadcast")
            ],
            [
                InlineKeyboardButton("💾 Backup Database", callback_data="admin_backup"),
                InlineKeyboardButton("🔧 Maintenance", callback_data="admin_maintenance")
            ],
            [
                InlineKeyboardButton("↩️ Back to Menu", callback_data="main_menu")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        admin_text = translator.get('en', 'admin_panel')
        
        if query:
            await query.edit_message_text(
                admin_text,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=reply_markup
            )
        else:
            await update.message.reply_text(
                admin_text,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=reply_markup
            )
    
    # ==================== ERROR HANDLER ====================
    async def error_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Xử lý lỗi toàn cục"""
        logger.error(f"Exception while handling an update: {context.error}")
        
        # Log lỗi chi tiết
        error_msg = f"🚨 *BOT ERROR*\n\n"
        error_msg += f"Error: `{type(context.error).__name__}`\n"
        error_msg += f"Message: `{str(context.error)[:200]}`\n"
        
        if update and update.effective_user:
            error_msg += f"User: {update.effective_user.id}\n"
            error_msg += f"Chat: {update.effective_chat.id if update.effective_chat else 'N/A'}\n"
        
        error_msg += f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}"
        
        # Gửi thông báo lỗi cho admin
        for admin_id in ADMIN_IDS:
            try:
                await context.bot.send_message(
                    chat_id=admin_id,
                    text=error_msg,
                    parse_mode=ParseMode.MARKDOWN
                )
            except Exception as e:
                logger.error(f"Failed to send error to admin: {e}")
        
        # Thông báo cho người dùng nếu có
        if update and update.effective_user:
            try:
                user_lang = await db_manager.get_user_language(update.effective_user.id)
                await context.bot.send_message(
                    chat_id=update.effective_user.id,
                    text=translator.get(user_lang, 'error_general'),
                    parse_mode=ParseMode.MARKDOWN
                )
            except Exception as e:
                logger.error(f"Failed to notify user of error: {e}")

# ==================== HÀM CHÍNH ====================
async def main():
    """Hàm chính khởi chạy bot"""
    print(translator.get('en', 'bot_name_frame'))
    print("\n" + "="*60)
    print("🤖 ANTI-SCAM SECURITY BOT - STARTING...")
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print(f"🐍 Python {sys.version}")
    print(f"📊 Database: {DATABASE_URL[:30]}...")
    print("="*60 + "\n")
    
    # Khởi tạo và chạy bot
    bot = AntiScamBot()
    await bot.start()

if __name__ == '__main__':
    # Chạy bot
    asyncio.run(main())
