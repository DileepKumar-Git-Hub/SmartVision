# SmartVision OCR Pro - Deployment Guide

## 🚀 Quick Start (Local Development)

### Prerequisites
- Python 3.10+ (recommended 3.12)
- Git
- Tesseract OCR (for local development)

### Windows Setup

1. **Install Tesseract OCR:**
   ```bash
   # Using Chocolatey:
   choco install tesseract

   # Or download installer from:
   # https://github.com/UB-Mannheim/tesseract/wiki
   ```

2. **Clone and Setup:**
   ```bash
   git clone <repository>
   cd smartvision-ocr-pro
   python -m venv .venv
   .venv\Scripts\activate
   pip install -r requirements.txt
   python -m textblob.download_corpora
   ```

3. **Update pytesseract config (Windows):**
   Edit `backend/app.py` and add after imports:
   ```python
   import pytesseract
   pytesseract.pytesseract.pytesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
   ```

4. **Run Locally:**
   ```bash
   # Terminal 1: Backend
   python backend/app.py

   # Terminal 2: Frontend (open in browser)
   start frontend/index.html
   ```

   Backend will be available at: `http://localhost:5000`

---

## 📦 Deploy to Vercel

### Prerequisites
- Vercel account (free)
- Git repository on GitHub

### Deployment Steps

1. **Push to GitHub:**
   ```bash
   git add .
   git commit -m "Initial commit"
   git push origin main
   ```

2. **Import to Vercel:**
   - Go to [vercel.com/new](https://vercel.com/new)
   - Import your GitHub repository
   - Click "Deploy"

3. **Configure Environment:**
   - No special env variables needed
   - Vercel will auto-detect Python requirements

4. **Access Your App:**
   - Frontend: `https://your-project.vercel.app`
   - API: `https://your-project.vercel.app/api/...`

### Important Notes:
- Database persists in `/tmp` during deployment
- First request will be slower (EasyOCR model loading)
- Large image processing may timeout (adjust in handlers)

---

## 🐳 Deploy to Docker (Alternative)

Create `Dockerfile`:
```dockerfile
FROM python:3.12-slim
RUN apt-get update && apt-get install -y tesseract-ocr libgl1
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt && python -m textblob.download_corpora
COPY . .
CMD ["gunicorn", "backend.app:app", "--bind", "0.0.0.0:5000"]
```

Deploy to Render:
1. Create `render.yaml` (included)
2. Connect GitHub repo to Render
3. Deploy!

---

## 🔧 Troubleshooting

### "Tesseract not found"
- **Windows:** Install via Chocolatey and update path in app.py
- **Linux:** `sudo apt-get install tesseract-ocr tesseract-ocr-all`
- **Mac:** `brew install tesseract`

### "Module not found"
```bash
pip install -r requirements.txt
```

### EasyOCR model loading timeout
- Models auto-download on first use (~350 MB)
- Subsequent requests are fast

### Vercel timeout on large images
- Limit image size to 5MB
- Reduce image resolution
- Increase serverless function timeout

---

## 📱 Configuration

### Frontend Settings
Open browser DevTools Console or Settings tab to:
- Change backend URL (e.g., for custom domain)
- Switch theme (dark/light)
- Clear history

Backend URL is stored in `localStorage.ocr_backend`

---

## 🎯 Features

✅ Dual OCR (Tesseract + EasyOCR)
✅ 25+ Languages
✅ Auto-correction & Grammar
✅ Language Detection
✅ Text-to-Speech (gTTS)
✅ Export (TXT/JSON/PDF)
✅ Scan History (SQLite)
✅ Live Webcam OCR
✅ Dark/Light Theme

---

## 📊 Architecture

```
smartvision-ocr-pro/
├── frontend/
│   ├── index.html          (Full SPA + CSS)
│   └── vercel.json         (Vercel config)
├── backend/
│   ├── app.py              (Flask API)
│   ├── requirements.txt     (Dependencies)
│   ├── Procfile            (Render deployment)
│   ├── render.yaml         (Render config)
│   └── build.sh            (Build script)
├── api/                    (Vercel serverless)
│   ├── health.py
│   ├── ocr.py
│   └── history.py
└── README.md
```

---

## 📈 Performance Tips

1. **Image Size:** Keep under 5MB
2. **Resolution:** 1200x800 optimal for OCR
3. **Language:** Specify language for faster processing
4. **Caching:** EasyOCR readers are cached per language

---

## 📝 License

MIT License - See LICENSE file

---

Made with ❤️ by SmartVision Team
