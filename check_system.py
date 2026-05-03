#!/usr/bin/env python
"""Complete system verification for SmartVision OCR Pro"""
import sys
import subprocess
from pathlib import Path

def check_file(path, description):
    """Check if a file exists"""
    if Path(path).exists():
        print(f"  ✅ {description}: {path}")
        return True
    else:
        print(f"  ❌ {description}: {path} - NOT FOUND")
        return False

def check_directory(path, description):
    """Check if a directory exists"""
    if Path(path).is_dir():
        print(f"  ✅ {description}: {path}")
        return True
    else:
        print(f"  ❌ {description}: {path} - NOT FOUND")
        return False

def main():
    print("\n╔═══════════════════════════════════════════════════════════╗")
    print("║  SmartVision OCR Pro - System Verification               ║")
    print("╚═══════════════════════════════════════════════════════════╝\n")
    
    all_good = True
    
    # Check project structure
    print("📁 Checking Project Structure...")
    all_good &= check_file("frontend/index.html", "Frontend UI")
    all_good &= check_file("frontend/vercel.json", "Vercel config")
    all_good &= check_file("backend/app.py", "Flask API")
    all_good &= check_file("backend/requirements.txt", "Backend deps")
    all_good &= check_file("backend/Procfile", "Procfile")
    all_good &= check_file("backend/render.yaml", "Render config")
    all_good &= check_directory("api", "API serverless functions")
    
    # Check documentation
    print("\n📚 Checking Documentation...")
    all_good &= check_file("README.md", "README")
    all_good &= check_file("DEPLOYMENT.md", "Deployment guide")
    all_good &= check_file(".gitignore", "Git ignore")
    
    # Check helper scripts
    print("\n🔧 Checking Helper Scripts...")
    all_good &= check_file("start.bat", "Windows startup")
    all_good &= check_file("test_ocr.py", "Test script")
    all_good &= check_file("verify_deps.py", "Dependency verification")
    
    # Check Python dependencies
    print("\n📦 Checking Python Dependencies...")
    required_packages = [
        ('flask', 'flask'),
        ('flask_cors', 'flask_cors'),
        ('cv2', 'cv2'),
        ('pytesseract', 'pytesseract'),
        ('easyocr', 'easyocr'),
        ('textblob', 'textblob'),
        ('langdetect', 'langdetect'),
        ('gtts', 'gtts'),
        ('PIL', 'PIL'),
        ('numpy', 'numpy'),
        ('fpdf2', 'fpdf'),
    ]
    
    for name, import_name in required_packages:
        try:
            __import__(import_name)
            print(f"  ✅ {name}")
        except ImportError:
            print(f"  ❌ {name} - NOT INSTALLED")
            all_good = False
    
    # Summary
    print("\n" + "═" * 60)
    if all_good:
        print("✅ ALL CHECKS PASSED! System is ready.\n")
        print("Next steps:")
        print("  1. Windows: Double-click start.bat")
        print("  2. Linux/Mac: python backend/app.py")
        print("  3. Open: frontend/index.html")
        print("  4. Deploy: Push to GitHub → vercel.com/new")
        return 0
    else:
        print("⚠️  SOME CHECKS FAILED! Please review above.\n")
        print("Run:")
        print("  pip install -r requirements.txt")
        print("  python verify_deps.py")
        return 1

if __name__ == "__main__":
    sys.exit(main())
