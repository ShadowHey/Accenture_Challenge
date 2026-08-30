import uuid
from typing import Dict, Any
from datetime import datetime

class FHIRParserError(Exception):
    pass

def parse_fhir_bundle(bundle: Dict[str, Any]) -> Dict[str, Any]:
    """
    Parses a FHIR standard Bundle containing Patient, Observation, and Condition resources.
    Translates it into the dictionary format expected by our custom PatientInput model.
    """
    if bundle.get("resourceType") != "Bundle":
        raise FHIRParserError("Expected a FHIR Bundle resource")
        
    entries = bundle.get("entry", [])
    
    patient_data = {
        "id": None,
        "name": "Unknown",
        "age": 0,
        "gender": "O",
        "chief_complaint": "Referred via FHIR Integration",
        "medical_history": [],
        "observed_signs": [],
        "symptoms": [],
        "arrival_mode": "transfer",
        "history_available": True
    }
    
    vitals_data = {}
    
    # Standard LOINC Codes used in FHIR for Vitals
    LOINC_MAP = {
        "8867-4": "heart_rate",
        "2708-6": "spo2",
        "8310-5": "temperature",
        "9279-1": "respiratory_rate",
        "72514-3": "pain_scale"
    }
    
    for entry in entries:
        resource = entry.get("resource", {})
        r_type = resource.get("resourceType")
        
        if r_type == "Patient":
            # Parse Patient Demographics
            if "id" in resource:
                patient_data["id"] = f"FHIR-{resource['id']}"
                
            name_list = resource.get("name", [])
            if name_list:
                given = " ".join(name_list[0].get("given", []))
                family = name_list[0].get("family", "")
                patient_data["name"] = f"{given} {family}".strip()
                
            gender = resource.get("gender", "unknown").lower()
            if gender == "male": patient_data["gender"] = "M"
            elif gender == "female": patient_data["gender"] = "F"
            else: patient_data["gender"] = "O"
            
            birthDate = resource.get("birthDate")
            if birthDate:
                try:
                    b_year = int(birthDate.split("-")[0])
                    current_year = datetime.now().year
                    patient_data["age"] = current_year - b_year
                except:
                    pass
                    
        elif r_type == "Observation":
            # Parse Vitals from Observations using LOINC codes
            coding = resource.get("code", {}).get("coding", [])
            loinc_code = None
            for c in coding:
                if c.get("system") == "http://loinc.org":
                    loinc_code = c.get("code")
                    break
                    
            if loinc_code in LOINC_MAP:
                internal_key = LOINC_MAP[loinc_code]
                value = resource.get("valueQuantity", {}).get("value")
                if value is not None:
                    # Pain scale is usually 0-10, temperature is float, others are usually ints in our system
                    if internal_key == "temperature":
                        vitals_data[internal_key] = float(value)
                    else:
                        vitals_data[internal_key] = int(value)
                        
            # Handle Blood Pressure (Often uses components: Systolic 8480-6, Diastolic 8462-4)
            if loinc_code == "85354-9":
                systolic = None
                diastolic = None
                for comp in resource.get("component", []):
                    comp_codes = [c.get("code") for c in comp.get("code", {}).get("coding", [])]
                    if "8480-6" in comp_codes:
                        systolic = comp.get("valueQuantity", {}).get("value")
                    elif "8462-4" in comp_codes:
                        diastolic = comp.get("valueQuantity", {}).get("value")
                if systolic and diastolic:
                    vitals_data["blood_pressure"] = f"{int(systolic)}/{int(diastolic)}"
                    
        elif r_type == "Condition":
            # Extract medical history or chief complaint from Condition resources
            code_display = resource.get("code", {}).get("text")
            if not code_display:
                # Try to get from coding if text isn't directly available
                coding = resource.get("code", {}).get("coding", [])
                if coding:
                    code_display = coding[0].get("display")
                    
            if code_display:
                status_coding = resource.get("clinicalStatus", {}).get("coding", [{}])
                status = status_coding[0].get("code") if status_coding else None
                
                # If it's an active condition (or reason for visit), treat as chief complaint
                if status == "active" and patient_data["chief_complaint"] == "Referred via FHIR Integration":
                    patient_data["chief_complaint"] = code_display
                else:
                    patient_data["medical_history"].append(code_display)
    
    if patient_data["id"] is None:
        patient_data["id"] = f"FHIR-{str(uuid.uuid4())[:8]}"
        
    # Assemble the final dictionary matching our PatientInput schema
    patient_data["vitals"] = vitals_data
    return patient_data
