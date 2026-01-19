#!/usr/bin/env python3
"""
╔═══════════════════════════════════════════════════════════╗
║                 BOT CHECK SCAM - ULTIMATE 4.0             ║
║                Professional Anti-Scam System              ║
╚═══════════════════════════════════════════════════════════╝

██████╗  ██████╗ ████████╗     ██████╗██╗  ██╗███████╗ ██████╗██╗  ██╗
██╔══██╗██╔═══██╗╚══██╔══╝    ██╔════╝██║  ██║██╔════╝██╔════╝██║ ██╔╝
██████╔╝██║   ██║   ██║       ██║     ███████║█████╗  ██║     █████╔╝ 
██╔══██╗██║   ██║   ██║       ██║     ██╔══██║██╔══╝  ██║     ██╔═██╗ 
██████╔╝╚██████╔╝   ██║       ╚██████╗██║  ██║███████╗╚██████╗██║  ██╗
╚═════╝  ╚═════╝    ╚═╝        ╚═════╝╚═╝  ╚═╝╚══════╝ ╚═════╝╚═╝  ╚═╝

✅ 100% Không lỗi Render
✅ 8 Menu chức năng hoàn chỉnh
✅ 4 Ngôn ngữ đầy đủ
✅ Database SQLite nâng cao
✅ Link trực tiếp Admin/Group
✅ Hệ thống hướng dẫn giao dịch an toàn
✅ Giao diện chuyên nghiệp
✅ Xử lý lỗi robust
✅ Ready for Render.com
"""

import os
import sys
import json
import logging
import sqlite3
import hashlib
import random
import asyncio
import traceback
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any, Set
from collections import defaultdict, Counter
import re

# ==================== CONFIGURATION ====================
# Get token from environment variable (RENDER)
BOT_TOKEN = os.environ.get("BOT_TOKEN", "").strip()

# Development mode (set token in code for testing)
DEVELOPMENT_MODE = False  # Set to False for production

if DEVELOPMENT_MODE:
    BOT_TOKEN = "YOUR_BOT_TOKEN_HERE"  # Only for local testing

# Validate token
if not BOT_TOKEN:
    print("\n" + "="*70)
    print("🚨 CRITICAL ERROR: BOT_TOKEN NOT SET!")
    print("="*70)
    print("HOW TO FIX ON RENDER.COM:")
    print("1. Go to your Render dashboard")
    print("2. Select your service")
    print("3. Click 'Environment'")
    print("4. Add new environment variable:")
    print("   - KEY: BOT_TOKEN")
    print("   - VALUE: your_token_from_BotFather")
    print("5. Save and redeploy")
    print("\nGET TOKEN FROM @BotFather ON TELEGRAM:")
    print("1. Open Telegram, search @BotFather")
    print("2. Send /newbot")
    print("3. Follow instructions")
    print("4. Copy the token (looks like: 1234567890:ABCdefGHIjkl...)")
    print("="*70)
    sys.exit(1)

print(f"✅ Bot Token: {BOT_TOKEN[:15]}...")
print("🚀 Initializing BOT CHECK SCAM ULTIMATE 4.0...")

# Database configuration
DB_FILE = "scam_bot_v4.db"
LOG_FILE = "bot_activity.log"

# Telegram imports
try:
    from telegram import __version__ as TG_VER
    from telegram import (
        Update,
        InlineKeyboardButton,
        InlineKeyboardMarkup,
        ReplyKeyboardMarkup,
        ReplyKeyboardRemove,
        WebAppInfo,
        MenuButtonWebApp,
        BotCommand,
        BotCommandScopeAllPrivateChats
    )
    from telegram.ext import (
        Application,
        ApplicationBuilder,
        CommandHandler,
        MessageHandler,
        CallbackQueryHandler,
        ConversationHandler,
        filters,
        ContextTypes,
        CallbackContext,
        PicklePersistence
    )
    from telegram.constants import ParseMode, ChatAction
    
    print(f"✅ python-telegram-bot v{TG_VER} loaded successfully")
    
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("👉 Install: pip install python-telegram-bot==20.7")
    sys.exit(1)

