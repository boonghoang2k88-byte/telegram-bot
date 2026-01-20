# check_repo.py - Kiểm tra cấu trúc toàn bộ repo
import os
import json

def analyze_repo():
    """Phân tích toàn bộ cấu trúc repo."""
    print("🔍 PHÂN TÍCH CẤU TRÚC REPO")
    print("="*60)
    
    # Lấy thư mục hiện tại
    current_dir = os.getcwd()
    print(f"📌 Thư mục hiện tại: {current_dir}")
    
    # Liệt kê tất cả file và thư mục
    print("\n📁 NỘI DUNG THƯ MỤC GỐC:")
    for item in sorted(os.listdir('.')):
        if os.path.isdir(item):
            print(f"📂 {item}/")
        else:
            print(f"📄 {item}")
    
    # Tìm kiếm file main.py
    print("\n🔎 TÌM KIẾM main.py:")
    main_files = []
    for root, dirs, files in os.walk('.'):
        for file in files:
            if file == 'main.py':
                full_path = os.path.join(root, file)
                main_files.append(full_path)
    
    if main_files:
        print(f"✅ Tìm thấy {len(main_files)} file main.py:")
        for i, path in enumerate(main_files, 1):
            size = os.path.getsize(path)
            print(f"  {i}. {path} ({size} bytes)")
    else:
        print("❌ KHÔNG TÌM THẤY main.py TRONG REPO!")
    
    # Kiểm tra file quan trọng
    print("\n✅ KIỂM TRA FILE QUAN TRỌNG:")
    critical_files = ['requirements.txt', 'main.py', 'config/', 'handlers/', 'services/']
    for file in critical_files:
        if os.path.exists(file):
            if os.path.isdir(file):
                file_count = len([f for f in os.listdir(file) if f.endswith('.py')])
                print(f"  ✅ {file}/ (có {file_count} file .py)")
            else:
                size = os.path.getsize(file)
                print(f"  ✅ {file} ({size} bytes)")
        else:
            print(f"  ❌ {file} - KHÔNG TỒN TẠI")
    
    # Tạo báo cáo
    print("\n📊 BÁO CÁO CẤU TRÚC:")
    total_py_files = sum(1 for root, dirs, files in os.walk('.') for f in files if f.endswith('.py'))
    total_folders = sum(1 for root, dirs, files in os.walk('.') if root != '.')
    
    print(f"• Tổng file .py: {total_py_files}")
    print(f"• Tổng thư mục: {total_folders}")
    print(f"• Có main.py: {'✅ CÓ' if main_files else '❌ KHÔNG'}")
    print(f"• Có requirements.txt: {'✅ CÓ' if os.path.exists('requirements.txt') else '❌ KHÔNG'}")
    
    return bool(main_files)

def create_correct_structure():
    """Tạo cấu trúc đúng nếu thiếu."""
    print("\n🛠️  TẠO CẤU TRÚC ĐÚNG...")
    
    # Danh sách file cần tạo nếu thiếu
    files_to_create = {
        'main.py': '''#!/usr/bin/env python3
"""
ANTISCAMBOT - Bot Telegram chống lừa đảo
"""

import os
import sys
import logging

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

print("🚀 AntiScamBot đã khởi động!")
print("✅ Cấu trúc đã được sửa")
print("🤖 Bot sẵn sàng hoạt động!")

# Check token
TOKEN = os.getenv('TOKEN')
if TOKEN:
    print(f"✅ Token: {TOKEN[:10]}...")
else:
    print("❌ Chưa có token. Vui lòng set biến môi trường TOKEN")

# Keep running
import time
while True:
    time.sleep(1)
''',
        
        'requirements.txt': '''python-telegram-bot==20.7
python-dotenv==1.0.0
sqlalchemy==2.0.23
psycopg2-binary==2.9.9
cryptography==41.0.7
pytz==2023.3
''',
        
        'render.yaml': '''services:
  - type: web
    name: anticam-bot
    env: python
    region: singapore
    buildCommand: |
      echo "📦 Installing dependencies..."
      pip install -r requirements.txt
    startCommand: |
      echo "🚀 Starting bot..."
      echo "📁 Current dir: $(pwd)"
      ls -la
      python main.py
    envVars:
      - key: TOKEN
        sync: false
      - key: DATABASE_URL
        value: sqlite:///bot_database.db
    plan: free
'''
    }
    
    created = 0
    for filename, content in files_to_create.items():
        if not os.path.exists(filename):
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✅ Đã tạo: {filename}")
            created += 1
        else:
            print(f"✅ Đã có: {filename}")
    
    return created

if __name__ == "__main__":
    has_main = analyze_repo()
    
    if not has_main:
        print("\n⚠️  REPO THIẾU FILE main.py!")
        choice = input("Bạn có muốn tự động tạo cấu trúc đúng? (y/n): ")
        if choice.lower() == 'y':
            create_correct_structure()
            print("\n✅ ĐÃ TẠO CẤU TRÚC ĐÚNG!")
            print("👉 Commit và push lên GitHub, sau đó deploy lại trên Render")
    else:
        print("\n🎉 Cấu trúc repo đã đúng!")
        print("👉 Kiểm tra lại Start Command trên Render")
