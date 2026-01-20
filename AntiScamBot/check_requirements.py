# check_requirements.py
import os
import sys

print("🔍 Checking project structure...")

# Check for requirements.txt
if os.path.exists('requirements.txt'):
    print("✅ requirements.txt found")
    with open('requirements.txt', 'r') as f:
        content = f.read()
        print(f"📄 Content ({len(content)} bytes):")
        print("-" * 40)
        print(content)
        print("-" * 40)
else:
    print("❌ requirements.txt NOT FOUND!")
    
    # Create it automatically
    print("📝 Creating requirements.txt...")
    requirements_content = """python-telegram-bot==20.7
python-dotenv==1.0.0
sqlalchemy==2.0.23
psycopg2-binary==2.9.9
cryptography==41.0.7
python-multipart==0.0.6
pytz==2023.3
"""
    
    with open('requirements.txt', 'w') as f:
        f.write(requirements_content)
    
    print("✅ Created requirements.txt")

# Check other essential files
print("\n📁 Checking other essential files:")
essential_files = ['main.py', 'config/', 'handlers/', 'services/', 'db/', 'locales/']
for item in essential_files:
    if os.path.exists(item):
        print(f"✅ {item}")
    else:
        print(f"❌ {item}")
