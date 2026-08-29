import re
import difflib

# Dictionary mapping vital sign keys to their common synonyms
VITALS_DICT = {
    "heart_rate": ["heart rate", "hr", "pulse", "bpm"],
    "blood_pressure": ["blood pressure", "bp", "pressure"],
    "spo2": ["spo2", "oxygen", "o2", "saturation", "sats", "sp", "spo"],
    "temperature": ["temperature", "temp", "t", "fever"],
    "respiratory_rate": ["respiratory rate", "resp rate", "rr", "respiration"],
    "gcs": ["gcs", "glasgow", "coma", "coma scale"]
}

# Stopwords to remove from phrases to isolate the vital name
STOPWORDS = {"is", "level", "abnormal", "normal", "the", "at", "of", "around", "and", "a", "an", "has", "with"}

def extract_vitals_from_text(text: str) -> dict:
    """
    Parses natural language text to extract patient vitals.
    Example: "spo2 level is 98 , bp is 170/60 and hr 190"
    """
    text = text.lower()
    
    # Split text into chunks based on commas or 'and'
    # We replace ' and ' with ',' to standardize chunking
    text = text.replace(" and ", ",")
    chunks = [chunk.strip() for chunk in text.split(",")]
    
    extracted_vitals = {}
    
    # Flatten dictionary for fuzzy matching: map synonym -> canonical key
    synonym_to_key = {}
    for key, synonyms in VITALS_DICT.items():
        for syn in synonyms:
            synonym_to_key[syn] = key
            
    all_synonyms = list(synonym_to_key.keys())

    for chunk in chunks:
        if not chunk:
            continue
            
        # 1. Extract number
        number_val = None
        
        # Check for BP first (e.g., 120/80)
        bp_match = re.search(r'\b(\d{2,3}/\d{2,3})\b', chunk)
        if bp_match:
            number_val = bp_match.group(1)
            # Remove the number from the chunk for text matching
            chunk_text = chunk.replace(number_val, "")
        else:
            # Check for general decimal or integer, ensuring it's not part of a word like 'spo2'
            num_match = re.search(r'\b(\d+(?:\.\d+)?)\b', chunk)
            if num_match:
                number_val = num_match.group(1)
                # Convert to float or int appropriately later, keep as string for now
                chunk_text = chunk.replace(number_val, "")
            else:
                # No number found in this chunk
                continue

        # 2. Extract context words (remove stopwords)
        words = re.findall(r'[a-z]+', chunk_text)
        filtered_words = [w for w in words if w not in STOPWORDS]
        context_string = " ".join(filtered_words)
        
        if not context_string:
            continue

        # 3. Fuzzy Match
        matches = difflib.get_close_matches(context_string, all_synonyms, n=1, cutoff=0.4)
        
        if matches:
            best_match = matches[0]
            canonical_key = synonym_to_key[best_match]
            
            # Format the value appropriately
            if canonical_key == "blood_pressure":
                extracted_vitals[canonical_key] = number_val
            elif canonical_key == "temperature":
                extracted_vitals[canonical_key] = float(number_val)
            else:
                # heart_rate, spo2, respiratory_rate, gcs are ints
                extracted_vitals[canonical_key] = int(float(number_val))

    return extracted_vitals
