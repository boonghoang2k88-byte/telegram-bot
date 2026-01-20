# fix_imports.py
import os
import sys

def fix_all_imports():
    """Fix imports by adding __init__.py files and checking structure."""
    
    print("🔧 Fixing imports structure...")
    
    # 1. Create __init__.py files
    create_init_files()
    
    # 2. Check import paths
    check_imports()
    
    # 3. Test imports
    test_imports()

def create_init_files():
    """Create __init__.py in all directories."""
    folders = ['.', 'config', 'core', 'handlers', 'services', 'db', 'locales', 'utils']
    
    for folder in folders:
        if os.path.exists(folder) and os.path.isdir(folder):
            init_file = os.path.join(folder, '__init__.py')
            if not os.path.exists(init_file):
                with open(init_file, 'w') as f:
                    f.write('# Package initialization\n')
                print(f"✅ Created: {init_file}")
            else:
                print(f"✅ Exists: {init_file}")

def check_imports():
    """Check all import statements in main.py."""
    print("\n🔍 Checking imports in main.py...")
    
    if os.path.exists('main.py'):
        with open('main.py', 'r') as f:
            content = f.read()
        
        # Check for problematic imports
        if 'from handlers.' in content or 'import handlers' in content:
            print("✅ Found handlers imports in main.py")
        else:
            print("⚠️  No handlers imports found in main.py")
            
        # Check if all imports are relative
        lines = content.split('\n')
        for i, line in enumerate(lines, 1):
            if 'import' in line and 'handlers' in line:
                print(f"  Line {i}: {line.strip()}")
    else:
        print("❌ main.py not found!")

def test_imports():
    """Test if imports work."""
    print("\n🧪 Testing imports...")
    
    # Add current directory to path
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    
    test_modules = [
        ('config.settings', 'TOKEN'),
        ('handlers.start', 'start_command'),
        ('services.language_service', 'get_text'),
        ('db.database', 'get_scam_statistics'),
    ]
    
    for module_path, attr_name in test_modules:
        try:
            module = __import__(module_path, fromlist=[attr_name])
            print(f"✅ {module_path}: OK")
        except ImportError as e:
            print(f"❌ {module_path}: {e}")

if __name__ == "__main__":
    fix_all_imports()
