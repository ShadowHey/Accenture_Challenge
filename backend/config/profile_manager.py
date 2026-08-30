import os
import json
from typing import Dict, List, Any

class ProfileManager:
    def __init__(self):
        self.profiles: Dict[str, dict] = {}
        self.active_profile_id: str = "standard_general"
        self._load_profiles()

    def _load_profiles(self):
        """Load all JSON profiles from the profiles directory."""
        base_dir = os.path.dirname(__file__)
        profiles_dir = os.path.join(base_dir, "profiles")
        if not os.path.exists(profiles_dir):
            return
            
        for filename in os.listdir(profiles_dir):
            if filename.endswith(".json"):
                path = os.path.join(profiles_dir, filename)
                try:
                    with open(path, "r") as f:
                        data = json.load(f)
                        if "id" in data:
                            self.profiles[data["id"]] = data
                except Exception as e:
                    print(f"Error loading profile {filename}: {e}")
                    
        if self.active_profile_id not in self.profiles and self.profiles:
            self.active_profile_id = list(self.profiles.keys())[0]

    def get_all_profiles(self) -> List[dict]:
        return list(self.profiles.values())

    def set_active_profile(self, profile_id: str) -> bool:
        if profile_id in self.profiles:
            self.active_profile_id = profile_id
            return True
        return False

    def get_active_profile(self) -> dict:
        return self.profiles.get(self.active_profile_id, {})

    def get_active_thresholds(self, surge_mode: bool = False) -> dict:
        """Returns wait thresholds, dynamically modified if in surge mode."""
        profile = self.get_active_profile()
        base_thresholds = profile.get("wait_thresholds_seconds", {})
        
        if not surge_mode:
            return base_thresholds
            
        # Apply surge multiplier
        multiplier = profile.get("surge_multiplier", 0.5)
        return {k: int(v * multiplier) for k, v in base_thresholds.items()}
        
    def get_surge_trigger_capacity(self) -> int:
        return self.get_active_profile().get("surge_capacity_trigger", 20)

profile_manager = ProfileManager()
