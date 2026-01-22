#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TELEGRAM BOT: FIGHT_SCAMS - COMMUNITY SCAM PREVENTION SYSTEM
Version: 3.2.0 - Professional Edition
Author: FIGHT_SCAMS TEAM
Description: Multi-sector scam checking and warning system
"""

import os
import json
import logging
import re
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Any, Set
from dotenv import load_dotenv
from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup, 
    ReplyKeyboardMarkup, KeyboardButton
)
from telegram.ext import (
    Updater, CommandHandler, MessageHandler, Filters,
    CallbackContext, CallbackQueryHandler, ConversationHandler
)

# ============================================
# CONFIGURATION AND INITIALIZATION
# ============================================

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# States for ConversationHandler
(
    REPORT_USERNAME, REPORT_LINK, REPORT_WALLET, 
    REPORT_AMOUNT, REPORT_PRODUCT, REPORT_CONFIRM,
    CHECK_INPUT
) = range(7)

# ============================================
# TEXT FORMATTING UTILITIES
# ============================================

def escape_markdown(text: str) -> str:
    """Escape special characters for MarkdownV2"""
    escape_chars = r'_*[]()~`>#+-=|{}.!'
    for char in escape_chars:
        text = text.replace(char, f'\\{char}')
    return text

def format_bold(text: str) -> str:
    """Format bold text for MarkdownV2"""
    return f"*{escape_markdown(text)}*"

def format_code(text: str) -> str:
    """Format code for MarkdownV2"""
    return f"`{escape_markdown(text)}`"

def format_link(text: str, url: str) -> str:
    """Format link for MarkdownV2"""
    return f"[{escape_markdown(text)}]({url})"

def clean_text(text: str) -> str:
    """Clean text to avoid parsing errors"""
    # Remove invalid characters
    text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', text)
    # Escape special characters
    text = escape_markdown(text)
    return text

# ============================================
# JSON DATABASE MANAGEMENT
# ============================================

class JSONDatabase:
    """Class for managing data storage in JSON file"""
    
    def __init__(self, filename='data.json'):
        self.filename = filename
        self.data = self._load_data()
    
    def _load_data(self) -> Dict:
        """Load data from JSON file"""
        try:
            if os.path.exists(self.filename):
                with open(self.filename, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                    # Convert lists to sets
                    for scammer_key, scammer in data.get('scammers', {}).items():
                        if 'reporters' in scammer and isinstance(scammer['reporters'], list):
                            scammer['reporters'] = set(scammer['reporters'])
                        if 'products' in scammer and isinstance(scammer['products'], list):
                            scammer['products'] = set(scammer['products'])
                    
                    # Ensure statistics has all required keys
                    if 'statistics' not in data:
                        data['statistics'] = {}
                    
                    stats = data['statistics']
                    default_stats = {
                        'total_reports': 0,
                        'total_users': 0,
                        'total_checks': 0,
                        'total_scammers': 0,
                        'total_amount_scammed': 0
                    }
                    
                    for key, default_val in default_stats.items():
                        if key not in stats:
                            stats[key] = default_val
                    
                    return data
        except Exception as e:
            logger.error(f"Error reading JSON file: {e}")
        
        # Default data structure
        default_data = {
            'users': {},
            'reports': [],
            'scammers': {},
            'statistics': {
                'total_reports': 0,
                'total_users': 0,
                'total_checks': 0,
                'total_scammers': 0,
                'total_amount_scammed': 0
            }
        }
        self._save_data(default_data)
        return default_data
    
    def _save_data(self, data: Dict = None):
        """Save data to JSON file"""
        if data is None:
            data = self.data
        
        # Create a copy to convert sets to lists
        save_data = json.loads(json.dumps(data, default=self._json_serializer))
        
        try:
            with open(self.filename, 'w', encoding='utf-8') as f:
                json.dump(save_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Error writing JSON file: {e}")
    
    def _json_serializer(self, obj):
        """Convert non-JSON serializable data types"""
        if isinstance(obj, set):
            return list(obj)
        if isinstance(obj, datetime):
            return obj.isoformat()
        raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")
    
    def save(self):
        """Save current data"""
        self._save_data(self.data)
    
    # ========== USER MANAGEMENT ==========
    
    def get_user(self, user_id: int) -> Dict:
        """Get user information"""
        user_id_str = str(user_id)
        if user_id_str not in self.data['users']:
            self.data['users'][user_id_str] = {
                'language': 'en',
                'reports_today': 0,
                'last_report_date': None,
                'report_count': 0,
                'check_count': 0,
                'join_date': datetime.now().isoformat(),
                'username': None,
                'first_name': None,
                'last_name': None
            }
            self.data['statistics']['total_users'] += 1
            self.save()
        return self.data['users'][user_id_str]
    
    def update_user_info(self, user_id: int, username: str, first_name: str, last_name: str):
        """Update user information"""
        user = self.get_user(user_id)
        user['username'] = username
        user['first_name'] = first_name
        user['last_name'] = last_name
        self.save()
    
    def update_user_language(self, user_id: int, language: str):
        """Update user language"""
        user = self.get_user(user_id)
        user['language'] = language
        self.save()
    
    def can_report(self, user_id: int) -> Tuple[bool, str]:
        """Check if user can report"""
        user = self.get_user(user_id)
        today = datetime.now().date().isoformat()
        
        if user['last_report_date'] != today:
            user['reports_today'] = 0
            user['last_report_date'] = today
            self.save()
        
        if user['reports_today'] >= 3:
            return False, "limit_exceeded"
        
        return True, ""
    
    def increment_user_report(self, user_id: int):
        """Increment user report count"""
        user = self.get_user(user_id)
        user['reports_today'] = user.get('reports_today', 0) + 1
        user['report_count'] = user.get('report_count', 0) + 1
        user['last_report_date'] = datetime.now().date().isoformat()
        self.save()
    
    def increment_user_check(self, user_id: int):
        """Increment user check count"""
        user = self.get_user(user_id)
        user['check_count'] = user.get('check_count', 0) + 1
        self.save()
        self.data['statistics']['total_checks'] += 1
    
    # ========== REPORT MANAGEMENT ==========
    
    def add_report(self, report_data: Dict) -> int:
        """Add new report"""
        try:
            report_id = len(self.data['reports']) + 1
            report_data['id'] = report_id
            report_data['timestamp'] = datetime.now().isoformat()
            report_data['status'] = 'active'
            
            self.data['reports'].append(report_data)
            
            # Create unique key for scammer
            scammer_key = f"{report_data.get('username', '').lower()}_{report_data.get('wallet_id', '').lower()}"
            
            if scammer_key not in self.data['scammers']:
                self.data['scammers'][scammer_key] = {
                    'username': report_data.get('username'),
                    'telegram_link': report_data.get('telegram_link'),
                    'wallet_id': report_data.get('wallet_id'),
                    'report_count': 0,
                    'reporter_count': 0,
                    'reporters': set(),
                    'total_amount': 0,
                    'products': set(),
                    'first_report': datetime.now().isoformat(),
                    'last_report': datetime.now().isoformat()
                }
            
            scammer = self.data['scammers'][scammer_key]
            scammer['report_count'] += 1
            scammer['reporters'].add(str(report_data['user_id']))
            scammer['reporter_count'] = len(scammer['reporters'])
            
            amount = float(report_data.get('amount', 0))
            if amount:
                scammer['total_amount'] = scammer.get('total_amount', 0) + amount
                # Ensure key exists
                if 'total_amount_scammed' not in self.data['statistics']:
                    self.data['statistics']['total_amount_scammed'] = 0
                self.data['statistics']['total_amount_scammed'] += amount
            
            product = report_data.get('product', '')
            if product:
                scammer['products'].add(product)
            
            scammer['last_report'] = datetime.now().isoformat()
            
            # Update statistics
            self.data['statistics']['total_reports'] += 1
            self.data['statistics']['total_scammers'] = len(self.data['scammers'])
            
            self.save()
            return report_id
        except Exception as e:
            logger.error(f"Error adding report: {e}")
            return 0
    
    # ========== SCAMMER SEARCH ==========
    
    def find_scammer(self, search_input: str) -> List[Dict]:
        """Search for scammer"""
        results = []
        search_input = search_input.lower().strip()
        
        # Process input
        if search_input.startswith('@'):
            search_input = search_input[1:]
        elif 't.me/' in search_input:
            search_input = search_input.split('t.me/')[-1].split('/')[0]
        
        for scammer_key, scammer in self.data['scammers'].items():
            match = False
            
            # Check username
            if scammer.get('username'):
                username_lower = scammer['username'].lower().replace('@', '')
                if search_input in username_lower:
                    match = True
            
            # Check telegram link
            if not match and scammer.get('telegram_link'):
                link_lower = scammer['telegram_link'].lower()
                if search_input in link_lower:
                    match = True
            
            # Check wallet ID
            if not match and scammer.get('wallet_id'):
                wallet_lower = scammer['wallet_id'].lower()
                if search_input in wallet_lower:
                    match = True
            
            if match:
                # Create safe copy
                scammer_copy = scammer.copy()
                scammer_copy['reporters'] = list(scammer_copy.get('reporters', set()))
                scammer_copy['products'] = list(scammer_copy.get('products', set()))
                results.append(scammer_copy)
        
        return results
    
    # ========== STATISTICS ==========
    
    def get_statistics(self) -> Dict:
        """Get overall statistics"""
        stats = self.data['statistics'].copy()
        stats['active_users'] = len(self.data['users'])
        stats['active_scammers'] = len(self.data['scammers'])
        
        # Calculate reports from last 7 days
        week_ago = (datetime.now() - timedelta(days=7)).isoformat()
        recent_reports = [r for r in self.data['reports'] if r.get('timestamp', '') > week_ago]
        stats['recent_reports'] = len(recent_reports)
        
        return stats
    
    def get_top_scammers(self, limit: int = 10) -> List[Dict]:
        """Get top scammers"""
        scammers_list = []
        for scammer_key, scammer in self.data['scammers'].items():
            scammer_copy = scammer.copy()
            scammer_copy['reporters'] = list(scammer_copy.get('reporters', set()))
            scammer_copy['products'] = list(scammer_copy.get('products', set()))
            scammers_list.append(scammer_copy)
        
        scammers_list.sort(key=lambda x: x['report_count'], reverse=True)
        return scammers_list[:limit]

# Initialize database
db = JSONDatabase()

# ============================================
# MULTI-LANGUAGE SYSTEM - FIXED
# ============================================

class LanguageManager:
    """Manage multi-language support for bot"""
    
    def __init__(self):
        self.languages = {
            'en': {
                'code': 'en',
                'name': '✅ 🇺🇸 English',
                'data': self._load_english()
            },
            'vi': {
                'code': 'vi',
                'name': '🇻🇳 Tiếng Việt',
                'data': self._load_vietnamese()
            },
            'zh': {
                'code': 'zh',
                'name': '🇨🇳 中文',
                'data': self._load_chinese()
            },
            'ru': {
                'code': 'ru',
                'name': '🇷🇺 Русский',
                'data': self._load_russian()
            }
        }
    
    def _load_english(self) -> Dict:
        """Load English language - PRIMARY LANGUAGE"""
        return {
            # Main menu
            'main_menu': '🛡️ *FIGHT\\_SCAMS BOT* \\- Community Scam Prevention System\n\n'
                        '🔐 *TRUST & CREDIBILITY SYSTEM*\n'
                        '• *Community\\-Powered Database*\\: Every report contributes to collective safety\n'
                        '• *Transparent Statistics*\\: Each entry shows report count and unique reporters\n'
                        '• *Real\\-Time Protection*\\: Instant warnings based on verified community reports\n\n'
                        '📊 *REPORT METRICS*\n'
                        '• ✅ *Report Count*\\: Total scam reports received\n'
                        '• 👥 *Unique Reporters*\\: Number of distinct users reporting\n'
                        '• 💰 *Financial Impact*\\: Total reported loss amount\n\n'
                        '⚠️ *IMPORTANT NOTICE*\\: Fight\\_Scams provides community\\-based risk indicators, '
                        'not legal conclusions\\. Always verify independently before transactions\\.\n\n'
                        '👇 *Select an option below to proceed\\:*',
            
            # Menu options
            'menu_language': '🌐 Language Settings',
            'menu_check': '🔍 Verify User/Transaction',
            'menu_report': '🚨 Report Scammer',
            'menu_tips': '⚠️ Security Guidelines',
            'menu_donate': '💝 Support Development',
            'menu_groups': '👥 Verified Communities',
            'menu_admins': '🛡️ Trusted Mediators',
            'menu_stats': '📊 Analytics Dashboard',
            'menu_help': 'ℹ️ Support Center',
            
            # General notifications
            'select_option': '📋 Please select an option\\:',
            'back': '↩️ Back',
            'cancel': '❌ Cancel',
            'confirm': '✅ Confirm',
            'yes': '✅ Yes',
            'no': '❌ No',
            
            # Report scam
            'report_start': '🚨 *SCAM REPORT INITIATION*\n\n'
                           'ℹ️ *Report Guidelines*\n'
                           '• Provide accurate information\n'
                           '• Include evidence if available\n'
                           '• Maximum 3 reports per 24 hours\n'
                           '• False reports may lead to restrictions\n\n'
                           '📝 *Please provide the following details\\:*',
            'report_username': '1️⃣ *Telegram Username*\nEnter the scammer\'s Telegram @username\\:',
            'report_link': '2️⃣ *Telegram Profile Link*\nEnter the complete Telegram profile link\\:',
            'report_wallet': '3️⃣ *Wallet/Crypto Identifier*\nEnter associated wallet IDs \\(Binance, OKX, USDT, etc\\.\\)\\:',
            'report_amount': '4️⃣ *Financial Impact*\nEnter approximate loss amount \\(e\\.g\\., 100\\$, 500\\$, 1000\\$\\)\\. Enter 0 if not applicable\\:',
            'report_product': '5️⃣ *Transaction Details*\nDescribe the product/service involved \\(software, accounts, funds, etc\\.\\)\\:',
            'report_confirm': '⚠️ *REPORT VERIFICATION REQUIRED*\n\n'
                             '📋 *Report Summary*\n'
                             '• 🔹 Username\\: `{username}`\n'
                             '• 🔹 Telegram\\: `{link}`\n'
                             '• 🔹 Wallet ID\\: `{wallet}`\n'
                             '• 🔹 Amount\\: `{amount}`\n'
                             '• 🔹 Product\\: `{product}`\n\n'
                             '❓ *Is all information accurate and truthful\\?*',
            'report_success': '✅ *REPORT SUCCESSFULLY REGISTERED*\n\n'
                             '✨ *Thank you for your contribution to community safety\\!*\n\n'
                             '📊 *Report Details*\n'
                             '• Report ID\\: `#{report_id}`\n'
                             '• Timestamp\\: `{timestamp}`\n'
                             '• Today\'s reports\\: `{count_today}/3`\n'
                             '• Total reports submitted\\: `{total_reports}`\n\n'
                             '🛡️ *Your report helps protect {protected_count} community members*\n'
                             '🔒 *Stay safe and always verify before transactions*\n\n'
                             '💙 *Community Protection \\= Collective Responsibility*',
            'report_limit': '⛔ *DAILY LIMIT REACHED*\n\n'
                           '📅 *Limit Information*\n'
                           '• Maximum reports per day\\: 3\n'
                           '• Your reports today\\: 3/3\n'
                           '• Reset time\\: 00\\:00 UTC\n\n'
                           '⚠️ Please try again tomorrow to submit additional reports\\.',
            'report_cancel': '❌ *REPORT CANCELLED*\n\n'
                            'Operation terminated\\. No data was saved\\.',
            'report_cancel_warning': '⚠️ *FALSE REPORT ATTEMPT DETECTED*\n\n'
                                    '🚨 *WARNING TO USER*\n'
                                    '• This cancellation has been recorded\n'
                                    '• Repeated false report attempts waste community resources\n'
                                    '• Multiple cancellations may lead to account restrictions\n'
                                    '• Only submit genuine scam reports\n\n'
                                    '🔒 *Community protection relies on accurate reporting*\n'
                                    '✅ Return to main menu to continue legitimate operations\\.',
            
            # Check scammer
            'check_input': '🔍 *USER VERIFICATION PORTAL*\n\n'
                          '🔎 *Search Parameters*\n'
                          'You can search using\\:\n'
                          '• 👤 Telegram username \\(with or without @\\)\n'
                          '• 🔗 Telegram profile link\n'
                          '• 💳 Crypto wallet address\n\n'
                          '📥 *Enter search query\\:*',
            'check_no_results': '✅ *NO RISK IDENTIFIED*\n\n'
                               '🔍 *Search Results*\n'
                               '• Query\\: `{query}`\n'
                               '• Status\\: *CLEAN*\n'
                               '• No scam reports found in database\n'
                               '• Database updated\\: {timestamp}\n\n'
                               '⚠️ *Reminder\\: Always verify transactions independently\\.*',
            'check_results': '🚨 *SCAM ALERT \\- VERIFICATION REPORT*\n\n'
                            '👤 *TARGET INFORMATION*\n'
                            '• Username\\: `{username}`\n'
                            '• Telegram Link\\: `{link}`\n'
                            '• Wallet ID\\: `{wallet}`\n\n'
                            '📊 *COMMUNITY REPORTS SUMMARY*\n'
                            '• Total Reports\\: `{report_count}`\n'
                            '• Unique Reporters\\: `{reporter_count}`\n'
                            '• Total Amount Reported\\: `{total_amount}`\n'
                            '• First Report Date\\: `{first_report}`\n'
                            '• Last Report Date\\: `{last_report}`\n'
                            '• Associated Products/Services\\: `{products}`\n\n'
                            '🛡️ *SECURITY ADVISORY*\n'
                            '• ⚠️ *HIGH RISK DETECTED* \\- Multiple community reports confirm fraudulent activity\n'
                            '• 🚫 *RECOMMENDATION*\\: Avoid ALL transactions with this entity\n'
                            '• 🔒 *ACTION REQUIRED*\\: Block and report to platform administrators\n\n'
                            '📞 *For mediation assistance, contact trusted mediators from the menu*\n'
                            '💡 *Remember\\: No legitimate business requires advance payment without verification*',
            
            # Safe trading tips
            'safe_tips': '⚠️ *SECURITY PROTOCOLS & BEST PRACTICES*\n\n'
                        '🔐 *TRANSACTION SECURITY*\n'
                        '1\\. 🛡️ Always use platform\\-verified mediators\n'
                        '2\\. 🔍 Run pre\\-transaction verification using this bot\n'
                        '3\\. 💰 Implement escrow services for large transactions\n'
                        '4\\. 📝 Maintain comprehensive communication logs\n'
                        '5\\. 🚨 Enable 2FA on all financial accounts\n'
                        '6\\. 👥 Prefer transactions within verified communities\n'
                        '7\\. ⏳ Allow reasonable processing time\n'
                        '8\\. ❓ Consult experienced community members\n\n'
                        '🛡️ *DIGITAL HYGIENE*\n'
                        '• Regular password updates\n'
                        '• Unique passwords per platform\n'
                        '• Suspicious link avoidance\n'
                        '• Regular security audits\n\n'
                        '✅ *VERIFIED PRACTICES \\= REDUCED RISK*',
            
            # Donation
            'donate': '💝 *SUPPORT & SUSTAINABILITY INITIATIVE*\n\n'
                     '🔄 *SYSTEM MAINTENANCE*\n'
                     'Your contributions enable\\:\n'
                     '• 🚀 Server infrastructure maintenance\n'
                     '• 🔒 Security enhancement implementation\n'
                     '• 📊 Database expansion and optimization\n'
                     '• 🌐 Multi\\-language support development\n'
                     '• ⚡ Performance improvement initiatives\n\n'
                     '💰 *SUPPORT CHANNELS*\n'
                     '• *Binance ID*\\: `154265504`\n'
                     '• *Network*\\: BEP20/BSC\n'
                     '• *Asset*\\: USDT \\(Recommended\\)\n\n'
                     '📜 *FINANCIAL TRANSPARENCY*\n'
                     'All contributions are allocated exclusively to\\:\n'
                     '1\\. Hosting and infrastructure costs\n'
                     '2\\. Security certificate renewals\n'
                     '3\\. Development and feature implementation\n'
                     '4\\. Community outreach and education\n\n'
                     '🤝 *PARTNERSHIP IN PROTECTION*\n'
                     'Every contribution strengthens community defense mechanisms\\.\n\n'
                     '✨ *Thank you for investing in collective security\\!*',
            
            # Trusted groups
            'trusted_groups': '👥 *VERIFIED COMMUNITY HUBS*\n\n'
                             '🔗 *Platform\\-Approved Communities*\n'
                             'Join these moderated spaces for safer transactions\\:\n\n'
                             '• *Main Trading Hub*\\: [Community Exchange Network](https://t\\.me/j5FS6B_V9DM5ZmVl)\n'
                             '• *Crypto Specialists*\\: [Digital Asset Marketplace](https://t\\.me/example_group1)\n'
                             '• *Gaming Ecosystem*\\: [Account Exchange Portal](https://t\\.me/example_group2)\n\n'
                             '🛡️ *COMMUNITY STANDARDS*\n'
                             '• Mandatory user verification\n'
                             '• Mediated dispute resolution\n'
                             '• Regular security audits\n'
                             '• Active moderation team\n\n'
                             '⚠️ *Always confirm user status before transacting*',
            
            # Trusted admins
            'trusted_admins': '🛡️ *CERTIFIED MEDIATION SERVICES*\n\n'
                             '👨‍⚖️ *Platform\\-Verified Mediators*\n'
                             'These professionals provide secure transaction services\\:\n\n'
                             '• *Lead Mediator*\\: [Siculator98](https://t\\.me/siculator98) \\- Complex dispute resolution\n'
                             '• *Crypto Specialist*\\: [CryptoGuardian](https://t\\.me/admin2) \\- Digital asset transactions\n'
                             '• *Gaming Expert*\\: [GameSecure](https://t\\.me/admin3) \\- Account transfers\n\n'
                             '⚖️ *MEDIATION PROTOCOLS*\n'
                             '• Escrow service provision\n'
                             '• Identity verification\n'
                             '• Transaction monitoring\n'
                             '• Dispute arbitration\n\n'
                             '✅ *Verified mediators enhance transaction security*',
            
            # Statistics
            'top_scammers': '📊 *ANALYTICS DASHBOARD*\n\n'
                           '🏆 *MOST REPORTED ENTITIES*\n{scammers_list}\n\n'
                           '📈 *SYSTEM METRICS*\n'
                           '• Total Reports\\: `{total_reports}`\n'
                           '• Active Scammers\\: `{total_scammers}`\n'
                           '• Community Members\\: `{active_users}`\n'
                           '• Total Checks\\: `{total_checks}`\n'
                           '• Estimated Loss\\: `{total_amount}`\n'
                           '• Recent Activity \\(7d\\)\\: `{recent_reports}` reports\n\n'
                           '📅 *Last updated\\: {timestamp}*',
            'scammer_item': '• `{username}` \\- {reports} reports \\({reporters} reporters\\) \\- {total_amount}',
            
            # Help
            'help': 'ℹ️ *SUPPORT & INFORMATION CENTER*\n\n'
                   '🤖 *SYSTEM OVERVIEW*\n'
                   'Fight\\_Scams is a community\\-powered scam prevention system designed to protect users in digital transactions across multiple sectors\\.\n\n'
                   '📋 *USER GUIDELINES*\n'
                   '1\\. Initialization\\: Use /start to access main interface\n'
                   '2\\. Pre\\-transaction\\: Always verify counterparties\n'
                   '3\\. Reporting\\: Submit detailed scam reports\n'
                   '4\\. Education\\: Review security protocols regularly\n\n'
                   '🛡️ *CREDIBILITY FRAMEWORK*\n'
                   '• All reports undergo community validation\n'
                   '• Database updates reflect real\\-time community input\n'
                   '• Transparency metrics ensure reliability\n\n'
                   '⚠️ *SYSTEM LIMITATIONS*\n'
                   '• Maximum 3 reports per user daily\n'
                   '• Community\\-based indicators, not legal determinations\n'
                   '• Requires community participation for effectiveness\n'
                   '• No guaranteed prevention of new scam patterns\n\n'
                   '📞 *TECHNICAL SUPPORT*\n'
                   'For assistance, contact\\: @siculator98\n\n'
                   '🔄 *SYSTEM VERSION*\\: 3\\.2\\.0 Professional Edition',
            
            # Errors
            'error': '❌ *SYSTEM ERROR ENCOUNTERED*\n\n'
                    '🔧 *Technical Information*\n'
                    '• Error type\\: Processing failure\n'
                    '• Status\\: Operation interrupted\n'
                    '• Action\\: Please retry operation\n\n'
                    '📞 *If issue persists, contact technical support\\.*',
            'invalid_input': '❌ *INPUT VALIDATION FAILED*\n\n'
                            '⚠️ *Issue Detected*\n'
                            '• Input format incorrect\n'
                            '• Required fields missing\n'
                            '• Data validation failed\n\n'
                            '🔄 *Please provide valid information and retry\\.*',
            'processing': '⏳ *PROCESSING REQUEST*\n\n'
                         '⚙️ *System Status*\n'
                         '• Query received\n'
                         '• Database access initiated\n'
                         '• Analysis in progress\n\n'
                         '✅ Please wait for completion\\.\\.\\.',
            
            # Success
            'success': '✅ *OPERATION COMPLETED SUCCESSFULLY*\n\n'
                      '✨ *Status Summary*\n'
                      '• All procedures executed correctly\n'
                      '• Data integrity maintained\n'
                      '• System updated accordingly\n\n'
                      '🔄 Returning to main interface\\.\\.\\.',
            
            # Language
            'language_changed': '🌐 *LANGUAGE CONFIGURATION UPDATED*\n\n'
                               '✅ *System Message*\n'
                               '• Interface language\\: *{language}*\n'
                               '• Localization applied\\: Complete\n'
                               '• All menus and messages updated\n\n'
                               '⚠️ *System Note*\\: English remains the primary operational language\n'
                               '🔄 System refreshed with new language settings\\.',
            'select_language': '🌐 *LANGUAGE SELECTION PANEL*\n\n'
                              '🔤 *Available Interfaces*\n'
                              'Select your preferred language\\:\n\n'
                              '⚠️ *System Note*\\: English is the primary operational language',
            
            # User statistics
            'user_stats': '📊 *PERSONAL ACTIVITY DASHBOARD*\n\n'
                         '👤 *User Profile*\n'
                         '• Member since\\: `{join_date}`\n'
                         '• Reports submitted\\: `{report_count}`\n'
                         '• Verification checks\\: `{check_count}`\n'
                         '• Today\'s reports\\: `{reports_today}/3`\n\n'
                         '🏆 *COMMUNITY CONTRIBUTION*\n'
                         '• Your reports protected `{protected_users}` users\n'
                         '• Contribution rank\\: `{rank}`\n'
                         '• Trust score\\: `{trust_score}/100`\n\n'
                         '✨ *Thank you for enhancing community security\\!*',
            
            # Validation errors
            'invalid_username': '❌ *Invalid username*\nPlease enter a valid Telegram username\\:',
            'invalid_wallet': '❌ *Invalid wallet ID*\nPlease enter a valid wallet identifier\\:',
            'invalid_product': '❌ *Invalid product description*\nPlease enter a valid product/service description\\:',
            
            # Private chat only
            'private_chat_only': '⚠️ *PRIVATE CHAT REQUIRED*\n\n'
                                'This bot only operates in private chats to protect user privacy\\.\n'
                                'Please start a private conversation with @fight_scams_bot',
        }
    
    def _load_vietnamese(self) -> Dict:
        """Load Vietnamese language"""
        return {
            'main_menu': '🛡️ *BOT FIGHT\\_SCAMS* \\- Hệ thống chống lừa đảo cộng đồng\n\n'
                        '🔐 *HỆ THỐNG TÍN NHIỆM & MINH BẠCH*\n'
                        '• *Cơ sở dữ liệu cộng đồng*\\: Mỗi báo cáo góp phần bảo vệ tập thể\n'
                        '• *Thống kê minh bạch*\\: Mỗi mục hiển thị số báo cáo và người báo cáo\n'
                        '• *Bảo vệ thời gian thực*\\: Cảnh báo tức thì từ báo cáo đã xác minh\n\n'
                        '📊 *CHỈ SỐ BÁO CÁO*\n'
                        '• ✅ *Số báo cáo*\\: Tổng lượt báo cáo lừa đảo\n'
                        '• 👥 *Người báo cáo*\\: Số người dùng khác nhau báo cáo\n'
                        '• 💰 *Tác động tài chính*\\: Tổng số tiền bị lừa đảo\n\n'
                        '⚠️ *THÔNG BÁO QUAN TRỌNG*\\: Fight\\_Scams cung cấp chỉ số rủi ro dựa trên cộng đồng, '
                        'không phải kết luận pháp lý\\. Luôn xác minh độc lập trước khi giao dịch\\.\n\n'
                        '👇 *Chọn một tùy chọn để tiếp tục\\:*',
            
            'menu_language': '🌐 Thiết lập ngôn ngữ',
            'menu_check': '🔍 Kiểm tra đối tượng',
            'menu_report': '🚨 Báo cáo lừa đảo',
            'menu_tips': '⚠️ Hướng dẫn bảo mật',
            'menu_donate': '💝 Hỗ trợ phát triển',
            'menu_groups': '👥 Cộng đồng uy tín',
            'menu_admins': '🛡️ Trung gian đáng tin',
            'menu_stats': '📊 Bảng thống kê',
            'menu_help': 'ℹ️ Trung tâm hỗ trợ',
            
            'report_amount': '4️⃣ *Tác động tài chính*\nNhập số tiền tổn thất ước tính \\(vd\\: 100\\$, 500\\$, 1000\\$\\)\\. Nhập 0 nếu không áp dụng\\:',
            
            'report_success': '✅ *BÁO CÁO ĐÃ ĐĂNG KÝ THÀNH CÔNG*\n\n'
                             '✨ *Cảm ơn bạn đã đóng góp cho an toàn cộng đồng\\!*\n\n'
                             '📊 *Chi tiết báo cáo*\n'
                             '• ID Báo cáo\\: `#{report_id}`\n'
                             '• Thời gian\\: `{timestamp}`\n'
                             '• Báo cáo hôm nay\\: `{count_today}/3`\n'
                             '• Tổng báo cáo đã gửi\\: `{total_reports}`\n\n'
                             '🛡️ *Báo cáo của bạn giúp bảo vệ {protected_count} thành viên cộng đồng*\n'
                             '🔒 *Luôn an toàn và xác minh trước khi giao dịch*\n\n'
                             '💙 *Bảo vệ cộng đồng \\= Trách nhiệm tập thể*',
            
            'report_cancel_warning': '⚠️ *PHÁT HIỆN CỐ GẮNG BÁO CÁO SAI*\n\n'
                                    '🚨 *CẢNH BÁO ĐẾN NGƯỜI DÙNG*\n'
                                    '• Hủy bỏ này đã được ghi nhận\n'
                                    '• Cố gắng báo cáo sai lặp lại lãng phí tài nguyên cộng đồng\n'
                                    '• Nhiều lần hủy có thể dẫn đến hạn chế tài khoản\n'
                                    '• Chỉ gửi báo cáo lừa đảo chính hãng\n\n'
                                    '🔒 *Bảo vệ cộng đồng dựa trên báo cáo chính xác*\n'
                                    '✅ Quay lại menu chính để tiếp tục hoạt động hợp pháp\\.',
            
            'check_results': '🚨 *CẢNH BÁO LỪA ĐẢO \\- BÁO CÁO XÁC MINH*\n\n'
                            '👤 *THÔNG TIN MỤC TIÊU*\n'
                            '• Tên người dùng\\: `{username}`\n'
                            '• Liên kết Telegram\\: `{link}`\n'
                            '• ID Ví\\: `{wallet}`\n\n'
                            '📊 *TÓM TẮT BÁO CÁO CỘNG ĐỒNG*\n'
                            '• Tổng số báo cáo\\: `{report_count}`\n'
                            '• Người báo cáo duy nhất\\: `{reporter_count}`\n'
                            '• Tổng số tiền báo cáo\\: `{total_amount}`\n'
                            '• Ngày báo cáo đầu tiên\\: `{first_report}`\n'
                            '• Ngày báo cáo gần nhất\\: `{last_report}`\n'
                            '• Sản phẩm/Dịch vụ liên quan\\: `{products}`\n\n'
                            '🛡️ *TƯ VẤN BẢO MẬT*\n'
                            '• ⚠️ *PHÁT HIỆN RỦI RO CAO* \\- Nhiều báo cáo cộng đồng xác nhận hoạt động lừa đảo\n'
                            '• 🚫 *ĐỀ XUẤT*\\: Tránh MỌI giao dịch với thực thể này\n'
                            '• 🔒 *HÀNH ĐỘNG CẦN THIẾT*\\: Chặn và báo cáo với quản trị viên nền tảng\n\n'
                            '📞 *Để được hỗ trợ trung gian, liên hệ với trung gian đáng tin từ menu*\n'
                            '💡 *Nhớ rằng\\: Không có doanh nghiệp hợp pháp nào yêu cầu thanh toán trước mà không xác minh*',
            
            'language_changed': '🌐 *ĐÃ CẬP NHẬT CẤU HÌNH NGÔN NGỮ*\n\n'
                               '✅ *Thông báo hệ thống*\n'
                               '• Ngôn ngữ giao diện\\: *{language}*\n'
                               '• Áp dụng bản địa hóa\\: Hoàn tất\n'
                               '• Tất cả menu và thông báo đã cập nhật\n\n'
                               '⚠️ *Lưu ý hệ thống*\\: Tiếng Anh vẫn là ngôn ngữ hoạt động chính\n'
                               '🔄 Hệ thống đã làm mới với cài đặt ngôn ngữ mới\\.',
            'select_language': '🌐 *BẢNG CHỌN NGÔN NGỮ*\n\n'
                              '🔤 *Giao diện có sẵn*\n'
                              'Chọn ngôn ngữ ưa thích của bạn\\:\n\n'
                              '⚠️ *Lưu ý hệ thống*\\: Tiếng Anh là ngôn ngữ hoạt động chính',
            
            'invalid_username': '❌ *Tên người dùng không hợp lệ*\nVui lòng nhập tên người dùng Telegram hợp lệ\\:',
            'invalid_wallet': '❌ *ID ví không hợp lệ*\nVui lòng nhập định danh ví hợp lệ\\:',
            'invalid_product': '❌ *Mô tả sản phẩm không hợp lệ*\nVui lòng nhập mô tả sản phẩm/dịch vụ hợp lệ\\:',
            
            'private_chat_only': '⚠️ *YÊU CẦU CHAT RIÊNG TƯ*\n\n'
                                'Bot này chỉ hoạt động trong chat riêng tư để bảo vệ quyền riêng tư người dùng\\.\n'
                                'Vui lòng bắt đầu cuộc trò chuyện riêng tư với @fight_scams_bot',
        }
    
    def _load_chinese(self) -> Dict:
        """Load Chinese language"""
        return {
            'main_menu': '🛡️ *FIGHT\\_SCAMS 机器人* \\- 社区防诈骗系统\n\n'
                        '🔐 **信任与信誉系统**\n'
                        '• **社区驱动数据库**：每个报告都增强集体安全\n'
                        '• **透明统计数据**：显示报告数量和独立举报人\n'
                        '• **实时保护**：基于已验证报告的即时警告\n\n'
                        '📊 **报告指标**\n'
                        '• ✅ **报告数量**：收到的诈骗报告总数\n'
                        '• 👥 **独立举报人**：不同用户报告数量\n'
                        '• 💰 **财务影响**：报告的总损失金额\n\n'
                        '⚠️ **重要通知**：Fight\\_Scams 基于社区报告提供风险指标，'
                        '并非法律结论。交易前请务必独立验证。\n\n'
                        '👇 *请选择以下选项继续：*',
            
            'menu_language': '🌐 语言设置',
            'menu_check': '🔍 验证用户/交易',
            'menu_report': '🚨 举报诈骗者',
            'menu_tips': '⚠️ 安全指南',
            'menu_donate': '💝 支持开发',
            'menu_groups': '👥 已验证社区',
            'menu_admins': '🛡️ 可信中介',
            'menu_stats': '📊 分析仪表板',
            'menu_help': 'ℹ️ 支持中心',
        }
    
    def _load_russian(self) -> Dict:
        """Load Russian language"""
        return {
            'main_menu': '🛡️ *БОТ FIGHT\\_SCAMS* \\- СИСТЕМА ЗАЩИТЫ ОТ МОШЕННИКОВ\n\n'
                        '🔐 **СИСТЕМА ДОВЕРИЯ И ПРОЗРАЧНОСТИ**\n'
                        '• **База данных сообщества**：Каждый отчет повышает коллективную безопасность\n'
                        '• **Прозрачная статистика**：Показывает количество отчетов и уникальных репортеров\n'
                        '• **Защита в реальном времени**：Мгновенные предупреждения на основе проверенных отчетов\n\n'
                        '📊 **ИНДИКАТОРЫ ОТЧЕТОВ**\n'
                        '• ✅ **Количество отчетов**：Всего получено отчетов о мошенничестве\n'
                        '• 👥 **Уникальные репортеры**：Количество разных пользователей\n'
                        '• 💰 **Финансовое влияние**：Общая сумма потерь\n\n'
                        '⚠️ **ВАЖНОЕ УВЕДОМЛЕНИЕ**：Fight\\_Scams предоставляет индикаторы риска на основе отчетов сообщества, '
                        'не юридические выводы。Всегда проверяйте независимо перед сделками。\n\n'
                        '👇 *Выберите опцию ниже для продолжения：*',
            
            'menu_language': '🌐 Настройки языка',
            'menu_check': '🔍 Проверить пользователя',
            'menu_report': '🚨 Сообщить о мошеннике',
            'menu_tips': '⚠️ Рекомендации по безопасности',
            'menu_donate': '💝 Поддержать разработку',
            'menu_groups': '👥 Проверенные сообщества',
            'menu_admins': '🛡️ Доверенные посредники',
            'menu_stats': '📊 Аналитика',
            'menu_help': 'ℹ️ Центр поддержки',
        }
    
    def get_text(self, user_id: int, key: str, **kwargs) -> str:
        """Get text in user's language"""
        user = db.get_user(user_id)
        lang_code = user['language']
        
        # Fallback to English if language not found
        if lang_code not in self.languages:
            lang_code = 'en'
        
        lang_data = self.languages[lang_code]['data']
        
        # Get text with English fallback
        text = lang_data.get(key, self.languages['en']['data'].get(key, key))
        
        # Add timestamp if needed
        if 'timestamp' not in kwargs:
            kwargs['timestamp'] = datetime.now().strftime("%Y-%m-%d %H:%M")
        
        # Replace parameters
        if kwargs:
            try:
                # Handle special formatting
                for k, v in kwargs.items():
                    if isinstance(v, datetime):
                        kwargs[k] = v.strftime("%Y-%m-%d")
                    elif isinstance(v, (int, float)):
                        if 'amount' in k or 'total_amount' in k:
                            kwargs[k] = f"{v:,.0f}$"
                        else:
                            kwargs[k] = f"{v:,.0f}"
                
                text = text.format(**kwargs)
            except KeyError as e:
                logger.warning(f"Missing key in text template: {e}")
            except Exception as e:
                logger.error(f"Error formatting text: {e}")
        
        return text
    
    def get_language_keyboard(self, user_id: int):
        """Create language selection keyboard"""
        keyboard = []
        user = db.get_user(user_id)
        current_lang = user['language']
        
        for lang_code, lang_info in self.languages.items():
            prefix = "✅ " if lang_code == current_lang else ""
            keyboard.append([InlineKeyboardButton(
                f"{prefix}{lang_info['name']}", 
                callback_data=f'setlang_{lang_code}'
            )])
        
        # Add cancel button
        keyboard.append([InlineKeyboardButton(
            self.get_text(user_id, 'back'),
            callback_data='cancel_language'
        )])
        
        return InlineKeyboardMarkup(keyboard)
    
    def get_menu_action(self, text: str, user_id: int) -> Optional[str]:
        """Determine action from menu text"""
        user = db.get_user(user_id)
        lang_code = user['language']
        
        # Map text to action based on current language
        lang_data = self.languages[lang_code]['data']
        
        menu_mapping = {
            lang_data.get('menu_language', 'Language Settings'): 'menu_language',
            lang_data.get('menu_check', 'Verify User/Transaction'): 'menu_check',
            lang_data.get('menu_report', 'Report Scammer'): 'menu_report',
            lang_data.get('menu_tips', 'Security Guidelines'): 'menu_tips',
            lang_data.get('menu_donate', 'Support Development'): 'menu_donate',
            lang_data.get('menu_groups', 'Verified Communities'): 'menu_groups',
            lang_data.get('menu_admins', 'Trusted Mediators'): 'menu_admins',
            lang_data.get('menu_stats', 'Analytics Dashboard'): 'menu_stats',
            lang_data.get('menu_help', 'Support Center'): 'menu_help',
        }
        
        return menu_mapping.get(text)

