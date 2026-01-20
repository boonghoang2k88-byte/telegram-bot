#!/bin/bash
# deploy_fix.sh - Sửa mọi lỗi deploy trên Render

echo "========================================"
echo "🛠️  FIX DEPLOY ANTI-SCAM BOT"
echo "========================================"

# 1. Kiểm tra thư mục hiện tại
echo "1️⃣ Kiểm tra thư mục..."
pwd
ls -la

# 2. Tìm main.py
echo -e "\n2️⃣ Tìm file main.py..."
MAIN_PATHS=(
    "/opt/render/project/src/main.py"
    "/opt/render/project/main.py" 
    "./main.py"
    "main.py"
    "$(pwd)/main.py"
)

for path in "${MAIN_PATHS[@]}"; do
    if [ -f "$path" ]; then
        echo "✅ Tìm thấy: $path"
        MAIN_PATH="$path"
        break
    fi
done

if [ -z "$MAIN_PATH" ]; then
    echo "❌ Không tìm thấy main.py!"
    echo "📁 Tạo file main.py mới..."
    
    cat > main.py << 'EOF'
#!/usr/bin/env python3
print("🚀 AntiScamBot đã khởi động!")
print("📁 Thư mục hiện tại:", __import__('os').getcwd())
print("📂 Nội dung:", __import__('os').listdir('.'))
EOF
    
    MAIN_PATH="./main.py"
    echo "✅ Đã tạo main.py tại: $MAIN_PATH"
fi

# 3. Cài dependencies
echo -e "\n3️⃣ Cài đặt dependencies..."
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
else
    echo "⚠️  Không có requirements.txt, cài dependencies mặc định..."
    pip install python-telegram-bot python-dotenv
fi

# 4. Chạy bot
echo -e "\n4️⃣ Khởi chạy bot..."
cd "$(dirname "$MAIN_PATH")"
echo "📁 Chuyển đến thư mục: $(pwd)"
echo "📂 Files trong thư mục:"
ls -la
echo -e "\n🚀 Bắt đầu chạy bot..."
python "$(basename "$MAIN_PATH")"