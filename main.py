#!/usr/bin/env python3
"""
ANTISCAMBOT - Bot Telegram chống lừa đảo Crypto/OTC
Version: 2.0.0 - All-in-One File
"""

import os
import sys
import json
import sqlite3
import logging
import asyncio
import hashlib
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from collections import defaultdict

# ==================== CONFIGURATION ====================
import dotenv
dotenv.load_dotenv()

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('bot.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

# Bot token
TOKEN = os.getenv('TOKEN')
if not TOKEN:
    logger.error("❌ ERROR: TOKEN environment variable not set!")
    logger.error("Get your token from @BotFather on Telegram")
    logger.error("On Render: Set TOKEN in Environment Variables")
    sys.exit(1)

# ==================== DATABASE SETUP ====================
class Database:
    """SQLite database for storing all bot data."""
    
    def __init__(self, db_path: str = "bot_database.db"):
        self.db_path = db_path
        self.init_database()
    
    def get_connection(self):
        """Get database connection."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def init_database(self):
        """Initialize database tables."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Users table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    telegram_id INTEGER UNIQUE NOT NULL,
                    username TEXT,
                    first_name TEXT,
                    last_name TEXT,
                    language TEXT DEFAULT 'en',
                    report_count INTEGER DEFAULT 0,
                    last_report_date TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Scammers table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS scammers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT,
                    username TEXT UNIQUE,
                    telegram_link TEXT,
                    binance_id TEXT,
                    crypto_wallet TEXT,
                    report_count INTEGER DEFAULT 0,
                    reporter_count INTEGER DEFAULT 0,
                    total_amount REAL DEFAULT 0.0,
                    first_reported TIMESTAMP,
                    last_reported TIMESTAMP,
                    is_active BOOLEAN DEFAULT 1,
                    risk_score INTEGER DEFAULT 0
                )
            ''')
            
            # Reports table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS reports (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    reporter_id INTEGER NOT NULL,
                    reporter_username TEXT,
                    scammer_id INTEGER NOT NULL,
                    scammer_name TEXT,
                    scammer_username TEXT,
                    scammer_link TEXT,
                    binance_id TEXT,
                    crypto_wallet TEXT,
                    amount REAL DEFAULT 0.0,
                    currency TEXT DEFAULT 'USDT',
                    description TEXT,
                    status TEXT DEFAULT 'confirmed',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (scammer_id) REFERENCES scammers (id)
                )
            ''')
            
            # User language preferences
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_languages (
                    user_id INTEGER PRIMARY KEY,
                    language TEXT DEFAULT 'en',
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.commit()
        logger.info("✅ Database initialized successfully")
    
    # User operations
    def get_user(self, telegram_id: int) -> Optional[Dict]:
        """Get user by Telegram ID."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM users WHERE telegram_id = ?', (telegram_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def create_or_update_user(self, telegram_id: int, username: str = None, 
                            first_name: str = None, last_name: str = None) -> Dict:
        """Create or update user."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Check if user exists
            cursor.execute('SELECT * FROM users WHERE telegram_id = ?', (telegram_id,))
            existing = cursor.fetchone()
            
            if existing:
                # Update existing user
                cursor.execute('''
                    UPDATE users 
                    SET username = COALESCE(?, username),
                        first_name = COALESCE(?, first_name),
                        last_name = COALESCE(?, last_name),
                        last_active = CURRENT_TIMESTAMP
                    WHERE telegram_id = ?
                ''', (username, first_name, last_name, telegram_id))
            else:
                # Create new user
                cursor.execute('''
                    INSERT INTO users (telegram_id, username, first_name, last_name)
                    VALUES (?, ?, ?, ?)
                ''', (telegram_id, username, first_name, last_name))
            
            conn.commit()
            
            # Return user data
            cursor.execute('SELECT * FROM users WHERE telegram_id = ?', (telegram_id,))
            return dict(cursor.fetchone())
    
    def increment_user_report_count(self, telegram_id: int):
        """Increment user's report count."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE users 
                SET report_count = report_count + 1,
                    last_report_date = CURRENT_TIMESTAMP,
                    last_active = CURRENT_TIMESTAMP
                WHERE telegram_id = ?
            ''', (telegram_id,))
            conn.commit()
    
    def get_user_reports_today(self, telegram_id: int) -> List:
        """Get user's reports from today."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM reports 
                WHERE reporter_id = ? 
                AND DATE(created_at) = DATE('now')
            ''', (telegram_id,))
            return [dict(row) for row in cursor.fetchall()]
    
    # Scammer operations
    def save_report(self, report_data: Dict) -> bool:
        """Save a new scam report."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Check if scammer already exists
                cursor.execute('''
                    SELECT id, reporter_count FROM scammers 
                    WHERE username = ? OR binance_id = ?
                ''', (report_data['scammer_username'], report_data.get('scammer_id')))
                
                scammer = cursor.fetchone()
                
                if scammer:
                    scammer_id = scammer['id']
                    # Update existing scammer
                    cursor.execute('''
                        UPDATE scammers 
                        SET report_count = report_count + 1,
                            total_amount = total_amount + ?,
                            last_reported = CURRENT_TIMESTAMP
                        WHERE id = ?
                    ''', (report_data.get('amount', 0), scammer_id))
                    
                    # Check if this reporter already reported this scammer
                    cursor.execute('''
                        SELECT id FROM reports 
                        WHERE reporter_id = ? AND scammer_id = ?
                    ''', (report_data['reporter_id'], scammer_id))
                    
                    if not cursor.fetchone():
                        # New reporter for this scammer
                        cursor.execute('''
                            UPDATE scammers 
                            SET reporter_count = reporter_count + 1
                            WHERE id = ?
                        ''', (scammer_id,))
                else:
                    # Create new scammer
                    cursor.execute('''
                        INSERT INTO scammers (
                            name, username, telegram_link, binance_id, crypto_wallet,
                            report_count, reporter_count, total_amount,
                            first_reported, last_reported
                        ) VALUES (?, ?, ?, ?, ?, 1, 1, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                    ''', (
                        report_data['scammer_name'],
                        report_data['scammer_username'],
                        report_data['scammer_link'],
                        report_data.get('scammer_id'),
                        report_data.get('crypto_wallet'),
                        report_data.get('amount', 0)
                    ))
                    scammer_id = cursor.lastrowid
                
                # Save the report
                cursor.execute('''
                    INSERT INTO reports (
                        reporter_id, reporter_username, scammer_id,
                        scammer_name, scammer_username, scammer_link,
                        binance_id, crypto_wallet, amount, currency, status
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'confirmed')
                ''', (
                    report_data['reporter_id'],
                    report_data.get('reporter_username'),
                    scammer_id,
                    report_data['scammer_name'],
                    report_data['scammer_username'],
                    report_data['scammer_link'],
                    report_data.get('scammer_id'),
                    report_data.get('crypto_wallet'),
                    report_data.get('amount', 0),
                    report_data.get('currency', 'USDT')
                ))
                
                # Update user report count
                cursor.execute('''
                    UPDATE users 
                    SET report_count = report_count + 1,
                        last_report_date = CURRENT_TIMESTAMP,
                        last_active = CURRENT_TIMESTAMP
                    WHERE telegram_id = ?
                ''', (report_data['reporter_id'],))
                
                conn.commit()
                return True
                
        except Exception as e:
            logger.error(f"Error saving report: {e}")
            return False
    
    def search_scammer(self, query: str) -> Optional[Dict]:
        """Search for scammer by various identifiers."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Try different search methods
            if query.startswith('@'):
                username = query[1:]
                cursor.execute('SELECT * FROM scammers WHERE username = ?', (username,))
            elif 't.me/' in query:
                username = query.split('t.me/')[-1].split('/')[0].split('?')[0]
                cursor.execute('SELECT * FROM scammers WHERE username = ? OR telegram_link LIKE ?', 
                             (username, f'%{username}%'))
            elif query.isdigit():
                cursor.execute('SELECT * FROM scammers WHERE binance_id = ?', (query,))
            else:
                cursor.execute('SELECT * FROM scammers WHERE name LIKE ? OR username LIKE ?', 
                             (f'%{query}%', f'%{query}%'))
            
            row = cursor.fetchone()
            if row:
                # Get additional report details
                cursor.execute('''
                    SELECT COUNT(DISTINCT reporter_id) as unique_reporters,
                           SUM(amount) as total_amount
                    FROM reports 
                    WHERE scammer_id = ?
                ''', (row['id'],))
                stats = cursor.fetchone()
                
                result = dict(row)
                result['unique_reporters'] = stats['unique_reporters'] if stats else 0
                result['total_amount'] = stats['total_amount'] if stats else 0
                return result
            
            return None
    
    def get_scam_statistics(self) -> Dict:
        """Get overall scam statistics."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('SELECT COUNT(*) as total_reports FROM reports')
            total_reports = cursor.fetchone()['total_reports']
            
            cursor.execute('SELECT COUNT(DISTINCT reporter_id) as unique_reporters FROM reports')
            unique_reporters = cursor.fetchone()['unique_reporters']
            
            cursor.execute('SELECT COUNT(*) as total_scammers FROM scammers')
            total_scammers = cursor.fetchone()['total_scammers']
            
            cursor.execute('SELECT SUM(amount) as total_amount FROM reports')
            total_amount = cursor.fetchone()['total_amount'] or 0
            
            cursor.execute('''
                SELECT COUNT(*) as reports_today 
                FROM reports 
                WHERE DATE(created_at) = DATE('now')
            ''')
            reports_today = cursor.fetchone()['reports_today']
            
            return {
                'total_reports': total_reports,
                'unique_reporters': unique_reporters,
                'total_scammers': total_scammers,
                'total_amount': total_amount,
                'reports_today': reports_today
            }
    
    def get_top_scammers(self, limit: int = 10) -> List[Dict]:
        """Get top scammers by report count."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT s.*, 
                       COUNT(DISTINCT r.reporter_id) as reporter_count,
                       SUM(r.amount) as total_amount
                FROM scammers s
                LEFT JOIN reports r ON s.id = r.scammer_id
                GROUP BY s.id
                ORDER BY s.report_count DESC
                LIMIT ?
            ''', (limit,))
            return [dict(row) for row in cursor.fetchall()]
    
    # Language operations
    def get_user_language(self, user_id: int) -> str:
        """Get user's preferred language."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT language FROM user_languages WHERE user_id = ?', (user_id,))
            row = cursor.fetchone()
            return row['language'] if row else 'en'
    
    def set_user_language(self, user_id: int, language: str):
        """Set user's preferred language."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO user_languages (user_id, language, updated_at)
                VALUES (?, ?, CURRENT_TIMESTAMP)
            ''', (user_id, language))
            conn.commit()

# Initialize database
db = Database()

# ==================== LANGUAGE SYSTEM ====================
class LanguageSystem:
    """Multi-language support system."""
    
    # Translations for all 4 languages
    TRANSLATIONS = {
        'en': {
            # Menu items
            'menu_language': '🌐 Language',
            'menu_check': '🔍 Check scam',
            'menu_report': '🚨 Report scam',
            'menu_help': '❓ Help',
            'menu_safety': '⚠️ Safety tips',
            'menu_donate': '💝 Donate',
            'menu_groups': '👥 Trusted groups',
            'menu_admins': '🛡 Trusted admins',
            'menu_stats': '📊 Scam stats',
            'menu_about': 'ℹ️ About',
            
            # Start and About
            'welcome': 'Hi {}, welcome to **BOT_TELE**! 🤖\n\nI\'m a community-driven bot for checking and reporting scams in Crypto, OTC, and intermediary transactions.\n\nUse the buttons below to navigate:',
            'about_title': 'About BOT_TELE',
            'about_description': 'Bot for community check, report, and warning of fraud in Crypto, OTC, and intermediary transactions.',
            'strengths_title': 'Strengths & credibility',
            'strength_1': 'Data built from actual community contributions',
            'strength_2': 'Each scam object shows: Report count & Reporter count',
            'strength_3': 'More reporters → Higher warning reliability',
            'strength_4': 'Helps users assess risk before trading',
            'community_stats': 'Community Statistics',
            'total_reports': 'Total reports',
            'unique_reporters': 'Unique reporters',
            'total_scammers': 'Total scammers',
            'disclaimer': 'Disclaimer',
            'disclaimer_text': 'BOT_TELE does not provide legal conclusions, only risk indicators based on actual reports.',
            
            # Check scam
            'check_instruction': 'Please send me the scammer\'s Telegram username (with @), Telegram link, or Binance ID to check.',
            'scammer_not_found': '✅ No reports found for this user. However, always stay cautious!',
            'warning_title': 'TRADING WARNING',
            'target': 'Target',
            'telegram_link': 'Telegram Link',
            'binance_id': 'Binance ID',
            'report_count': 'Report count',
            'reporter_count': 'Reporter count',
            'total_amount': 'Total amount',
            'risk_assessment': 'Risk Assessment',
            'recommendation': 'Recommendation',
            'do_not_trade': 'DO NOT TRADE',
            
            # Report scam
            'report_instruction': '🚨 **REPORT SCAM PROCESS**\n\nYou will be asked for the following information:\n1. Scammer\'s Telegram display name\n2. Scammer\'s Telegram username\n3. Scammer\'s Telegram link\n4. Scammer\'s Binance ID / Crypto wallet\n5. Scam amount (if known)\n\n⚠️ **Note**: You can only submit 3 reports per 24 hours.',
            'ask_name': '📝 **Step 1/5**\nPlease send the scammer\'s Telegram DISPLAY NAME:',
            'ask_username': '📝 **Step 2/5**\nPlease send the scammer\'s Telegram USERNAME (with @):',
            'ask_link': '📝 **Step 3/5**\nPlease send the scammer\'s Telegram LINK:',
            'ask_id': '📝 **Step 4/5**\nPlease send the scammer\'s Binance ID or Crypto wallet address:',
            'ask_amount': '📝 **Step 5/5**\nPlease send the scam amount (in USDT):',
            'report_summary': '📋 **REPORT SUMMARY**\n\n• **Name**: {}\n• **Username**: {}\n• **Link**: {}\n• **ID/Wallet**: {}\n• **Amount**: {} USDT\n\n✅ Please confirm if this information is correct:',
            'confirm_yes': '✅ YES, submit report',
            'confirm_no': '❌ NO, cancel report',
            'report_success': '✅ **REPORT SUBMITTED SUCCESSFULLY!**\n\nThank you for helping the community. Your report has been recorded and will help protect others.',
            'report_cancelled': '❌ Report cancelled.',
            'report_warning': '⚠️ **WARNING**: Not reporting scammers puts the community at risk. Please report any suspicious activity!',
            'report_limit_exceeded': '⚠️ **REPORT LIMIT REACHED**\n\nYou have reached the limit of 3 reports per 24 hours. Please try again tomorrow.',
            
            # Help
            'help_title': 'Help & Instructions',
            
            # Safety tips
            'safety_title': 'TRADING SAFETY TIPS',
            
            # Donate
            'donate_title': 'Support Development',
            'donation_message': '''Binance ID: 154265504

Every donation helps BOT_TELE maintain servers,
upgrade security and serve the community long-term.
Thank you sincerely!''',
            
            # Trusted groups/admins
            'trusted_groups_title': 'Trusted Trading Groups',
            'trusted_admins_title': 'Trusted Admins/Mediators',
            
            # Statistics
            'stats_title': 'Scam Statistics',
            
            # Language
            'language_changed': '✅ Language changed successfully!',
            'select_language': '🌐 Please select your language:'
        },
        
        'vi': {
            # Menu items
            'menu_language': '🌐 Ngôn ngữ',
            'menu_check': '🔍 Kiểm tra lừa đảo',
            'menu_report': '🚨 Báo cáo scam',
            'menu_help': '❓ Hướng dẫn sử dụng',
            'menu_safety': '⚠️ Lưu ý giao dịch an toàn',
            'menu_donate': '💝 Ủng hộ nhà phát triển',
            'menu_groups': '👥 Group giao dịch uy tín',
            'menu_admins': '🛡 Admin/trung gian uy tín',
            'menu_stats': '📊 Thống kê scammer lớn',
            'menu_about': 'ℹ️ Giới thiệu BOT_TELE',
            
            # Start and About
            'welcome': 'Chào {}, chào mừng đến với **BOT_TELE**! 🤖\n\nTôi là bot do cộng đồng vận hành để kiểm tra và báo cáo lừa đảo trong giao dịch Crypto, OTC và trung gian.\n\nSử dụng các nút bên dưới để điều hướng:',
            'about_title': 'Giới thiệu BOT_TELE',
            'about_description': 'Bot hỗ trợ cộng đồng kiểm tra – báo cáo – cảnh báo lừa đảo trong giao dịch Crypto, OTC và trung gian.',
            'strengths_title': 'Điểm mạnh & độ uy tín',
            'strength_1': 'Dữ liệu được xây dựng từ đóng góp thực tế của cộng đồng',
            'strength_2': 'Mỗi đối tượng scam hiển thị: Số lượt báo cáo & Số người báo cáo',
            'strength_3': 'Càng nhiều người báo cáo → Độ tin cậy cảnh báo càng cao',
            'strength_4': 'Giúp người dùng đánh giá rủi ro trước khi giao dịch',
            'community_stats': 'Thống kê cộng đồng',
            'total_reports': 'Tổng số báo cáo',
            'unique_reporters': 'Số người báo cáo',
            'total_scammers': 'Tổng số scammer',
            'disclaimer': 'Lưu ý',
            'disclaimer_text': 'BOT_TELE không kết luận pháp lý, chỉ cung cấp chỉ số rủi ro dựa trên số lượng báo cáo thực tế.',
            
            # Check scam
            'check_instruction': 'Vui lòng gửi cho tôi username Telegram (có @), link Telegram, hoặc ID Binance của đối tượng cần kiểm tra.',
            'scammer_not_found': '✅ Không tìm thấy báo cáo nào cho người dùng này. Tuy nhiên, hãy luôn thận trọng!',
            'warning_title': 'CẢNH BÁO GIAO DỊCH',
            'target': 'Đối tượng',
            'telegram_link': 'Link Telegram',
            'binance_id': 'ID Binance',
            'report_count': 'Số lượt bị báo cáo',
            'reporter_count': 'Số người tham gia báo cáo',
            'total_amount': 'Tổng số tiền liên quan',
            'risk_assessment': 'Đánh giá rủi ro',
            'recommendation': 'Khuyến nghị',
            'do_not_trade': 'KHÔNG giao dịch',
            
            # Report scam
            'report_instruction': '🚨 **QUY TRÌNH BÁO CÁO SCAM**\n\nBạn sẽ được hỏi các thông tin sau:\n1. Tên hiển thị Telegram của scammer\n2. Username Telegram của scammer\n3. Link Telegram của scammer\n4. ID Binance / Ví Crypto của scammer\n5. Số tiền bị lừa (nếu biết)\n\n⚠️ **Lưu ý**: Bạn chỉ được báo cáo tối đa 3 lần trong 24 giờ.',
            'ask_name': '📝 **Bước 1/5**\nVui lòng gửi TÊN HIỂN THỊ TELEGRAM của scammer:',
            'ask_username': '📝 **Bước 2/5**\nVui lòng gửi USERNAME TELEGRAM của scammer (có @):',
            'ask_link': '📝 **Bước 3/5**\nVui lòng gửi LINK TELEGRAM của scammer:',
            'ask_id': '📝 **Bước 4/5**\nVui lòng gửi ID BINANCE hoặc địa chỉ Ví Crypto của scammer:',
            'ask_amount': '📝 **Bước 5/5**\nVui lòng gửi số tiền bị lừa (đơn vị USDT):',
            'report_summary': '📋 **TÓM TẮT BÁO CÁO**\n\n• **Tên**: {}\n• **Username**: {}\n• **Link**: {}\n• **ID/Ví**: {}\n• **Số tiền**: {} USDT\n\n✅ Vui lòng xác nhận nếu thông tin này chính xác:',
            'confirm_yes': '✅ CÓ, gửi báo cáo',
            'confirm_no': '❌ KHÔNG, hủy báo cáo',
            'report_success': '✅ **BÁO CÁO ĐÃ ĐƯỢC GỬI THÀNH CÔNG!**\n\nCảm ơn bạn đã giúp đỡ cộng đồng. Báo cáo của bạn đã được ghi nhận và sẽ giúp bảo vệ người khác.',
            'report_cancelled': '❌ Đã hủy báo cáo.',
            'report_warning': '⚠️ **CẢNH BÁO**: Không báo cáo scammer sẽ đặt cộng đồng vào nguy cơ. Vui lòng báo cáo bất kỳ hoạt động đáng ngờ nào!',
            'report_limit_exceeded': '⚠️ **ĐẠT GIỚI HẠN BÁO CÁO**\n\nBạn đã đạt giới hạn 3 báo cáo trong 24 giờ. Vui lòng thử lại vào ngày mai.',
            
            # Donate
            'donate_title': 'Ủng hộ phát triển',
            'donation_message': '''Binance ID: 154265504

Mọi sự ủng hộ giúp BOT_TELE duy trì máy chủ,
nâng cấp bảo mật và phục vụ cộng đồng lâu dài.
Xin chân thành cảm ơn!''',
            
            # Language
            'language_changed': '✅ Đã đổi ngôn ngữ thành công!',
            'select_language': '🌐 Vui lòng chọn ngôn ngữ:'
        },
        
        'zh': {
            # Menu items
            'menu_language': '🌐 语言',
            'menu_check': '🔍 检查欺诈',
            'menu_report': '🚨 报告欺诈',
            'menu_help': '❓ 使用帮助',
            'menu_safety': '⚠️ 安全交易提示',
            'menu_donate': '💝 支持开发者',
            'menu_groups': '👥 可信交易群组',
            'menu_admins': '🛡 可信管理员/中介',
            'menu_stats': '📊 欺诈统计',
            'menu_about': 'ℹ️ 关于BOT_TELE',
            
            # Start and About
            'welcome': '你好 {}, 欢迎使用 **BOT_TELE**！🤖\n\n我是基于社区驱动的Telegram机器人，用于检查、报告和警告加密货币、场外交易和中介交易中的欺诈行为。\n\n请使用下方按钮导航：',
            
            # Donate
            'donate_title': '支持开发',
            'donation_message': '''Binance ID: 154265504

每笔捐赠都将帮助BOT_TELE维护服务器，
升级安全系统并长期服务社区。
衷心感谢！''',
            
            # Language
            'language_changed': '✅ 语言切换成功！',
            'select_language': '🌐 请选择语言：'
        },
        
        'ru': {
            # Menu items
            'menu_language': '🌐 Язык',
            'menu_check': '🔍 Проверить мошенничество',
            'menu_report': '🚨 Сообщить о мошенничестве',
            'menu_help': '❓ Инструкция по использованию',
            'menu_safety': '⚠️ Рекомендации по безопасным сделкам',
            'menu_donate': '💝 Поддержать разработчика',
            'menu_groups': '👥 Надежные группы для сделок',
            'menu_admins': '🛡 Надежные администраторы/посредники',
            'menu_stats': '📊 Статистика мошенничеств',
            'menu_about': 'ℹ️ О BOT_TELE',
            
            # Start and About
            'welcome': 'Привет {}, добро пожаловать в **BOT_TELE**! 🤖\n\nЯ Telegram-бот, поддерживающий сообщество в проверке, отчетности и предупреждении о мошенничестве в сделках с криптовалютой, OTC и посреднических сделках.\n\nИспользуйте кнопки ниже для навигации：',
            
            # Donate
            'donate_title': 'Поддержка разработки',
            'donation_message': '''Binance ID: 154265504

Каждое пожертвование помогает BOT_TELE поддерживать серверы,
обновлять безопасность и долгосрочно служить сообществу.
Искренне благодарим!''',
            
            # Language
            'language_changed': '✅ Язык успешно изменен!',
            'select_language': '🌐 Пожалуйста, выберите язык：'
        }
    }
    
    @classmethod
    def get_text(cls, user_id: int, key: str) -> str:
        """Get text for user in their preferred language."""
        lang = db.get_user_language(user_id)
        translations = cls.TRANSLATIONS.get(lang, cls.TRANSLATIONS['en'])
        return translations.get(key, cls.TRANSLATIONS['en'].get(key, key))
    
    @classmethod
    def get_available_languages(cls):
        """Get list of available languages."""
        return [
            ('en', '🇺🇸 English'),
            ('vi', '🇻🇳 Tiếng Việt'),
            ('zh', '🇨🇳 中文'),
            ('ru', '🇷🇺 Русский')
        ]

lang = LanguageSystem()

# ==================== TELEGRAM BOT SETUP ====================
# Import Telegram libraries
try:
    from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
    from telegram.ext import (
        Application,
        CommandHandler,
        MessageHandler,
        filters,
        CallbackQueryHandler,
        ConversationHandler,
        ContextTypes
    )
except ImportError:
    logger.error("❌ python-telegram-bot not installed!")
    logger.error("Run: pip install python-telegram-bot")
    sys.exit(1)

# Conversation states for report
NAME, USERNAME, LINK, SCAMMER_ID, AMOUNT, CONFIRM = range(6)

# ==================== HANDLER FUNCTIONS ====================
class BotHandlers:
    """All bot handler functions."""
    
    @staticmethod
    async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command."""
        user = update.effective_user
        
        # Create/update user in database
        db.create_or_update_user(
            telegram_id=user.id,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name
        )
        
        # Get user language
        text = lang.get_text(user.id, 'welcome').format(user.first_name)
        
        # Create main menu keyboard
        keyboard = [
            [InlineKeyboardButton(lang.get_text(user.id, 'menu_language'), callback_data='menu_language')],
            [InlineKeyboardButton(lang.get_text(user.id, 'menu_check'), callback_data='menu_check')],
            [InlineKeyboardButton(lang.get_text(user.id, 'menu_report'), callback_data='menu_report')],
            [InlineKeyboardButton(lang.get_text(user.id, 'menu_help'), callback_data='menu_help')],
            [InlineKeyboardButton(lang.get_text(user.id, 'menu_safety'), callback_data='menu_safety')],
            [InlineKeyboardButton(lang.get_text(user.id, 'menu_donate'), callback_data='menu_donate')],
            [InlineKeyboardButton(lang.get_text(user.id, 'menu_groups'), callback_data='menu_groups')],
            [InlineKeyboardButton(lang.get_text(user.id, 'menu_admins'), callback_data='menu_admins')],
            [InlineKeyboardButton(lang.get_text(user.id, 'menu_stats'), callback_data='menu_stats')],
            [InlineKeyboardButton(lang.get_text(user.id, 'menu_about'), callback_data='menu_about')],
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')
    
    @staticmethod
    async def about_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /about command."""
        user = update.effective_user
        stats = db.get_scam_statistics()
        
        text = f"""**BOT_TELE** - {lang.get_text(user.id, 'about_title')}

{lang.get_text(user.id, 'about_description')}

🔎 **{lang.get_text(user.id, 'strengths_title')}**
• {lang.get_text(user.id, 'strength_1')}
• {lang.get_text(user.id, 'strength_2')}
• {lang.get_text(user.id, 'strength_3')}
• {lang.get_text(user.id, 'strength_4')}

📊 **{lang.get_text(user.id, 'community_stats')}**
• {lang.get_text(user.id, 'total_reports')}: **{stats['total_reports']}**
• {lang.get_text(user.id, 'unique_reporters')}: **{stats['unique_reporters']}**
• {lang.get_text(user.id, 'total_scammers')}: **{stats['total_scammers']}**
• {lang.get_text(user.id, 'total_amount')}: **~ {stats['total_amount']} USDT**

⚠️ **{lang.get_text(user.id, 'disclaimer')}**
{lang.get_text(user.id, 'disclaimer_text')}
"""
        
        await update.message.reply_text(text, parse_mode='Markdown')
    
    @staticmethod
    async def language_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /language command."""
        user = update.effective_user
        
        keyboard = []
        for lang_code, lang_name in lang.get_available_languages():
            keyboard.append([InlineKeyboardButton(lang_name, callback_data=f'lang_{lang_code}')])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            lang.get_text(user.id, 'select_language'),
            reply_markup=reply_markup
        )
    
    @staticmethod
    async def language_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle language selection callback."""
        query = update.callback_query
        await query.answer()
        
        user = query.from_user
        lang_code = query.data.split('_')[1]
        
        # Set user language
        db.set_user_language(user.id, lang_code)
        
        await query.edit_message_text(lang.get_text(user.id, 'language_changed'))
    
    @staticmethod
    async def check_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /check command."""
        user = update.effective_user
        
        if context.args:
            # User provided query in command
            query = ' '.join(context.args)
            await BotHandlers.process_check_query(update, context, query, user)
        else:
            # Ask for query
            await update.message.reply_text(lang.get_text(user.id, 'check_instruction'))
    
    @staticmethod
    async def process_check_query(update: Update, context: ContextTypes.DEFAULT_TYPE, query: str, user):
        """Process scammer check query."""
        scammer = db.search_scammer(query)
        
        if scammer:
            # Calculate risk level
            report_count = scammer['report_count']
            reporter_count = scammer.get('unique_reporters', 0)
            
            if report_count >= 10 or reporter_count >= 5:
                risk_level = "🔴 HIGH"
                recommendation = lang.get_text(user.id, 'do_not_trade')
            elif report_count >= 5 or reporter_count >= 3:
                risk_level = "🟡 MEDIUM"
                recommendation = "Exercise extreme caution"
            elif report_count >= 2:
                risk_level = "🟠 LOW"
                recommendation = "Proceed with caution"
            else:
                risk_level = "🟢 MINIMAL"
                recommendation = "Standard verification recommended"
            
            # Format warning message
            text = f"""🚨 **{lang.get_text(user.id, 'warning_title')}**

• **{lang.get_text(user.id, 'target')}**: {scammer.get('username', 'N/A')}
• **{lang.get_text(user.id, 'telegram_link')}**: {scammer.get('telegram_link', 'N/A')}
• **{lang.get_text(user.id, 'binance_id')}**: {scammer.get('binance_id', 'N/A')}

📊 **{lang.get_text(user.id, 'community_stats')}**
• {lang.get_text(user.id, 'report_count')}: **{report_count}**
• {lang.get_text(user.id, 'reporter_count')}: **{reporter_count}**
• {lang.get_text(user.id, 'total_amount')}: **~ {scammer.get('total_amount', 0)} USDT**

⚠️ **{lang.get_text(user.id, 'risk_assessment')}**: {risk_level}
📢 **{lang.get_text(user.id, 'recommendation')}**: {recommendation}
"""
        else:
            text = lang.get_text(user.id, 'scammer_not_found')
        
        await update.message.reply_text(text, parse_mode='Markdown')
    
    @staticmethod
    async def report_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Start report process."""
        user = update.effective_user
        
        # Check rate limit (3 reports per day)
        reports_today = db.get_user_reports_today(user.id)
        if len(reports_today) >= 3:
            await update.message.reply_text(lang.get_text(user.id, 'report_limit_exceeded'))
            return ConversationHandler.END
        
        # Ask for scammer name
        await update.message.reply_text(lang.get_text(user.id, 'ask_name'))
        return NAME
    
    @staticmethod
    async def report_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Store scammer name."""
        context.user_data['scammer_name'] = update.message.text
        user = update.effective_user
        
        await update.message.reply_text(lang.get_text(user.id, 'ask_username'))
        return USERNAME
    
    @staticmethod
    async def report_username(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Store scammer username."""
        username = update.message.text.strip()
        if not username.startswith('@'):
            username = '@' + username
        context.user_data['scammer_username'] = username
        user = update.effective_user
        
        await update.message.reply_text(lang.get_text(user.id, 'ask_link'))
        return LINK
    
    @staticmethod
    async def report_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Store scammer Telegram link."""
        link = update.message.text.strip()
        if not link.startswith('https://t.me/'):
            link = f'https://t.me/{link.replace("@", "")}'
        context.user_data['scammer_link'] = link
        user = update.effective_user
        
        await update.message.reply_text(lang.get_text(user.id, 'ask_id'))
        return SCAMMER_ID
    
    @staticmethod
    async def report_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Store scammer ID or wallet."""
        context.user_data['scammer_id'] = update.message.text
        user = update.effective_user
        
        await update.message.reply_text(lang.get_text(user.id, 'ask_amount'))
        return AMOUNT
    
    @staticmethod
    async def report_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Store scam amount."""
        amount_text = update.message.text
        # Extract numbers
        numbers = re.findall(r'\d+\.?\d*', amount_text)
        amount = float(numbers[0]) if numbers else 0
        
        context.user_data['amount'] = amount
        user = update.effective_user
        
        # Show summary
        text = lang.get_text(user.id, 'report_summary').format(
            context.user_data['scammer_name'],
            context.user_data['scammer_username'],
            context.user_data['scammer_link'],
            context.user_data['scammer_id'],
            context.user_data['amount']
        )
        
        keyboard = [
            [
                InlineKeyboardButton(lang.get_text(user.id, 'confirm_yes'), callback_data='yes_report'),
                InlineKeyboardButton(lang.get_text(user.id, 'confirm_no'), callback_data='no_report')
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(text, reply_markup=reply_markup)
        return CONFIRM
    
    @staticmethod
    async def report_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle report confirmation."""
        query = update.callback_query
        await query.answer()
        
        user = query.from_user
        
        if query.data == 'yes_report':
            # Save report
            report_data = {
                'reporter_id': user.id,
                'reporter_username': user.username,
                'scammer_name': context.user_data['scammer_name'],
                'scammer_username': context.user_data['scammer_username'],
                'scammer_link': context.user_data['scammer_link'],
                'scammer_id': context.user_data.get('scammer_id'),
                'amount': context.user_data.get('amount', 0),
                'currency': 'USDT'
            }
            
            success = db.save_report(report_data)
            
            if success:
                text = lang.get_text(user.id, 'report_success')
            else:
                text = "❌ Error saving report. Please try again."
        else:
            text = f"{lang.get_text(user.id, 'report_cancelled')}\n\n{lang.get_text(user.id, 'report_warning')}"
        
        # Clear conversation data
        context.user_data.clear()
        
        await query.edit_message_text(text)
        return ConversationHandler.END
    
    @staticmethod
    async def cancel_report(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Cancel report process."""
        user = update.effective_user
        
        text = f"{lang.get_text(user.id, 'report_cancelled')}\n\n{lang.get_text(user.id, 'report_warning')}"
        
        # Clear conversation data
        context.user_data.clear()
        
        await update.message.reply_text(text)
        return ConversationHandler.END
    
    @staticmethod
    async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command."""
        user = update.effective_user
        
        text = f"""**{lang.get_text(user.id, 'help_title')}**

**1. /check** - {lang.get_text(user.id, 'menu_check')}
{lang.get_text(user.id, 'check_instruction')}

**2. /report** - {lang.get_text(user.id, 'menu_report')}
{lang.get_text(user.id, 'report_instruction')}

**3. /safety** - {lang.get_text(user.id, 'menu_safety')}
Important safety tips for trading

**4. /donate** - {lang.get_text(user.id, 'menu_donate')}
Support bot development

**5. /trusted_groups** - {lang.get_text(user.id, 'menu_groups')}
List of trusted trading groups

**6. /trusted_admins** - {lang.get_text(user.id, 'menu_admins')}
List of trusted admins/mediators

**7. /stats** - {lang.get_text(user.id, 'menu_stats')}
Scam statistics and top scammers

**8. /about** - {lang.get_text(user.id, 'menu_about')}
About BOT_TELE and community stats

**9. /language** - {lang.get_text(user.id, 'menu_language')}
Change bot language

**⚠️ Important Notes:**
• Rate limit: 3 reports per user per 24 hours
• All reports are community-driven
• Bot provides risk indicators, not legal conclusions
"""
        
        await update.message.reply_text(text, parse_mode='Markdown')
    
    @staticmethod
    async def safety_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /safety command."""
        user = update.effective_user
        
        text = f"""**{lang.get_text(user.id, 'safety_title')}**

**1. Verify Identity Thoroughly**
• Always check Telegram username and join date
• Verify Binance ID matches the profile
• Ask for social proof or references

**2. Use Secure Payment Methods**
• Use escrow services when available
• Avoid direct transfers to unknown wallets
• Start with small amounts for new contacts

**3. Avoid Common Scams**
• Beware of "too good to be true" offers
• Watch for urgency pressure tactics
• Avoid deals requiring upfront "fees"

**4. Use Trusted Platforms**
• Use verified OTC desks
• Trade on reputable exchanges
• Join verified community groups

**5. Report Suspicious Activity**
• Report any suspicious users immediately
• Share scam alerts with community

**⚠️ IMPORTANT**: If something feels wrong, it probably is. Trust your instincts and walk away.
"""
        
        await update.message.reply_text(text, parse_mode='Markdown')
    
    @staticmethod
    async def donate_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /donate command."""
        user = update.effective_user
        
        text = f"""**{lang.get_text(user.id, 'donate_title')}**

{lang.get_text(user.id, 'donation_message')}

**Donations will be used for:**
• Server maintenance and hosting costs
• Security upgrades and monitoring
• Bot development and new features
• Community outreach and education

**Transparency Commitment:**
We commit to using all donations transparently – solely for bot operation and long-term development.

Thank you sincerely for your support!
"""
        
        await update.message.reply_text(text, parse_mode='Markdown')
    
    @staticmethod
    async def trusted_groups_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /trusted_groups command."""
        user = update.effective_user
        
        text = f"""**{lang.get_text(user.id, 'trusted_groups_title')}**

The following groups have good reputations in the community. However, always do your own due diligence:

• **OTC Crypto Việt Nam**: https://t.me/otccryptovietnam
• **Binance P2P Việt Nam**: https://t.me/binancep2pvn
• **Crypto Trading Vietnam**: https://t.me/cryptotradingvietnam
• **Global Crypto Trading**: https://t.me/globalcrypto
• **Binance P2P Official**: https://t.me/binancep2p

⚠️ **Note**: Even in trusted groups, always verify identities and use caution.
"""
        
        await update.message.reply_text(text, parse_mode='Markdown', disable_web_page_preview=True)
    
    @staticmethod
    async def trusted_admins_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /trusted_admins command."""
        user = update.effective_user
        
        text = f"""**{lang.get_text(user.id, 'trusted_admins_title')}**

These admins have established good reputations as mediators. Contact them for assistance:

• **Admin OTC Việt Nam**: @otcadmin_vn
• **Binance Support VN**: @binancesupport_vn
• **Global Crypto Admin**: @globaladmin
• **Binance Official Support**: @binancesupport

⚠️ **Note**: Always verify admin identities within groups.
"""
        
        await update.message.reply_text(text, parse_mode='Markdown')
    
    @staticmethod
    async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /stats command."""
        user = update.effective_user
        stats = db.get_scam_statistics()
        top_scammers = db.get_top_scammers(limit=5)
        
        text = f"""**{lang.get_text(user.id, 'stats_title')}**

**Overall Statistics:**
• {lang.get_text(user.id, 'total_reports')}: **{stats['total_reports']}**
• {lang.get_text(user.id, 'unique_reporters')}: **{stats['unique_reporters']}**
• {lang.get_text(user.id, 'total_scammers')}: **{stats['total_scammers']}**
• {lang.get_text(user.id, 'total_amount')}: **{stats['total_amount']} USDT**
• Reports today: **{stats['reports_today']}**

**Top Scammers:**
"""
        
        for i, scammer in enumerate(top_scammers, 1):
            text += f"\n**{i}. {scammer['username']}**"
            text += f"\n   📈 Reports: {scammer['report_count']}"
            text += f"\n   👥 Reporters: {scammer.get('reporter_count', 0)}"
            text += f"\n   💰 Amount: {scammer.get('total_amount', 0)} USDT"
        
        text += "\n\n**Note**: Statistics are based on community reports only."
        
        await update.message.reply_text(text, parse_mode='Markdown')
    
    @staticmethod
    async def menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle menu callback queries."""
        query = update.callback_query
        await query.answer()
        
        user = query.from_user
        action = query.data
        
        # Map callback actions to commands
        action_handlers = {
            'menu_language': BotHandlers.language_command,
            'menu_check': BotHandlers.check_command,
            'menu_report': BotHandlers.report_command,
            'menu_help': BotHandlers.help_command,
            'menu_safety': BotHandlers.safety_command,
            'menu_donate': BotHandlers.donate_command,
            'menu_groups': BotHandlers.trusted_groups_command,
            'menu_admins': BotHandlers.trusted_admins_command,
            'menu_stats': BotHandlers.stats_command,
            'menu_about': BotHandlers.about_command,
        }
        
        if action in action_handlers:
            # Create a mock update with message
            mock_update = Update(
                update.update_id,
                message=query.message
            )
            await action_handlers[action](mock_update, context)

# ==================== MAIN BOT SETUP ====================
def main():
    """Main function to start the bot."""
    logger.info("🚀 Starting AntiScamBot...")
    logger.info(f"✅ Token: {TOKEN[:10]}...")
    logger.info(f"✅ Database: bot_database.db")
    logger.info(f"✅ Languages: 4 (en, vi, zh, ru)")
    logger.info(f"✅ Features: 10 menus, 3 reports/day limit, no admin approval")
    
    # Create application
    application = Application.builder().token(TOKEN).build()
    
    # Setup conversation handler for report
    report_conv_handler = ConversationHandler(
        entry_points=[CommandHandler('report', BotHandlers.report_command)],
        states={
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, BotHandlers.report_name)],
            USERNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, BotHandlers.report_username)],
            LINK: [MessageHandler(filters.TEXT & ~filters.COMMAND, BotHandlers.report_link)],
            SCAMMER_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, BotHandlers.report_id)],
            AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, BotHandlers.report_amount)],
            CONFIRM: [CallbackQueryHandler(BotHandlers.report_confirm, pattern='^(yes|no)_report$')]
        },
        fallbacks=[CommandHandler('cancel', BotHandlers.cancel_report)],
    )
    
    # Add command handlers
    application.add_handler(CommandHandler('start', BotHandlers.start_command))
    application.add_handler(CommandHandler('about', BotHandlers.about_command))
    application.add_handler(CommandHandler('language', BotHandlers.language_command))
    application.add_handler(CommandHandler('check', BotHandlers.check_command))
    application.add_handler(report_conv_handler)
    application.add_handler(CommandHandler('help', BotHandlers.help_command))
    application.add_handler(CommandHandler('safety', BotHandlers.safety_command))
    application.add_handler(CommandHandler('donate', BotHandlers.donate_command))
    application.add_handler(CommandHandler('trusted_groups', BotHandlers.trusted_groups_command))
    application.add_handler(CommandHandler('trusted_admins', BotHandlers.trusted_admins_command))
    application.add_handler(CommandHandler('stats', BotHandlers.stats_command))
    
    # Add callback query handlers
    application.add_handler(CallbackQueryHandler(BotHandlers.language_callback, pattern='^lang_'))
    application.add_handler(CallbackQueryHandler(BotHandlers.menu_callback, pattern='^menu_'))
    
    # Add message handler for check command with query
    application.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND & filters.Regex(r'^(@|t\.me/|https://t\.me/)'),
        lambda update, context: BotHandlers.process_check_query(
            update, context, update.message.text, update.effective_user
        )
    ))
    
    # Start the bot
    logger.info("🤖 Bot is running...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

# ==================== RENDER COMPATIBILITY ====================
if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        logger.info("👋 Bot stopped by user")
    except Exception as e:
        logger.error(f"❌ Bot crashed: {e}")
        logger.error("Restarting in 10 seconds...")
        import time
        time.sleep(10)
        main()
