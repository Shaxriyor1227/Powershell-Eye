# -*- coding: utf-8 -*-
"""
Biometrik Xotira Menejeri (Biometric Identity & Memory Storage)
"""

import os
import json
from datetime import datetime

MEMORY_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
MEMORY_FILE = os.path.join(MEMORY_DIR, "optic_memory.json")

class BiometricMemory:
    def __init__(self, default_name="Boss"):
        self.default_name = default_name
        self.profile = None
        self.is_new_user = False
        self.load()

    def load(self):
        if not os.path.exists(MEMORY_DIR):
            os.makedirs(MEMORY_DIR, exist_ok=True)

        if os.path.exists(MEMORY_FILE):
            try:
                with open(MEMORY_FILE, "r", encoding="utf-8") as f:
                    self.profile = json.load(f)
                    self.profile["sessions_count"] = self.profile.get("sessions_count", 0) + 1
                    self.profile["last_seen"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    self.is_new_user = False
                    self.save()
                    return
            except Exception:
                pass

        # Yangi profil
        self.is_new_user = True
        self.profile = {
            "operator_name": self.default_name,
            "biometric_id": "SHX-0821-ALPHA",
            "retinal_dna_hash": "0x7F4A9B81C2E0",
            "clearance_level": "LEVEL 5 // ROOT OPERATOR",
            "first_registered": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "last_seen": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "sessions_count": 1,
            "match_rate": 99.85
        }
        self.save()

    def register_new_operator(self, new_name, dna_hash=None):
        """Yangi operatorni ro'yxatga olish."""
        self.profile["operator_name"] = new_name
        if dna_hash:
            self.profile["retinal_dna_hash"] = dna_hash
        self.profile["last_seen"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.profile["sessions_count"] = 1
        self.save()

    def save(self):
        try:
            with open(MEMORY_FILE, "w", encoding="utf-8") as f:
                json.dump(self.profile, f, indent=4, ensure_ascii=False)
        except Exception:
            pass

    @property
    def name(self):
        return self.profile.get("operator_name", self.default_name)

    @property
    def session_count(self):
        return self.profile.get("sessions_count", 1)

    @property
    def match_rate(self):
        return self.profile.get("match_rate", 99.8)

    @property
    def clearance(self):
        return self.profile.get("clearance_level", "ROOT")