# Initialize language manager
lang = LanguageManager()

# ============================================
# SUPPORT UTILITIES
# ============================================

def create_main_menu_keyboard(user_id: int) -> ReplyKeyboardMarkup:
    """Create main menu keyboard"""
    keyboard = [
        [lang.get_text(user_id, 'menu_check'), lang.get_text(user_id, 'menu_report')],
        [lang.get_text(user_id, 'menu_tips'), lang.get_text(user_id, 'menu_donate')],
        [lang.get_text(user_id, 'menu_groups'), lang.get_text(user_id, 'menu_admins')],
        [lang.get_text(user_id, 'menu_stats'), lang.get_text(user_id, 'menu_help')],
        [lang.get_text(user_id, 'menu_language')]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=False)

def create_cancel_keyboard(user_id: int) -> ReplyKeyboardMarkup:
    """Create cancel keyboard"""
    keyboard = [[lang.get_text(user_id, 'cancel')]]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)

def create_confirm_keyboard(user_id: int) -> InlineKeyboardMarkup:
    """Create confirmation keyboard"""
    keyboard = [
        [
            InlineKeyboardButton(
                lang.get_text(user_id, 'yes'), 
                callback_data='report_confirm_yes'
            ),
            InlineKeyboardButton(
                lang.get_text(user_id, 'no'), 
                callback_data='report_confirm_no'
            )
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def format_scammer_list(scammers: List[Dict], user_id: int) -> str:
    """Format scammer list"""
    if not scammers:
        return ""
    
    result = ""
    for i, scammer in enumerate(scammers[:10], 1):
        username = scammer.get('username', 'Unknown')
        report_count = scammer.get('report_count', 0)
        reporter_count = scammer.get('reporter_count', 0)
        total_amount = scammer.get('total_amount', 0)
        
        result += lang.get_text(
            user_id, 
            'scammer_item',
            username=username,
            reports=report_count,
            reporters=reporter_count,
            total_amount=f"{total_amount:,.0f}$"
        ) + "\n"
    
    return result

# ============================================
# MAIN HANDLERS
# ============================================

def check_private_chat(update: Update) -> bool:
    """Check if chat is private"""
    if update.message and update.message.chat.type != 'private':
        user_id = update.effective_user.id
        try:
            text = lang.get_text(user_id, 'private_chat_only')
            update.message.reply_text(text, parse_mode='MarkdownV2')
        except:
            update.message.reply_text("⚠️ Please use the bot in private chat.")
        return False
    return True

def start_command(update: Update, context: CallbackContext) -> None:
    """Handle /start command"""
    if not check_private_chat(update):
        return
    
    user = update.effective_user
    user_id = user.id
    
    # Update user information
    db.update_user_info(user_id, user.username, user.first_name, user.last_name)
    
    # Send welcome message
    welcome_text = lang.get_text(user_id, 'main_menu')
    
    try:
        update.message.reply_text(
            welcome_text,
            parse_mode='MarkdownV2',
            reply_markup=create_main_menu_keyboard(user_id),
            disable_web_page_preview=True
        )
    except Exception as e:
        logger.error(f"Error sending message: {e}")
        # Try without formatting
        update.message.reply_text(
            "🛡️ FIGHT_SCAMS BOT - Community Scam Prevention System\n\nWelcome!",
            reply_markup=create_main_menu_keyboard(user_id)
        )
    
    logger.info(f"User {user_id} started bot")

def help_command(update: Update, context: CallbackContext) -> None:
    """Handle /help command"""
    if not check_private_chat(update):
        return
    
    user_id = update.effective_user.id
    help_text = lang.get_text(user_id, 'help')
    
    try:
        update.message.reply_text(
            help_text,
            parse_mode='MarkdownV2',
            reply_markup=create_main_menu_keyboard(user_id),
            disable_web_page_preview=True
        )
    except Exception as e:
        logger.error(f"Error sending help: {e}")
        update.message.reply_text(
            "ℹ️ Help: Use the menus below to interact with the bot.",
            reply_markup=create_main_menu_keyboard(user_id)
        )

def handle_message(update: Update, context: CallbackContext) -> None:
    """Handle regular messages"""
    if not check_private_chat(update):
        return
    
    user_id = update.effective_user.id
    text = update.message.text
    
    # Debug log
    logger.info(f"User {user_id} sent: {text}")
    
    # Determine action from menu text
    menu_action = lang.get_menu_action(text, user_id)
    
    if menu_action == 'menu_check':
        start_check(update, context)
    elif menu_action == 'menu_report':
        start_report(update, context)
    elif menu_action == 'menu_tips':
        show_safe_tips(update, context)
    elif menu_action == 'menu_donate':
        show_donate(update, context)
    elif menu_action == 'menu_groups':
        show_trusted_groups(update, context)
    elif menu_action == 'menu_admins':
        show_trusted_admins(update, context)
    elif menu_action == 'menu_stats':
        show_top_scammers(update, context)
    elif menu_action == 'menu_help':
        help_command(update, context)
    elif menu_action == 'menu_language':
        show_language_menu(update, context)
    elif text == lang.get_text(user_id, 'cancel'):
        cancel_operation(update, context)
    else:
        # Default to main menu
        start_command(update, context)

# ============================================
# LANGUAGE HANDLING
# ============================================

def show_language_menu(update: Update, context: CallbackContext) -> None:
    """Show language selection menu"""
    if not check_private_chat(update):
        return
    
    user_id = update.effective_user.id
    text = lang.get_text(user_id, 'select_language')
    
    update.message.reply_text(
        text,
        parse_mode='MarkdownV2',
        reply_markup=lang.get_language_keyboard(user_id)
    )

def set_language(update: Update, context: CallbackContext) -> None:
    """Set user language"""
    query = update.callback_query
    user_id = query.from_user.id
    
    query.answer()
    
    if query.data == 'cancel_language':
        query.edit_message_text(lang.get_text(user_id, 'cancel'))
        context.bot.send_message(
            chat_id=user_id,
            text=lang.get_text(user_id, 'select_option'),
            reply_markup=create_main_menu_keyboard(user_id)
        )
        return
    
    lang_code = query.data.split('_')[1]
    
    # Update language
    db.update_user_language(user_id, lang_code)
    
    # Success notification
    language_name = {
        'en': 'English',
        'vi': 'Vietnamese',
        'zh': 'Chinese',
        'ru': 'Russian'
    }.get(lang_code, 'English')
    
    success_text = lang.get_text(
        user_id, 
        'language_changed',
        language=language_name
    )
    
    try:
        query.edit_message_text(
            text=success_text,
            parse_mode='MarkdownV2'
        )
    except:
        query.edit_message_text("✅ Language changed successfully!")
    
    # Show main menu with new language
    welcome_text = lang.get_text(user_id, 'main_menu')
    try:
        context.bot.send_message(
            chat_id=user_id,
            text=welcome_text,
            parse_mode='MarkdownV2',
            reply_markup=create_main_menu_keyboard(user_id),
            disable_web_page_preview=True
        )
    except:
        context.bot.send_message(
            chat_id=user_id,
            text="🛡️ FIGHT_SCAMS BOT\n\nWelcome!",
            reply_markup=create_main_menu_keyboard(user_id)
        )
    
    logger.info(f"User {user_id} changed language to {lang_code}")

# ============================================
# SCAM REPORT HANDLING
# ============================================

def start_report(update: Update, context: CallbackContext) -> int:
    """Start report process"""
    if not check_private_chat(update):
        return ConversationHandler.END
    
    user_id = update.effective_user.id
    
    # Check report limit
    can_report, reason = db.can_report(user_id)
    if not can_report:
        if reason == 'limit_exceeded':
            update.message.reply_text(
                lang.get_text(user_id, 'report_limit'),
                parse_mode='MarkdownV2',
                reply_markup=create_main_menu_keyboard(user_id)
            )
        return ConversationHandler.END
    
    # Start process
    context.user_data['report'] = {'user_id': user_id}
    
    update.message.reply_text(
        lang.get_text(user_id, 'report_start'),
        parse_mode='MarkdownV2',
        reply_markup=create_cancel_keyboard(user_id)
    )
    
    update.message.reply_text(
        lang.get_text(user_id, 'report_username'),
        parse_mode='MarkdownV2'
    )
    
    return REPORT_USERNAME

def report_username(update: Update, context: CallbackContext) -> int:
    """Handle scammer username"""
    user_id = update.effective_user.id
    username = update.message.text.strip()
    
    # Validate and format username
    if username.startswith('https://t.me/'):
        username = '@' + username.split('/')[-1]
    elif not username.startswith('@'):
        username = '@' + username
    
    if len(username) < 3:
        update.message.reply_text(
            lang.get_text(user_id, 'invalid_username'),
            parse_mode='MarkdownV2'
        )
        return REPORT_USERNAME
    
    context.user_data['report']['username'] = username
    
    update.message.reply_text(
        lang.get_text(user_id, 'report_link'),
        parse_mode='MarkdownV2'
    )
    
    return REPORT_LINK

def report_link(update: Update, context: CallbackContext) -> int:
    """Handle Telegram link"""
    user_id = update.effective_user.id
    telegram_link = update.message.text.strip()
    
    # Validate link
    if not telegram_link.startswith('http'):
        if telegram_link.startswith('@'):
            telegram_link = f"https://t.me/{telegram_link[1:]}"
        else:
            telegram_link = f"https://t.me/{telegram_link}"
    
    context.user_data['report']['telegram_link'] = telegram_link
    
    update.message.reply_text(
        lang.get_text(user_id, 'report_wallet'),
        parse_mode='MarkdownV2'
    )
    
    return REPORT_WALLET

def report_wallet(update: Update, context: CallbackContext) -> int:
    """Handle wallet ID"""
    user_id = update.effective_user.id
    wallet_id = update.message.text.strip()
    
    if len(wallet_id) < 5:
        update.message.reply_text(
            lang.get_text(user_id, 'invalid_wallet'),
            parse_mode='MarkdownV2'
        )
        return REPORT_WALLET
    
    context.user_data['report']['wallet_id'] = wallet_id
    
    update.message.reply_text(
        lang.get_text(user_id, 'report_amount'),
        parse_mode='MarkdownV2'
    )
    
    return REPORT_AMOUNT

def report_amount(update: Update, context: CallbackContext) -> int:
    """Handle scam amount"""
    user_id = update.effective_user.id
    amount_text = update.message.text.strip()
    
    try:
        # Remove $ symbol if present
        amount_text_clean = amount_text.replace('$', '').replace(',', '').replace(' ', '')
        amount = float(amount_text_clean)
        if amount < 0:
            amount = 0
    except:
        amount = 0
    
    context.user_data['report']['amount'] = amount
    
    update.message.reply_text(
        lang.get_text(user_id, 'report_product'),
        parse_mode='MarkdownV2'
    )
    
    return REPORT_PRODUCT

def report_product(update: Update, context: CallbackContext) -> int:
    """Handle product/service"""
    user_id = update.effective_user.id
    product = update.message.text.strip()
    
    if len(product) < 3:
        update.message.reply_text(
            lang.get_text(user_id, 'invalid_product'),
            parse_mode='MarkdownV2'
        )
        return REPORT_PRODUCT
    
    context.user_data['report']['product'] = product
    
    # Show confirmation
    report_data = context.user_data['report']
    amount_display = f"{report_data.get('amount', 0):,.0f}$"
    
    confirm_text = lang.get_text(
        user_id, 
        'report_confirm',
        username=report_data.get('username', 'N/A'),
        link=report_data.get('telegram_link', 'N/A'),
        wallet=report_data.get('wallet_id', 'N/A'),
        amount=amount_display,
        product=report_data.get('product', 'N/A')
    )
    
    update.message.reply_text(
        confirm_text,
        parse_mode='MarkdownV2',
        reply_markup=create_confirm_keyboard(user_id)
    )
    
    return REPORT_CONFIRM

def report_confirm(update: Update, context: CallbackContext) -> int:
    """Handle report confirmation"""
    query = update.callback_query
    user_id = query.from_user.id
    
    query.answer()
    
    if query.data == 'report_confirm_yes':
        # Save report
        report_data = context.user_data.get('report', {})
        if not report_data:
            query.edit_message_text(
                text=lang.get_text(user_id, 'error'),
                parse_mode='MarkdownV2'
            )
            return ConversationHandler.END
        
        report_id = db.add_report(report_data)
        
        if report_id > 0:
            db.increment_user_report(user_id)
            user = db.get_user(user_id)
            
            # Calculate protected users (estimate)
            protected_count = user['report_count'] * 3
            
            # Professional success notification
            success_text = lang.get_text(
                user_id,
                'report_success',
                report_id=report_id,
                timestamp=datetime.now().strftime("%Y-%m-%d %H:%M"),
                count_today=user['reports_today'],
                total_reports=user['report_count'],
                protected_count=protected_count
            )
            
            try:
                query.edit_message_text(
                    text=success_text,
                    parse_mode='MarkdownV2'
                )
            except:
                query.edit_message_text("✅ Report submitted successfully! Thank you for protecting the community!")
            
            logger.info(f"Report #{report_id} submitted by user {user_id}")
        else:
            query.edit_message_text(
                text=lang.get_text(user_id, 'error'),
                parse_mode='MarkdownV2'
            )
        
        # Show main menu
        context.bot.send_message(
            chat_id=user_id,
            text=lang.get_text(user_id, 'select_option'),
            reply_markup=create_main_menu_keyboard(user_id)
        )
    else:
        # Cancel report - WARNING
        try:
            query.edit_message_text(
                text=lang.get_text(user_id, 'report_cancel_warning'),
                parse_mode='MarkdownV2'
            )
        except:
            query.edit_message_text("❌ Report cancelled. Warning: False reports waste community resources.")
        
        # Show main menu
        context.bot.send_message(
            chat_id=user_id,
            text=lang.get_text(user_id, 'report_cancel'),
            reply_markup=create_main_menu_keyboard(user_id)
        )
    
    # Clear temporary data
    if 'report' in context.user_data:
        del context.user_data['report']
    
    return ConversationHandler.END

# ============================================
# SCAMMER CHECK HANDLING
# ============================================

def start_check(update: Update, context: CallbackContext) -> int:
    """Start check process"""
    if not check_private_chat(update):
        return ConversationHandler.END
    
    user_id = update.effective_user.id
    
    update.message.reply_text(
        lang.get_text(user_id, 'check_input'),
        parse_mode='MarkdownV2',
        reply_markup=create_cancel_keyboard(user_id)
    )
    
    return CHECK_INPUT

def process_check(update: Update, context: CallbackContext) -> int:
    """Process scammer search"""
    user_id = update.effective_user.id
    search_input = update.message.text.strip()
    
    if not search_input:
        update.message.reply_text(
            lang.get_text(user_id, 'invalid_input'),
            parse_mode='MarkdownV2',
            reply_markup=create_main_menu_keyboard(user_id)
        )
        return ConversationHandler.END
    
    # Show processing message
    try:
        processing_msg = update.message.reply_text(
            lang.get_text(user_id, 'processing'),
            parse_mode='MarkdownV2'
        )
    except:
        processing_msg = update.message.reply_text("⏳ Processing...")
    
    # Search
    results = db.find_scammer(search_input)
    
    # Update check count
    db.increment_user_check(user_id)
    
    # Remove processing message
    try:
        context.bot.delete_message(
            chat_id=user_id,
            message_id=processing_msg.message_id
        )
    except:
        pass
    
    if not results:
        no_results_text = lang.get_text(
            user_id,
            'check_no_results',
            query=search_input[:50],
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M")
        )
        
        try:
            update.message.reply_text(
                no_results_text,
                parse_mode='MarkdownV2',
                reply_markup=create_main_menu_keyboard(user_id)
            )
        except:
            update.message.reply_text(
                f"✅ No scam reports found for: {search_input[:50]}",
                reply_markup=create_main_menu_keyboard(user_id)
            )
        
        return ConversationHandler.END
    
    # Show detailed results
    for scammer in results[:3]:  # Limit to 3 results
        # Format dates
        first_report = scammer.get('first_report', datetime.now().isoformat())
        last_report = scammer.get('last_report', datetime.now().isoformat())
        
        try:
            first_date = datetime.fromisoformat(first_report).strftime("%Y-%m-%d")
            last_date = datetime.fromisoformat(last_report).strftime("%Y-%m-%d")
        except:
            first_date = first_report[:10]
            last_date = last_report[:10]
        
        # Get product list
        products = scammer.get('products', [])
        products_text = ', '.join(products) if products else 'Various products/services'
        
        # Format amount
        total_amount_display = f"{scammer.get('total_amount', 0):,.0f}$"
        
        check_text = lang.get_text(
            user_id,
            'check_results',
            username=scammer.get('username', 'Unknown'),
            link=scammer.get('telegram_link', 'N/A'),
            wallet=scammer.get('wallet_id', 'N/A'),
            report_count=scammer.get('report_count', 0),
            reporter_count=scammer.get('reporter_count', 0),
            total_amount=total_amount_display,
            first_report=first_date,
            last_report=last_date,
            products=products_text
        )
        
        try:
            update.message.reply_text(
                check_text,
                parse_mode='MarkdownV2',
                disable_web_page_preview=True
            )
        except Exception as e:
            logger.error(f"Error sending results: {e}")
            # Send simplified version
            simple_text = f"🚨 SCAM ALERT: {scammer.get('username', 'Unknown')}\n"
            simple_text += f"📊 Total Reports: {scammer.get('report_count', 0)}\n"
            simple_text += f"👥 Unique Reporters: {scammer.get('reporter_count', 0)}\n"
            simple_text += f"💰 Total Amount: {scammer.get('total_amount', 0):,.0f}$\n"
            simple_text += f"📅 First Report: {first_date}\n"
            simple_text += f"📅 Last Report: {last_date}\n"
            simple_text += f"📦 Products: {products_text}\n"
            simple_text += f"⚠️ RECOMMENDATION: Avoid ALL transactions with this user"
            
            update.message.reply_text(
                simple_text,
                disable_web_page_preview=True
            )
    
    # Return to main menu
    update.message.reply_text(
        lang.get_text(user_id, 'select_option'),
        reply_markup=create_main_menu_keyboard(user_id)
    )
    
    return ConversationHandler.END

# ============================================
# OTHER MENUS
# ============================================

def show_safe_tips(update: Update, context: CallbackContext) -> None:
    """Show safe trading tips"""
    if not check_private_chat(update):
        return
    
    user_id = update.effective_user.id
    tips_text = lang.get_text(user_id, 'safe_tips')
    
    try:
        update.message.reply_text(
            tips_text,
            parse_mode='MarkdownV2',
            reply_markup=create_main_menu_keyboard(user_id),
            disable_web_page_preview=True
        )
    except:
        update.message.reply_text(
            "⚠️ SECURITY TIPS:\n\n1. Always verify users before transactions\n2. Use trusted mediators\n3. Never send payment in advance\n4. Keep transaction evidence\n5. Use escrow for large amounts",
            reply_markup=create_main_menu_keyboard(user_id)
        )

def show_donate(update: Update, context: CallbackContext) -> None:
    """Show donation information"""
    if not check_private_chat(update):
        return
    
    user_id = update.effective_user.id
    
    try:
        donate_text = lang.get_text(user_id, 'donate')
        
        update.message.reply_text(
            donate_text,
            parse_mode='MarkdownV2',
            disable_web_page_preview=True,
            reply_markup=create_main_menu_keyboard(user_id)
        )
    except Exception as e:
        logger.error(f"Error in show_donate: {e}")
        update.message.reply_text(
            "💝 SUPPORT DEVELOPMENT\n\n"
            "Binance ID: 154265504\n\n"
            "Thank you for supporting the system!",
            reply_markup=create_main_menu_keyboard(user_id)
        )

def show_trusted_groups(update: Update, context: CallbackContext) -> None:
    """Show trusted trading groups"""
    if not check_private_chat(update):
        return
    
    user_id = update.effective_user.id
    groups_text = lang.get_text(user_id, 'trusted_groups')
    
    try:
        update.message.reply_text(
            groups_text,
            parse_mode='MarkdownV2',
            disable_web_page_preview=False,
            reply_markup=create_main_menu_keyboard(user_id)
        )
    except:
        update.message.reply_text(
            "👥 TRUSTED TRADING GROUPS:\n\n"
            "• Community Trading Hub: https://t.me/j5FS6B_V9DM5ZmVl\n"
            "• Crypto Trading Network\n"
            "• Game Account Marketplace",
            disable_web_page_preview=False,
            reply_markup=create_main_menu_keyboard(user_id)
        )

def show_trusted_admins(update: Update, context: CallbackContext) -> None:
    """Show trusted mediators"""
    if not check_private_chat(update):
        return
    
    user_id = update.effective_user.id
    admins_text = lang.get_text(user_id, 'trusted_admins')
    
    try:
        update.message.reply_text(
            admins_text,
            parse_mode='MarkdownV2',
            disable_web_page_preview=False,
            reply_markup=create_main_menu_keyboard(user_id)
        )
    except:
        update.message.reply_text(
            "🛡️ TRUSTED MEDIATORS:\n\n"
            "• Siculator98: https://t.me/siculator98\n"
            "• Admin2\n"
            "• Admin3",
            disable_web_page_preview=False,
            reply_markup=create_main_menu_keyboard(user_id)
        )

def show_top_scammers(update: Update, context: CallbackContext) -> None:
    """Show scammer statistics"""
    if not check_private_chat(update):
        return
    
    user_id = update.effective_user.id
    
    # Get top scammers
    top_scammers = db.get_top_scammers(10)
    stats = db.get_statistics()
    
    # Create scammer list
    scammers_list = format_scammer_list(top_scammers, user_id)
    
    # Format amount
    total_amount_display = f"{stats.get('total_amount_scammed', 0):,.0f}$"
    
    stats_text = lang.get_text(
        user_id,
        'top_scammers',
        scammers_list=scammers_list,
        total_reports=stats.get('total_reports', 0),
        total_scammers=stats.get('total_scammers', 0),
        active_users=stats.get('active_users', 0),
        total_checks=stats.get('total_checks', 0),
        total_amount=total_amount_display,
        recent_reports=stats.get('recent_reports', 0),
        timestamp=datetime.now().strftime("%Y-%m-%d %H:%M")
    )
    
    try:
        update.message.reply_text(
            stats_text,
            parse_mode='MarkdownV2',
            reply_markup=create_main_menu_keyboard(user_id),
            disable_web_page_preview=True
        )
    except:
        # Send simplified version
        simple_text = f"📊 SCAMMER STATISTICS\n\n"
        simple_text += f"Total Reports: {stats.get('total_reports', 0)}\n"
        simple_text += f"Total Scammers: {stats.get('total_scammers', 0)}\n"
        simple_text += f"Users: {stats.get('active_users', 0)}\n"
        simple_text += f"Checks: {stats.get('total_checks', 0)}\n"
        simple_text += f"Total Loss: {stats.get('total_amount_scammed', 0):,.0f}$"
        
        update.message.reply_text(
            simple_text,
            reply_markup=create_main_menu_keyboard(user_id)
        )

# ============================================
# SUPPORT UTILITIES
# ============================================

def cancel_operation(update: Update, context: CallbackContext) -> int:
    """Cancel current operation"""
    user_id = update.effective_user.id
    
    update.message.reply_text(
        lang.get_text(user_id, 'report_cancel'),
        reply_markup=create_main_menu_keyboard(user_id)
    )
    
    # Clear temporary data
    if 'report' in context.user_data:
        del context.user_data['report']
    
    return ConversationHandler.END

def error_handler(update: Update, context: CallbackContext) -> None:
    """Handle errors"""
    logger.error(f"Update {update} caused error {context.error}", exc_info=True)
    
    if update and update.effective_user:
        user_id = update.effective_user.id
        try:
            context.bot.send_message(
                chat_id=user_id,
                text=lang.get_text(user_id, 'error'),
                reply_markup=create_main_menu_keyboard(user_id)
            )
        except:
            pass

# ============================================
# MAIN FUNCTION
# ============================================

def main() -> None:
    """Main function to run the bot"""
    
    # Get token from environment variable
    TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
    if not TOKEN:
        print("❌ Please set TELEGRAM_BOT_TOKEN in .env file")
        print("👉 Create .env file with: TELEGRAM_BOT_TOKEN=your_token_here")
        return
    
    # Initialize updater
    updater = Updater(TOKEN, use_context=True)
    dispatcher = updater.dispatcher
    
    # ========== CONVERSATION HANDLERS ==========
    
    # Handler for scam report
    report_conv_handler = ConversationHandler(
        entry_points=[MessageHandler(
            Filters.regex(r'^(🚨 Report Scammer|🚨 Báo cáo lừa đảo)$'), 
            start_report
        )],
        states={
            REPORT_USERNAME: [MessageHandler(Filters.text & ~Filters.command, report_username)],
            REPORT_LINK: [MessageHandler(Filters.text & ~Filters.command, report_link)],
            REPORT_WALLET: [MessageHandler(Filters.text & ~Filters.command, report_wallet)],
            REPORT_AMOUNT: [MessageHandler(Filters.text & ~Filters.command, report_amount)],
            REPORT_PRODUCT: [MessageHandler(Filters.text & ~Filters.command, report_product)],
            REPORT_CONFIRM: [CallbackQueryHandler(report_confirm, pattern='^report_confirm_')],
        },
        fallbacks=[
            CommandHandler('cancel', cancel_operation),
            MessageHandler(Filters.regex(r'^(❌ Cancel)$'), cancel_operation)
        ],
        allow_reentry=True
    )
    
    # Handler for scammer check
    check_conv_handler = ConversationHandler(
        entry_points=[MessageHandler(
            Filters.regex(r'^(🔍 Verify User/Transaction|🔍 Kiểm tra đối tượng)$'), 
            start_check
        )],
        states={
            CHECK_INPUT: [MessageHandler(Filters.text & ~Filters.command, process_check)],
        },
        fallbacks=[
            CommandHandler('cancel', cancel_operation),
            MessageHandler(Filters.regex(r'^(❌ Cancel)$'), cancel_operation)
        ],
        allow_reentry=True
    )
    
    # ========== REGISTER HANDLERS ==========
    
    # Command handlers
    dispatcher.add_handler(CommandHandler('start', start_command))
    dispatcher.add_handler(CommandHandler('help', help_command))
    dispatcher.add_handler(CommandHandler('stats', show_top_scammers))
    dispatcher.add_handler(CommandHandler('donate', show_donate))
    
    # Conversation handlers
    dispatcher.add_handler(report_conv_handler)
    dispatcher.add_handler(check_conv_handler)
    
    # Callback query handlers
    dispatcher.add_handler(CallbackQueryHandler(set_language, pattern='^(setlang_|cancel_language)'))
    
    # Message handler
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))
    
    # Error handler
    dispatcher.add_error_handler(error_handler)
    
    # ========== START BOT ==========
    
    # Run bot
    print("🛡️  FIGHT_SCAMS BOT - COMMUNITY SCAM PREVENTION SYSTEM")
    print("=" * 60)
    print(f"📊 System Statistics:")
    stats = db.get_statistics()
    print(f"   • Total Reports: {stats['total_reports']}")
    print(f"   • Total Scammers: {stats['total_scammers']}")
    print(f"   • Total Users: {stats['active_users']}")
    print(f"   • Total Checks: {stats['total_checks']}")
    print(f"   • Total Loss: {stats.get('total_amount_scammed', 0):,.0f}$")
    print("=" * 60)
    
    # Start polling
    updater.start_polling()
    print("✅ Bot started successfully!")
    print("📱 Use /start on Telegram to begin")
    print("⚡ Version: 3.2.0 - Professional Edition")
    print("🌐 Primary Language: ENGLISH (Default & System Operations)")
    print("⚠️  Note: Bot operates only in private chat")
    print("=" * 60)
    
    # Run until Ctrl+C
    updater.idle()

# ============================================
# MAIN ENTRY POINT
# ============================================

if __name__ == '__main__':
    main()
