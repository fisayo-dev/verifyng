# app/ela.py

import cv2
import numpy as np
from PIL import Image
import io
import os

def perform_ela(image_path: str, quality: int = 90) -> dict:
    """
    Error Level Analysis — detects tampered regions in certificate images.
    
    Returns:
        anomaly_score: 0–100 (higher = more likely tampered)
        risk_level: LOW / MEDIUM / HIGH
        flags: list of specific issues detected
    """
    try:
        # Load original image
        original = Image.open(image_path).convert('RGB')
        original_array = np.array(original, dtype=np.float32)
        
        # Re-save at lower quality (simulate compression)
        buffer = io.BytesIO()
        original.save(buffer, 'JPEG', quality=quality)
        buffer.seek(0)
        compressed = Image.open(buffer).convert('RGB')
        compressed_array = np.array(compressed, dtype=np.float32)
        
        # Calculate pixel-level difference
        diff = np.abs(original_array - compressed_array)
        
        # Normalize to 0–255
        if diff.max() > 0:
            diff_normalized = (diff / diff.max() * 255).astype(np.uint8)
        else:
            diff_normalized = diff.astype(np.uint8)
        
        # Calculate anomaly metrics
        mean_diff = float(np.mean(diff))
        std_diff = float(np.std(diff))
        max_diff = float(np.max(diff))
        
        # Detect high-anomaly regions (potential edit zones)
        gray_diff = cv2.cvtColor(diff_normalized, cv2.COLOR_RGB2GRAY)
        anomaly_threshold = max(25, float(np.percentile(gray_diff, 95)))
        _, high_anomaly_mask = cv2.threshold(
            gray_diff, anomaly_threshold, 255, cv2.THRESH_BINARY
        )
        anomaly_pixel_ratio = float(
            np.sum(high_anomaly_mask > 0) / high_anomaly_mask.size
        )
        
        # Calculate final anomaly score (0–100)
        # Keep the background noise low, but reward concentrated edit spikes.
        concentrated_artifact_boost = max_diff if max_diff > 50 else max_diff * 0.2
        raw_score = (
            (mean_diff * 5) +
            (std_diff * 5) +
            (anomaly_pixel_ratio * 20) +
            concentrated_artifact_boost
        )
        anomaly_score = min(round(raw_score, 2), 100)
        
        # Determine risk level
        if anomaly_score < 30:
            risk_level = "LOW"
        elif anomaly_score < 60:
            risk_level = "MEDIUM"
        else:
            risk_level = "HIGH"
        
        # Generate specific flags
        flags = []
        if mean_diff > 3:
            flags.append("Significant pixel-level inconsistencies detected")
        if std_diff > 5:
            flags.append("High variance in image compression patterns")
        if anomaly_pixel_ratio > 0.02:
            flags.append("Large proportion of image shows editing artifacts")
        if max_diff > 50:
            flags.append("Extreme pixel differences found in specific regions")
        
        return {
            "success": True,
            "anomaly_score": anomaly_score,
            "risk_level": risk_level,
            "flags": flags,
            "metrics": {
                "mean_difference": round(mean_diff, 4),
                "std_difference": round(std_diff, 4),
                "anomaly_pixel_ratio": round(anomaly_pixel_ratio, 4),
                "max_difference": round(max_diff, 4)
            }
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "anomaly_score": None,
            "risk_level": "UNKNOWN"
        }


def check_metadata_consistency(image_path: str) -> dict:
    """
    Check image metadata for inconsistencies.
    A 2019 certificate should not have a 2024 creation date.
    """
    try:
        from PIL.ExifTags import TAGS
        
        image = Image.open(image_path)
        exif_data = image._getexif()
        
        flags = []
        metadata = {}
        
        if exif_data:
            for tag_id, value in exif_data.items():
                tag = TAGS.get(tag_id, tag_id)
                metadata[tag] = str(value)
            
            # Check for suspicious software tags
            software = metadata.get("Software", "").lower()
            suspicious_software = [
                "photoshop", "gimp", "canva", 
                "paint", "illustrator", "inkscape"
            ]
            for s in suspicious_software:
                if s in software:
                    flags.append(f"Document edited with: {software}")
                    break
            
            # Check DateTime vs claimed year (if available)
            datetime_str = metadata.get("DateTime", "")
            if datetime_str:
                metadata["creation_detected"] = datetime_str
        else:
            flags.append("No EXIF metadata found — may indicate processing")
        
        return {
            "success": True,
            "flags": flags,
            "metadata": metadata,
            "suspicious": len(flags) > 0
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "flags": [],
            "suspicious": False
        }


def analyze_visual_consistency(image_path: str) -> dict:
    """
    Check for visual inconsistencies:
    - Mixed font regions
    - Unusual noise patterns
    - Copy-paste artifacts
    """
    try:
        img = cv2.imread(image_path)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        flags = []
        
        # Check for unusual noise patterns (copy-paste artifacts)
        laplacian = cv2.Laplacian(gray, cv2.CV_64F)
        local_variance = laplacian.var()
        
        # Divide image into quadrants and compare variance
        h, w = gray.shape
        quadrants = [
            gray[:h//2, :w//2],    # Top-left
            gray[:h//2, w//2:],    # Top-right
            gray[h//2:, :w//2],    # Bottom-left
            gray[h//2:, w//2:]     # Bottom-right
        ]
        
        variances = [cv2.Laplacian(q, cv2.CV_64F).var() for q in quadrants]
        variance_std = np.std(variances)
        
        # High variance between quadrants = inconsistent image
        # Only flag if extremely inconsistent (natural certificate design is OK)
        if variance_std > 1000:
            flags.append("Inconsistent sharpness across document regions")
        
        # Check for JPEG blocking artifacts (sign of re-compression)
        dct_score = detect_blocking_artifacts(gray)
        if dct_score > 0.5:
            flags.append("JPEG blocking artifacts suggest multiple re-saves")
        
        return {
            "success": True,
            "flags": flags,
            "local_variance": round(float(local_variance), 2),
            "quadrant_variance_std": round(float(variance_std), 2)
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "flags": []
        }


def detect_blocking_artifacts(gray_image: np.ndarray) -> float:
    """Detect JPEG blocking artifacts — sign of multiple saves/edits"""
    h, w = gray_image.shape
    
    # Check 8x8 block boundaries (JPEG compression blocks)
    horizontal_diff = 0
    vertical_diff = 0
    count = 0
    
    for i in range(8, h - 8, 8):
        diff = abs(float(np.mean(gray_image[i, :])) - 
                   float(np.mean(gray_image[i-1, :])))
        horizontal_diff += diff
        count += 1
    
    for j in range(8, w - 8, 8):
        diff = abs(float(np.mean(gray_image[:, j])) - 
                   float(np.mean(gray_image[:, j-1])))
        vertical_diff += diff
        count += 1
    
    if count == 0:
        return 0.0
    
    avg_boundary_diff = (horizontal_diff + vertical_diff) / count
    return min(avg_boundary_diff / 50, 1.0)  # Normalize to 0–1
