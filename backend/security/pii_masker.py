def mask_name(name: str) -> str:
    """
    Masks a name to preserve privacy (e.g., John Doe -> J*** D***).
    """
    if not name:
        return name
    
    parts = name.split()
    masked_parts = []
    for part in parts:
        if len(part) <= 1:
            masked_parts.append(part)
        elif len(part) == 2:
            masked_parts.append(part[0] + "*")
        else:
            masked_parts.append(part[0] + "***")
    
    return " ".join(masked_parts)

def mask_patient_dict(patient_data: dict) -> dict:
    """
    Returns a copy of the patient dictionary with PII masked.
    """
    masked_data = patient_data.copy()
    if "name" in masked_data and isinstance(masked_data["name"], str):
        masked_data["name"] = mask_name(masked_data["name"])
    # We leave age intact as per requirements
    return masked_data
