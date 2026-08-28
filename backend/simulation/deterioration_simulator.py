from __future__ import annotations
import random

def simulate_deterioration(queue_items: dict, percentage: float = 0.15) -> list[str]:
    deteriorated_ids = []
    
    if not queue_items:
        return deteriorated_ids
        
    num_to_deteriorate = int(len(queue_items) * percentage)
    if num_to_deteriorate == 0 and random.random() < percentage:
        num_to_deteriorate = 1
        
    if num_to_deteriorate > len(queue_items):
        num_to_deteriorate = len(queue_items)
        
    patients_to_modify = random.sample(list(queue_items.keys()), num_to_deteriorate)
    
    for pid in patients_to_modify:
        item = queue_items[pid]
        # Depending on queue_items structure, usually item.patient.vitals
        vitals = getattr(item, 'patient', item).vitals
        
        changes = random.sample(['hr', 'spo2', 'temp', 'gcs', 'rr'], random.randint(1, 3))
        
        for change in changes:
            if change == 'hr':
                if vitals.heart_rate is not None:
                    vitals.heart_rate += random.randint(10, 30)
                else:
                    vitals.heart_rate = random.randint(90, 110)
            elif change == 'spo2':
                if vitals.spo2 is not None:
                    vitals.spo2 = max(0, vitals.spo2 - random.randint(2, 8))
                else:
                    vitals.spo2 = random.randint(88, 94)
            elif change == 'temp':
                if vitals.temperature is not None:
                    vitals.temperature += random.uniform(0.3, 1.0)
                    vitals.temperature = round(vitals.temperature, 1)
                else:
                    vitals.temperature = round(37.5 + random.uniform(0.3, 1.0), 1)
            elif change == 'gcs':
                if vitals.gcs is not None:
                    vitals.gcs = max(3, vitals.gcs - random.randint(1, 2))
            elif change == 'rr':
                if vitals.respiratory_rate is not None:
                    vitals.respiratory_rate += random.randint(4, 8)
                else:
                    vitals.respiratory_rate = random.randint(20, 26)
                    
        deteriorated_ids.append(pid)
        
    return deteriorated_ids
