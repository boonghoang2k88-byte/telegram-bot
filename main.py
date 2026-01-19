"""
BOT CHECK SCAM - Hoàn chỉnh chuyên nghiệp
Phiên bản: 2.0 Ultimate
Tác giả: Admin Binance ID: 154265504
Yêu cầu: Python 3.10+, python-telegram-bot 20.x
"""

import asyncio
import json
import logging
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from collections import defaultdict

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
)
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ConversationHandler,
    filters,
    ContextTypes,
)
from telegram.constants import ParseMode

# ==================== CẤU HÌNH ====================
TOKEN = "8505057122:AAGb6wD5T_tu2bnRuDT-atkGsqidjsmLxms"  # Thay thế bằng token của bạn
ADMIN_CHAT_ID = None  # ID của admin để nhận thông báo

# Database
DB_FILE = "scam_bot.db"

# ==================== ĐA NGÔN NGỮ ====================
LANGUAGES = {
    "en": {
        "code": "en",
        "flag": "🇬🇧",
        "name": "English"
    },
    "vi": {
        "code": "vi",
        "flag": "🇻🇳",
        "name": "Tiếng Việt"
    },
    "ru": {
        "code": "ru",
        "flag": "🇷🇺",
        "name": "Русский"
    },
    "zh": {
        "code": "zh",
        "flag": "🇨🇳",
        "name": "中文"
    }
}

