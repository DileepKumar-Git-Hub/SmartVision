"""History endpoint"""
import json
import sqlite3
import os

def get_db_path():
    """Get database path - use /tmp for Vercel"""
    if os.environ.get("VERCEL"):
        return "/tmp/ocr_history.db"
    return os.path.join(os.path.dirname(__file__), "..", "ocr_history.db")

def handler(request):
    """Get OCR history"""
    try:
        db_path = get_db_path()
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            """SELECT id, filename, corrected, language, confidence, best_source,
                      summary, timestamp 
               FROM scans ORDER BY timestamp DESC LIMIT 50"""
        ).fetchall()
        conn.close()
        
        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
            },
            "body": json.dumps({
                "success": True,
                "history": [dict(r) for r in rows]
            })
        }
    except Exception as e:
        return {
            "statusCode": 500,
            "headers": {"Content-Type": "application/json", "Access-Control-Allow-Origin": "*"},
            "body": json.dumps({"error": str(e)})
        }
