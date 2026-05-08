# backend/main.py

import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .ocr import extract_text
import uvicorn

app = FastAPI(
    title="VerifyNG API",
    description="AI-powered certificate verification",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "version": "1.0.0",
        "service": "VerifyNG"
    }

@app.get("/test-ocr")
def test_ocr():
    """Quick test endpoint — remove before production"""
    image_path = os.path.join(os.path.dirname(__file__), "test_cert.jpg")
    result = extract_text(image_path)
    return result

if __name__ == "__main__":
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
