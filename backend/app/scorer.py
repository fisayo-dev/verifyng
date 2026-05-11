# app/scorer.py

def calculate_visual_trust_score(ela_result: dict, metadata_result: dict, visual_result: dict) -> dict:
    """
    Combine all visual analysis into one trust score.
    
    Score logic:
    - Start at 100 (assume authentic)
    - Deduct points for each flag
    - ELA score directly reduces trust
    """
    
    trust_score = 100
    all_flags = []
    
    # ELA deduction (most important signal — 40% weight)
    if ela_result.get("success"):
        ela_score = ela_result.get("anomaly_score", 0)
        ela_deduction = ela_score * 0.4
        trust_score -= ela_deduction
        all_flags.extend(ela_result.get("flags", []))
    
    # Metadata deduction (30% weight)
    if metadata_result.get("success"):
        meta_flags = metadata_result.get("flags", [])
        trust_score -= len(meta_flags) * 15  # -15 per metadata flag
        all_flags.extend(meta_flags)
    
    # Visual consistency deduction (30% weight)
    if visual_result.get("success"):
        visual_flags = visual_result.get("flags", [])
        trust_score -= len(visual_flags) * 10  # -10 per visual flag
        all_flags.extend(visual_flags)
    
    # Clamp to 0–100
    trust_score = max(0, min(100, round(trust_score, 1)))
    
    # Determine verdict
    if trust_score >= 75:
        verdict = "LIKELY AUTHENTIC"
    elif trust_score >= 50:
        verdict = "REQUIRES MANUAL REVIEW"
    elif trust_score >= 25:
        verdict = "SUSPICIOUS"
    else:
        verdict = "LIKELY FORGED"
    
    return {
        "trust_score": trust_score,
        "verdict": verdict,
        "flags": all_flags,
        "flag_count": len(all_flags)
    }
