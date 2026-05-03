"""
SmartVision OCR Pro — Vercel Serverless API
Handles OCR processing with Tesseract and EasyOCR
"""

import os
import io
import json
import base64
import sqlite3
import datetime
import uuid
import re
import traceback
from pathlib import Path

import cv2
import numpy as np
from PIL import Image
import pytesseract
import easyocr
from textblob import TextBlob
from langdetect import detect, DetectorFactory

# ─── Configuration ────────────────────────────────────────────────────────────
DetectorFactory.seed = 0

# Cache for EasyOCR readers to avoid reloading
_easyocr_cache = {}

def get_reader(languages: list):
    """Lazy load EasyOCR readers with caching"""
    key = tuple(sorted(languages))
    if key not in _easyocr_cache:
        _easyocr_cache[key] = easyocr.Reader(list(languages), gpu=False)
    return _easyocr_cache[key]

# ─── Database ─────────────────────────────────────────────────────────────────
def get_db_path():
    """Get database path - use /tmp for Vercel"""
    if os.environ.get("VERCEL"):
        return "/tmp/ocr_history.db"
    return os.path.join(os.path.dirname(__file__), "..", "ocr_history.db")

def init_db():
    """Initialize SQLite database"""
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS scans (
            id          TEXT PRIMARY KEY,
            filename    TEXT,
            raw_text    TEXT,
            corrected   TEXT,
            language    TEXT,
            lang_code   TEXT,
            confidence  REAL,
            best_source TEXT,
            summary     TEXT,
            corrections TEXT,
            tess_text   TEXT,
            tess_conf   REAL,
            easy_text   TEXT,
            easy_conf   REAL,
            annotated   TEXT,
            timestamp   TEXT
        )
    """)
    conn.commit()
    conn.close()

init_db()

# ─── Image Preprocessing ──────────────────────────────────────────────────────
def preprocess(image_bgr):
    """Preprocess image: CLAHE enhancement, adaptive threshold, denoising"""
    gray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY)
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
    enhanced = clahe.apply(gray)
    thresh = cv2.adaptiveThreshold(
        enhanced, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
    )
    denoised = cv2.fastNlMeansDenoising(thresh, h=10)
    return denoised, gray

def detect_text_regions(gray):
    """Find text bounding boxes using morphological operations"""
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (20, 6))
    dilated = cv2.dilate(gray, kernel, iterations=1)
    contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    boxes = []
    for c in contours:
        x, y, w, h = cv2.boundingRect(c)
        if w > 40 and h > 10 and w / h < 40:
            boxes.append({"x": int(x), "y": int(y), "w": int(w), "h": int(h)})
    return boxes

def draw_boxes(image_bgr, boxes):
    """Draw bounding boxes on image"""
    out = image_bgr.copy()
    for b in boxes:
        x, y, w, h = b["x"], b["y"], b["w"], b["h"]
        cv2.rectangle(out, (x, y), (x + w, y + h), (0, 230, 80), 2)
        overlay = out.copy()
        cv2.rectangle(overlay, (x, y), (x + w, y + h), (0, 230, 80), -1)
        cv2.addWeighted(overlay, 0.08, out, 0.92, 0, out)
    return out

def img_to_b64(image_bgr):
    """Convert OpenCV image to base64"""
    _, buf = cv2.imencode(".jpg", image_bgr, [cv2.IMWRITE_JPEG_QUALITY, 90])
    return base64.b64encode(buf).decode("utf-8")

# ─── OCR Engines ──────────────────────────────────────────────────────────────
def run_tesseract(processed_gray):
    """Run Tesseract OCR"""
    try:
        config = "--oem 3 --psm 6"
        data = pytesseract.image_to_data(
            processed_gray, config=config, output_type=pytesseract.Output.DICT
        )
        words, confs = [], []
        for i, word in enumerate(data["text"]):
            conf = int(data["conf"][i])
            if word.strip() and conf > 0:
                words.append(word)
                confs.append(conf)
        text = " ".join(words)
        avg = sum(confs) / len(confs) if confs else 0.0
        return text, round(avg, 2)
    except Exception as e:
        print(f"Tesseract error: {e}")
        return "", 0.0

def run_easyocr(image_bgr, lang_codes):
    """Run EasyOCR"""
    try:
        reader = get_reader(lang_codes)
        results = reader.readtext(image_bgr, detail=1, paragraph=False)
        texts, confs = [], []
        for (_, text, conf) in results:
            if text.strip():
                texts.append(text)
                confs.append(conf * 100)
        combined = " ".join(texts)
        avg = sum(confs) / len(confs) if confs else 0.0
        return combined, round(avg, 2)
    except Exception as e:
        print(f"EasyOCR error: {e}")
        return "", 0.0

def fuse(tess_text, tess_conf, easy_text, easy_conf):
    """Fuse results from both OCR engines"""
    if easy_conf >= tess_conf:
        best, conf, src = easy_text, easy_conf, "easyocr"
    else:
        best, conf, src = tess_text, tess_conf, "tesseract"
    comparison = {
        "tesseract": {"text": tess_text, "confidence": tess_conf},
        "easyocr": {"text": easy_text, "confidence": easy_conf},
    }
    return best, conf, src, comparison

# ─── NLP Utilities ────────────────────────────────────────────────────────────
def auto_correct(text):
    """Auto-correct text using TextBlob"""
    try:
        blob = TextBlob(text)
        corrected = str(blob.correct())
        orig_words = text.split()
        corr_words = corrected.split()
        corrections = {}
        for o, c in zip(orig_words, corr_words):
            if o.lower() != c.lower():
                corrections[o] = c
        return corrected, corrections
    except Exception:
        return text, {}

def detect_language(text):
    """Detect language from text"""
    try:
        code = detect(text)
    except Exception:
        code = "en"
    
    names = {
        "en": "English", "hi": "Hindi", "fr": "French", "es": "Spanish",
        "de": "German", "zh-cn": "Chinese (Simplified)", "zh-tw": "Chinese (Traditional)",
        "ja": "Japanese", "ar": "Arabic", "pt": "Portuguese", "ru": "Russian",
        "ko": "Korean", "it": "Italian", "nl": "Dutch",
    }
    ocr_langs = {
        "en": ["en"], "hi": ["hi"], "fr": ["fr"], "es": ["es"], "de": ["de"],
        "zh-cn": ["ch_sim"], "zh-tw": ["ch_tra"], "ja": ["ja"], "ar": ["ar"],
        "pt": ["pt"], "ru": ["ru"], "ko": ["ko"], "it": ["it"], "nl": ["nl"],
    }
    return code, names.get(code, code.upper()), ocr_langs.get(code, ["en"])

def summarize(text, sentences_out=3):
    """Extractive summarization"""
    raw_sents = re.split(r"(?<=[.!?])\s+", text.strip())
    sents = [s for s in raw_sents if len(s.split()) > 4]
    if len(sents) <= sentences_out:
        return text
    words = re.findall(r"\b\w{4,}\b", text.lower())
    freq = {}
    for w in words:
        freq[w] = freq.get(w, 0) + 1
    scored = sorted(
        sents,
        key=lambda s: sum(freq.get(w.lower(), 0) for w in re.findall(r"\b\w+\b", s)),
        reverse=True,
    )
    top = scored[:sentences_out]
    ordered = [s for s in sents if s in top]
    return " ".join(ordered)

# ─── Handler ──────────────────────────────────────────────────────────────────
def handler(request):
    """Main OCR handler for Vercel"""
    try:
        # Parse request body
        if request.method == "OPTIONS":
            return {
                "statusCode": 200,
                "headers": {
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
                    "Access-Control-Allow-Headers": "Content-Type",
                },
                "body": ""
            }

        content_type = request.headers.get("Content-Type", "")
        
        # Handle multipart/form-data (file upload)
        if "multipart/form-data" in content_type:
            if hasattr(request, 'files') and 'image' in request.files:
                f = request.files['image']
                raw = f.read()
                filename = f.filename or "upload.jpg"
            else:
                return json_response({"error": "No image file provided"}, 400)
        # Handle application/json (base64)
        elif "application/json" in content_type:
            try:
                body = json.loads(request.body) if isinstance(request.body, str) else request.body
                b64 = body.get("image_data", "")
                if not b64:
                    return json_response({"error": "No image_data provided"}, 400)
                if "," in b64:
                    b64 = b64.split(",", 1)[1]
                raw = base64.b64decode(b64)
                filename = "camera_frame.jpg"
            except Exception as e:
                return json_response({"error": f"Invalid JSON: {str(e)}"}, 400)
        else:
            return json_response({"error": "No image provided"}, 400)

        # Decode image
        nparr = np.frombuffer(raw, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if image is None:
            return json_response({"error": "Cannot decode image"}, 400)

        # Process
        processed, gray = preprocess(image)
        boxes = detect_text_regions(processed)
        annotated = draw_boxes(image, boxes)
        annotated_b64 = img_to_b64(annotated)

        # Quick language detection
        quick_text, _ = run_tesseract(processed)
        lang_code, lang_name, ocr_langs = detect_language(quick_text)

        # Dual OCR
        tess_text, tess_conf = run_tesseract(processed)
        easy_text, easy_conf = run_easyocr(image, ocr_langs)

        # Fusion
        best_text, best_conf, best_src, comparison = fuse(
            tess_text, tess_conf, easy_text, easy_conf
        )

        # NLP
        corrected_text, corrections = auto_correct(best_text)
        summary = summarize(corrected_text)

        # Save to database
        scan_id = str(uuid.uuid4())
        db_path = get_db_path()
        conn = sqlite3.connect(db_path)
        conn.execute(
            """INSERT INTO scans VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                scan_id, filename, best_text, corrected_text,
                lang_name, lang_code, best_conf, best_src,
                summary, json.dumps(corrections),
                tess_text, tess_conf, easy_text, easy_conf,
                annotated_b64, datetime.datetime.utcnow().isoformat(),
            ),
        )
        conn.commit()
        conn.close()

        result = {
            "success": True,
            "scan_id": scan_id,
            "annotated_image": annotated_b64,
            "raw_text": best_text,
            "corrected_text": corrected_text,
            "corrections": corrections,
            "language": lang_name,
            "language_code": lang_code,
            "confidence": best_conf,
            "best_source": best_src,
            "comparison": comparison,
            "bounding_boxes": boxes,
            "summary": summary,
            "word_count": len(corrected_text.split()),
            "char_count": len(corrected_text),
        }
        return json_response(result, 200)

    except Exception as e:
        traceback.print_exc()
        return json_response({"error": str(e), "detail": traceback.format_exc()}, 500)


def json_response(data, status_code=200):
    """Helper to create JSON response"""
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type",
        },
        "body": json.dumps(data)
    }
