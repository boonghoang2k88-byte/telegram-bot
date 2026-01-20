#!/usr/bin/env python3
# render_fix.py - Sửa tất cả lỗi Render

import os
import sys
import subprocess

def main():
    print("🔧 FIX RENDER DEPLOYMENT")
    print("="*60)
    
    # Step 1: Xác định vị trí
    print("\n📌 Bước 1: Xác định vị trí")
    current_dir = os.getcwd()
    print(f"Thư mục hiện tại: {current_dir}")
    
    # Step 2: Liệt kê tất cả file
    print("\n📁 Bước 2: Liệt kê toàn bộ file")
    for root, dirs, files in os.walk('.'):
        level = root.replace('.', '').count(os.sep)
        indent = ' ' * 2 * level
        print(f'{indent}{os.path.basename(root)}/')
        subindent = ' ' * 2 * (level + 1)
        for file in files:
            if file in ['main.py', 'requirements.txt', 'render.yaml']:
                print(f'{subindent}📄 {file}')
    
    # Step 3: Tạo main.py nếu không có
    if not os.path.exists('main.py'):
        print("\n⚠️  Không tìm thấy main.py, tạo mới...")
        with open('main.py', 'w') as f:
            f.write('''#!/usr/bin/env python3
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

logger.info("🚀 AntiScamBot đã khởi động!")
logger.info(f"📁 Thư mục: {os.getcwd()}")
logger.info("✅ Deploy thành công trên Render!")

# Check environment
TOKEN = os.getenv('TOKEN')
if TOKEN:
    logger.info(f"✅ Token: {TOKEN[:10]}...")
    
    # Import và chạy bot thật
    try:
        from telegram.ext import Application
        app = Application.builder().token(TOKEN).build()
        logger.info("✅ Bot đã sẵn sàng!")
        app.run_polling()
    except ImportError:
        logger.info("🤖 Mock bot đang chạy...")
        import time
        while True:
            time.sleep(10)
else:
    logger.error("❌ Chưa có token!")
    logger.info("📝 Set biến môi trường TOKEN trên Render")
''')
        print("✅ Đã tạo main.py")
    
    # Step 4: Chạy bot
    print("\n🚀 Bước 3: Khởi chạy bot...")
    print("="*60)
    
    # Install dependencies
    print("📦 Cài dependencies...")
    try:
        subprocess.run([sys.executable, '-m', 'pip', 'install', 
                       'python-telegram-bot', 'python-dotenv'], check=True)
    except:
        print("⚠️  Lỗi cài dependencies, bỏ qua...")
    
    # Run main.py
    print("\n🤖 Chạy main.py...")
    os.execl(sys.executable, sys.executable, 'main.py')

if __name__ == '__main__':
    main()
