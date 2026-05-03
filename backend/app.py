"""
SmartVision OCR Pro — Backend (Flask)
Full-stack OCR with hybrid Tesseract + EasyOCR, NLP, TTS, history, and export.
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

from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import cv2
import numpy as np
from PIL import Image
import pytesseract
import easyocr
from textblob import TextBlob
from langdetect import detect, DetectorFactory
from gtts import gTTS
from fpdf import FPDF

# ─── App Setup ────────────────────────────────────────────────────────────────
app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})

DetectorFactory.seed = 0  # Reproducible language detection

# ─── EasyOCR Lazy Loader ──────────────────────────────────────────────────────
_easyocr_cache = {}

def get_reader(languages: list):
    key = tuple(sorted(languages))
    if key not in _easyocr_cache:
        _easyocr_cache[key] = easyocr.Reader(list(languages), gpu=False)
    return _easyocr_cache[key]

# ─── Database ─────────────────────────────────────────────────────────────────
DB_PATH = os.path.join(os.path.dirname(__file__), "ocr_history.db")

def init_db():
    conn = sqlite3.connect(DB_PATH)
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
    """Return (processed_gray, original_gray) for OCR + bounding boxes."""
    gray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY)
    # CLAHE for contrast enhancement
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
    enhanced = clahe.apply(gray)
    # Adaptive threshold + mild denoise
    thresh = cv2.adaptiveThreshold(
        enhanced, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
    )
    denoised = cv2.fastNlMeansDenoising(thresh, h=10)
    return denoised, gray

# ─── Bounding Box Detection ───────────────────────────────────────────────────
def detect_text_regions(gray):
    """Morphological dilation to find text-block bounding boxes."""
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (20, 6))
    dilated = cv2.dilate(gray, kernel, iterations=1)
    contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    boxes = []
    for c in contours:
        x, y, w, h = cv2.boundingRect(c)
        if w > 40 and h > 10 and w / h < 40:  # filter noise + horizontal lines
            boxes.append({"x": int(x), "y": int(y), "w": int(w), "h": int(h)})
    return boxes

def draw_boxes(image_bgr, boxes):
    out = image_bgr.copy()
    for b in boxes:
        x, y, w, h = b["x"], b["y"], b["w"], b["h"]
        cv2.rectangle(out, (x, y), (x + w, y + h), (0, 230, 80), 2)
        # semi-transparent fill
        overlay = out.copy()
        cv2.rectangle(overlay, (x, y), (x + w, y + h), (0, 230, 80), -1)
        cv2.addWeighted(overlay, 0.08, out, 0.92, 0, out)
    return out

def img_to_b64(image_bgr):
    _, buf = cv2.imencode(".jpg", image_bgr, [cv2.IMWRITE_JPEG_QUALITY, 90])
    return base64.b64encode(buf).decode("utf-8")

# ─── OCR Engines ──────────────────────────────────────────────────────────────
def run_tesseract(processed_gray):
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

def run_easyocr(image_bgr, lang_codes):
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

def fuse(tess_text, tess_conf, easy_text, easy_conf):
    """Weighted confidence fusion: pick winner, expose both."""
    if easy_conf >= tess_conf:
        best, conf, src = easy_text, easy_conf, "easyocr"
    else:
        best, conf, src = tess_text, tess_conf, "tesseract"
    comparison = {
        "tesseract": {"text": tess_text, "confidence": tess_conf},
        "easyocr":   {"text": easy_text, "confidence": easy_conf},
    }
    return best, conf, src, comparison

# ─── NLP Utilities ────────────────────────────────────────────────────────────
def auto_correct(text):
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
    # EasyOCR language-code mapping (subset)
    ocr_langs = {
        "en": ["en"], "hi": ["hi"], "fr": ["fr"], "es": ["es"], "de": ["de"],
        "zh-cn": ["ch_sim"], "zh-tw": ["ch_tra"], "ja": ["ja"], "ar": ["ar"],
        "pt": ["pt"], "ru": ["ru"], "ko": ["ko"], "it": ["it"], "nl": ["nl"],
    }
    return code, names.get(code, code.upper()), ocr_langs.get(code, ["en"])

def summarize(text, sentences_out=3):
    """Extractive summarization by TF-weighted sentence scoring."""
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
    # Restore original order
    ordered = [s for s in sents if s in top]
    return " ".join(ordered)

# ─── API Routes ───────────────────────────────────────────────────────────────

@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({"status": "healthy", "version": "1.0.0", "timestamp": datetime.datetime.utcnow().isoformat()})


@app.route("/api/ocr", methods=["POST"])
def ocr():
    """
    Accepts:
      - multipart/form-data with 'image' file  (upload / PDF page)
      - application/json with 'image_data' key (base64 camera frame)
    Returns full OCR analysis JSON.
    """
    try:
        # ── Load image ──
        if request.files.get("image"):
            f = request.files["image"]
            raw = f.read()
            filename = f.filename or "upload.jpg"
        elif request.is_json and request.json.get("image_data"):
            b64 = request.json["image_data"]
            if "," in b64:
                b64 = b64.split(",", 1)[1]
            raw = base64.b64decode(b64)
            filename = "camera_frame.jpg"
        else:
            return jsonify({"error": "No image provided"}), 400

        nparr = np.frombuffer(raw, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if image is None:
            return jsonify({"error": "Cannot decode image"}), 400

        # ── Preprocess + detect regions ──
        processed, gray = preprocess(image)
        boxes = detect_text_regions(processed)
        annotated = draw_boxes(image, boxes)
        annotated_b64 = img_to_b64(annotated)

        # ── First-pass: detect language using quick Tesseract run ──
        quick_text, _ = run_tesseract(processed)
        lang_code, lang_name, ocr_langs = detect_language(quick_text)

        # ── Dual OCR ──
        tess_text, tess_conf = run_tesseract(processed)
        easy_text, easy_conf = run_easyocr(image, ocr_langs)

        # ── Fusion ──
        best_text, best_conf, best_src, comparison = fuse(
            tess_text, tess_conf, easy_text, easy_conf
        )

        # ── NLP ──
        corrected_text, corrections = auto_correct(best_text)
        summary = summarize(corrected_text)

        # ── Persist ──
        scan_id = str(uuid.uuid4())
        conn = sqlite3.connect(DB_PATH)
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

        return jsonify({
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
        })

    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@app.route("/api/tts", methods=["POST"])
def tts():
    """Convert text to MP3 and return base64 audio."""
    try:
        data = request.json or {}
        text = (data.get("text") or "").strip()[:600]
        lang = data.get("lang", "en")
        if not text:
            return jsonify({"error": "No text"}), 400
        tts_obj = gTTS(text=text, lang=lang, slow=False)
        buf = io.BytesIO()
        tts_obj.write_to_fp(buf)
        buf.seek(0)
        audio_b64 = base64.b64encode(buf.read()).decode()
        return jsonify({"success": True, "audio": audio_b64})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/history", methods=["GET"])
def history():
    """Return last 50 scans (no heavy annotated image blob)."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        """SELECT id, filename, corrected, language, confidence, best_source,
                  summary, timestamp, word_count
           FROM (
               SELECT *, length(corrected) - length(replace(corrected,' ','')) + 1 as word_count
               FROM scans
           ) ORDER BY timestamp DESC LIMIT 50"""
    ).fetchall()
    conn.close()
    return jsonify({"success": True, "history": [dict(r) for r in rows]})


@app.route("/api/history/search", methods=["GET"])
def search():
    keyword = request.args.get("q", "").strip()
    start   = request.args.get("start", "")
    end     = request.args.get("end", "")
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    q = "SELECT id, filename, corrected, language, confidence, best_source, summary, timestamp FROM scans WHERE 1=1"
    params = []
    if keyword:
        q += " AND (corrected LIKE ? OR filename LIKE ?)"
        params += [f"%{keyword}%", f"%{keyword}%"]
    if start:
        q += " AND timestamp >= ?"
        params.append(start)
    if end:
        q += " AND timestamp <= ?"
        params.append(end + "T23:59:59")
    q += " ORDER BY timestamp DESC"
    rows = conn.execute(q, params).fetchall()
    conn.close()
    return jsonify({"success": True, "results": [dict(r) for r in rows], "count": len(rows)})


@app.route("/api/history/<scan_id>", methods=["DELETE"])
def delete_scan(scan_id):
    conn = sqlite3.connect(DB_PATH)
    conn.execute("DELETE FROM scans WHERE id=?", (scan_id,))
    conn.commit()
    conn.close()
    return jsonify({"success": True})


@app.route("/api/export", methods=["POST"])
def export_result():
    """Export as TXT / JSON / PDF."""
    data = request.json or {}
    fmt  = data.get("format", "txt")
    text = data.get("text", "")
    meta = data.get("metadata", {})
    ts   = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if fmt == "txt":
        body = (
            f"SmartVision OCR Pro — Export\n{'='*44}\n"
            f"File      : {meta.get('filename','N/A')}\n"
            f"Language  : {meta.get('language','N/A')}\n"
            f"Confidence: {meta.get('confidence','N/A')}%\n"
            f"Source    : {meta.get('best_source','N/A')}\n"
            f"Exported  : {ts}\n{'='*44}\n\n{text}"
        )
        buf = io.BytesIO(body.encode("utf-8"))
        return send_file(buf, mimetype="text/plain", as_attachment=True, download_name="ocr_result.txt")

    if fmt == "json":
        payload = {
            "exported_at": ts,
            "metadata": meta,
            "extracted_text": text,
            "word_count": len(text.split()),
            "char_count": len(text),
        }
        buf = io.BytesIO(json.dumps(payload, indent=2).encode("utf-8"))
        return send_file(buf, mimetype="application/json", as_attachment=True, download_name="ocr_result.json")

    if fmt == "pdf":
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", "B", 16)
        pdf.cell(0, 10, "SmartVision OCR Pro", ln=True, align="C")
        pdf.set_font("Arial", size=10)
        pdf.set_text_color(120, 120, 120)
        pdf.cell(0, 8, f"Exported: {ts}", ln=True, align="C")
        pdf.ln(4)
        pdf.set_draw_color(0, 200, 100)
        pdf.set_line_width(0.8)
        pdf.line(10, pdf.get_y(), 200, pdf.get_y())
        pdf.ln(5)
        pdf.set_text_color(0, 0, 0)
        pdf.set_font("Arial", "B", 11)
        for k, v in [("File", meta.get("filename","N/A")),
                     ("Language", meta.get("language","N/A")),
                     ("Confidence", f"{meta.get('confidence','N/A')}%"),
                     ("OCR Source", meta.get("best_source","N/A"))]:
            pdf.cell(40, 7, f"{k}:", ln=False)
            pdf.set_font("Arial", size=11)
            pdf.cell(0, 7, str(v), ln=True)
            pdf.set_font("Arial", "B", 11)
        pdf.ln(5)
        pdf.set_font("Arial", size=11)
        safe = text.encode("latin-1", "replace").decode("latin-1")
        pdf.multi_cell(0, 7, safe)
        buf = io.BytesIO()
        pdf_str = pdf.output(dest="S")
        buf.write(pdf_str.encode("latin-1") if isinstance(pdf_str, str) else pdf_str)
        buf.seek(0)
        return send_file(buf, mimetype="application/pdf", as_attachment=True, download_name="ocr_result.pdf")

    return jsonify({"error": "Unknown format"}), 400


# ─── Entrypoint ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
