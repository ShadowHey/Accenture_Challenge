from typing import Optional, Tuple

def _level_to_num(level_str: str) -> int:
    """Convert 'LEVEL X' to integer X. Lower = more severe."""
    try:
        return int(level_str.split()[-1])
    except (ValueError, IndexError):
        return 5

def reconcile(rules_priority: str, rules_confidence: float,
              ml_priority: Optional[str], ml_confidence: Optional[float]) -> Tuple[str, str, Optional[str]]:
    """
    Merge rules engine output and ML output.
    
    SAFETY INVARIANT: ML can escalate (lower level number = more severe)
    but NEVER downgrade below the rules floor.
    
    Returns (final_priority, source, disagreement_explanation)
    """
    if ml_priority is None:
        return rules_priority, 'RULES', None

    if ml_confidence is not None and ml_confidence < 0.60:
        # If the ML model is highly uncertain, flag for immediate human review.
        return rules_priority, 'CLINICIAN_REVIEW_REQUIRED', f"ML confidence too low ({int(ml_confidence*100)}%), review required"

    rules_num = _level_to_num(rules_priority)
    ml_num = _level_to_num(ml_priority)

    if rules_num == ml_num:
        return rules_priority, 'HYBRID_AGREE', None

    if ml_num < rules_num:
        # ML thinks it's MORE severe — allow escalation
        return ml_priority, 'ML_ESCALATED', f"Rules suggested {rules_priority}, ML escalated to {ml_priority}"
    else:
        # ML thinks it's LESS severe — rules floor holds (safety invariant)
        return rules_priority, 'RULES_FLOOR', f"ML suggested {ml_priority}, but rules floor held at {rules_priority}"
