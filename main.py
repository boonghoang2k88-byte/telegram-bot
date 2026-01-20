#!/usr/bin/env python3
"""
ANTISCAMBOT - Bot Telegram chống lừa đảo Crypto/OTC
Version: 3.0.0 - Complete All-in-One
Deploy: render.com
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

# ==================== DEBUG INFO ====================
print("="*60)
print("🚀 ANTISCAMBOT STARTING...")
print("="*60)
print(f"📁 Current directory: {os.getcwd()}")
print(f"📂 Files in directory: {', '.join(os.listdir('.'))}")
print(f"🐍 Python version: {sys.version}")

# ==================== CONFIGURATION ====================
# Try to load dotenv if exists
try:
    from dotenv import load_dotenv
    if os.path.exists('.env'):
        load_dotenv()
        print("✅ Loaded .env file")
    else:
        print("⚠️ No .env file found")
except ImportError:
    print("⚠️ python-dotenv not installed, skipping")

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

# Get token with multiple fallbacks
def get_token():
    """Get bot token from multiple sources."""
    # Try environment variables
    token = os.getenv('TOKEN')
    if token:
        return token
    
    # Try Render's environment
    token = os.getenv('TELEGRAM_TOKEN') or os.getenv('BOT_TOKEN')
    if token:
        return token
    
    # Try reading from .env file directly
    try:
        if os.path.exists('.env'):
            with open('.env', 'r') as f:
                for line in f:
                    if line.strip().startswith('TOKEN='):
                        return line.split('=', 1)[1].strip()
    except:
        pass
    
    return None

TOKEN = get_token()
if not TOKEN:
    logger.error("="*60)
    logger.error("❌ ERROR: TOKEN NOT FOUND!")
    logger.error("="*60)
    logger.error("Please set TOKEN environment variable on Render:")
    logger.error("1. Go to Render Dashboard")
    logger.error("2. Select your service")
    logger.error("3. Click 'Environment'")
    logger.error("4. Add variable: TOKEN=your_bot_token_here")
    logger.error("5. Save and redeploy")
    logger.error("="*60)
    sys.exit(1)

logger.info(f"✅ Token loaded: {TOKEN[:10]}...")
print(f"✅ Token loaded: {TOKEN[:10]}...")

# ==================== DATABASE SYSTEM ====================
class Database:
    """SQLite database manager."""
    
    def __init__(self, db_path="bot_database.db"):
        self.db_path = db_path
        self.init_db()
    
    def get_connection(self):
        """Get database connection."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def init_db(self):
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
                    status TEXT DEFAULT 'confirmed',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.commit()
        
        logger.info("✅ Database initialized")
        print("✅ Database initialized")
    
    def save_report(self, report_data: Dict) -> bool:
        """Save a scam report."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Find or create scammer
                cursor.execute('''
                    SELECT id FROM scammers 
                    WHERE username = ? OR binance_id = ?
                ''', (report_data['scammer_username'], report_data.get('binance_id')))
                
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
                    
                    # Check if new reporter
                    cursor.execute('''
                        SELECT id FROM reports 
                        WHERE reporter_id = ? AND scammer_id = ?
                    ''', (report_data['reporter_id'], scammer_id))
                    
                    if not cursor.fetchone():
                        cursor.execute('''
                            UPDATE scammers 
                            SET reporter_count = reporter_count + 1
                            WHERE id = ?
                        ''', (scammer_id,))
                else:
                    # Create new scammer
                    cursor.execute('''
                        INSERT INTO scammers (
                            name, username, telegram_link, binance_id,
                            report_count, reporter_count, total_amount,
                            first_reported, last_reported
                        ) VALUES (?, ?, ?, ?, 1, 1, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                    ''', (
                        report_data['scammer_name'],
                        report_data['scammer_username'],
                        report_data['scammer_link'],
                        report_data.get('binance_id'),
                        report_data.get('amount', 0)
                    ))
                    scammer_id = cursor.lastrowid
                
                # Save report
                cursor.execute('''
                    INSERT INTO reports (
                        reporter_id, reporter_username, scammer_id,
                        scammer_name, scammer_username, scammer_link,
                        binance_id, amount, currency, status
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'confirmed')
                ''', (
                    report_data['reporter_id'],
                    report_data.get('reporter_username'),
                    scammer_id,
                    report_data['scammer_name'],
                    report_data['scammer_username'],
                    report_data['scammer_link'],
                    report_data.get('binance_id'),
                    report_data.get('amount', 0),
                    report_data.get('currency', 'USDT')
                ))
                
                # Update user
                cursor.execute('''
                    INSERT OR REPLACE INTO users 
                    (telegram_id, username, first_name, last_name, 
                     report_count, last_report_date, last_active)
                    VALUES (?, ?, ?, ?, 
                            COALESCE((SELECT report_count FROM users WHERE telegram_id = ?), 0) + 1,
                            CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                ''', (
                    report_data['reporter_id'],
                    report_data.get('reporter_username'),
                    report_data.get('first_name'),
                    report_data.get('last_name'),
                    report_data['reporter_id']
                ))
                
                conn.commit()
                return True
                
        except Exception as e:
            logger.error(f"❌ Error saving report: {e}")
            return False
    
    def search_scammer(self, query: str) -> Optional[Dict]:
        """Search for scammer."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            if query.startswith('@'):
                username = query[1:]
                cursor.execute('SELECT * FROM scammers WHERE username = ?', (username,))
            elif 't.me/' in query:
                username = query.split('t.me/')[-1].split('/')[0]
                cursor.execute('SELECT * FROM scammers WHERE username = ?', (username,))
            elif query.isdigit():
                cursor.execute('SELECT * FROM scammers WHERE binance_id = ?', (query,))
            else:
                cursor.execute('SELECT * FROM scammers WHERE name LIKE ? OR username LIKE ?', 
                             (f'%{query}%', f'%{query}%'))
            
            row = cursor.fetchone()
            if row:
                # Get reporter count
                cursor.execute('''
                    SELECT COUNT(DISTINCT reporter_id) as unique_reporters,
                           SUM(amount) as total_amount
                    FROM reports WHERE scammer_id = ?
                ''', (row['id'],))
                stats = cursor.fetchone()
                
                return {
                    'id': row['id'],
                    'name': row['name'],
                    'username': row['username'],
                    'telegram_link': row['telegram_link'],
                    'binance_id': row['binance_id'],
                    'report_count': row['report_count'],
                    'reporter_count': stats['unique_reporters'] if stats else 0,
                    'total_amount': stats['total_amount'] if stats else 0
                }
            
            return None
    
    def get_user_reports_today(self, user_id: int) -> int:
        """Get user's reports today."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT COUNT(*) as count FROM reports 
                WHERE reporter_id = ? 
                AND DATE(created_at) = DATE('now')
            ''', (user_id,))
            return cursor.fetchone()['count']
    
    def get_stats(self) -> Dict:
        """Get bot statistics."""
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
            
            return {
                'total_reports': total_reports,
                'unique_reporters': unique_reporters,
                'total_scammers': total_scammers,
                'total_amount': total_amount
            }
    
    def get_top_scammers(self, limit: int = 5) -> List[Dict]:
        """Get top scammers."""
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
            
            return [
                {
                    'username': row['username'],
                    'report_count': row['report_count'],
                    'reporter_count': row['reporter_count'],
                    'total_amount': row['total_amount'] or 0
                }
                for row in cursor.fetchall()
            ]

db = Database()

# ==================== LANGUAGE SYSTEM ====================
class LanguageSystem:
    """Multi-language support."""
    
    TRANSLATIONS = {
        'en': {
            'welcome': "Hi {}, welcome to **BOT_TELE**! 🤖\n\nI'm a community-driven bot for checking and reporting scams in Crypto, OTC, and intermediary transactions.",
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
            
            # About
            'about_title': 'About BOT_TELE',
            'strength_1': '• Data built from actual community contributions',
            'strength_2': '• Each scam object shows: Report count & Reporter count',
            'strength_3': '• More reporters → Higher warning reliability',
            'strength_4': '• Helps users assess risk before trading',
            
            # Check
            'check_instruction': 'Send scammer\'s Telegram @username, link, or Binance ID:',
            'scammer_not_found': '✅ No reports found. Stay cautious!',
            'warning_title': '🚨 TRADING WARNING',
            'target': 'Target',
            'telegram_link': 'Telegram Link',
            'binance_id': 'Binance ID',
            'report_count': 'Report count',
            'reporter_count': 'Reporter count',
            'total_amount': 'Total amount',
            'do_not_trade': 'DO NOT TRADE',
            
            # Report
            'report_instruction': '🚨 **REPORT PROCESS** (max 3/day)\n\nYou will provide:\n1. Scammer\'s display name\n2. Telegram username\n3. Telegram link\n4. Binance ID/wallet\n5. Amount (if known)',
            'ask_name': '📝 Step 1/5: Scammer\'s DISPLAY NAME:',
            'ask_username': '📝 Step 2/5: Telegram USERNAME (with @):',
            'ask_link': '📝 Step 3/5: Telegram LINK:',
            'ask_id': '📝 Step 4/5: Binance ID / Crypto wallet:',
            'ask_amount': '📝 Step 5/5: Scam amount (USDT):',
            'report_success': '✅ **REPORT SUBMITTED!**\n\nThank you for helping the community!',
            'report_cancelled': '❌ Report cancelled.',
            'report_limit': '⚠️ **LIMIT REACHED**\n\nMax 3 reports per 24 hours.',
            
            # Stats
            'stats_title': '📊 SCAM STATISTICS',
            'total_reports': 'Total reports',
            'unique_reporters': 'Unique reporters',
            'total_scammers': 'Total scammers',
            'top_scammers': 'Top Scammers',
            
            # Donate
            'donate_title': '💝 SUPPORT DEVELOPMENT',
            'donate_message': '''Binance ID: 154265504

Every donation helps maintain servers,
upgrade security and serve the community.

Thank you sincerely!''',
        },
        
        'vi': {
            'welcome': "Chào {}, chào mừng đến với **BOT_TELE**! 🤖\n\nTôi là bot kiểm tra và báo cáo lừa đảo Crypto, OTC và trung gian.",
            'menu_language': '🌐 Ngôn ngữ',
            'menu_check': '🔍 Kiểm tra lừa đảo',
            'menu_report': '🚨 Báo cáo scam',
            'menu_help': '❓ Hướng dẫn',
            'menu_safety': '⚠️ An toàn giao dịch',
            'menu_donate': '💝 Ủng hộ',
            'menu_groups': '👥 Group uy tín',
            'menu_admins': '🛡 Admin uy tín',
            'menu_stats': '📊 Thống kê',
            'menu_about': 'ℹ️ Giới thiệu',
            
            # About
            'about_title': 'Giới thiệu BOT_TELE',
            'strength_1': '• Dữ liệu từ đóng góp cộng đồng',
            'strength_2': '• Hiển thị số lượt báo cáo & số người báo cáo',
            'strength_3': '• Càng nhiều người báo cáo → càng đáng tin',
            'strength_4': '• Giúp đánh giá rủi ro trước giao dịch',
            
            # Check
            'check_instruction': 'Gửi @username, link Telegram, hoặc ID Binance của scammer:',
            'scammer_not_found': '✅ Không tìm thấy báo cáo. Vẫn cần thận trọng!',
            'warning_title': '🚨 CẢNH BÁO GIAO DỊCH',
            'target': 'Đối tượng',
            'telegram_link': 'Link Telegram',
            'binance_id': 'ID Binance',
            'report_count': 'Số lượt báo cáo',
            'reporter_count': 'Số người báo cáo',
            'total_amount': 'Tổng số tiền',
            'do_not_trade': 'KHÔNG GIAO DỊCH',
            
            # Report
            'report_instruction': '🚨 **QUY TRÌNH BÁO CÁO** (tối đa 3/ngày)\n\nBạn cung cấp:\n1. Tên hiển thị\n2. Username Telegram\n3. Link Telegram\n4. ID Binance/ví\n5. Số tiền (nếu biết)',
            'ask_name': '📝 Bước 1/5: Tên hiển thị của scammer:',
            'ask_username': '📝 Bước 2/5: USERNAME Telegram (có @):',
            'ask_link': '📝 Bước 3/5: LINK Telegram:',
            'ask_id': '📝 Bước 4/5: ID Binance / Ví crypto:',
            'ask_amount': '📝 Bước 5/5: Số tiền bị lừa (USDT):',
            'report_success': '✅ **ĐÃ BÁO CÁO!**\n\nCảm ơn bạn đã giúp cộng đồng!',
            'report_cancelled': '❌ Đã hủy báo cáo.',
            'report_limit': '⚠️ **ĐẠT GIỚI HẠN**\n\nTối đa 3 báo cáo/24h.',
            
            # Stats
            'stats_title': '📊 THỐNG KÊ SCAM',
            'total_reports': 'Tổng báo cáo',
            'unique_reporters': 'Số người báo cáo',
            'total_scammers': 'Tổng scammer',
            'top_scammers': 'Scammer hàng đầu',
            
            # Donate
            'donate_title': '💝 ỦNG HỘ PHÁT TRIỂN',
            'donate_message': '''Binance ID: 154265504

Mọi ủng hộ giúp duy trì máy chủ,
nâng cấp bảo mật và phục vụ cộng đồng.

Xin chân thành cảm ơn!''',
        }
    }
    
    @staticmethod
    def get_text(user_id: int, key: str) -> str:
        """Get translation for user."""
        # Simple language detection - for now use English
        # In real app, store user language preference
        return LanguageSystem.TRANSLATIONS['en'].get(key, key)

lang = LanguageSystem()

# ==================== TELEGRAM BOT ====================
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
    print("✅ telegram library imported")
except ImportError as e:
    print(f"❌ Error importing telegram: {e}")
    print("Please install: pip install python-telegram-bot")
    sys.exit(1)

# Conversation states
NAME, USERNAME, LINK, ID, AMOUNT = range(5)

class AntiScamBot:
    """Main bot class."""
    
    def __init__(self):
        self.application = None
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command."""
        user = update.effective_user
        text = f"""Hi {user.first_name}! 👋

🤖 **AntiScamBot** - Community Scam Reporting System

I help you:
✅ Check if someone has been reported as scammer
✅ Report new scammers to protect others
✅ Get safety tips for Crypto/OTC trading

**Community-driven**: All reports come from users like you.
**No admin approval**: Reports are recorded immediately.

Use the commands below or click menu:"""
        
        keyboard = [
            [InlineKeyboardButton("🔍 Check Scammer", callback_data='check')],
            [InlineKeyboardButton("🚨 Report Scammer", callback_data='report')],
            [InlineKeyboardButton("📊 Statistics", callback_data='stats')],
            [InlineKeyboardButton("⚠️ Safety Tips", callback_data='safety')],
            [InlineKeyboardButton("👥 Trusted Groups", callback_data='groups')],
            [InlineKeyboardButton("💝 Donate", callback_data='donate')],
            [InlineKeyboardButton("❓ Help", callback_data='help')],
            [InlineKeyboardButton("ℹ️ About", callback_data='about')],
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')
    
    async def about_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /about command."""
        stats = db.get_stats()
        
        text = f"""**🤖 AntiScamBot**

**Mission**: Protect the community from Crypto/OTC scams through collective reporting.

**How it works**:
1. Users report scammers (Telegram, Binance ID, etc.)
2. Reports are counted and displayed
3. Others can check before trading
4. More reports = higher reliability warning

**Community Statistics**:
• 📊 Total Reports: **{stats['total_reports']}**
• 👥 Unique Reporters: **{stats['unique_reporters']}**
• 🎭 Total Scammers: **{stats['total_scammers']}**
• 💰 Total Amount: **{stats['total_amount']} USDT**

**⚠️ Disclaimer**: This bot provides risk indicators based on community reports, not legal conclusions.

**✅ Features**:
• No admin approval needed
• 3 reports/day/user limit
• Real-time database
• Multiple identifiers (Telegram, Binance, etc.)
• Community-driven reliability score"""
        
        await update.message.reply_text(text, parse_mode='Markdown')
    
    async def check_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /check command."""
        text = """🔍 **CHECK SCAMMER**

Send me:
• Telegram @username
• Telegram link (t.me/...)
• Binance ID
• Or any identifier

I'll search our database for reports.

Example:
`@scammer123`
`t.me/scammer123`
`123456789` (Binance ID)"""
        
        await update.message.reply_text(text, parse_mode='Markdown')
    
    async def process_check(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Process check query."""
        query = update.message.text.strip()
        scammer = db.search_scammer(query)
        
        if scammer:
            # Calculate risk
            risk = "🔴 HIGH" if scammer['report_count'] > 5 else "🟡 MEDIUM" if scammer['report_count'] > 2 else "🟢 LOW"
            
            text = f"""🚨 **SCAMMER FOUND**

**Target**: {scammer['username']}
**Telegram**: {scammer['telegram_link']}
**Binance ID**: {scammer['binance_id'] or 'N/A'}

**📊 Community Reports**:
• Reports: **{scammer['report_count']}**
• Unique Reporters: **{scammer['reporter_count']}**
• Total Amount: **{scammer['total_amount']} USDT**

**⚠️ Risk Level**: {risk}
**📢 Recommendation**: {"DO NOT TRADE" if risk == "🔴 HIGH" else "EXTREME CAUTION" if risk == "🟡 MEDIUM" else "Verify carefully"}

This user has been reported by multiple community members."""
        else:
            text = """✅ **NO REPORTS FOUND**

No community reports found for this user.

**⚠️ Still be cautious**:
• Verify identity thoroughly
• Check join date, profile photos
• Start with small amounts
• Use escrow if possible"""
        
        await update.message.reply_text(text, parse_mode='Markdown')
    
    async def report_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Start report process."""
        user = update.effective_user
        
        # Check rate limit
        if db.get_user_reports_today(user.id) >= 3:
            await update.message.reply_text("""⚠️ **REPORT LIMIT REACHED**

You've reached the limit of 3 reports per 24 hours.

Please try again tomorrow or ask a friend to report.

This limit prevents spam and ensures report quality.""")
            return ConversationHandler.END
        
        text = """🚨 **REPORT A SCAMMER**

I'll guide you through 5 simple steps.

**Step 1/5**: What is the scammer's Telegram DISPLAY NAME?
(Example: "John Crypto Trader")"""
        
        await update.message.reply_text(text)
        return NAME
    
    async def report_name(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Get scammer name."""
        context.user_data['name'] = update.message.text
        
        text = """**Step 2/5**: What is the scammer's Telegram USERNAME?
(Example: "@scammer123", must include @)"""
        
        await update.message.reply_text(text, parse_mode='Markdown')
        return USERNAME
    
    async def report_username(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Get scammer username."""
        username = update.message.text.strip()
        if not username.startswith('@'):
            username = '@' + username
        context.user_data['username'] = username
        
        text = """**Step 3/5**: What is the scammer's Telegram LINK?
(Example: "https://t.me/scammer123" or "t.me/scammer123")"""
        
        await update.message.reply_text(text, parse_mode='Markdown')
        return LINK
    
    async def report_link(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Get scammer link."""
        link = update.message.text.strip()
        if not link.startswith('http'):
            link = f'https://t.me/{link.replace("@", "")}'
        context.user_data['link'] = link
        
        text = """**Step 4/5**: What is the scammer's Binance ID or Crypto Wallet?
(Example: "123456789" or "0x742d35Cc6634C0532925a3b844Bc9e")"""
        
        await update.message.reply_text(text, parse_mode='Markdown')
        return ID
    
    async def report_id(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Get scammer ID."""
        context.user_data['binance_id'] = update.message.text
        
        text = """**Step 5/5**: How much was scammed? (in USDT)
(Example: "100" or "0" if unknown)"""
        
        await update.message.reply_text(text, parse_mode='Markdown')
        return AMOUNT
    
    async def report_amount(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Get scam amount and confirm."""
        try:
            amount = float(re.findall(r'\d+\.?\d*', update.message.text)[0])
        except:
            amount = 0
        
        context.user_data['amount'] = amount
        user = update.effective_user
        
        # Show summary
        text = f"""📋 **REPORT SUMMARY**

✅ Please confirm this information:

**Scammer Details**:
• Name: {context.user_data['name']}
• Username: {context.user_data['username']}
• Link: {context.user_data['link']}
• Binance/Wallet: {context.user_data['binance_id']}
• Amount: {amount} USDT

**Your Info**:
• Reporter: {user.first_name} (@{user.username or 'N/A'})
• Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}
• Reports today: {db.get_user_reports_today(user.id)}/3

**⚠️ Important**: False reports harm the community. Only submit if you're certain."""
        
        keyboard = [
            [
                InlineKeyboardButton("✅ CONFIRM & SUBMIT", callback_data='confirm_report'),
                InlineKeyboardButton("❌ CANCEL", callback_data='cancel_report')
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')
        return ConversationHandler.END
    
    async def report_confirm(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle report confirmation."""
        query = update.callback_query
        await query.answer()
        
        user = query.from_user
        
        if query.data == 'confirm_report':
            # Save report
            report_data = {
                'reporter_id': user.id,
                'reporter_username': user.username,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'scammer_name': context.user_data['name'],
                'scammer_username': context.user_data['username'],
                'scammer_link': context.user_data['link'],
                'binance_id': context.user_data['binance_id'],
                'amount': context.user_data.get('amount', 0)
            }
            
            success = db.save_report(report_data)
            
            if success:
                text = """✅ **REPORT SUBMITTED SUCCESSFULLY!**

Thank you for protecting the community! Your report has been recorded and will help others avoid this scammer.

**What happens next**:
• Your report counts toward this scammer's warning level
• Others checking will see your report
• More reports = higher warning reliability

**You have contributed to making Crypto safer!** 🛡️"""
            else:
                text = "❌ Error saving report. Please try again."
        else:
            text = """❌ **REPORT CANCELLED**

No report was submitted.

Remember: Reporting scammers helps protect everyone in the community."""
        
        # Clear conversation data
        context.user_data.clear()
        
        await query.edit_message_text(text, parse_mode='Markdown')
    
    async def cancel_report(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Cancel report process."""
        context.user_data.clear()
        await update.message.reply_text("❌ Report process cancelled.")
        return ConversationHandler.END
    
    async def stats_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /stats command."""
        stats = db.get_stats()
        top_scammers = db.get_top_scammers(5)
        
        text = f"""📊 **COMMUNITY STATISTICS**

**Overall**:
• 📈 Total Reports: **{stats['total_reports']}**
• 👥 Unique Reporters: **{stats['unique_reporters']}**
• 🎭 Total Scammers: **{stats['total_scammers']}**
• 💰 Total Amount: **{stats['total_amount']} USDT**

**🏆 Top 5 Most Reported Scammers**:"""
        
        for i, scammer in enumerate(top_scammers, 1):
            text += f"\n{i}. **{scammer['username']}**"
            text += f"\n   📊 Reports: {scammer['report_count']}"
            text += f"\n   👥 Reporters: {scammer['reporter_count']}"
            text += f"\n   💰 Amount: {scammer['total_amount']} USDT"
        
        text += "\n\n**⚠️ Note**: Statistics update in real-time from community reports."
        
        await update.message.reply_text(text, parse_mode='Markdown')
    
    async def safety_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /safety command."""
        text = """⚠️ **CRYPTO TRADING SAFETY GUIDE**

**1. VERIFY IDENTITY**:
• Check Telegram join date (older = better)
• Verify Binance ID matches profile
• Ask for video call or social proof
• Check profile photos (real people have multiple)

**2. SAFE PAYMENT METHODS**:
✅ Use Binance P2P escrow
✅ Use trusted OTC desks with reputation
✅ Small test transaction first
❌ Never send directly to unknown wallets
❌ Avoid "too good to be true" rates

**3. RED FLAGS**:
• Urgency pressure ("quick quick!")
• Requests for upfront "fees"
• Different contact methods mid-deal
• Refuses video/voice verification
• New account with no history

**4. TRUSTED PLATFORMS**:
• Binance P2P (official groups)
• LocalBitcoins (with escrow)
• Reputable OTC desks with reviews
• Community-verified groups

**5. IF SCAMMED**:
1. Report immediately to this bot
2. Warn community groups
3. Report to Binance/Exchange
4. Gather evidence (screenshots)

**Remember**: If it feels wrong, it probably is!"""
        
        await update.message.reply_text(text, parse_mode='Markdown')
    
    async def donate_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /donate command."""
        text = """💝 **SUPPORT ANTISCAMBOT**

**Binance ID**: `154265504`

Your donation helps:
• 🖥️ Maintain servers 24/7
• 🔒 Upgrade security systems
• 🚀 Add new features
• 📢 Community outreach

**Transparency Promise**:
Every donation is used ONLY for:
1. Render hosting costs
2. Database maintenance
3. Development time
4. Security audits

**Thank you for supporting a safer Crypto community!** 🙏

**Note**: This is entirely optional. The bot will always remain free for the community."""
        
        await update.message.reply_text(text, parse_mode='Markdown')
    
    async def trusted_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /trusted command."""
        text = """👥 **TRUSTED COMMUNITY GROUPS**

**⚠️ DISCLAIMER**: Even in trusted groups, always verify identities!

**Official Groups**:
• Binance P2P Official: @binancep2p
• Binance P2P Vietnam: @binancep2pvn
• Crypto Trading Vietnam: @cryptotradingvietnam

**Community Groups**:
• OTC Crypto Vietnam: @otccryptovietnam
• Global Crypto Trading: @globalcrypto

**Trusted Admins/Mediators**:
• Admin OTC VN: @otcadmin_vn
• Binance Support VN: @binancesupport_vn

**How to verify admins**:
1. Check if they're listed in group description
2. Look for verification badge
3. Ask other members
4. Start with small test transaction

**Remember**: No group is 100% safe. Always do your own due diligence!"""
        
        await update.message.reply_text(text, parse_mode='Markdown', disable_web_page_preview=True)
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command."""
        text = """❓ **ANTISCAMBOT HELP GUIDE**

**AVAILABLE COMMANDS**:
/start - Start bot & main menu
/check - Check if someone is reported
/report - Report a new scammer
/stats - View community statistics
/safety - Crypto trading safety tips
/trusted - Trusted groups & admins
/donate - Support bot development
/about - About this bot
/help - This help message

**HOW TO USE**:
1. **Check scammer**: Use /check then send username/link/ID
2. **Report scammer**: Use /report and follow 5 steps
3. **View stats**: See community reporting statistics

**REPORTING RULES**:
• ✅ Max 3 reports per user per 24 hours
• ✅ Reports are anonymous to community
• ✅ False reports harm the system
• ✅ Provide accurate information

**NEED HELP?** The bot is community-driven. For technical issues, check the GitHub repository.

**⚠️ IMPORTANT**: This bot provides risk indicators only, not legal advice."""
        
        await update.message.reply_text(text, parse_mode='Markdown')
    
    async def callback_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle callback queries."""
        query = update.callback_query
        await query.answer()
        
        user = query.from_user
        action = query.data
        
        # Map actions to handlers
        handlers = {
            'check': self.check_command,
            'report': self.report_command,
            'stats': self.stats_command,
            'safety': self.safety_command,
            'donate': self.donate_command,
            'groups': self.trusted_command,
            'help': self.help_command,
            'about': self.about_command,
            'confirm_report': self.report_confirm,
            'cancel_report': lambda u, c: query.edit_message_text("❌ Report cancelled.")
        }
        
        if action in handlers:
            if action in ['confirm_report', 'cancel_report']:
                await handlers[action](query, context)
            else:
                # Create mock update for command handlers
                mock_update = Update(
                    update.update_id,
                    message=query.message
                )
                await handlers[action](mock_update, context)
    
    def setup_handlers(self):
        """Setup all bot handlers."""
        # Report conversation
        report_conv = ConversationHandler(
            entry_points=[CommandHandler('report', self.report_command)],
            states={
                NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.report_name)],
                USERNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.report_username)],
                LINK: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.report_link)],
                ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.report_id)],
                AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.report_amount)],
            },
            fallbacks=[CommandHandler('cancel', self.cancel_report)],
        )
        
        # Add all handlers
        self.application.add_handler(CommandHandler('start', self.start_command))
        self.application.add_handler(CommandHandler('about', self.about_command))
        self.application.add_handler(CommandHandler('check', self.check_command))
        self.application.add_handler(report_conv)
        self.application.add_handler(CommandHandler('stats', self.stats_command))
        self.application.add_handler(CommandHandler('safety', self.safety_command))
        self.application.add_handler(CommandHandler('donate', self.donate_command))
        self.application.add_handler(CommandHandler('trusted', self.trusted_command))
        self.application.add_handler(CommandHandler('help', self.help_command))
        
        # Callback handler
        self.application.add_handler(CallbackQueryHandler(self.callback_handler))
        
        # Check message handler
        self.application.add_handler(MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            self.process_check
        ))
    
    def run(self):
        """Start the bot."""
        print("🤖 Creating application...")
        self.application = Application.builder().token(TOKEN).build()
        
        print("🔧 Setting up handlers...")
        self.setup_handlers()
        
        print("🚀 Starting bot...")
        print("="*60)
        print("✅ AntiScamBot is now running!")
        print(f"✅ Token: {TOKEN[:10]}...")
        print(f"✅ Database: bot_database.db")
        print(f"✅ Features: Check, Report, Stats, Safety, Trusted groups")
        print(f"✅ Rate limit: 3 reports/day/user")
        print(f"✅ Community-driven: No admin approval")
        print("="*60)
        print("📱 Go to Telegram and start using the bot!")
        print("💡 Commands: /start, /check, /report, /stats, /help")
        print("="*60)
        
        self.application.run_polling(allowed_updates=['message', 'callback_query'])

# ==================== MAIN EXECUTION ====================
def main():
    """Main entry point."""
    try:
        bot = AntiScamBot()
        bot.run()
    except Exception as e:
        logger.error(f"❌ Bot crashed: {e}")
        print(f"❌ Bot crashed: {e}")
        print("🔄 Restarting in 10 seconds...")
        import time
        time.sleep(10)
        main()

if __name__ == '__main__':
    main()
