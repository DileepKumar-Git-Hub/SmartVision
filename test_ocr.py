#!/usr/bin/env python
"""Test the OCR API with a sample image"""
import base64
import json
import urllib.request
import urllib.error
import numpy as np
import cv2
from PIL import Image, ImageDraw, ImageFont

# Create a simple test image with text
def create_test_image():
    """Create a test image with text"""
    width, height = 800, 400
    img = Image.new('RGB', (width, height), color='white')
    draw = ImageDraw.Draw(img)
    
    # Draw text
    text_lines = [
        "SmartVision OCR Pro",
        "Testing text recognition",
        "Line 3: Python 3.12.10"
    ]
    
    y = 50
    for line in text_lines:
        draw.text((50, y), line, fill='black')
        y += 80
    
    # Convert to numpy array
    img_array = np.array(img)
    img_bgr = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
    
    return img_bgr

def test_ocr_api():
    """Test the OCR API"""
    print("📷 Creating test image...")
    img_bgr = create_test_image()
    
    # Encode to base64
    _, buffer = cv2.imencode('.jpg', img_bgr)
    img_b64 = base64.b64encode(buffer).decode('utf-8')
    
    # Prepare request
    payload = {
        "image_data": f"data:image/jpeg;base64,{img_b64}"
    }
    
    print("🚀 Sending OCR request to http://localhost:5000/api/ocr...")
    
    try:
        req = urllib.request.Request(
            'http://localhost:5000/api/ocr',
            data=json.dumps(payload).encode('utf-8'),
            headers={'Content-Type': 'application/json'}
        )
        
        with urllib.request.urlopen(req, timeout=60) as response:
            result = json.loads(response.read().decode('utf-8'))
            
            print("\n✅ OCR Successful!\n")
            print(f"Raw Text:\n{result.get('raw_text', 'N/A')}\n")
            print(f"Corrected Text:\n{result.get('corrected_text', 'N/A')}\n")
            print(f"Language: {result.get('language', 'N/A')}")
            print(f"Confidence: {result.get('confidence', 'N/A')}%")
            print(f"Best Source: {result.get('best_source', 'N/A')}")
            print(f"Bounding Boxes: {len(result.get('bounding_boxes', []))} regions detected")
            
            return True
            
    except urllib.error.URLError as e:
        print(f"❌ Connection failed: {e}")
        print("Make sure Flask backend is running: python backend/app.py")
        return False
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON response: {e}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    success = test_ocr_api()
    exit(0 if success else 1)
