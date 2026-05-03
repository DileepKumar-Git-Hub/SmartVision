#!/usr/bin/env python
"""Verify dependencies are installed"""
import sys

try:
    print("✓ Flask")
    import flask
    print("✓ Flask-CORS")
    import flask_cors
    print("✓ OpenCV")
    import cv2
    print("✓ NumPy")
    import numpy
    print("✓ Pillow")
    import PIL
    print("✓ TextBlob")
    from textblob import TextBlob
    print("✓ langdetect")
    from langdetect import detect
    print("✓ EasyOCR")
    import easyocr
    print("✓ gTTS")
    from gtts import gTTS
    print("✓ fpdf2")
    from fpdf import FPDF
    print("✓ pytesseract")
    import pytesseract
    print("\n✅ All dependencies installed successfully!")
    
    # Download TextBlob corpora
    print("\nDownloading TextBlob corpora...")
    import nltk
    nltk.download('brown', quiet=True)
    nltk.download('punkt', quiet=True)
    print("✓ TextBlob corpora downloaded")
    
except ImportError as e:
    print(f"❌ Missing dependency: {e}", file=sys.stderr)
    sys.exit(1)
except Exception as e:
    print(f"⚠️  Warning: {e}")
