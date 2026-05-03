#!/bin/bash
# Install Tesseract OCR and language packs
apt-get update && apt-get install -y tesseract-ocr tesseract-ocr-all libgl1
# Download TextBlob corpora
python -m textblob.download_corpora
echo "✅ System dependencies installed"
