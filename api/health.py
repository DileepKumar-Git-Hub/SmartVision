"""Health check endpoint"""
import json
import datetime

def handler(request):
    return {
        "statusCode": 200,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type",
        },
        "body": json.dumps({
            "status": "healthy",
            "version": "1.0.0",
            "timestamp": datetime.datetime.utcnow().isoformat()
        })
    }