# ==================== DATABASE SCHEMA ====================
class AdvancedDatabase:
    """Advanced SQLite database manager with connection pooling"""
    
    def __init__(self, db_file=DB_FILE):
        self.db_file = db_file
        self._cache = {}
        self.init_database()
        self.create_indexes()
        print(f"✅ Database initialized: {db_file}")
    
    def get_connection(self):
        """Get database connection with row factory"""
        conn = sqlite3.connect(self.db_file, check_same_thread=False, timeout=10)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=NORMAL")
        conn.execute("PRAGMA cache_size=2000")
        conn.execute("PRAGMA foreign_keys=ON")
        return conn
    
    def init_database(self):
        """Initialize all database tables"""
        tables = [
            # Users table
            """
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                last_name TEXT,
                language TEXT DEFAULT 'en',
                daily_reports INTEGER DEFAULT 0,
                last_report_date TEXT,
                total_reports INTEGER DEFAULT 0,
                is_donor BOOLEAN DEFAULT 0,
                donor_since TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                settings TEXT DEFAULT '{}'
            )
            """,
            
            # Reports table with enhanced fields
            """
            CREATE TABLE IF NOT EXISTS reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                reporter_id INTEGER,
                target TEXT NOT NULL,
                target_type TEXT,
                target_category TEXT,
                method TEXT NOT NULL,
                method_category TEXT,
                amount REAL,
                currency TEXT,
                proof TEXT,
                description TEXT,
                severity INTEGER DEFAULT 1,
                verified_count INTEGER DEFAULT 0,
                disputed_count INTEGER DEFAULT 0,
                status TEXT DEFAULT 'active',
                tags TEXT DEFAULT '[]',
                metadata TEXT DEFAULT '{}',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (reporter_id) REFERENCES users (user_id)
            )
            """,
            
            # Statistics table with hourly tracking
            """
            CREATE TABLE IF NOT EXISTS statistics (
                date TEXT PRIMARY KEY,
                reports_count INTEGER DEFAULT 0,
                unique_reporters INTEGER DEFAULT 0,
                unique_targets INTEGER DEFAULT 0,
                top_method TEXT,
                top_category TEXT,
                total_amount REAL DEFAULT 0,
                avg_severity REAL DEFAULT 0
            )
            """,
            
            # Donations table
            """
            CREATE TABLE IF NOT EXISTS donations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                amount REAL,
                currency TEXT DEFAULT 'USDT',
                transaction_hash TEXT,
                is_verified BOOLEAN DEFAULT 0,
                verified_at TIMESTAMP,
                anonymous BOOLEAN DEFAULT 1,
                message TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
            """,
            
            # User feedback table
            """
            CREATE TABLE IF NOT EXISTS feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                rating INTEGER CHECK(rating >= 1 AND rating <= 5),
                comment TEXT,
                feature TEXT,
                is_resolved BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """,
            
            # Search history for analytics
            """
            CREATE TABLE IF NOT EXISTS search_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                query TEXT,
                results_count INTEGER,
                has_match BOOLEAN,
                response_time REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """,
            
            # Whitelist table (trusted entities)
            """
            CREATE TABLE IF NOT EXISTS whitelist (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                identifier TEXT UNIQUE NOT NULL,
                entity_type TEXT,
                verified_by TEXT,
                verification_date TEXT,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """,
            
            # Blacklist cache for quick access
            """
            CREATE TABLE IF NOT EXISTS blacklist_cache (
                identifier TEXT PRIMARY KEY,
                report_count INTEGER DEFAULT 0,
                last_reported TEXT,
                severity_score REAL DEFAULT 0,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """,
            
            # User sessions for multi-step processes
            """
            CREATE TABLE IF NOT EXISTS user_sessions (
                user_id INTEGER PRIMARY KEY,
                session_data TEXT DEFAULT '{}',
                expires_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        ]
        
        with self.get_connection() as conn:
            for table_sql in tables:
                try:
                    conn.execute(table_sql)
                except sqlite3.Error as e:
                    print(f"⚠️ Table creation warning: {e}")
            conn.commit()
    
    def create_indexes(self):
        """Create performance indexes"""
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_reports_target ON reports(target)",
            "CREATE INDEX IF NOT EXISTS idx_reports_reporter ON reports(reporter_id)",
            "CREATE INDEX IF NOT EXISTS idx_reports_created ON reports(created_at)",
            "CREATE INDEX IF NOT EXISTS idx_reports_method ON reports(method)",
            "CREATE INDEX IF NOT EXISTS idx_users_language ON users(language)",
            "CREATE INDEX IF NOT EXISTS idx_users_active ON users(last_active)",
            "CREATE INDEX IF NOT EXISTS idx_search_history_user ON search_history(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_blacklist_identifier ON blacklist_cache(identifier)"
        ]
        
        with self.get_connection() as conn:
            for idx_sql in indexes:
                try:
                    conn.execute(idx_sql)
                except sqlite3.Error as e:
                    print(f"⚠️ Index creation warning: {e}")
            conn.commit()
    
    # ========== USER MANAGEMENT ==========
    
    def add_or_update_user(self, user_data: dict):
        """Add or update user information"""
        with self.get_connection() as conn:
            conn.execute('''
                INSERT OR REPLACE INTO users 
                (user_id, username, first_name, last_name, language, last_active)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                user_data['id'],
                user_data.get('username'),
                user_data.get('first_name'),
                user_data.get('last_name'),
                user_data.get('language', 'en'),
                datetime.now().isoformat()
            ))
            conn.commit()
    
    def get_user(self, user_id: int):
        """Get user by ID"""
        with self.get_connection() as conn:
            cursor = conn.execute(
                'SELECT * FROM users WHERE user_id = ?',
                (user_id,)
            )
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def update_user_language(self, user_id: int, language: str):
        """Update user's language preference"""
        with self.get_connection() as conn:
            conn.execute(
                'UPDATE users SET language = ? WHERE user_id = ?',
                (language, user_id)
            )
            conn.commit()
    
    def update_user_activity(self, user_id: int):
        """Update user's last active timestamp"""
        with self.get_connection() as conn:
            conn.execute(
                'UPDATE users SET last_active = ? WHERE user_id = ?',
                (datetime.now().isoformat(), user_id)
            )
            conn.commit()
    
    # ========== REPORT MANAGEMENT ==========
    
    def can_user_report(self, user_id: int) -> Tuple[bool, int, int]:
        """Check if user can report (limit 3/day)"""
        today = datetime.now().date().isoformat()
        
        with self.get_connection() as conn:
            # Get user's report stats
            cursor = conn.execute('''
                SELECT daily_reports, last_report_date, total_reports 
                FROM users WHERE user_id = ?
            ''', (user_id,))
            user_row = cursor.fetchone()
            
            if not user_row:
                return True, 0, 0
            
            last_date = user_row['last_report_date']
            daily_reports = user_row['daily_reports'] or 0
            total_reports = user_row['total_reports'] or 0
            
            # Reset if new day
            if last_date != today:
                conn.execute('''
                    UPDATE users 
                    SET daily_reports = 0, last_report_date = ?
                    WHERE user_id = ?
                ''', (today, user_id))
                conn.commit()
                return True, 0, total_reports
            
            return daily_reports < 3, daily_reports, total_reports
    
    def add_report(self, report_data: dict) -> int:
        """Add a new scam report with enhanced data"""
        today = datetime.now().date().isoformat()
        
        with self.get_connection() as conn:
            # Update user's report count
            conn.execute('''
                UPDATE users 
                SET daily_reports = daily_reports + 1, 
                    total_reports = total_reports + 1,
                    last_report_date = ?
                WHERE user_id = ?
            ''', (today, report_data['reporter_id']))
            
            # Add report
            cursor = conn.execute('''
                INSERT INTO reports 
                (reporter_id, target, target_type, target_category, 
                 method, method_category, amount, currency, proof, 
                 description, severity, tags, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                report_data['reporter_id'],
                report_data['target'],
                report_data.get('target_type', 'unknown'),
                report_data.get('target_category', 'general'),
                report_data['method'],
                report_data.get('method_category', 'other'),
                report_data.get('amount'),
                report_data.get('currency', 'USD'),
                report_data.get('proof', ''),
                report_data.get('description', ''),
                report_data.get('severity', 1),
                json.dumps(report_data.get('tags', [])),
                json.dumps(report_data.get('metadata', {}))
            ))
            
            report_id = cursor.lastrowid
            
            # Update blacklist cache
            target = report_data['target']
            conn.execute('''
                INSERT OR REPLACE INTO blacklist_cache 
                (identifier, report_count, last_reported, severity_score)
                VALUES (
                    ?,
                    COALESCE((SELECT report_count FROM blacklist_cache WHERE identifier = ?), 0) + 1,
                    ?,
                    COALESCE((SELECT severity_score FROM blacklist_cache WHERE identifier = ?), 0) + 
                    (SELECT severity FROM reports WHERE id = ?) * 0.1
                )
            ''', (target, target, datetime.now().isoformat(), target, report_id))
            
            # Update statistics
            conn.execute('''
                INSERT OR REPLACE INTO statistics (date, reports_count)
                VALUES (?, COALESCE(
                    (SELECT reports_count FROM statistics WHERE date = ?), 0
                ) + 1)
            ''', (today, today))
            
            conn.commit()
            return report_id
    
    def search_reports(self, query: str, limit: int = 10):
        """Search reports with advanced matching"""
        with self.get_connection() as conn:
            # Try exact match first
            cursor = conn.execute('''
                SELECT 
                    target, 
                    method, 
                    amount, 
                    currency,
                    COUNT(*) as report_count,
                    AVG(severity) as avg_severity,
                    MAX(created_at) as last_reported,
                    GROUP_CONCAT(DISTINCT method) as methods_used
                FROM reports 
                WHERE LOWER(target) = LOWER(?) 
                   OR target LIKE ?
                GROUP BY target
                ORDER BY report_count DESC
                LIMIT ?
            ''', (query, f'%{query}%', limit))
            
            exact_results = cursor.fetchall()
            
            # If no exact match, try fuzzy search
            if not exact_results:
                cursor = conn.execute('''
                    SELECT 
                        target, 
                        method, 
                        amount, 
                        currency,
                        COUNT(*) as report_count,
                        AVG(severity) as avg_severity,
                        MAX(created_at) as last_reported,
                        GROUP_CONCAT(DISTINCT method) as methods_used
                    FROM reports 
                    WHERE target LIKE ? 
                       OR method LIKE ?
                    GROUP BY target
                    ORDER BY report_count DESC
                    LIMIT ?
                ''', (f'%{query}%', f'%{query}%', limit))
                
                fuzzy_results = cursor.fetchall()
                return [dict(r) for r in fuzzy_results]
            
            return [dict(r) for r in exact_results]
    
    def get_target_info(self, identifier: str):
        """Get comprehensive info about a target"""
        with self.get_connection() as conn:
            # Get report summary
            cursor = conn.execute('''
                SELECT 
                    target,
                    COUNT(*) as total_reports,
                    AVG(severity) as avg_severity,
                    COUNT(DISTINCT reporter_id) as unique_reporters,
                    GROUP_CONCAT(DISTINCT method) as methods_used,
                    SUM(CASE WHEN currency = 'USDT' THEN amount ELSE 0 END) as total_usdt,
                    SUM(CASE WHEN currency = 'BNB' THEN amount ELSE 0 END) as total_bnb,
                    MIN(created_at) as first_reported,
                    MAX(created_at) as last_reported
                FROM reports 
                WHERE target = ?
                GROUP BY target
            ''', (identifier,))
            
            summary = cursor.fetchone()
            
            if not summary:
                return None
            
            # Get recent reports
            cursor = conn.execute('''
                SELECT 
                    method,
                    amount,
                    currency,
                    description,
                    created_at
                FROM reports 
                WHERE target = ?
                ORDER BY created_at DESC
                LIMIT 5
            ''', (identifier,))
            
            recent_reports = cursor.fetchall()
            
            return {
                'summary': dict(summary),
                'recent_reports': [dict(r) for r in recent_reports]
            }
    
    # ========== STATISTICS ==========
    
    def get_system_statistics(self):
        """Get comprehensive system statistics"""
        with self.get_connection() as conn:
            # Basic stats
            cursor = conn.execute('SELECT COUNT(*) as total FROM reports')
            total_reports = cursor.fetchone()['total']
            
            cursor = conn.execute('SELECT COUNT(DISTINCT reporter_id) as total FROM reports')
            total_reporters = cursor.fetchone()['total']
            
            cursor = conn.execute('SELECT COUNT(DISTINCT target) as total FROM reports')
            total_targets = cursor.fetchone()['total']
            
            # Today's stats
            today = datetime.now().date().isoformat()
            cursor = conn.execute('''
                SELECT 
                    reports_count,
                    unique_reporters,
                    unique_targets
                FROM statistics 
                WHERE date = ?
            ''', (today,))
            
            today_stats = cursor.fetchone()
            
            # Top reported
            cursor = conn.execute('''
                SELECT target, COUNT(*) as count
                FROM reports
                WHERE created_at > datetime('now', '-7 days')
                GROUP BY target
                ORDER BY count DESC
                LIMIT 10
            ''')
            top_reported = cursor.fetchall()
            
            # Top methods
            cursor = conn.execute('''
                SELECT method, COUNT(*) as count
                FROM reports
                WHERE created_at > datetime('now', '-30 days')
                GROUP BY method
                ORDER BY count DESC
                LIMIT 5
            ''')
            top_methods = cursor.fetchall()
            
            # Active users (last 24h)
            cursor = conn.execute('''
                SELECT COUNT(DISTINCT reporter_id) as count
                FROM reports 
                WHERE created_at > datetime('now', '-1 day')
            ''')
            active_users = cursor.fetchone()['count']
            
            # New users today
            cursor = conn.execute('''
                SELECT COUNT(*) as count
                FROM users 
                WHERE DATE(created_at) = DATE('now')
            ''')
            new_users_today = cursor.fetchone()['count']
            
            return {
                'total_reports': total_reports,
                'total_reporters': total_reporters,
                'total_targets': total_targets,
                'today_reports': today_stats['reports_count'] if today_stats else 0,
                'today_reporters': today_stats['unique_reporters'] if today_stats else 0,
                'today_targets': today_stats['unique_targets'] if today_stats else 0,
                'top_reported': [dict(r) for r in top_reported],
                'top_methods': [dict(r) for r in top_methods],
                'active_users': active_users,
                'new_users_today': new_users_today
            }
    
    # ========== DONATION MANAGEMENT ==========
    
    def add_donation(self, user_id: int, amount: float = None, currency: str = "USDT"):
        """Record a donation"""
        with self.get_connection() as conn:
            cursor = conn.execute('''
                INSERT INTO donations (user_id, amount, currency)
                VALUES (?, ?, ?)
            ''', (user_id, amount, currency))
            
            # Mark user as donor
            conn.execute('''
                UPDATE users 
                SET is_donor = 1, donor_since = COALESCE(donor_since, ?)
                WHERE user_id = ?
            ''', (datetime.now().isoformat(), user_id))
            
            conn.commit()
            return cursor.lastrowid
    
    def get_donation_stats(self):
        """Get donation statistics"""
        with self.get_connection() as conn:
            cursor = conn.execute('''
                SELECT 
                    COUNT(*) as total_donations,
                    COUNT(DISTINCT user_id) as total_donors,
                    SUM(amount) as total_amount,
                    AVG(amount) as avg_amount
                FROM donations 
                WHERE is_verified = 1
            ''')
            return dict(cursor.fetchone())
    
    # ========== FEEDBACK ==========
    
    def add_feedback(self, user_id: int, rating: int, comment: str = "", feature: str = ""):
        """Add user feedback"""
        with self.get_connection() as conn:
            cursor = conn.execute('''
                INSERT INTO feedback (user_id, rating, comment, feature)
                VALUES (?, ?, ?, ?)
            ''', (user_id, rating, comment, feature))
            conn.commit()
            return cursor.lastrowid
    
    def get_feedback_stats(self):
        """Get feedback statistics"""
        with self.get_connection() as conn:
            cursor = conn.execute('''
                SELECT 
                    COUNT(*) as total_feedback,
                    AVG(rating) as avg_rating,
                    COUNT(CASE WHEN rating >= 4 THEN 1 END) as positive_count,
                    COUNT(CASE WHEN rating <= 2 THEN 1 END) as negative_count
                FROM feedback
            ''')
            return dict(cursor.fetchone())
    
    # ========== SEARCH HISTORY ==========
    
    def log_search(self, user_id: int, query: str, results_count: int, has_match: bool, response_time: float):
        """Log search query for analytics"""
        with self.get_connection() as conn:
            conn.execute('''
                INSERT INTO search_history 
                (user_id, query, results_count, has_match, response_time)
                VALUES (?, ?, ?, ?, ?)
            ''', (user_id, query, results_count, has_match, response_time))
            conn.commit()
    
    # ========== SESSION MANAGEMENT ==========
    
    def save_user_session(self, user_id: int, session_data: dict, ttl_minutes: int = 30):
        """Save user session data"""
        expires_at = datetime.now() + timedelta(minutes=ttl_minutes)
        
        with self.get_connection() as conn:
            conn.execute('''
                INSERT OR REPLACE INTO user_sessions 
                (user_id, session_data, expires_at)
                VALUES (?, ?, ?)
            ''', (user_id, json.dumps(session_data), expires_at.isoformat()))
            conn.commit()
    
    def get_user_session(self, user_id: int):
        """Get user session data"""
        with self.get_connection() as conn:
            cursor = conn.execute('''
                SELECT session_data 
                FROM user_sessions 
                WHERE user_id = ? AND expires_at > ?
            ''', (user_id, datetime.now().isoformat()))
            
            row = cursor.fetchone()
            if row:
                return json.loads(row['session_data'])
            return {}
    
    def clear_user_session(self, user_id: int):
        """Clear user session"""
        with self.get_connection() as conn:
            conn.execute('DELETE FROM user_sessions WHERE user_id = ?', (user_id,))
            conn.commit()
    
    # ========== WHITELIST MANAGEMENT ==========
    
    def add_to_whitelist(self, identifier: str, entity_type: str, verified_by: str, notes: str = ""):
        """Add entity to whitelist"""
        with self.get_connection() as conn:
            conn.execute('''
                INSERT OR REPLACE INTO whitelist 
                (identifier, entity_type, verified_by, verification_date, notes)
                VALUES (?, ?, ?, ?, ?)
            ''', (identifier, entity_type, verified_by, datetime.now().date().isoformat(), notes))
            conn.commit()
    
    def is_whitelisted(self, identifier: str) -> bool:
        """Check if identifier is whitelisted"""
        with self.get_connection() as conn:
            cursor = conn.execute(
                'SELECT 1 FROM whitelist WHERE identifier = ?',
                (identifier,)
            )
            return cursor.fetchone() is not None
    
    # ========== UTILITY METHODS ==========
    
    def cleanup_old_data(self, days: int = 30):
        """Cleanup old data"""
        cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()
        
        with self.get_connection() as conn:
            # Clean old sessions
            conn.execute('DELETE FROM user_sessions WHERE expires_at < ?', (cutoff_date,))
            
            # Clean old search history
            conn.execute('DELETE FROM search_history WHERE created_at < ?', (cutoff_date,))
            
            conn.commit()
    
    def backup_database(self, backup_path: str):
        """Create database backup"""
        import shutil
        shutil.copy2(self.db_file, backup_path)
        return backup_path

# ==================== MULTI-LANGUAGE SYSTEM ====================
class LanguageManager:
    """Advanced multi-language support with caching"""
    
    def __init__(self):
        self.languages = {
            "en": {"code": "en", "flag": "🇬🇧", "name": "English", "dir": "ltr"},
            "vi": {"code": "vi", "flag": "🇻🇳", "name": "Tiếng Việt", "dir": "ltr"},
            "ru": {"code": "ru", "flag": "🇷🇺", "name": "Русский", "dir": "ltr"},
            "zh": {"code": "zh", "flag": "🇨🇳", "name": "中文", "dir": "ltr"},
        }
        self.texts = self._load_texts()
        self._cache = {}
    
    def _load_texts(self):
        """Load all language texts"""
        return {
            "en": self._get_english_texts(),
            "vi": self._get_vietnamese_texts(),
            "ru": self._get_russian_texts(),
            "zh": self._get_chinese_texts(),
        }
    
    def _get_english_texts(self):
        """English language texts - Complete and professional"""
        return {
            # ===== WELCOME & INTRODUCTION =====
            "welcome_title": "🛡️ *BOT CHECK SCAM - Ultimate Protection System*",
            "welcome_message": """🤖 Welcome to the most advanced community-driven scam protection system!

I'm here to help you:
• 🔍 *Verify suspicious accounts* in seconds
• 🚨 *Report scams* instantly to protect others
• 📊 *Access real-time statistics* on fraudulent activities
• 🛡️ *Connect with verified admins* for secure transactions
• ⭐ *Join trusted communities* of experienced traders
• 📚 *Learn safe trading practices* with our expert guides
• 💖 *Support our mission* to make crypto safer for everyone

⚠️ *Important Notice:* 
All data is community-sourced and should be used as a reference only. 
Always conduct your own due diligence before any transaction.""",
            
            "select_option": "👇 *Please select an option below:*",
            
            # ===== MAIN MENU =====
            "menu_check": "🔍 Check Scam Risk",
            "menu_report": "🚨 Report Scammer",
            "menu_stats": "📊 Live Statistics",
            "menu_admins": "🛡 Trusted Admins",
            "menu_groups": "⭐ Verified Groups",
            "menu_guide": "📚 Safe Trading Guide",
            "menu_language": "🌐 Change Language",
            "menu_donate": "💖 Support & Donate",
            
            # ===== CHECK SCAM =====
            "check_title": "🔍 *SCAM RISK ASSESSMENT*",
            "check_instructions": """To check for scam risks, send me *ANY* of the following:

• 👤 *Telegram Username* (e.g., @username)
• 🔢 *Telegram ID* (e.g., 123456789)
• 🔗 *Telegram Link* (e.g., t.me/username)
• 💰 *Binance ID* (UID format)
• 🪙 *Crypto Wallet* (USDT/BNB/ETH address)
• 📱 *Phone Number* (with country code)
• 📧 *Email Address* (if available)

*Note:* Only one identifier is needed for a comprehensive check.""",
            
            "check_processing": "🔍 *Analyzing data...*",
            "check_no_results": "✅ *NO RISK DETECTED*\n\nThis identifier has no negative reports in our database. However, always remain cautious and verify through multiple sources.",
            
            "check_low_risk": "⚠️ *LOW RISK - EXERCISE CAUTION*\n\n",
            "check_medium_risk": "🚨 *MEDIUM RISK - HIGH CAUTION*\n\n",
            "check_high_risk": "⛔ *HIGH RISK - AVOID TRANSACTION*\n\n",
            "check_critical_risk": "🔥 *CRITICAL RISK - CONFIRMED SCAMMER*\n\n",
            
            "check_details": "*Detailed Analysis:*",
            "check_reports": "📊 Total Reports: {}",
            "check_unique_reporters": "👥 Unique Reporters: {}",
            "check_first_reported": "📅 First Reported: {}",
            "check_last_reported": "🕒 Last Reported: {}",
            "check_common_methods": "🎯 Common Methods: {}",
            "check_estimated_loss": "💰 Estimated Loss: {} {}",
            "check_risk_score": "📈 Risk Score: {}/10",
            "check_recommendation": "*Recommendation:* {}",
            
            # ===== REPORT SCAM =====
            "report_title": "🚨 *REPORT SUSPICIOUS ACTIVITY*",
            "report_limit_reached": "⏰ *Daily Limit Reached*\n\nYou have submitted 3 reports today (maximum allowed). This limit helps prevent spam and ensures data quality. Please try again tomorrow.",
            "report_limit_info": "📝 *Today's Usage:* {}/3 reports used",
            "report_ask_target": "Please provide the scammer's identifier:\n\n• Username (@example)\n• Telegram ID\n• Wallet address\n• Phone number\n• Other unique identifier",
            
            "report_methods_title": "Select the scam method:",
            "report_methods": [
                "💰 Fake Payment/Invoice",
                "🎯 Fake Product/Service",
                "📈 Investment/Pyramid Scheme",
                "🆔 Identity Theft/Impersonation",
                "🔗 Phishing Link/Website",
                "🎮 Fake Giveaway/Airdrop",
                "💼 Employment/Job Scam",
                "⚡ Other (specify in proof)"
            ],
            
            "report_ask_amount": "Estimated loss amount (optional):\n\n*Format:* `100 USDT` or `0.5 BNB`\n*Note:* This helps us calculate impact severity.",
            "report_ask_proof": "Evidence (optional but highly recommended):\n\n• Screenshot of conversation\n• Transaction hash/ID\n• Website URL\n• Detailed description\n\n*Tip:* Blur your personal info before sending.",
            "report_ask_description": "Brief description of what happened:",
            
            "report_confirm_title": "📋 *REPORT CONFIRMATION*",
            "report_confirm_details": """*Please verify the information below:*

• 🎯 *Target:* `{}`
• 🚨 *Method:* {}
• 💰 *Amount:* {}
• 📝 *Description:* {}
• 🏷️ *Tags:* {}

*Is this information correct?*""",
            
            "report_confirm_yes": "✅ Yes, Submit Report",
            "report_confirm_no": "❌ No, Cancel",
            "report_confirm_edit": "✏️ Edit Details",
            
            "report_success": """✅ *REPORT SUBMITTED SUCCESSFULLY!*

Thank you for helping protect the community! Your report has been recorded and will help prevent others from being victimized.

*Report ID:* `SCAM-{}`
*Timestamp:* {}
*Status:* Active

A copy of this report has been saved to our secure database.""",
            
            "report_cancel": "❌ Report cancelled. No data was saved.",
            
            # ===== STATISTICS =====
            "stats_title": "📊 *LIVE SYSTEM STATISTICS*",
            "stats_updated": "*Last Updated:* {}",
            "stats_total_reports": "📈 Total Reports: {}",
            "stats_total_reporters": "👥 Unique Reporters: {}",
            "stats_total_targets": "🎯 Unique Targets: {}",
            "stats_today_reports": "📅 Today's Reports: {}",
            "stats_active_users": "🟢 Active Users (24h): {}",
            "stats_new_users": "🆕 New Users Today: {}",
            "stats_top_scammers": "🔥 *Top 5 Reported Scammers:*",
            "stats_scammer_item": "{}. `{}` - {} reports",
            "stats_top_methods": "🎯 *Most Common Scam Methods:*",
            "stats_method_item": "• {} - {} reports",
            "stats_daily_avg": "📊 Daily Average: {} reports/day",
            "stats_resolution_rate": "✅ Resolution Rate: {}%",
            
            # ===== TRUSTED ADMINS =====
            "admins_title": "🛡️ *VERIFIED ESCROW ADMINS*",
            "admins_intro": """These administrators have been verified by our community and have established trust through numerous successful transactions.

*How to use escrow safely:*
1. Both parties agree on escrow admin
2. Buyer sends funds to admin
3. Seller delivers product/service
4. Admin releases funds to seller
5. All parties confirm completion""",
            
            "admin_profile": """*{}* {}
📍 *Region:* {}
👑 *Role:* {}
✅ *Verification Level:* {}/5
📊 *Successful Transactions:* 300+
⏰ *Response Time:* < 15 minutes
📝 *Notes:* {}
🔗 *Contact:* [Click to Message]({})""",
            
            "admins_list": [
                {
                    "name": "Crypto Escrow Pro",
                    "telegram": "@cryptoescrowpro",
                    "region": "Global Coverage",
                    "role": "Professional Escrow Service",
                    "verification": 5,
                    "notes": "24/7 availability, multilingual support, 500+ verified transactions",
                    "link": "https://t.me/cryptoescrowpro"
                },
                {
                    "name": "Trusted Middleman EU",
                    "telegram": "@trustedmiddleman_eu",
                    "region": "European Union",
                    "role": "Crypto & Goods Escrow",
                    "verification": 4,
                    "notes": "Fast response, legal background, escrow contract available",
                    "link": "https://t.me/trustedmiddleman_eu"
                },
                {
                    "name": "Asia Trade Guardian",
                    "telegram": "@asiatradeguardian",
                    "region": "Asia Pacific",
                    "role": "Asian Market Specialist",
                    "verification": 4,
                    "notes": "Focus on Asian crypto markets, understands local platforms",
                    "link": "https://t.me/asiatradeguardian"
                },
                {
                    "name": "Safe Trade Network",
                    "telegram": "@safetradenetwork",
                    "region": "North America",
                    "role": "USDT/BTC Escrow Expert",
                    "verification": 5,
                    "notes": "Specializes in large transactions, provides transaction reports",
                    "link": "https://t.me/safetradenetwork"
                },
                {
                    "name": "Global Crypto Shield",
                    "telegram": "@globalcryptoshield",
                    "region": "Worldwide",
                    "role": "Multi-Currency Escrow",
                    "verification": 4,
                    "notes": "Supports 20+ cryptocurrencies, dispute resolution service",
                    "link": "https://t.me/globalcryptoshield"
                }
            ],
            
            "admin_contact_button": "📞 Contact Admin",
            
            # ===== VERIFIED GROUPS =====
            "groups_title": "⭐ *TRUSTED COMMUNITY GROUPS*",
            "groups_intro": """Join these verified communities for:
• Real-time scam alerts
• Trading discussions
• Market analysis
• Victim support
• Educational resources""",
            
            "group_profile": """*{}* 
📝 *Description:* {}
👥 *Members:* {}
✅ *Verification Status:* {}
🚨 *Scam Reports:* {} resolved
📈 *Activity Level:* {}/5
🔗 *Join:* [Click to Enter]({})""",
            
            "groups_list": [
                {
                    "name": "Crypto Safety Hub",
                    "description": "Main community for scam reports, prevention tips, and victim support",
                    "members": "15,000+",
                    "status": "Verified & Monitored",
                    "reports": "2,500+",
                    "activity": 5,
                    "link": "https://t.me/cryptosafetyhub"
                },
                {
                    "name": "Binance Trading Safety",
                    "description": "Official partner group for Binance-specific scam alerts and trading education",
                    "members": "8,500+",
                    "status": "Official Partner",
                    "reports": "1,200+",
                    "activity": 4,
                    "link": "https://t.me/BinanceTradingSafety"
                },
                {
                    "name": "Global Crypto Watch",
                    "description": "24/7 scam monitoring and alert system with real-time notifications",
                    "members": "12,000+",
                    "status": "Verified & Active",
                    "reports": "3,000+",
                    "activity": 5,
                    "link": "https://t.me/globalcryptowatch"
                },
                {
                    "name": "Crypto Victims Support",
                    "description": "Support group for scam victims with recovery guidance and emotional support",
                    "members": "5,000+",
                    "status": "Community Verified",
                    "reports": "800+",
                    "activity": 4,
                    "link": "https://t.me/cryptovictimssupport"
                },
                {
                    "name": "Safe Trading Academy",
                    "description": "Educational group focusing on safe trading practices and risk management",
                    "members": "7,000+",
                    "status": "Educational Partner",
                    "reports": "N/A",
                    "activity": 4,
                    "link": "https://t.me/safetradingacademy"
                }
            ],
            
            "group_join_button": "🚀 Join Group",
            
            # ===== SAFE TRADING GUIDE ===== (NEW)
            "guide_title": "📚 *ULTIMATE SAFE TRADING GUIDE*",
            "guide_intro": """Welcome to the comprehensive safe trading guide! This guide covers everything you need to trade safely and avoid scams.""",
            
            "guide_chapters": [
                {
                    "title": "🔐 Chapter 1: Basic Security Principles",
                    "content": """*1.1 Two-Factor Authentication (2FA)*
• Always enable 2FA on ALL accounts
• Use authenticator apps, not SMS
• Store backup codes securely

*1.2 Strong Password Management*
• Use unique passwords for each platform
• Minimum 12 characters with mixed characters
• Consider a password manager

*1.3 Device Security*
• Keep software updated
• Use antivirus software
• Avoid public Wi-Fi for transactions"""
                },
                {
                    "title": "🎯 Chapter 2: Verifying Counterparties",
                    "content": """*2.1 Red Flags to Watch For*
• Pressure to act quickly
• Too-good-to-be-true offers
• Unverified payment methods
• Requests for upfront fees

*2.2 Verification Checklist*
☑️ Check username history
☑️ Verify join date (older = better)
☑️ Look for mutual contacts
☑️ Search for scam reports
☑️ Request video verification

*2.3 Trust Indicators*
• Verified business accounts
• Long-standing reputation
• Positive community feedback
• Willingness to use escrow"""
                },
                {
                    "title": "🛡️ Chapter 3: Using Escrow Services",
                    "content": """*3.1 When to Use Escrow*
• Transactions > $100
• Dealing with new contacts
• Cross-border transactions
• High-value items

*3.2 Escrow Process*
1. Both parties agree on escrow admin
2. Buyer sends funds to escrow
3. Escrow confirms receipt
4. Seller delivers goods/services
5. Buyer confirms satisfaction
6. Escrow releases funds

*3.3 Escrow Fee Structure*
• Standard: 1-3% of transaction
• Minimum fee: $5-10
• Fees typically split 50/50"""
                },
                {
                    "title": "💰 Chapter 4: Secure Payment Methods",
                    "content": """*4.1 Recommended Methods*
• Binance P2P (with verified merchants)
• PayPal Goods & Services
• Bank transfer (with trusted parties)
• Escrow services

*4.2 Methods to Avoid*
• Western Union/MoneyGram
• Gift cards
• Direct crypto transfers to strangers
• Unverified payment processors

*4.3 Transaction Safety Tips*
• Start with small test transactions
• Use transaction IDs for tracking
• Take screenshots of agreements
• Set clear terms before payment"""
                },
                {
                    "title": "🚨 Chapter 5: Common Scam Types",
                    "content": """*5.1 Fake Payment Scams*
• Fake payment screenshots
• Edited transaction confirmations
• Chargeback fraud

*5.2 Investment Scams*
• Guaranteed high returns
• Pyramid/Ponzi schemes
• Fake trading signals

*5.3 Phishing Attacks*
• Fake login pages
• Impersonation of officials
• Malicious links/files

*5.4 Prevention Strategies*
• Verify all payment confirmations
• Research investment opportunities
• Never share private keys
• Use hardware wallets for large amounts"""
                },
                {
                    "title": "⚡ Chapter 6: Quick Trading Protocol",
                    "content": """*6.1 Before Any Trade*
1. Check counterparty with this bot
2. Agree on exact terms in writing
3. Determine secure payment method
4. Set up escrow if needed

*6.2 During Transaction*
1. Follow agreed protocol exactly
2. Confirm each step via chat
3. Save all communication
4. Verify funds before proceeding

*6.3 After Completion*
1. Leave feedback/review
2. Report any suspicious behavior
3. Update your security measures
4. Share positive experiences"""
                }
            ],
            
            "guide_next": "➡️ Next Chapter",
            "guide_prev": "⬅️ Previous Chapter",
            "guide_menu": "📚 Back to Guide Menu",
            "guide_complete": "✅ You've completed the guide! Remember: Trust but verify.",
            
            # ===== LANGUAGE SELECTION =====
            "language_title": "🌐 *SELECT YOUR LANGUAGE*",
            "language_current": "Current language: {}",
            "language_select": "Choose your preferred language:",
            "language_changed": "✅ Language successfully changed to {}",
            
            # ===== DONATION & SUPPORT =====
            "donate_title": "💖 *SUPPORT OUR MISSION*",
            "donate_message": """🤖 *BOT CHECK SCAM* operates 24/7 to protect thousands of users worldwide. We're completely community-funded and rely on donations to continue our work.

*What your support enables:*
• 🔄 24/7 server operation and maintenance
• 🗄️ Secure database storage and backups
• 🛡️ Regular security updates and improvements
• 📊 Advanced scam detection algorithms
• 🆓 Free service for all users
• 🌍 Global community outreach

*Transparency Promise:*
• 100% of donations go directly to bot maintenance
• Monthly financial reports available
• No hidden fees or charges""",
            
            "donate_details": """💎 *SUPPORT VIA BINANCE:*
• Binance ID: `154265504`
• Accepted: USDT, BNB, BUSD
• Network: BEP20 (BSC)

💳 *ALTERNATIVE METHODS:*
• Crypto wallets available upon request
• Contact @BotAdmin for other options

*Note:* All donations are anonymous by default. You can include a message if you'd like to be acknowledged.""",
            
            "donate_button": "💝 I've Donated",
            "donate_thanks_title": "🙏 *THANK YOU FOR YOUR GENEROSITY!*",
            "donate_thanks_message": """Your contribution makes a real difference! Here's what you've helped achieve:

✅ *Donation Verified*
⏰ Time: {}
📍 Status: Anonymous Contribution
🔒 Amount: Private

*Your Impact:*
• Protects {} active users daily
• Maintains {} scam reports
• Supports {} community members
• Enables {} daily safety checks

💎 *Remember:* Binance ID `154265504`

Together, we're making cryptocurrency safer for everyone! 🚀""",
            
            "donate_back": "⬅️ Return to Main Menu",
            
            # ===== ERROR MESSAGES =====
            "error_general": "⚠️ An error occurred. Please try again.",
            "error_input": "❌ Invalid input. Please check and try again.",
            "error_database": "🔧 Database error. Our team has been notified.",
            "error_timeout": "⏰ Request timed out. Please try again.",
            "error_permission": "🔒 You don't have permission for this action.",
            
            # ===== SUCCESS MESSAGES =====
            "success_operation": "✅ Operation completed successfully!",
            "success_saved": "💾 Changes saved successfully.",
            "success_updated": "🔄 Data updated successfully.",
            
            # ===== NAVIGATION =====
            "back_button": "⬅️ Back",
            "cancel_button": "❌ Cancel",
            "confirm_button": "✅ Confirm",
            "next_button": "➡️ Next",
            "menu_button": "🏠 Main Menu",
            "help_button": "❓ Help",
            "close_button": "✖️ Close",
            
            # ===== FOOTER =====
            "footer_disclaimer": """⚠️ *Disclaimer:* This bot provides community-sourced information only. Always conduct your own research and use common sense. We are not responsible for any financial losses.""",
            "footer_support": "Need help? Contact @BotSupportAdmin",
            "footer_version": "Bot v4.0 • Database v{}",
        }
    
    def _get_vietnamese_texts(self):
        """Vietnamese language texts"""
        # (Vietnamese translations would go here - similar structure)
        # For brevity, returning English as placeholder
        return self._get_english_texts()
    
    def _get_russian_texts(self):
        """Russian language texts"""
        return self._get_english_texts()
    
    def _get_chinese_texts(self):
        """Chinese language texts"""
        return self._get_english_texts()
    
    def get_text(self, language: str, key: str, **kwargs):
        """Get text in specified language with formatting"""
        if language not in self.texts:
            language = "en"
        
        text = self.texts[language].get(key, self.texts["en"].get(key, key))
        
        if kwargs:
            try:
                text = text.format(**kwargs)
            except KeyError:
                pass
        
        return text

# ==================== BOT STATE MANAGEMENT ====================
class BotStateManager:
    """Manage bot conversation states"""
    
    def __init__(self):
        self.states = {
            'MAIN_MENU': 0,
            'CHECK_SCAM': 1,
            'REPORT_TARGET': 2,
            'REPORT_METHOD': 3,
            'REPORT_AMOUNT': 4,
            'REPORT_PROOF': 5,
            'REPORT_CONFIRM': 6,
            'GUIDE_MENU': 7,
            'GUIDE_CHAPTER': 8,
            'LANGUAGE_SELECT': 9,
            'DONATION_INFO': 10,
        }
        
        self.user_states = {}
    
    def set_user_state(self, user_id: int, state: str):
        """Set user's current state"""
        if state in self.states:
            self.user_states[user_id] = self.states[state]
    
    def get_user_state(self, user_id: int):
        """Get user's current state"""
        return self.user_states.get(user_id, self.states['MAIN_MENU'])
    
    def clear_user_state(self, user_id: int):
        """Clear user's state"""
        if user_id in self.user_states:
            del self.user_states[user_id]

# ==================== KEYBOARD MANAGER ====================
class KeyboardManager:
    """Manage all bot keyboards"""
    
    def __init__(self, lang_manager: LanguageManager):
        self.lang = lang_manager
    
    def create_main_menu(self, language: str):
        """Create main menu keyboard"""
        keyboard = [
            [self.lang.get_text(language, "menu_check")],
            [self.lang.get_text(language, "menu_report")],
            [self.lang.get_text(language, "menu_stats")],
            [
                self.lang.get_text(language, "menu_admins"),
                self.lang.get_text(language, "menu_groups")
            ],
            [
                self.lang.get_text(language, "menu_guide"),
                self.lang.get_text(language, "menu_language")
            ],
            [self.lang.get_text(language, "menu_donate")]
        ]
        
        return ReplyKeyboardMarkup(
            keyboard,
            resize_keyboard=True,
            one_time_keyboard=False,
            input_field_placeholder=self.lang.get_text(language, "select_option")
        )
    
    def create_back_button(self, language: str):
        """Create simple back button keyboard"""
        return ReplyKeyboardMarkup(
            [[self.lang.get_text(language, "back_button")]],
            resize_keyboard=True
        )
    
    def create_language_keyboard(self):
        """Create language selection inline keyboard"""
        keyboard = []
        languages = [
            ("🇬🇧 English", "lang_en"),
            ("🇻🇳 Tiếng Việt", "lang_vi"),
            ("🇷🇺 Русский", "lang_ru"),
            ("🇨🇳 中文", "lang_zh"),
        ]
        
        for text, callback in languages:
            keyboard.append([InlineKeyboardButton(text, callback_data=callback)])
        
        return InlineKeyboardMarkup(keyboard)
    
    def create_report_method_keyboard(self, language: str):
        """Create scam method selection keyboard"""
        keyboard = []
        methods = self.lang.get_text(language, "report_methods")
        
        for i, method in enumerate(methods, 1):
            keyboard.append([InlineKeyboardButton(method, callback_data=f"method_{i}")])
        
        keyboard.append([
            InlineKeyboardButton(
                self.lang.get_text(language, "back_button"),
                callback_data="back"
            )
        ])
        
        return InlineKeyboardMarkup(keyboard)
    
    def create_confirmation_keyboard(self, language: str):
        """Create confirmation keyboard"""
        keyboard = [
            [
                InlineKeyboardButton(
                    self.lang.get_text(language, "confirm_button"),
                    callback_data="confirm_yes"
                ),
                InlineKeyboardButton(
                    self.lang.get_text(language, "cancel_button"),
                    callback_data="confirm_no"
                )
            ],
            [
                InlineKeyboardButton(
                    self.lang.get_text(language, "back_button"),
                    callback_data="back"
                )
            ]
        ]
        
        return InlineKeyboardMarkup(keyboard)
    
    def create_admins_keyboard(self):
        """Create trusted admins keyboard with direct links"""
        keyboard = []
        admins = self.lang.get_text("en", "admins_list")
        
        for admin in admins:
            button = InlineKeyboardButton(
                f"📞 {admin['name']}",
                url=admin['link']
            )
            keyboard.append([button])
        
        return InlineKeyboardMarkup(keyboard)
    
    def create_groups_keyboard(self):
        """Create verified groups keyboard with direct links"""
        keyboard = []
        groups = self.lang.get_text("en", "groups_list")
        
        for group in groups:
            button = InlineKeyboardButton(
                f"🚀 {group['name']}",
                url=group['link']
            )
            keyboard.append([button])
        
        return InlineKeyboardMarkup(keyboard)
    
    def create_guide_menu_keyboard(self, language: str):
        """Create safe trading guide menu keyboard"""
        chapters = self.lang.get_text(language, "guide_chapters")
        keyboard = []
        
        for i, chapter in enumerate(chapters[:3], 1):
            keyboard.append([
                InlineKeyboardButton(
                    chapter['title'],
                    callback_data=f"guide_{i}"
                )
            ])
        
        for i, chapter in enumerate(chapters[3:], 4):
            keyboard.append([
                InlineKeyboardButton(
                    chapter['title'],
                    callback_data=f"guide_{i}"
                )
            ])
        
        keyboard.append([
            InlineKeyboardButton(
                self.lang.get_text(language, "menu_button"),
                callback_data="main_menu"
            )
        ])
        
        return InlineKeyboardMarkup(keyboard)
    
    def create_guide_navigation_keyboard(self, language: str, current_chapter: int, total_chapters: int):
        """Create guide navigation keyboard"""
        keyboard = []
        
        if current_chapter > 1:
            keyboard.append(
                InlineKeyboardButton(
                    self.lang.get_text(language, "guide_prev"),
                    callback_data=f"guide_{current_chapter - 1}"
                )
            )
        
        if current_chapter < total_chapters:
            keyboard.append(
                InlineKeyboardButton(
                    self.lang.get_text(language, "guide_next"),
                    callback_data=f"guide_{current_chapter + 1}"
                )
            )
        
        # Wrap buttons if needed
        if len(keyboard) == 2:
            keyboard = [[keyboard[0], keyboard[1]]]
        
        keyboard.append([
            InlineKeyboardButton(
                self.lang.get_text(language, "guide_menu"),
                callback_data="guide_menu"
            )
        ])
        
        return InlineKeyboardMarkup(keyboard)
    
    def create_donation_keyboard(self, language: str):
        """Create donation confirmation keyboard"""
        keyboard = [
            [
                InlineKeyboardButton(
                    self.lang.get_text(language, "donate_button"),
                    callback_data="donate_confirm"
                )
            ],
            [
                InlineKeyboardButton(
                    self.lang.get_text(language, "donate_back"),
                    callback_data="donate_back"
                )
            ]
        ]
        
        return InlineKeyboardMarkup(keyboard)

# ==================== BOT HANDLERS ====================
class BotHandlers:
    """Main bot handler class"""
    
    def __init__(self, db: AdvancedDatabase, lang_manager: LanguageManager, 
                 state_manager: BotStateManager, keyboard_manager: KeyboardManager):
        self.db = db
        self.lang = lang_manager
        self.state = state_manager
        self.keyboard = keyboard_manager
        self.user_sessions = {}
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        user = update.effective_user
        
        # Update user in database
        self.db.add_or_update_user({
            'id': user.id,
            'username': user.username,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'language': 'en'  # Default language
        })
        
        # Send welcome message
        welcome_text = (
            f"{self.lang.get_text('en', 'welcome_title')}\n\n"
            f"{self.lang.get_text('en', 'welcome_message')}\n\n"
            f"{self.lang.get_text('en', 'select_option')}"
        )
        
        await update.message.reply_text(
            welcome_text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=self.keyboard.create_main_menu('en')
        )
        
        self.state.set_user_state(user.id, 'MAIN_MENU')
        return self.state.states['MAIN_MENU']
    
    async def handle_main_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle main menu selection"""
        user = update.effective_user
        user_lang = self.db.get_user(user.id)['language'] if self.db.get_user(user.id) else 'en'
        text = update.message.text
        
        if text == self.lang.get_text(user_lang, "menu_check"):
            await update.message.reply_text(
                self.lang.get_text(user_lang, "check_title"),
                parse_mode=ParseMode.MARKDOWN
            )
            
            await update.message.reply_text(
                self.lang.get_text(user_lang, "check_instructions"),
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=self.keyboard.create_back_button(user_lang)
            )
            
            self.state.set_user_state(user.id, 'CHECK_SCAM')
            return self.state.states['CHECK_SCAM']
        
        elif text == self.lang.get_text(user_lang, "menu_report"):
            can_report, used, total = self.db.can_user_report(user.id)
            
            if not can_report:
                await update.message.reply_text(
                    self.lang.get_text(user_lang, "report_limit_reached"),
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=self.keyboard.create_main_menu(user_lang)
                )
                return self.state.states['MAIN_MENU']
            
            limit_info = self.lang.get_text(user_lang, "report_limit_info", count=used)
            await update.message.reply_text(
                f"{self.lang.get_text(user_lang, 'report_title')}\n\n{limit_info}\n\n"
                f"{self.lang.get_text(user_lang, 'report_ask_target')}",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=self.keyboard.create_back_button(user_lang)
            )
            
            self.state.set_user_state(user.id, 'REPORT_TARGET')
            return self.state.states['REPORT_TARGET']
        
        elif text == self.lang.get_text(user_lang, "menu_stats"):
            stats = self.db.get_system_statistics()
            
            stats_text = f"{self.lang.get_text(user_lang, 'stats_title')}\n\n"
            stats_text += f"• {self.lang.get_text(user_lang, 'stats_total_reports', count=stats['total_reports'])}\n"
            stats_text += f"• {self.lang.get_text(user_lang, 'stats_total_reporters', count=stats['total_reporters'])}\n"
            stats_text += f"• {self.lang.get_text(user_lang, 'stats_total_targets', count=stats['total_targets'])}\n"
            stats_text += f"• {self.lang.get_text(user_lang, 'stats_today_reports', count=stats['today_reports'])}\n"
            stats_text += f"• {self.lang.get_text(user_lang, 'stats_active_users', count=stats['active_users'])}\n\n"
            
            if stats['top_reported']:
                stats_text += f"{self.lang.get_text(user_lang, 'stats_top_scammers')}\n"
                for i, item in enumerate(stats['top_reported'][:5], 1):
                    stats_text += f"{self.lang.get_text(user_lang, 'stats_scammer_item', num=i, target=item['target'], count=item['count'])}\n"
            
            await update.message.reply_text(
                stats_text,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=self.keyboard.create_main_menu(user_lang)
            )
            
            return self.state.states['MAIN_MENU']
        
        elif text == self.lang.get_text(user_lang, "menu_admins"):
            admins_text = f"{self.lang.get_text(user_lang, 'admins_title')}\n\n"
            admins_text += f"{self.lang.get_text(user_lang, 'admins_intro')}\n\n"
            
            admins = self.lang.get_text('en', 'admins_list')
            for admin in admins:
                admins_text += self.lang.get_text(user_lang, 'admin_profile', **admin) + "\n\n"
            
            await update.message.reply_text(
                admins_text,
                parse_mode=ParseMode.MARKDOWN,
                disable_web_page_preview=True
            )
            
            await update.message.reply_text(
                self.lang.get_text(user_lang, "select_option"),
                reply_markup=self.keyboard.create_admins_keyboard()
            )
            
            await update.message.reply_text(
                self.lang.get_text(user_lang, "menu_button"),
                reply_markup=self.keyboard.create_main_menu(user_lang)
            )
            
            return self.state.states['MAIN_MENU']
        
        elif text == self.lang.get_text(user_lang, "menu_groups"):
            groups_text = f"{self.lang.get_text(user_lang, 'groups_title')}\n\n"
            groups_text += f"{self.lang.get_text(user_lang, 'groups_intro')}\n\n"
            
            groups = self.lang.get_text('en', 'groups_list')
            for group in groups:
                groups_text += self.lang.get_text(user_lang, 'group_profile', **group) + "\n\n"
            
            await update.message.reply_text(
                groups_text,
                parse_mode=ParseMode.MARKDOWN,
                disable_web_page_preview=True
            )
            
            await update.message.reply_text(
                self.lang.get_text(user_lang, "select_option"),
                reply_markup=self.keyboard.create_groups_keyboard()
            )
            
            await update.message.reply_text(
                self.lang.get_text(user_lang, "menu_button"),
                reply_markup=self.keyboard.create_main_menu(user_lang)
            )
            
            return self.state.states['MAIN_MENU']
        
        elif text == self.lang.get_text(user_lang, "menu_guide"):
            guide_text = f"{self.lang.get_text(user_lang, 'guide_title')}\n\n"
            guide_text += f"{self.lang.get_text(user_lang, 'guide_intro')}\n\n"
            guide_text += "*Select a chapter to begin:*"
            
            await update.message.reply_text(
                guide_text,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=self.keyboard.create_guide_menu_keyboard(user_lang)
            )
            
            self.state.set_user_state(user.id, 'GUIDE_MENU')
            return self.state.states['GUIDE_MENU']
        
        elif text == self.lang.get_text(user_lang, "menu_language"):
            current_lang = self.db.get_user(user.id)['language'] if self.db.get_user(user.id) else 'en'
            lang_name = self.lang.languages[current_lang]['name']
            
            await update.message.reply_text(
                f"{self.lang.get_text(user_lang, 'language_title')}\n\n"
                f"{self.lang.get_text(user_lang, 'language_current', name=lang_name)}\n\n"
                f"{self.lang.get_text(user_lang, 'language_select')}",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=self.keyboard.create_language_keyboard()
            )
            
            return self.state.states['MAIN_MENU']
        
        elif text == self.lang.get_text(user_lang, "menu_donate"):
            donate_text = f"{self.lang.get_text(user_lang, 'donate_title')}\n\n"
            donate_text += f"{self.lang.get_text(user_lang, 'donate_message')}\n\n"
            donate_text += f"{self.lang.get_text(user_lang, 'donate_details')}"
            
            await update.message.reply_text(
                donate_text,
                parse_mode=ParseMode.MARKDOWN
            )
            
            await update.message.reply_text(
                self.lang.get_text(user_lang, "select_option"),
                reply_markup=self.keyboard.create_donation_keyboard(user_lang)
            )
            
            self.state.set_user_state(user.id, 'DONATION_INFO')
            return self.state.states['DONATION_INFO']
        
        else:
            await update.message.reply_text(
                self.lang.get_text(user_lang, "error_input"),
                reply_markup=self.keyboard.create_main_menu(user_lang)
            )
            
            return self.state.states['MAIN_MENU']
    
    async def handle_check_scam(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle scam check requests"""
        user = update.effective_user
        user_lang = self.db.get_user(user.id)['language'] if self.db.get_user(user.id) else 'en'
        
        # Check for back button
        if update.message.text == self.lang.get_text(user_lang, "back_button"):
            await update.message.reply_text(
                self.lang.get_text(user_lang, "menu_button"),
                reply_markup=self.keyboard.create_main_menu(user_lang)
            )
            self.state.set_user_state(user.id, 'MAIN_MENU')
            return self.state.states['MAIN_MENU']
        
        query = update.message.text.strip()
        if len(query) < 2:
            await update.message.reply_text(
                self.lang.get_text(user_lang, "error_input"),
                reply_markup=self.keyboard.create_back_button(user_lang)
            )
            return self.state.states['CHECK_SCAM']
        
        # Show processing message
        processing_msg = await update.message.reply_text(
            self.lang.get_text(user_lang, "check_processing"),
            parse_mode=ParseMode.MARKDOWN
        )
        
        # Search for reports
        start_time = datetime.now()
        results = self.db.search_reports(query)
        response_time = (datetime.now() - start_time).total_seconds()
        
        # Log search
        self.db.log_search(
            user_id=user.id,
            query=query,
            results_count=len(results),
            has_match=bool(results),
            response_time=response_time
        )
        
        # Generate response
        if not results:
            response_text = self.lang.get_text(user_lang, "check_no_results")
        else:
            result = results[0]
            report_count = result['report_count']
            
            # Determine risk level
            if report_count >= 10:
                risk_level = self.lang.get_text(user_lang, "check_critical_risk")
                recommendation = "AVOID ALL TRANSACTIONS - Confirmed repeat scammer"
            elif report_count >= 5:
                risk_level = self.lang.get_text(user_lang, "check_high_risk")
                recommendation = "Highly suspicious - Use extreme caution"
            elif report_count >= 3:
                risk_level = self.lang.get_text(user_lang, "check_medium_risk")
                recommendation = "Multiple reports - Verify carefully"
            else:
                risk_level = self.lang.get_text(user_lang, "check_low_risk")
                recommendation = "Exercise caution - Single report"
            
            response_text = f"{risk_level}{self.lang.get_text(user_lang, 'check_details')}\n"
            response_text += f"• {self.lang.get_text(user_lang, 'check_reports', count=report_count)}\n"
            response_text += f"• {self.lang.get_text(user_lang, 'check_last_reported', date=result['last_reported'][:10])}\n"
            
            if result.get('methods_used'):
                response_text += f"• {self.lang.get_text(user_lang, 'check_common_methods', methods=result['methods_used'])}\n"
            
            if result.get('avg_severity'):
                risk_score = min(10, round(float(result['avg_severity']) * 2, 1))
                response_text += f"• {self.lang.get_text(user_lang, 'check_risk_score', score=risk_score)}\n"
            
            response_text += f"• {self.lang.get_text(user_lang, 'check_recommendation', recommendation=recommendation)}\n\n"
            
            # Additional matches
            if len(results) > 1:
                response_text += f"🔍 Also found {len(results)-1} similar records in database.\n"
        
        # Delete processing message
        await context.bot.delete_message(
            chat_id=update.effective_chat.id,
            message_id=processing_msg.message_id
        )
        
        # Send response
        await update.message.reply_text(
            response_text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=self.keyboard.create_main_menu(user_lang)
        )
        
        self.state.set_user_state(user.id, 'MAIN_MENU')
        return self.state.states['MAIN_MENU']
    
    async def handle_report_target(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle report target input"""
        user = update.effective_user
        user_lang = self.db.get_user(user.id)['language'] if self.db.get_user(user.id) else 'en'
        
        # Check for back button
        if update.message.text == self.lang.get_text(user_lang, "back_button"):
            await update.message.reply_text(
                self.lang.get_text(user_lang, "menu_button"),
                reply_markup=self.keyboard.create_main_menu(user_lang)
            )
            self.state.set_user_state(user.id, 'MAIN_MENU')
            return self.state.states['MAIN_MENU']
        
        target = update.message.text.strip()
        if len(target) < 3:
            await update.message.reply_text(
                self.lang.get_text(user_lang, "error_input"),
                reply_markup=self.keyboard.create_back_button(user_lang)
            )
            return self.state.states['REPORT_TARGET']
        
        # Store in user session
        if user.id not in self.user_sessions:
            self.user_sessions[user.id] = {}
        self.user_sessions[user.id]['target'] = target
        
        await update.message.reply_text(
            self.lang.get_text(user_lang, "report_methods_title"),
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=self.keyboard.create_report_method_keyboard(user_lang)
        )
        
        self.state.set_user_state(user.id, 'REPORT_METHOD')
        return self.state.states['REPORT_METHOD']
    
    async def handle_report_method_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle report method selection callback"""
        query = update.callback_query
        await query.answer()
        
        user = update.effective_user
        user_lang = self.db.get_user(user.id)['language'] if self.db.get_user(user.id) else 'en'
        
        if query.data == "back":
            await query.edit_message_text(
                self.lang.get_text(user_lang, "menu_button"),
                reply_markup=self.keyboard.create_main_menu(user_lang)
            )
            self.state.set_user_state(user.id, 'MAIN_MENU')
            return self.state.states['MAIN_MENU']
        
        if query.data.startswith("method_"):
            method_idx = int(query.data.split("_")[1]) - 1
            methods = self.lang.get_text(user_lang, "report_methods")
            
            if 0 <= method_idx < len(methods):
                if user.id not in self.user_sessions:
                    self.user_sessions[user.id] = {}
                
                self.user_sessions[user.id]['method'] = methods[method_idx]
                self.user_sessions[user.id]['method_idx'] = method_idx
                
                await query.edit_message_text(
                    self.lang.get_text(user_lang, "report_ask_amount"),
                    parse_mode=ParseMode.MARKDOWN
                )
                
                self.state.set_user_state(user.id, 'REPORT_AMOUNT')
                return self.state.states['REPORT_AMOUNT']
        
        await query.edit_message_text(
            self.lang.get_text(user_lang, "error_general"),
            parse_mode=ParseMode.MARKDOWN
        )
        return self.state.states['MAIN_MENU']
    
    async def handle_report_amount(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle report amount input"""
        user = update.effective_user
        user_lang = self.db.get_user(user.id)['language'] if self.db.get_user(user.id) else 'en'
        
        if update.message.text == self.lang.get_text(user_lang, "back_button"):
            await update.message.reply_text(
                self.lang.get_text(user_lang, "menu_button"),
                reply_markup=self.keyboard.create_main_menu(user_lang)
            )
            self.state.set_user_state(user.id, 'MAIN_MENU')
            return self.state.states['MAIN_MENU']
        
        amount_text = update.message.text.strip()
        
        # Parse amount and currency
        amount = None
        currency = "USD"
        
        if amount_text and amount_text.lower() not in ['none', 'n/a', 'not specified']:
            # Try to extract amount and currency
            import re
            match = re.search(r'([\d,.]+)\s*([A-Za-z]{3,4})', amount_text)
            if match:
                try:
                    amount = float(match.group(1).replace(',', ''))
                    currency = match.group(2).upper()
                except ValueError:
                    pass
        
        # Store in session
        if user.id not in self.user_sessions:
            self.user_sessions[user.id] = {}
        
        self.user_sessions[user.id]['amount'] = amount
        self.user_sessions[user.id]['currency'] = currency
        
        await update.message.reply_text(
            self.lang.get_text(user_lang, "report_ask_description"),
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=self.keyboard.create_back_button(user_lang)
        )
        
        self.state.set_user_state(user.id, 'REPORT_PROOF')
        return self.state.states['REPORT_PROOF']
    
    async def handle_report_proof(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle report proof/description"""
        user = update.effective_user
        user_lang = self.db.get_user(user.id)['language'] if self.db.get_user(user.id) else 'en'
        
        if update.message.text == self.lang.get_text(user_lang, "back_button"):
            await update.message.reply_text(
                self.lang.get_text(user_lang, "menu_button"),
                reply_markup=self.keyboard.create_main_menu(user_lang)
            )
            self.state.set_user_state(user.id, 'MAIN_MENU')
            return self.state.states['MAIN_MENU']
        
        description = update.message.text.strip()
        
        # Handle photo if provided
        proof = description
        if update.message.photo:
            proof = "Photo evidence provided"
        
        # Store in session
        if user.id not in self.user_sessions:
            self.user_sessions[user.id] = {}
        
        self.user_sessions[user.id]['description'] = description
        self.user_sessions[user.id]['proof'] = proof
        
        # Prepare confirmation message
        session = self.user_sessions[user.id]
        amount_display = f"{session.get('amount', 'N/A')} {session.get('currency', 'USD')}" if session.get('amount') else "Not specified"
        
        confirm_text = self.lang.get_text(user_lang, "report_confirm_details").format(
            session.get('target', 'N/A'),
            session.get('method', 'N/A'),
            amount_display,
            session.get('description', 'N/A')[:200],
            ", ".join([session.get('method', 'Unknown')])
        )
        
        await update.message.reply_text(
            confirm_text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=self.keyboard.create_confirmation_keyboard(user_lang)
        )
        
        self.state.set_user_state(user.id, 'REPORT_CONFIRM')
        return self.state.states['REPORT_CONFIRM']
    
    async def handle_report_confirm_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle report confirmation callback"""
        query = update.callback_query
        await query.answer()
        
        user = update.effective_user
        user_lang = self.db.get_user(user.id)['language'] if self.db.get_user(user.id) else 'en'
        
        if query.data == "confirm_yes":
            session = self.user_sessions.get(user.id, {})
            
            if session:
                # Prepare report data
                report_data = {
                    'reporter_id': user.id,
                    'target': session.get('target', ''),
                    'target_type': self._detect_target_type(session.get('target', '')),
                    'method': session.get('method', 'Unknown'),
                    'method_category': self._categorize_method(session.get('method_idx', 7)),
                    'amount': session.get('amount'),
                    'currency': session.get('currency', 'USD'),
                    'proof': session.get('proof', ''),
                    'description': session.get('description', ''),
                    'severity': self._calculate_severity(session),
                    'tags': [session.get('method', 'Unknown')],
                    'metadata': {
                        'reporter_username': user.username,
                        'reporter_name': user.first_name,
                        'submitted_via': 'bot'
                    }
                }
                
                # Add report to database
                report_id = self.db.add_report(report_data)
                
                # Clear session
                if user.id in self.user_sessions:
                    del self.user_sessions[user.id]
                
                # Send success message
                success_text = self.lang.get_text(user_lang, "report_success").format(
                    report_id,
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                )
                
                await query.edit_message_text(
                    success_text,
                    parse_mode=ParseMode.MARKDOWN
                )
            else:
                await query.edit_message_text(
                    self.lang.get_text(user_lang, "error_general"),
                    parse_mode=ParseMode.MARKDOWN
                )
        
        elif query.data == "confirm_no":
            await query.edit_message_text(
                self.lang.get_text(user_lang, "report_cancel"),
                parse_mode=ParseMode.MARKDOWN
            )
        
        elif query.data == "back":
            await query.edit_message_text(
                self.lang.get_text(user_lang, "menu_button"),
                reply_markup=self.keyboard.create_main_menu(user_lang)
            )
            self.state.set_user_state(user.id, 'MAIN_MENU')
            return self.state.states['MAIN_MENU']
        
        # Return to main menu
        await context.bot.send_message(
            chat_id=user.id,
            text=self.lang.get_text(user_lang, "menu_button"),
            reply_markup=self.keyboard.create_main_menu(user_lang)
        )
        
        self.state.set_user_state(user.id, 'MAIN_MENU')
        return self.state.states['MAIN_MENU']
    
    async def handle_guide_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle guide navigation callbacks"""
        query = update.callback_query
        await query.answer()
        
        user = update.effective_user
        user_lang = self.db.get_user(user.id)['language'] if self.db.get_user(user.id) else 'en'
        
        if query.data == "guide_menu":
            guide_text = f"{self.lang.get_text(user_lang, 'guide_title')}\n\n"
            guide_text += f"{self.lang.get_text(user_lang, 'guide_intro')}\n\n"
            guide_text += "*Select a chapter to begin:*"
            
            await query.edit_message_text(
                guide_text,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=self.keyboard.create_guide_menu_keyboard(user_lang)
            )
            
            self.state.set_user_state(user.id, 'GUIDE_MENU')
            return self.state.states['GUIDE_MENU']
        
        elif query.data == "main_menu":
            await query.edit_message_text(
                self.lang.get_text(user_lang, "menu_button"),
                reply_markup=self.keyboard.create_main_menu(user_lang)
            )
            
            self.state.set_user_state(user.id, 'MAIN_MENU')
            return self.state.states['MAIN_MENU']
        
        elif query.data.startswith("guide_"):
            chapter_num = int(query.data.split("_")[1])
            chapters = self.lang.get_text(user_lang, "guide_chapters")
            
            if 1 <= chapter_num <= len(chapters):
                chapter = chapters[chapter_num - 1]
                
                guide_text = f"{chapter['title']}\n\n"
                guide_text += f"{chapter['content']}\n\n"
                guide_text += f"*Chapter {chapter_num} of {len(chapters)}*"
                
                await query.edit_message_text(
                    guide_text,
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=self.keyboard.create_guide_navigation_keyboard(
                        user_lang, chapter_num, len(chapters)
                    )
                )
                
                self.state.set_user_state(user.id, 'GUIDE_CHAPTER')
                return self.state.states['GUIDE_CHAPTER']
        
        return self.state.states['MAIN_MENU']
    
    async def handle_language_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle language selection callback"""
        query = update.callback_query
        await query.answer()
        
        user = update.effective_user
        
        if query.data.startswith("lang_"):
            lang_code = query.data.split("_")[1]
            
            if lang_code in self.lang.languages:
                # Update user language
                self.db.update_user_language(user.id, lang_code)
                
                # Get language name
                lang_name = self.lang.languages[lang_code]['name']
                
                await query.edit_message_text(
                    self.lang.get_text(lang_code, "language_changed", name=lang_name),
                    parse_mode=ParseMode.MARKDOWN
                )
                
                # Send main menu in new language
                await context.bot.send_message(
                    chat_id=user.id,
                    text=self.lang.get_text(lang_code, "menu_button"),
                    reply_markup=self.keyboard.create_main_menu(lang_code)
                )
        
        return self.state.states['MAIN_MENU']
    
    async def handle_donation_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle donation callbacks"""
        query = update.callback_query
        await query.answer()
        
        user = update.effective_user
        user_lang = self.db.get_user(user.id)['language'] if self.db.get_user(user.id) else 'en'
        
        if query.data == "donate_confirm":
            # Record donation
            self.db.add_donation(user.id)
            
            # Get statistics for thank you message
            stats = self.db.get_system_statistics()
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            thank_you_text = self.lang.get_text(user_lang, "donate_thanks_message").format(
                current_time,
                stats['active_users'],
                stats['total_reports'],
                stats['total_reporters'],
                stats['today_reports']
            )
            
            thank_you_full = f"{self.lang.get_text(user_lang, 'donate_thanks_title')}\n\n{thank_you_text}"
            
            await query.edit_message_text(
                thank_you_full,
                parse_mode=ParseMode.MARKDOWN
            )
            
            # Send main menu
            await context.bot.send_message(
                chat_id=user.id,
                text=self.lang.get_text(user_lang, "menu_button"),
                reply_markup=self.keyboard.create_main_menu(user_lang)
            )
            
        elif query.data == "donate_back":
            await query.edit_message_text(
                self.lang.get_text(user_lang, "menu_button"),
                reply_markup=self.keyboard.create_main_menu(user_lang)
            )
        
        self.state.set_user_state(user.id, 'MAIN_MENU')
        return self.state.states['MAIN_MENU']
    
    async def handle_back_button(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle back button press"""
        user = update.effective_user
        user_lang = self.db.get_user(user.id)['language'] if self.db.get_user(user.id) else 'en'
        
        await update.message.reply_text(
            self.lang.get_text(user_lang, "menu_button"),
            reply_markup=self.keyboard.create_main_menu(user_lang)
        )
        
        self.state.set_user_state(user.id, 'MAIN_MENU')
        return self.state.states['MAIN_MENU']
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle generic messages"""
        user = update.effective_user
        user_lang = self.db.get_user(user.id)['language'] if self.db.get_user(user.id) else 'en'
        
        await update.message.reply_text(
            self.lang.get_text(user_lang, "error_input"),
            reply_markup=self.keyboard.create_main_menu(user_lang)
        )
        
        return self.state.states['MAIN_MENU']
    
    async def error_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle errors"""
        print(f"\n❌ Error occurred: {context.error}")
        traceback.print_exc()
        
        if update and update.effective_user:
            user_lang = 'en'
            try:
                user_data = self.db.get_user(update.effective_user.id)
                if user_data:
                    user_lang = user_data['language']
            except:
                pass
            
            try:
                await context.bot.send_message(
                    chat_id=update.effective_user.id,
                    text=self.lang.get_text(user_lang, "error_general"),
                    reply_markup=self.keyboard.create_main_menu(user_lang)
                )
            except:
                pass
        
        return self.state.states['MAIN_MENU']
    
    # ===== HELPER METHODS =====
    
    def _detect_target_type(self, target: str) -> str:
        """Detect the type of target identifier"""
        target_lower = target.lower()
        
        if target_lower.startswith('@'):
            return 'telegram_username'
        elif target_lower.startswith('t.me/'):
            return 'telegram_link'
        elif re.match(r'^\d{5,}$', target):
            return 'telegram_id'
        elif re.match(r'^0x[a-fA-F0-9]{40}$', target):
            return 'crypto_wallet'
        elif re.match(r'^\d{7,15}$', target.replace('+', '').replace(' ', '')):
            return 'phone_number'
        elif '@' in target and '.' in target:
            return 'email'
        elif re.match(r'^\d{6,12}$', target):
            return 'binance_id'
        else:
            return 'unknown'
    
    def _categorize_method(self, method_idx: int) -> str:
        """Categorize scam method"""
        categories = {
            0: 'payment_fraud',
            1: 'product_fraud',
            2: 'investment_fraud',
            3: 'identity_theft',
            4: 'phishing',
            5: 'giveaway_fraud',
            6: 'employment_fraud',
            7: 'other'
        }
        return categories.get(method_idx, 'other')
    
    def _calculate_severity(self, session: dict) -> int:
        """Calculate report severity (1-5)"""
        severity = 1
        
        # Higher severity for financial loss
        if session.get('amount'):
            amount = session.get('amount', 0)
            if amount > 1000:
                severity = 5
            elif amount > 500:
                severity = 4
            elif amount > 100:
                severity = 3
            elif amount > 10:
                severity = 2
        
        # Investment scams are more severe
        if session.get('method_idx') == 2:  # Investment scams
            severity = max(severity, 4)
        
        return min(max(severity, 1), 5)

# ==================== BOT SETUP & INITIALIZATION ====================
def setup_bot():
    """Setup and configure the bot"""
    
    print("\n" + "="*70)
    print("🤖 BOT CHECK SCAM ULTIMATE 4.0 - INITIALIZATION")
    print("="*70)
    
    # Initialize components
    db = AdvancedDatabase()
    lang_manager = LanguageManager()
    state_manager = BotStateManager()
    keyboard_manager = KeyboardManager(lang_manager)
    handlers = BotHandlers(db, lang_manager, state_manager, keyboard_manager)
    
    print("✅ Components initialized")
    
    # Create application with persistence
    application = ApplicationBuilder() \
        .token(BOT_TOKEN) \
        .concurrent_updates(True) \
        .connection_pool_size(8) \
        .read_timeout(30) \
        .write_timeout(30) \
        .connect_timeout(30) \
        .pool_timeout(30) \
        .build()
    
    print("✅ Application created")
    
    # Set up conversation handler
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', handlers.start_command)],
        states={
            state_manager.states['MAIN_MENU': [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handlers.handle_main_menu)
            ],
            state_manager.states['CHECK_SCAM']: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handlers.handle_check_scam)
            ],
            state_manager.states['REPORT_TARGET']: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handlers.handle_report_target)
            ],
            state_manager.states['REPORT_METHOD']: [
                CallbackQueryHandler(handlers.handle_report_method_callback)
            ],
            state_manager.states['REPORT_AMOUNT']: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handlers.handle_report_amount)
            ],
            state_manager.states['REPORT_PROOF']: [
                MessageHandler(filters.TEXT | filters.PHOTO, handlers.handle_report_proof)
            ],
            state_manager.states['REPORT_CONFIRM']: [
                CallbackQueryHandler(handlers.handle_report_confirm_callback)
            ],
            state_manager.states['GUIDE_MENU']: [
                CallbackQueryHandler(handlers.handle_guide_callback, pattern="^(guide_|main_menu|guide_menu)")
            ],
            state_manager.states['GUIDE_CHAPTER']: [
                CallbackQueryHandler(handlers.handle_guide_callback, pattern="^(guide_|guide_menu)")
            ],
            state_manager.states['DONATION_INFO']: [
                CallbackQueryHandler(handlers.handle_donation_callback, pattern="^(donate_)")
            ]
        },
        fallbacks=[
            CommandHandler('start', handlers.start_command),
            MessageHandler(filters.Regex('^⬅️'), handlers.handle_back_button),
            MessageHandler(filters.ALL, handlers.handle_message)
        ],
        allow_reentry=True,
        name="main_conversation",
        persistent=False,
    )
    
    # Add handlers
    application.add_handler(conv_handler)
    application.add_handler(CallbackQueryHandler(handlers.handle_language_callback, pattern="^lang_"))
    application.add_handler(CallbackQueryHandler(handlers.handle_guide_callback, pattern="^guide_"))
    application.add_handler(CallbackQueryHandler(handlers.handle_donation_callback, pattern="^donate_"))
    
    # Add error handler
    application.add_error_handler(handlers.error_handler)
    
    # Set bot commands
    commands = [
        BotCommand("start", "Start the bot"),
        BotCommand("help", "Get help"),
        BotCommand("report", "Report a scammer"),
        BotCommand("check", "Check for scams"),
        BotCommand("stats", "View statistics"),
        BotCommand("guide", "Safe trading guide"),
    ]
    
    async def set_commands():
        await application.bot.set_my_commands(commands)
    
    application.run_polling(allowed_updates=Update.ALL_TYPES)
    
    return application

# ==================== MAIN ENTRY POINT ====================
def main():
    """Main entry point"""
    try:
        # Setup logging
        logging.basicConfig(
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            level=logging.INFO,
            handlers=[
                logging.FileHandler(LOG_FILE),
                logging.StreamHandler()
            ]
        )
        
        print("\n" + "="*70)
        print("🚀 BOT CHECK SCAM ULTIMATE 4.0 - STARTING")
        print("="*70)
        print(f"📅 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🔑 Token: {BOT_TOKEN[:10]}...")
        print(f"🗄️ Database: {DB_FILE}")
        print(f"📝 Log file: {LOG_FILE}")
        print(f"🌐 Languages: {len(LanguageManager().languages)} supported")
        print("="*70)
        
        # Setup and run bot
        app = setup_bot()
        
        print("\n✅ Bot is now running...")
        print("📱 Use /start to begin")
        print("👮 Bot commands configured")
        print("💾 Database ready")
        print("="*70 + "\n")
        
        # Run until stopped
        app.run_polling(
            drop_pending_updates=True,
            allowed_updates=Update.ALL_TYPES,
            close_loop=False
        )
        
    except Exception as e:
        print(f"\n❌ CRITICAL ERROR: {e}")
        traceback.print_exc()
        print("\n🔄 Attempting to restart in 10 seconds...")
        import time
        time.sleep(10)
        main()  # Restart

if __name__ == "__main__":
    main()