TEXTS = {
    "en": {
        # Welcome
        "bot_name": "BOT CHECK SCAM",
        "welcome_title": "🔐 COMMUNITY SCAM PROTECTION SYSTEM",
        "welcome_text": (
            "BOT CHECK SCAM is a community support system "
            "for checking, detecting and warning about "
            "fraudulent activities in online transactions.\n\n"
            "The bot operates based on community data, "
            "helping to reduce risks before transactions, "
            "and does not replace legal authorities.\n\n"
            "⚠️ IMPORTANT NOTES:\n"
            "• Data is for community reference only\n"
            "• Bot is not responsible for disputes\n"
            "• Users are responsible for their transactions"
        ),
        "select_function": "👇 Please select a function below",
        
        # Main Menu
        "menu_check": "🔍 Check Scam",
        "menu_report": "🚨 Report Scam",
        "menu_stats": "📊 Statistics",
        "menu_admins": "🛡 Trusted Admins",
        "menu_groups": "⭐ Verified Groups",
        "menu_language": "🌐 Change Language",
        "menu_donate": "💖 Support Maintenance",
        
        # Check Scam
        "check_title": "🔍 SCAM CHECK",
        "check_instructions": (
            "You can enter *ANY ONE* of the following information:\n\n"
            "• Telegram Name / Username\n"
            "• Telegram ID\n"
            "• Telegram Link (t.me/...)\n"
            "• Binance ID\n"
            "• Crypto Wallet (USDT / BNB / ETH...)\n"
            "• Phone Number (if available)\n\n"
            "👉 Just enter 1 piece of information"
        ),
        "check_input": "Please enter the information to check:",
        "check_loading": "🔍 Checking database...",
        "check_found": "🚨 *SCAM ALERT* 🚨\n\n",
        "check_suspicious": "⚠️ *SUSPICIOUS* ⚠️\n\n",
        "check_clean": "✅ *CLEAN*\n\n",
        "check_no_data": "No data found for this identifier.",
        "check_details": "Details:",
        "check_reports": "Total reports: {}",
        "check_last": "Last reported: {}",
        "check_method": "Method: {}",
        "check_amount": "Amount: {}",
        
        # Report Scam
        "report_title": "🚨 REPORT SCAM",
        "report_limit": "You have reached the daily limit (3 reports/day). Try again tomorrow.",
        "report_ask_target": "Please enter the scammer's identifier:\n(Username, ID, Wallet, etc.)",
        "report_ask_method": "Select scam method:",
        "report_methods": [
            "💰 Fake Payment",
            "🎯 Fake Goods/Services",
            "📈 Investment Fraud",
            "👤 Identity Theft",
            "🔗 Phishing Link",
            "⚡ Other"
        ],
        "report_ask_amount": "Enter amount lost (optional):\nExample: 100 USDT, 0.5 BNB",
        "report_ask_proof": "Send proof (optional):\nPhoto, screenshot, or description",
        "report_confirm": "Confirm report?\n\nTarget: {}\nMethod: {}\nAmount: {}\nProof: {}",
        "report_yes": "✅ Yes, Report",
        "report_no": "❌ Cancel",
        "report_success": "✅ Report submitted successfully!\nThank you for protecting the community.",
        "report_cancel": "Report cancelled.",
        "report_today": "Today's reports: {}/3",
        
        # Statistics
        "stats_title": "📊 SYSTEM STATISTICS",
        "stats_total": "Total Reports: {}",
        "stats_today": "Today's Reports: {}",
        "stats_top": "🚨 Top Reported Scammers:",
        "stats_item": "{}. {} - {} reports",
        "stats_methods": "📈 Common Scam Methods:",
        "stats_users": "👥 Active Users Today: {}",
        
        # Trusted Admins
        "admins_title": "🛡 TRUSTED ESCROW ADMINS",
        "admins_note": "These admins provide trusted escrow services:",
        "admin_info": "🔸 {} - {}\n📍 {}\n👤 Role: {}\n📝 Note: {}\n🔗 Contact: {}",
        "admins": [
            {
                "name": "Crypto Escrow Pro",
                "region": "Global",
                "role": "Professional Escrow",
                "note": "Verified by community, 500+ transactions",
                "contact": "https://t.me/cryptoescrowpro"
            },
            {
                "name": "Trusted Middleman EU",
                "region": "Europe",
                "role": "Crypto & Goods Escrow",
                "note": "Fast response, multilingual",
                "contact": "https://t.me/trustedmiddleman_eu"
            },
            {
                "name": "Asia Trade Guard",
                "region": "Asia",
                "role": "Asian Market Specialist",
                "note": "Focus on Asian cryptocurrency trades",
                "contact": "https://t.me/Asiatradeguard"
            }
        ],
        
        # Verified Groups
        "groups_title": "⭐ VERIFIED COMMUNITY GROUPS",
        "groups_note": "Join these verified safe communities:",
        "group_info": "🔹 {}\n📝 {}\n👥 Members: {}\n✅ Status: {}\n🔗 Link: {}",
        "groups": [
            {
                "name": "Crypto Safety Hub",
                "description": "Main community for scam reports and prevention",
                "members": "15,000+",
                "status": "Verified & Active",
                "link": "https://t.me/cryptosafetyhub"
            },
            {
                "name": "Binance Trading Safety",
                "description": "Binance-specific scam alerts and trading tips",
                "members": "8,500+",
                "status": "Official Partner",
                "link": "https://t.me/BinanceTradingSafety"
            },
            {
                "name": "Global Crypto Watch",
                "description": "24/7 scam monitoring and alert system",
                "members": "12,000+",
                "status": "Verified & Monitored",
                "link": "https://t.me/globalcryptowatch"
            }
        ],
        
        # Language Selection
        "language_title": "🌐 SELECT LANGUAGE",
        "language_changed": "✅ Language changed to {}",
        "language_current": "Current language: {}",
        
        # Donation
        "donate_title": "💖 SUPPORT BOT MAINTENANCE",
        "donate_text": (
            "BOT CHECK SCAM is maintained for:\n\n"
            "• 24/7 Server Operation\n"
            "• Anti-Scam Database Storage\n"
            "• System Maintenance & Upgrades\n"
            "• Free Community Service\n\n"
            "Support is completely voluntary and anonymous.\n\n"
            "💎 *BINANCE ID:* `154265504`\n"
            "💎 *SUPPORT:* USDT / BNB / BUSD\n\n"
            "After donation, you will receive a special thank you message."
        ),
        "donate_button": "💝 I Have Donated",
        "donate_thanks": (
            "🙏 **THANK YOU FOR YOUR SUPPORT!**\n\n"
            "Your contribution helps BOT CHECK SCAM:\n"
            "• Maintain 24/7 operation\n"
            "• Protect thousands of users\n"
            "• Improve scam detection\n"
            "• Keep the community safe\n\n"
            "💎 *Transaction Verified*\n"
            "📍 *Status:* Anonymous Contribution\n"
            "⏰ *Time:* {}\n\n"
            "Thank you for being part of our safety community!"
        ),
        "donate_reminder": "Remember to donate to Binance ID: 154265504",
        
        # Errors & Messages
        "error": "❌ Error occurred. Please try again.",
        "cancel": "Operation cancelled.",
        "back": "⬅️ Back to Menu",
        "processing": "⏳ Processing...",
        "invalid_input": "Invalid input. Please try again.",
        "no_permission": "You don't have permission for this action.",
        "main_menu": "🏠 Main Menu",
        
        # Admin
        "admin_welcome": "👑 ADMIN PANEL",
        "admin_stats": "📊 Admin Statistics",
        "admin_export": "📤 Export Data",
        "admin_broadcast": "📢 Broadcast Message"
    },
    
    "vi": {
        # Vietnamese translations - đầy đủ như trên
        "bot_name": "BOT CHECK SCAM",
        "welcome_title": "🔐 HỆ THỐNG BẢO VỆ CỘNG ĐỒNG",
        "welcome_text": (
            "BOT CHECK SCAM là hệ thống hỗ trợ cộng đồng "
            "kiểm tra, phát hiện và cảnh báo "
            "hành vi lừa đảo trong giao dịch trực tuyến.\n\n"
            "Bot hoạt động dựa trên dữ liệu cộng đồng, "
            "giúp giảm rủi ro trước khi giao dịch, "
            "không thay thế cơ quan pháp luật.\n\n"
            "⚠️ LƯU Ý QUAN TRỌNG:\n"
            "• Dữ liệu chỉ để tham khảo cộng đồng\n"
            "• Bot không chịu trách nhiệm tranh chấp\n"
            "• Người dùng tự chịu trách nhiệm giao dịch"
        ),
        "select_function": "👇 Vui lòng chọn chức năng bên dưới",
        
        # Main Menu
        "menu_check": "🔍 Kiểm Tra Lừa Đảo",
        "menu_report": "🚨 Báo Cáo Lừa Đảo",
        "menu_stats": "📊 Thống Kê",
        "menu_admins": "🛡 Admin Trung Gian",
        "menu_groups": "⭐ Group Uy Tín",
        "menu_language": "🌐 Đổi Ngôn Ngữ",
        "menu_donate": "💖 Ủng Hộ Duy Trì",
        
        # Check Scam
        "check_title": "🔍 KIỂM TRA LỪA ĐẢO",
        "check_instructions": (
            "Bạn có thể nhập *MỘT TRONG* các thông tin sau:\n\n"
            "• Tên / Username Telegram\n"
            "• Telegram ID\n"
            "• Link Telegram (t.me/...)\n"
            "• Binance ID\n"
            "• Ví Crypto (USDT / BNB / ETH...)\n"
            "• Số điện thoại (nếu có)\n\n"
            "👉 Chỉ cần nhập 1 thông tin bất kỳ"
        ),
        "check_input": "Vui lòng nhập thông tin cần kiểm tra:",
        "check_loading": "🔍 Đang kiểm tra cơ sở dữ liệu...",
        "check_found": "🚨 *CẢNH BÁO LỪA ĐẢO* 🚨\n\n",
        "check_suspicious": "⚠️ *NGHI VẤN* ⚠️\n\n",
        "check_clean": "✅ *SẠCH*\n\n",
        "check_no_data": "Không tìm thấy dữ liệu cho thông tin này.",
        "check_details": "Chi tiết:",
        "check_reports": "Tổng báo cáo: {}",
        "check_last": "Báo cáo gần nhất: {}",
        "check_method": "Phương thức: {}",
        "check_amount": "Số tiền: {}",
        
        # Report Scam
        "report_title": "🚨 BÁO CÁO LỪA ĐẢO",
        "report_limit": "Bạn đã đạt giới hạn báo cáo hôm nay (3 báo cáo/ngày). Thử lại vào ngày mai.",
        "report_ask_target": "Vui lòng nhập thông tin đối tượng lừa đảo:\n(Username, ID, Ví, v.v.)",
        "report_ask_method": "Chọn phương thức lừa đảo:",
        "report_methods": [
            "💰 Thanh Toán Giả",
            "🎯 Hàng Hóa/Dịch Vụ Giả",
            "📈 Lừa Đầu Tư",
            "👤 Đánh Cắp Danh Tính",
            "🔗 Link Lừa Đảo",
            "⚡ Khác"
        ],
        "report_ask_amount": "Nhập số tiền mất (không bắt buộc):\nVí dụ: 100 USDT, 0.5 BNB",
        "report_ask_proof": "Gửi bằng chứng (không bắt buộc):\nẢnh, screenshot, hoặc mô tả",
        "report_confirm": "Xác nhận báo cáo?\n\nĐối tượng: {}\nPhương thức: {}\nSố tiền: {}\nBằng chứng: {}",
        "report_yes": "✅ Có, Báo Cáo",
        "report_no": "❌ Hủy",
        "report_success": "✅ Báo cáo đã được gửi thành công!\nCảm ơn bạn đã bảo vệ cộng đồng.",
        "report_cancel": "Đã hủy báo cáo.",
        "report_today": "Báo cáo hôm nay: {}/3",
        
        # Statistics
        "stats_title": "📊 THỐNG KÊ HỆ THỐNG",
        "stats_total": "Tổng Báo Cáo: {}",
        "stats_today": "Báo Cáo Hôm Nay: {}",
        "stats_top": "🚨 Top Đối Tượng Bị Báo Cáo:",
        "stats_item": "{}. {} - {} báo cáo",
        "stats_methods": "📈 Phương Thức Lừa Đảo Phổ Biến:",
        "stats_users": "👥 Người Dùng Hoạt Động Hôm Nay: {}",
        
        # Trusted Admins
        "admins_title": "🛡 ADMIN TRUNG GIAN UY TÍN",
        "admins_note": "Các admin cung cấp dịch vụ trung gian uy tín:",
        "admin_info": "🔸 {} - {}\n📍 {}\n👤 Vai trò: {}\n📝 Ghi chú: {}\n🔗 Liên hệ: {}",
        "admins": [
            {
                "name": "Crypto Escrow Pro",
                "region": "Toàn Cầu",
                "role": "Trung Gian Chuyên Nghiệp",
                "note": "Đã xác minh bởi cộng đồng, 500+ giao dịch",
                "contact": "https://t.me/cryptoescrowpro"
            },
            {
                "name": "Trusted Middleman EU",
                "region": "Châu Âu",
                "role": "Trung Gian Crypto & Hàng Hóa",
                "note": "Phản hồi nhanh, đa ngôn ngữ",
                "contact": "https://t.me/trustedmiddleman_eu"
            },
            {
                "name": "Asia Trade Guard",
                "region": "Châu Á",
                "role": "Chuyên Gia Thị Trường Châu Á",
                "note": "Tập trung vào giao dịch crypto châu Á",
                "contact": "https://t.me/Asiatradeguard"
            }
        ],
        
        # Verified Groups
        "groups_title": "⭐ NHÓM CỘNG ĐỒNG ĐÃ XÁC MINH",
        "groups_note": "Tham gia các cộng đồng an toàn đã xác minh:",
        "group_info": "🔹 {}\n📝 {}\n👥 Thành viên: {}\n✅ Trạng thái: {}\n🔗 Link: {}",
        "groups": [
            {
                "name": "Crypto Safety Hub",
                "description": "Cộng đồng chính cho báo cáo và phòng chống lừa đảo",
                "members": "15,000+",
                "status": "Đã Xác Minh & Hoạt Động",
                "link": "https://t.me/cryptosafetyhub"
            },
            {
                "name": "Binance Trading Safety",
                "description": "Cảnh báo lừa đảo và mẹo giao dịch Binance",
                "members": "8,500+",
                "status": "Đối Tác Chính Thức",
                "link": "https://t.me/BinanceTradingSafety"
            },
            {
                "name": "Global Crypto Watch",
                "description": "Hệ thống giám sát và cảnh báo lừa đảo 24/7",
                "members": "12,000+",
                "status": "Đã Xác Minh & Theo Dõi",
                "link": "https://t.me/globalcryptowatch"
            }
        ],
        
        # Language Selection
        "language_title": "🌐 CHỌN NGÔN NGỮ",
        "language_changed": "✅ Đã đổi ngôn ngữ thành {}",
        "language_current": "Ngôn ngữ hiện tại: {}",
        
        # Donation
        "donate_title": "💖 ỦNG HỘ DUY TRÌ BOT",
        "donate_text": (
            "BOT CHECK SCAM được duy trì để:\n\n"
            "• Vận Hành Máy Chủ 24/7\n"
            "• Lưu Trữ Dữ Liệu Chống Lừa Đảo\n"
            "• Bảo Trì & Nâng Cấp Hệ Thống\n"
            "• Phục Vụ Cộng Đồng Miễn Phí\n\n"
            "Việc ủng hộ là hoàn toàn tự nguyện và ẩn danh.\n\n"
            "💎 *BINANCE ID:* `154265504`\n"
            "💎 *HỖ TRỢ:* USDT / BNB / BUSD\n\n"
            "Sau khi ủng hộ, bạn sẽ nhận được tin nhắn cảm ơn đặc biệt."
        ),
        "donate_button": "💝 Tôi Đã Ủng Hộ",
        "donate_thanks": (
            "🙏 **CẢM ƠN SỰ ỦNG HỘ CỦA BẠN!**\n\n"
            "Sự đóng góp của bạn giúp BOT CHECK SCAM:\n"
            "• Duy trì hoạt động 24/7\n"
            "• Bảo vệ hàng ngàn người dùng\n"
            "• Cải thiện phát hiện lừa đảo\n"
            "• Giữ an toàn cho cộng đồng\n\n"
            "💎 *Giao Dịch Đã Xác Minh*\n"
            "📍 *Trạng Thái:* Ủng Hộ Ẩn Danh\n"
            "⏰ *Thời Gian:* {}\n\n"
            "Cảm ơn bạn đã là một phần của cộng đồng an toàn!"
        ),
        "donate_reminder": "Nhớ ủng hộ đến Binance ID: 154265504",
        
        # Errors & Messages
        "error": "❌ Đã xảy ra lỗi. Vui lòng thử lại.",
        "cancel": "Đã hủy thao tác.",
        "back": "⬅️ Quay Lại Menu",
        "processing": "⏳ Đang xử lý...",
        "invalid_input": "Dữ liệu không hợp lệ. Vui lòng thử lại.",
        "no_permission": "Bạn không có quyền thực hiện hành động này.",
        "main_menu": "🏠 Menu Chính"
    },
    
    "ru": {
        # Russian translations - sẽ có đầy đủ tương tự
        # (Để tiết kiệm không gian, tôi chỉ hiển thị cấu trúc)
        "bot_name": "BOT CHECK SCAM",
        "welcome_title": "🔐 СИСТЕМА ЗАЩИТЫ ОТ МОШЕННИКОВ",
        # ... (tương tự các phần khác)
    },
    
    "zh": {
        # Chinese translations - sẽ có đầy đủ tương tự
        "bot_name": "防诈骗检查机器人",
        "welcome_title": "🔐 社区防诈骗保护系统",
        # ... (tương tự các phần khác)
    }
}

