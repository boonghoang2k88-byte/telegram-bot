# create_init_files.py
import os

# Danh sách thư mục cần tạo __init__.py
folders = [
    '.',
    'config',
    'core',
    'handlers',
    'services',
    'db',
    'locales',
    'utils'
]

print("📁 Creating __init__.py files...")

for folder in folders:
    if os.path.exists(folder):
        init_file = os.path.join(folder, '__init__.py')
        if not os.path.exists(init_file):
            with open(init_file, 'w') as f:
                f.write('# Package initialization\n')
            print(f"✅ Created: {init_file}")
        else:
            print(f"✅ Already exists: {init_file}")
    else:
        print(f"⚠️  Folder not found: {folder}")

print("\n✅ Done! All __init__.py files created.")
