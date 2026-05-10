# backend/main.py

import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .ocr import extract_text
from .ela import perform_ela, check_metadata_consistency, analyze_visual_consistency
from .scorer import calculate_visual_trust_score
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
    image_path = os.path.join(os.path.dirname(__file__), "..", "test_cert.jpg")
    result = extract_text(image_path)
    return result

@app.get("/test-ela")
def test_ela():
    """Test ELA on both real and fake certificates"""
    
    results = {}
    base_path = os.path.join(os.path.dirname(__file__), "..")
    
    # Test real certificate (test_cert.jpg)
    real_cert_path = os.path.join(base_path, "test_cert.jpg")
    if os.path.exists(real_cert_path):
        ela = perform_ela(real_cert_path)
        meta = check_metadata_consistency(real_cert_path)
        visual = analyze_visual_consistency(real_cert_path)
        results["real_cert"] = {
            "ela_score": ela.get("anomaly_score"),
            "risk_level": ela.get("risk_level"),
            "ela_flags": ela.get("flags"),
            "metadata_flags": meta.get("flags"),
            "visual_flags": visual.get("flags")
        }
    
    # Test fake certificate
    fake_cert_path = os.path.join(base_path, "fake_cert.jpg")
    if os.path.exists(fake_cert_path):
        ela = perform_ela(fake_cert_path)
        meta = check_metadata_consistency(fake_cert_path)
        visual = analyze_visual_consistency(fake_cert_path)
        results["fake_cert"] = {
            "ela_score": ela.get("anomaly_score"),
            "risk_level": ela.get("risk_level"),
            "ela_flags": ela.get("flags"),
            "metadata_flags": meta.get("flags"),
            "visual_flags": visual.get("flags")
        }
    
    return results

@app.get("/verify-certificate")
def verify_certificate():
    """Verify both certificates and return trust scores"""
    
    results = {}
    base_path = os.path.join(os.path.dirname(__file__), "..")
    
    # Verify real certificate
    real_cert_path = os.path.join(base_path, "test_cert.jpg")
    if os.path.exists(real_cert_path):
        ela = perform_ela(real_cert_path)
        meta = check_metadata_consistency(real_cert_path)
        visual = analyze_visual_consistency(real_cert_path)
        trust = calculate_visual_trust_score(ela, meta, visual)
        results["real_cert"] = {
            "ela_score": ela.get("anomaly_score"),
            "ela_risk": ela.get("risk_level"),
            "trust_score": trust.get("trust_score"),
            "verdict": trust.get("verdict"),
            "flags": trust.get("flags"),
            "flag_count": trust.get("flag_count")
        }
    
    # Verify fake certificate
    fake_cert_path = os.path.join(base_path, "fake_cert.jpg")
    if os.path.exists(fake_cert_path):
        ela = perform_ela(fake_cert_path)
        meta = check_metadata_consistency(fake_cert_path)
        visual = analyze_visual_consistency(fake_cert_path)
        trust = calculate_visual_trust_score(ela, meta, visual)
        results["fake_cert"] = {
            "ela_score": ela.get("anomaly_score"),
            "ela_risk": ela.get("risk_level"),
            "trust_score": trust.get("trust_score"),
            "verdict": trust.get("verdict"),
            "flags": trust.get("flags"),
            "flag_count": trust.get("flag_count")
        }
    
    return results

if __name__ == "__main__":
    uvicorn.run("backend.app.main:app", host="0.0.0.0", port=8000, reload=True)