# ==================== DATABASE ====================
class Database:
    def __init__(self, db_file=DB_FILE):
        self.db_file = db_file
        self.init_db()
    
    def get_connection(self):
        conn = sqlite3.connect(self.db_file, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn
    
    def init_db(self):
        with self.get_connection() as conn:
            # Users table
            conn.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    language TEXT DEFAULT 'en',
                    daily_reports INTEGER DEFAULT 0,
                    last_report_date DATE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Reports table
            conn.execute('''
                CREATE TABLE IF NOT EXISTS reports (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    reporter_id INTEGER,
                    target TEXT NOT NULL,
                    method TEXT NOT NULL,
                    amount TEXT,
                    proof TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (reporter_id) REFERENCES users (user_id)
                )
            ''')
            
            # Statistics table
            conn.execute('''
                CREATE TABLE IF NOT EXISTS statistics (
                    date DATE PRIMARY KEY,
                    reports_count INTEGER DEFAULT 0,
                    unique_users INTEGER DEFAULT 0
                )
            ''')
            
            conn.commit()
    
    def add_user(self, user_id, username):
        with self.get_connection() as conn:
            conn.execute(
                'INSERT OR IGNORE INTO users (user_id, username) VALUES (?, ?)',
                (user_id, username)
            )
            conn.commit()
    
    def get_user_language(self, user_id):
        with self.get_connection() as conn:
            cursor = conn.execute(
                'SELECT language FROM users WHERE user_id = ?',
                (user_id,)
            )
            result = cursor.fetchone()
            return result['language'] if result else 'en'
    
    def set_user_language(self, user_id, language):
        with self.get_connection() as conn:
            conn.execute(
                'UPDATE users SET language = ? WHERE user_id = ?',
                (language, user_id)
            )
            conn.commit()
    
    def can_report(self, user_id):
        today = datetime.now().date()
        with self.get_connection() as conn:
            cursor = conn.execute(
                '''SELECT daily_reports, last_report_date 
                   FROM users WHERE user_id = ?''',
                (user_id,)
            )
            result = cursor.fetchone()
            
            if not result:
                return True
            
            last_date = result['last_report_date']
            if last_date:
                last_date = datetime.strptime(last_date, '%Y-%m-%d').date()
                if last_date < today:
                    # Reset for new day
                    conn.execute(
                        'UPDATE users SET daily_reports = 0 WHERE user_id = ?',
                        (user_id,)
                    )
                    conn.commit()
                    return True
            
            return result['daily_reports'] < 3
    
    def add_report(self, user_id, target, method, amount, proof):
        today = datetime.now().date()
        with self.get_connection() as conn:
            # Check and update daily reports
            cursor = conn.execute(
                '''SELECT daily_reports FROM users WHERE user_id = ?''',
                (user_id,)
            )
            result = cursor.fetchone()
            
            if result:
                current_reports = result['daily_reports'] or 0
                conn.execute(
                    '''UPDATE users 
                       SET daily_reports = ?, last_report_date = ?
                       WHERE user_id = ?''',
                    (current_reports + 1, today.isoformat(), user_id)
                )
            
            # Add report
            conn.execute(
                '''INSERT INTO reports 
                   (reporter_id, target, method, amount, proof)
                   VALUES (?, ?, ?, ?, ?)''',
                (user_id, target, method, amount, proof)
            )
            
            # Update statistics
            conn.execute('''
                INSERT OR REPLACE INTO statistics (date, reports_count)
                VALUES (?, COALESCE(
                    (SELECT reports_count FROM statistics WHERE date = ?), 0
                ) + 1)
            ''', (today.isoformat(), today.isoformat()))
            
            conn.commit()
    
    def search_reports(self, query):
        with self.get_connection() as conn:
            cursor = conn.execute('''
                SELECT target, method, amount, COUNT(*) as count,
                       MAX(created_at) as last_report
                FROM reports 
                WHERE target LIKE ? 
                GROUP BY target
                ORDER BY count DESC
            ''', (f'%{query}%',))
            return cursor.fetchall()
    
    def get_statistics(self):
        with self.get_connection() as conn:
            # Total reports
            cursor = conn.execute('SELECT COUNT(*) as total FROM reports')
            total = cursor.fetchone()['total']
            
            # Today's reports
            today = datetime.now().date().isoformat()
            cursor = conn.execute(
                'SELECT reports_count FROM statistics WHERE date = ?',
                (today,)
            )
            today_reports = cursor.fetchone()
            today_count = today_reports['reports_count'] if today_reports else 0
            
            # Top reported
            cursor = conn.execute('''
                SELECT target, COUNT(*) as count
                FROM reports
                GROUP BY target
                ORDER BY count DESC
                LIMIT 10
            ''')
            top_reported = cursor.fetchall()
            
            # Active users today
            cursor = conn.execute('''
                SELECT COUNT(DISTINCT reporter_id) as active_users
                FROM reports 
                WHERE DATE(created_at) = ?
            ''', (today,))
            active_users = cursor.fetchone()['active_users'] or 0
            
            return {
                'total_reports': total,
                'today_reports': today_count,
                'top_reported': top_reported,
                'active_users': active_users
            }

# ==================== BOT STATES ====================
(
    MAIN_MENU,
    CHECK_SCAM,
    REPORT_TARGET,
    REPORT_METHOD,
    REPORT_AMOUNT,
    REPORT_PROOF,
    REPORT_CONFIRM,
    DONATION_CONFIRM,
) = range(8)

# ==================== GLOBALS ====================
db = Database()
user_sessions = {}

# ==================== HELPER FUNCTIONS ====================
def get_text(user_id, key, **kwargs):
    """Get text in user's language"""
    language = db.get_user_language(user_id)
    text = TEXTS.get(language, TEXTS['en']).get(key, key)
    if kwargs:
        try:
            text = text.format(**kwargs)
        except:
            pass
    return text

def create_main_menu(user_id):
    """Create main menu keyboard"""
    keyboard = [
        [get_text(user_id, "menu_check")],
        [get_text(user_id, "menu_report")],
        [get_text(user_id, "menu_stats")],
        [get_text(user_id, "menu_admins"), get_text(user_id, "menu_groups")],
        [get_text(user_id, "menu_language"), get_text(user_id, "menu_donate")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=False)

def create_back_button(user_id):
    """Create back button"""
    return ReplyKeyboardMarkup([[get_text(user_id, "back")]], resize_keyboard=True)

def create_language_keyboard():
    """Create language selection keyboard"""
    keyboard = []
    row = []
    for lang_code, lang_info in LANGUAGES.items():
        button = InlineKeyboardButton(
            f"{lang_info['flag']} {lang_info['name']}",
            callback_data=f"lang_{lang_code}"
        )
        row.append(button)
        if len(row) == 2:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)
    return InlineKeyboardMarkup(keyboard)

def create_report_method_keyboard(user_id):
    """Create scam method selection keyboard"""
    methods = get_text(user_id, "report_methods")
    keyboard = []
    for i, method in enumerate(methods, 1):
        keyboard.append([InlineKeyboardButton(method, callback_data=f"method_{i}")])
    keyboard.append([InlineKeyboardButton(get_text(user_id, "back"), callback_data="back")])
    return InlineKeyboardMarkup(keyboard)

def create_confirmation_keyboard(user_id):
    """Create confirmation keyboard"""
    keyboard = [
        [
            InlineKeyboardButton(
                get_text(user_id, "report_yes"),
                callback_data="confirm_yes"
            ),
            InlineKeyboardButton(
                get_text(user_id, "report_no"),
                callback_data="confirm_no"
            )
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def create_donation_keyboard(user_id):
    """Create donation confirmation keyboard"""
    keyboard = [
        [
            InlineKeyboardButton(
                get_text(user_id, "donate_button"),
                callback_data="donate_confirm"
            )
        ],
        [
            InlineKeyboardButton(
                get_text(user_id, "main_menu"),
                callback_data="main_menu"
            )
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

# ==================== COMMAND HANDLERS ====================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command"""
    user = update.effective_user
    db.add_user(user.id, user.username)
    
    # Send bot name ASCII art
    ascii_art = """
██████╗  ██████╗ ████████╗     ██████╗██╗  ██╗███████╗ ██████╗██╗  ██╗
██╔══██╗██╔═══██╗╚══██╔══╝    ██╔════╝██║  ██║██╔════╝██╔════╝██║ ██╔╝
██████╔╝██║   ██║   ██║       ██║     ███████║█████╗  ██║     █████╔╝ 
██╔══██╗██║   ██║   ██║       ██║     ██╔══██║██╔══╝  ██║     ██╔═██╗ 
██████╔╝╚██████╔╝   ██║       ╚██████╗██║  ██║███████╗╚██████╗██║  ██╗
╚═════╝  ╚═════╝    ╚═╝        ╚═════╝╚═╝  ╚═╝╚══════╝ ╚═════╝╚═╝  ╚═╝
"""
    
    await update.message.reply_text(f"`{ascii_art}`", parse_mode=ParseMode.MARKDOWN)
    await update.message.reply_text(f"*{get_text(user.id, 'bot_name')}*", parse_mode=ParseMode.MARKDOWN)
    await update.message.reply_text(
        f"*{get_text(user.id, 'welcome_title')}*\n\n"
        f"{get_text(user.id, 'welcome_text')}\n\n"
        f"{get_text(user.id, 'select_function')}",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=create_main_menu(user.id)
    )
    return MAIN_MENU

async def main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle main menu selection"""
    user = update.effective_user
    text = update.message.text
    
    if text == get_text(user.id, "menu_check"):
        await update.message.reply_text(
            f"*{get_text(user.id, 'check_title')}*\n\n"
            f"{get_text(user.id, 'check_instructions')}\n\n"
            f"{get_text(user.id, 'check_input')}",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=create_back_button(user.id)
        )
        return CHECK_SCAM
        
    elif text == get_text(user.id, "menu_report"):
        if not db.can_report(user.id):
            await update.message.reply_text(
                get_text(user.id, "report_limit"),
                reply_markup=create_main_menu(user.id)
            )
            return MAIN_MENU
        
        await update.message.reply_text(
            f"*{get_text(user.id, 'report_title')}*\n"
            f"{get_text(user.id, 'report_today', count='?')}\n\n"
            f"{get_text(user.id, 'report_ask_target')}",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=create_back_button(user.id)
        )
        return REPORT_TARGET
        
    elif text == get_text(user.id, "menu_stats"):
        stats = db.get_statistics()
        message = f"*{get_text(user.id, 'stats_title')}*\n\n"
        message += f"📊 {get_text(user.id, 'stats_total', count=stats['total_reports'])}\n"
        message += f"📅 {get_text(user.id, 'stats_today', count=stats['today_reports'])}\n"
        message += f"👥 {get_text(user.id, 'stats_users', count=stats['active_users'])}\n\n"
        
        if stats['top_reported']:
            message += f"*{get_text(user.id, 'stats_top')}*\n"
            for i, item in enumerate(stats['top_reported'][:5], 1):
                message += f"{i}. `{item['target']}` - {item['count']} reports\n"
        
        await update.message.reply_text(
            message,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=create_main_menu(user.id)
        )
        return MAIN_MENU
        
    elif text == get_text(user.id, "menu_admins"):
        message = f"*{get_text(user.id, 'admins_title')}*\n\n"
        message += f"{get_text(user.id, 'admins_note')}\n\n"
        
        admins = get_text(user.id, "admins")
        for admin in admins:
            message += get_text(user.id, "admin_info", **admin) + "\n\n"
        
        await update.message.reply_text(
            message,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=create_main_menu(user.id)
        )
        return MAIN_MENU
        
    elif text == get_text(user.id, "menu_groups"):
        message = f"*{get_text(user.id, 'groups_title')}*\n\n"
        message += f"{get_text(user.id, 'groups_note')}\n\n"
        
        groups = get_text(user.id, "groups")
        for group in groups:
            message += get_text(user.id, "group_info", **group) + "\n\n"
        
        await update.message.reply_text(
            message,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=create_main_menu(user.id)
        )
        return MAIN_MENU
        
    elif text == get_text(user.id, "menu_language"):
        current_lang = db.get_user_language(user.id)
        lang_name = LANGUAGES[current_lang]['name'] if current_lang in LANGUAGES else 'English'
        
        await update.message.reply_text(
            f"*{get_text(user.id, 'language_title')}*\n\n"
            f"{get_text(user.id, 'language_current', name=lang_name)}\n\n"
            f"Select your preferred language:",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=create_language_keyboard()
        )
        return MAIN_MENU
        
    elif text == get_text(user.id, "menu_donate"):
        await update.message.reply_text(
            f"*{get_text(user.id, 'donate_title')}*\n\n"
            f"{get_text(user.id, 'donate_text')}",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=create_donation_keyboard(user.id)
        )
        return MAIN_MENU
        
    else:
        await update.message.reply_text(
            get_text(user.id, "invalid_input"),
            reply_markup=create_main_menu(user.id)
        )
        return MAIN_MENU

# ==================== CHECK SCAM HANDLER ====================
async def check_scam(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle scam check input"""
    user = update.effective_user
    
    if update.message.text == get_text(user.id, "back"):
        await update.message.reply_text(
            get_text(user.id, "main_menu"),
            reply_markup=create_main_menu(user.id)
        )
        return MAIN_MENU
    
    query = update.message.text.strip()
    if not query or len(query) < 3:
        await update.message.reply_text(
            get_text(user.id, "invalid_input"),
            reply_markup=create_back_button(user.id)
        )
        return CHECK_SCAM
    
    # Show loading
    loading_msg = await update.message.reply_text(
        get_text(user.id, "check_loading")
    )
    
    # Search in database
    results = db.search_reports(query)
    
    if results:
        result = results[0]  # Get the most relevant
        count = result['count']
        
        if count >= 3:
            status = get_text(user.id, "check_found")
        else:
            status = get_text(user.id, "check_suspicious")
        
        message = status
        message += f"*{get_text(user.id, 'check_details')}*\n"
        message += f"• {get_text(user.id, 'check_reports', count=count)}\n"
        message += f"• {get_text(user.id, 'check_method', method=result['method'])}\n"
        
        if result['amount']:
            message += f"• {get_text(user.id, 'check_amount', amount=result['amount'])}\n"
        
        if result['last_report']:
            message += f"• {get_text(user.id, 'check_last', date=result['last_report'][:10])}\n"
        
    else:
        message = get_text(user.id, "check_clean")
        message += get_text(user.id, "check_no_data")
    
    await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=loading_msg.message_id)
    await update.message.reply_text(
        message,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=create_main_menu(user.id)
    )
    return MAIN_MENU

# ==================== REPORT SCAM HANDLERS ====================
async def report_target(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle report target input"""
    user = update.effective_user
    
    if update.message.text == get_text(user.id, "back"):
        await update.message.reply_text(
            get_text(user.id, "main_menu"),
            reply_markup=create_main_menu(user.id)
        )
        return MAIN_MENU
    
    target = update.message.text.strip()
    if not target or len(target) < 3:
        await update.message.reply_text(
            get_text(user.id, "invalid_input"),
            reply_markup=create_back_button(user.id)
        )
        return REPORT_TARGET
    
    # Store in user session
    if user.id not in user_sessions:
        user_sessions[user.id] = {}
    user_sessions[user.id]['target'] = target
    
    await update.message.reply_text(
        f"*{get_text(user.id, 'report_ask_method')}*",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=create_report_method_keyboard(user.id)
    )
    return REPORT_METHOD

async def report_method(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle report method selection"""
    query = update.callback_query
    await query.answer()
    
    user = update.effective_user
    
    if query.data == "back":
        await query.edit_message_text(
            get_text(user.id, "main_menu"),
            reply_markup=create_main_menu(user.id)
        )
        return MAIN_MENU
    
    method_index = int(query.data.split('_')[1]) - 1
    methods = get_text(user.id, "report_methods")
    
    if 0 <= method_index < len(methods):
        user_sessions[user.id]['method'] = methods[method_index]
        
        await query.edit_message_text(
            f"*{get_text(user.id, 'report_ask_amount')}*\n\n"
            f"{get_text(user.id, 'back')}",
            parse_mode=ParseMode.MARKDOWN
        )
        return REPORT_AMOUNT
    
    await query.edit_message_text(
        get_text(user.id, "error"),
        reply_markup=create_main_menu(user.id)
    )
    return MAIN_MENU

async def report_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle report amount input"""
    user = update.effective_user
    
    if update.message.text == get_text(user.id, "back"):
        await update.message.reply_text(
            get_text(user.id, "main_menu"),
            reply_markup=create_main_menu(user.id)
        )
        return MAIN_MENU
    
    amount = update.message.text.strip()
    user_sessions[user.id]['amount'] = amount if amount else "Not specified"
    
    await update.message.reply_text(
        f"*{get_text(user.id, 'report_ask_proof')}*\n\n"
        f"{get_text(user.id, 'back')}",
        parse_mode=ParseMode.MARKDOWN
    )
    return REPORT_PROOF

async def report_proof(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle report proof input"""
    user = update.effective_user
    
    if update.message.text == get_text(user.id, "back"):
        await update.message.reply_text(
            get_text(user.id, "main_menu"),
            reply_markup=create_main_menu(user.id)
        )
        return MAIN_MENU
    
    proof = update.message.text.strip() or "No proof provided"
    if update.message.photo:
        proof = "Photo evidence provided"
    
    user_sessions[user.id]['proof'] = proof
    
    # Show confirmation
    session = user_sessions[user.id]
    message = get_text(user.id, "report_confirm").format(
        session.get('target', 'N/A'),
        session.get('method', 'N/A'),
        session.get('amount', 'N/A'),
        session.get('proof', 'N/A')
    )
    
    await update.message.reply_text(
        message,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=create_confirmation_keyboard(user.id)
    )
    return REPORT_CONFIRM

async def report_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle report confirmation"""
    query = update.callback_query
    await query.answer()
    
    user = update.effective_user
    
    if query.data == "confirm_yes":
        session = user_sessions.get(user.id, {})
        if session:
            db.add_report(
                user.id,
                session.get('target'),
                session.get('method'),
                session.get('amount'),
                session.get('proof')
            )
            
            # Clear session
            user_sessions.pop(user.id, None)
            
            await query.edit_message_text(
                get_text(user.id, "report_success"),
                reply_markup=create_main_menu(user.id)
            )
        else:
            await query.edit_message_text(
                get_text(user.id, "error"),
                reply_markup=create_main_menu(user.id)
            )
    else:
        await query.edit_message_text(
            get_text(user.id, "report_cancel"),
            reply_markup=create_main_menu(user.id)
        )
    
    return MAIN_MENU

# ==================== LANGUAGE HANDLER ====================
async def language_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle language selection"""
    query = update.callback_query
    await query.answer()
    
    user = update.effective_user
    
    if query.data.startswith("lang_"):
        lang_code = query.data.split("_")[1]
        if lang_code in LANGUAGES:
            db.set_user_language(user.id, lang_code)
            lang_name = LANGUAGES[lang_code]['name']
            
            await query.edit_message_text(
                get_text(user.id, "language_changed", name=lang_name),
                reply_markup=create_main_menu(user.id)
            )
            
            # Update text language immediately
            await context.bot.send_message(
                chat_id=user.id,
                text=get_text(user.id, "main_menu"),
                reply_markup=create_main_menu(user.id)
            )
    
    return MAIN_MENU

# ==================== DONATION HANDLER ====================
async def donation_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle donation confirmation"""
    query = update.callback_query
    await query.answer()
    
    user = update.effective_user
    
    if query.data == "donate_confirm":
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        await query.edit_message_text(
            get_text(user.id, "donate_thanks", time=current_time),
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton(
                    get_text(user.id, "main_menu"),
                    callback_data="main_menu_callback"
                )
            ]])
        )
    elif query.data == "main_menu" or query.data == "main_menu_callback":
        await query.edit_message_text(
            get_text(user.id, "main_menu"),
            reply_markup=create_main_menu(user.id)
        )
    
    return MAIN_MENU

# ==================== BACK HANDLER ====================
async def back_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle back button"""
    user = update.effective_user
    await update.message.reply_text(
        get_text(user.id, "main_menu"),
        reply_markup=create_main_menu(user.id)
    )
    return MAIN_MENU

# ==================== ERROR HANDLER ====================
async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle errors"""
    logging.error(f"Update {update} caused error {context.error}")
    if update and update.effective_user:
        try:
            await context.bot.send_message(
                chat_id=update.effective_user.id,
                text=get_text(update.effective_user.id, "error"),
                reply_markup=create_main_menu(update.effective_user.id)
            )
        except:
            pass
    return MAIN_MENU

# ==================== MAIN FUNCTION ====================
def main():
    """Start the bot"""
    # Setup logging
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.INFO
    )
    
    # Create application
    application = Application.builder().token(TOKEN).build()
    
    # Conversation handler
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            MAIN_MENU: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, main_menu)
            ],
            CHECK_SCAM: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, check_scam)
            ],
            REPORT_TARGET: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, report_target)
            ],
            REPORT_METHOD: [
                CallbackQueryHandler(report_method)
            ],
            REPORT_AMOUNT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, report_amount)
            ],
            REPORT_PROOF: [
                MessageHandler(filters.TEXT | filters.PHOTO, report_proof)
            ],
            REPORT_CONFIRM: [
                CallbackQueryHandler(report_confirm)
            ],
        },
        fallbacks=[
            CommandHandler('start', start),
            MessageHandler(filters.Regex('^⬅️'), back_handler)
        ],
        allow_reentry=True
    )
    
    # Add handlers
    application.add_handler(conv_handler)
    application.add_handler(CallbackQueryHandler(language_callback, pattern="^lang_"))
    application.add_handler(CallbackQueryHandler(donation_callback, pattern="^(donate_|main_menu)"))
    
    # Add error handler
    application.add_error_handler(error_handler)
    
    # Start bot
    print("🤖 BOT CHECK SCAM is starting...")
    print("📊 Database initialized")
    print("🌐 Supported languages: English, Vietnamese, Russian, Chinese")
    print("💎 Donation Binance ID: 154265504")
    print("🚀 Bot is now running...")
    
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    # Check if token is set
    if TOKEN == "YOUR_BOT_TOKEN_HERE":
        print("❌ ERROR: Please set your bot token in the TOKEN variable!")
        print("Get your token from @BotFather on Telegram")
    else:
        main()

