# app/config.py
import os

TIER_LABELS = {
    0: "Emergency",
    1: "ASHA / Paramedic",
    2: "Pharmacist",
    3: "Doctor / Full Access",
}

TIER_KEYS = {
    0: b"TIER0KEY_EMERGENCY_PLAIN_NO_ENCR",
    1: b"TIER1KEY_ASHA_WORKER_32BYTES!!!X",
    2: b"TIER2KEY_PHARMACIST_32BYTES!!!!X",
    3: b"TIER3KEY_DOCTOR_FULL_ACCESS!!!!X",
}

BASE_DIR      = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATABASE_PATH = os.path.join(BASE_DIR, "database", "medichain.db")
DATABASE_URL  = f"sqlite:///{DATABASE_PATH}"

QR_OUTPUT_DIR = os.path.join(BASE_DIR, "qr_codes")
os.makedirs(QR_OUTPUT_DIR, exist_ok=True)