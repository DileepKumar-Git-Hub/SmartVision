# 👁️ SmartVision OCR Pro

> Advanced OCR with hybrid Tesseract + EasyOCR, NLP auto-correction, TTS, history, and exports

![Status](https://img.shields.io/badge/status-active-brightgreen)
![Python](https://img.shields.io/badge/python-3.10+-blue)
![License](https://img.shields.io/badge/license-MIT-green)

---

## ✨ Features

✅ **Dual OCR Engines** - Tesseract + EasyOCR with intelligent fusion  
✅ **25+ Languages** - Auto-detection and multi-language support  
✅ **Auto-Correction** - Grammar and spelling fixes via TextBlob  
✅ **Text Detection** - Visual bounding boxes for recognized regions  
✅ **Live Webcam** - Real-time OCR from camera feed  
✅ **Text-to-Speech** - Convert extracted text to MP3 (gTTS)  
✅ **Export** - TXT, JSON, PDF formats with metadata  
✅ **History** - SQLite database with search and filtering  
✅ **Dark/Light Theme** - Beautiful responsive UI  
✅ **Fast** - Cached model loading and optimized preprocessing  

---

## 🏗 Project Structure

```
smartvision-ocr-pro/
├── frontend/
│   ├── index.html              # Complete SPA + CSS
│   └── vercel.json             # Vercel configuration
├── backend/
│   ├── app.py                  # Flask API
│   ├── requirements.txt         # Python dependencies
│   ├── Procfile                # Render deployment
│   ├── render.yaml             # Render configuration
│   └── build.sh                # Build script
├── api/                        # Vercel serverless functions
│   ├── health.py
│   ├── ocr.py
│   └── history.py
├── test_ocr.py                 # Test script
├── verify_deps.py              # Dependency verification
├── start.bat                   # Windows startup script
├── .gitignore
├── README.md                   # Documentation
└── DEPLOYMENT.md               # Deployment guide
```

---

## 🚀 Quick Start

### Windows (Easiest)

```bash
# 1. Clone repository
git clone https://github.com/yourusername/smartvision-ocr-pro.git
cd smartvision-ocr-pro

# 2. Run startup script
start.bat

# 3. Open browser
start frontend/index.html
```

### Linux / Mac

```bash
# 1. Install Tesseract
# Ubuntu:
sudo apt-get install tesseract-ocr tesseract-ocr-all

# macOS:
brew install tesseract

# 2. Clone and setup
git clone https://github.com/yourusername/smartvision-ocr-pro.git
cd smartvision-ocr-pro

python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python -m textblob.download_corpora

# 3. Run backend
python backend/app.py

# 4. Open frontend in browser
open frontend/index.html
```

---

## 📦 Full Installation

### Prerequisites
- **Python 3.10+** (Tested on 3.12.10)
- **Tesseract OCR**
- **Git**

### Windows Installation

1. **Install Tesseract:**
   ```bash
   choco install tesseract  # Using Chocolatey
   # OR download from: https://github.com/UB-Mannheim/tesseract/wiki
   ```

2. **Install Dependencies:**
   ```bash
   python -m venv .venv
   .venv\Scripts\activate
   pip install -r requirements.txt
   python -m textblob.download_corpora
   ```

3. **Configure Tesseract Path (if needed):**
   Edit `backend/app.py` after imports:
   ```python
   import pytesseract
   pytesseract.pytesseract.pytesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
   ```

4. **Run:**
   ```bash
   python backend/app.py
   ```

### Linux Installation

```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install -y python3-pip tesseract-ocr tesseract-ocr-all libgl1

# Install Python dependencies
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python -m nltk.downloader brown punkt
```

### macOS Installation

```bash
# Install Tesseract
brew install tesseract tesseract-lang

# Python setup
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python -m textblob.download_corpora
```

---

## 🌐 Deployment

### Deploy to Vercel (Recommended)

1. **Push to GitHub:**
   ```bash
   git add .
   git commit -m "Initial commit"
   git push origin main
   ```

2. **Go to [vercel.com/new](https://vercel.com/new)**
   - Import your GitHub repository
   - Click Deploy

3. **Access your app:**
   - Frontend: `https://your-project.vercel.app`
   - Backend API: Same URL (`/api/*` routes)

### Deploy to Render (Docker)

1. Create Render account
2. Connect GitHub repository
3. Deploy from `render.yaml`

See [DEPLOYMENT.md](DEPLOYMENT.md) for detailed instructions.

---

## 🎮 Usage

### Local Development

**Terminal 1 - Backend:**
```bash
python backend/app.py
```
Runs on `http://localhost:5000`

**Terminal 2 - Frontend:**
```bash
# Windows
start frontend/index.html

# Linux/Mac
open frontend/index.html
```

### API Endpoints

#### Health Check
```bash
GET /api/health
```

#### OCR Processing
```bash
POST /api/ocr
Content-Type: multipart/form-data OR application/json

# Upload file:
curl -F "image=@image.jpg" http://localhost:5000/api/ocr

# Send base64:
curl -X POST http://localhost:5000/api/ocr \
  -H "Content-Type: application/json" \
  -d '{"image_data":"data:image/jpeg;base64,..."}'
```

**Response:**
```json
{
  "success": true,
  "scan_id": "uuid-here",
  "raw_text": "Extracted text",
  "corrected_text": "Corrected text",
  "language": "English",
  "confidence": 94.5,
  "best_source": "easyocr",
  "summary": "Summary",
  "bounding_boxes": []
}
```

#### Scan History
```bash
GET /api/history
```

#### Search History
```bash
GET /api/history/search?q=keyword&start=2024-01-01&end=2024-12-31
```

#### Delete Scan
```bash
DELETE /api/history/{scan_id}
```

#### Text-to-Speech
```bash
POST /api/tts
{"text": "Say this", "lang": "en"}
```

#### Export
```bash
POST /api/export
{"format": "pdf", "text": "Content", "metadata": {...}}
```

---

## 🔧 Configuration

### Frontend Settings (In-Browser)

Click **⚙️ Settings** tab:
- Change backend URL
- Toggle dark/light theme
- Clear history

### Backend Configuration

Edit `backend/app.py`:
```python
# Tesseract path (Windows)
pytesseract.pytesseract.pytesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# Database location
DB_PATH = "custom/path/ocr_history.db"
```

---

## 📊 Performance

| Operation | Time |
|-----------|------|
| Image preprocessing | ~50ms |
| Tesseract OCR | ~200-500ms |
| EasyOCR | ~800-1500ms |
| Full pipeline | 1.2-2.5s |

**Optimization tips:**
- Resize to 1200x800 or smaller
- Specify language if known
- Enable caching

---

## 🐛 Troubleshooting

### "TesseractNotFoundError"
```bash
# Check installation
where tesseract  # Windows
which tesseract  # Linux/Mac

# Reinstall:
choco install tesseract          # Windows
sudo apt-get install tesseract-ocr  # Linux
brew install tesseract          # Mac
```

### "Port 5000 already in use"
```bash
# Windows
netstat -ano | findstr :5000
taskkill /PID <PID> /F

# Linux/Mac
lsof -ti:5000 | xargs kill -9
```

### EasyOCR slow on first run
- Models (~350 MB) download automatically
- Subsequent requests are 10x faster
- Cached in `~/.EasyOCR/`

### Vercel timeout on large images
- Limit to 5 MB uploads
- Reduce resolution
- Crop to relevant area

---

## 🌍 Supported Languages

25+ languages: English, Spanish, French, German, Chinese, Japanese, Korean, Arabic, Hindi, Portuguese, Russian, Italian, Dutch, Polish, Turkish, Thai, Vietnamese, Greek, Czech, Hungarian, and more!

---

## 🔒 Security & Privacy

- ✅ All processing server-side
- ✅ Local database (not cloud-synced)
- ✅ No telemetry
- ✅ CORS enabled for safe cross-origin
- ✅ Input validation on all endpoints

---

## 📚 Technologies

**Frontend:** HTML5, CSS3, Vanilla JavaScript  
**Backend:** Flask, OpenCV, Tesseract, EasyOCR, TextBlob, gTTS, fpdf2  
**Database:** SQLite  
**Deployment:** Vercel, Render.com  

---

## 📝 License

MIT License © 2024

---

**Made with ❤️ for the OCR community**

[⬆ back to top](#-smartvision-ocr-pro)

---

## 🚀 Local Setup

### 1. Install System Dependencies

**Ubuntu / Debian (or Render):**
```bash
sudo apt-get update
sudo apt-get install -y tesseract-ocr tesseract-ocr-all libgl1
```

**macOS:**
```bash
brew install tesseract
```

**Windows:**
- Download Tesseract installer from: https://github.com/UB-Mannheim/tesseract/wiki
- Add to PATH: `C:\Program Files\Tesseract-OCR`

### 2. Backend Setup

```bash
cd backend

# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate       # Windows: venv\Scripts\activate

# Install Python packages
pip install -r requirements.txt

# Download TextBlob corpora
python -m textblob.download_corpora

# Start the server
python app.py
```

Backend runs at: `http://localhost:5000`

### 3. Frontend

Just open `frontend/index.html` in your browser — it's a static file.
Set the Backend URL in the top banner to `http://localhost:5000` and click **Connect**.

---

## ☁️ Deployment

### Backend → Render.com (FREE, supports heavy Python deps)

1. Push the `backend/` folder to a GitHub repo
2. Go to [render.com](https://render.com) → **New Web Service**
3. Connect your GitHub repo
4. Set:
   - **Build Command:** `bash build.sh && pip install -r requirements.txt`
   - **Start Command:** `gunicorn app:app --bind 0.0.0.0:$PORT --timeout 120`
   - **Environment:** Python 3.11
5. Deploy → copy your URL, e.g. `https://smartvision-ocr.onrender.com`

### Frontend → Vercel (FREE)

1. Push the `frontend/` folder to a GitHub repo (or same repo, different folder)
2. Go to [vercel.com](https://vercel.com) → **New Project**
3. Import repo, set **Root Directory** to `frontend/`
4. Deploy → you get a URL like `https://smartvision-ocr.vercel.app`
5. Open the app, set Backend URL to your Render URL → click **Connect**

---

## 🔌 API Reference

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/health` | Health check |
| POST | `/api/ocr` | Process image (multipart or base64) |
| POST | `/api/tts` | Convert text to speech (MP3 base64) |
| GET | `/api/history` | Last 50 scans |
| GET | `/api/history/search?q=&start=&end=` | Search history |
| DELETE | `/api/history/<id>` | Delete a scan |
| POST | `/api/export` | Export TXT/JSON/PDF |

### OCR Request (file upload)
```bash
curl -X POST http://localhost:5000/api/ocr \
  -F "image=@sample.jpg"
```

### OCR Request (base64 / camera)
```bash
curl -X POST http://localhost:5000/api/ocr \
  -H "Content-Type: application/json" \
  -d '{"image_data": "data:image/jpeg;base64,..."}'
```

### OCR Response
```json
{
  "success": true,
  "scan_id": "uuid",
  "raw_text": "...",
  "corrected_text": "...",
  "corrections": {"teh": "the"},
  "language": "English",
  "language_code": "en",
  "confidence": 87.3,
  "best_source": "easyocr",
  "comparison": {
    "tesseract": {"text": "...", "confidence": 71.2},
    "easyocr":   {"text": "...", "confidence": 87.3}
  },
  "bounding_boxes": [{"x":10,"y":20,"w":200,"h":40}],
  "summary": "...",
  "word_count": 42,
  "char_count": 287,
  "annotated_image": "<base64 jpeg>"
}
```

---

## 🧪 Test Images

Use any image with printed/handwritten text. Good test sources:
- Screenshots of documents
- Scanned pages
- Photos of signs or books
- Printed invoices

---

## ⚠️ Troubleshooting

| Problem | Solution |
|---|---|
| `tesseract not found` | Install Tesseract and ensure it's in PATH |
| `EasyOCR slow first run` | It downloads models (~1.5GB) on first use. Be patient. |
| CORS error in browser | Ensure backend is running and URL is correct |
| `libGL.so.1 not found` | Run `apt-get install -y libgl1` on Linux |
| Render free plan sleeps | Use health endpoint to warm it up before scanning |

---

## 📦 Tech Stack

- **Frontend:** Vanilla HTML5 · CSS3 (custom dark/light tokens) · JavaScript ES2022
- **Backend:** Python 3.11 · Flask 3.0 · Flask-CORS
- **OCR:** Tesseract (pytesseract) + EasyOCR (PyTorch)
- **CV:** OpenCV (headless)
- **NLP:** TextBlob · langdetect
- **TTS:** gTTS (Google Text-to-Speech)
- **Export:** fpdf2
- **DB:** SQLite3 (via stdlib)
- **Deploy:** Vercel (frontend) · Render (backend)

---

## 👨‍💻 Author

Built as a mini project for SmartVision OCR Pro.
