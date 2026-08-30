from backend.models import PatientInput
from backend.ml.feature_extractor import extract_features, FEATURE_NAMES
from backend.ml.model_loader import load_model

def predict_triage(patient: PatientInput) -> tuple:
    model = load_model()
    if not model:
        return None, None, None
    
    # Apply PII masking before sending to ML feature extraction
    from backend.security.pii_masker import mask_name
    patient_copy = patient.model_copy(deep=True) if hasattr(patient, 'model_copy') else patient.copy(deep=True)
    patient_copy.name = mask_name(patient_copy.name)
    
    features = extract_features(patient_copy)
    
    try:
        import pandas as pd
        features_df = pd.DataFrame([features], columns=FEATURE_NAMES)
        pred_label = model.predict(features_df)[0]
        probas = model.predict_proba(features_df)[0]
        max_proba = max(probas)
        
        importances = getattr(model, "feature_importances_", None)
        top_importances = {}
        if importances is not None:
            feat_imp = list(zip(FEATURE_NAMES, importances))
            feat_imp.sort(key=lambda x: x[1], reverse=True)
            top_importances = {k: float(v) for k, v in feat_imp[:5]}
            
        return pred_label, float(max_proba), top_importances
    except Exception as e:
        import logging
        logging.getLogger(__name__).warning(f"Prediction failed: {e}")
        return None, None, None
