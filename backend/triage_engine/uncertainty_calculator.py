from typing import List

def calculate_uncertainty(missing_fields: List[str], reasons: List[str]):
    """
    Calculates uncertainty based on missing fields and ambiguous presentation.
    Returns (confidence_score, uncertainty_level, escalation_flag)
    """
    confidence = 1.0
    
    # Each missing vital sign reduces confidence by 0.1
    # Missing medical history reduces by 0.15
    for field in missing_fields:
        if field == "medical_history":
            confidence -= 0.15
        else:
            confidence -= 0.1
            
    # Ambiguous symptoms can reduce confidence
    ambiguous = False
    for r in reasons:
        if "vague" in r.lower() or "dizziness" in r.lower():
            ambiguous = True
            
    if ambiguous:
        confidence -= 0.1
        
    confidence = max(0.0, round(confidence, 2))
    
    if confidence >= 0.8:
        uncertainty_level = "LOW"
    elif confidence >= 0.5:
        uncertainty_level = "MODERATE"
    else:
        uncertainty_level = "HIGH"
        
    # Safety: Escalate if we are uncertain but there are concerning reasons
    # or just if uncertainty is high/moderate and we are missing history
    escalation = False
    if uncertainty_level in ["MODERATE", "HIGH"] and "medical_history" in missing_fields:
        escalation = True
        
    return confidence, uncertainty_level, escalation
