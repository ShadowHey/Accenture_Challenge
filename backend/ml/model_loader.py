import os
import joblib
import logging
import sys

_MODEL = None

# Model path: backend/ml/models/triage_model.joblib
MODEL_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "models",
    "triage_model.joblib"
)

def load_model():
    """
    Loads the trained ML model from disk. Caches it in a module-level variable
    so it's only loaded once per process.
    Returns the model or None if unavailable.
    """
    global _MODEL
    if _MODEL is not None:
        return _MODEL
    try:
        if not os.path.exists(MODEL_PATH):
            print(f"Warning: ML model not found at {MODEL_PATH}. Running in rules-only mode.", file=sys.stderr)
            return None
        _MODEL = joblib.load(MODEL_PATH)
        print(f"ML model loaded successfully from {MODEL_PATH}", file=sys.stderr)
        return _MODEL
    except Exception as e:
        logging.getLogger(__name__).warning(f"Failed to load model from {MODEL_PATH}: {e}")
        print(f"Warning: Failed to load ML model: {e}. Running in rules-only mode.", file=sys.stderr)
        return None
