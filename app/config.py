# app/config.py — FIXED
import os
import base64

TIER_LABELS = {
    0: "Emergency",
    1: "ASHA / Paramedic",
    2: "Pharmacist",
    3: "Doctor / Full Access",
}

def _load_key(env_var: str, fallback: bytes) -> bytes:
    """Load a 32-byte AES key from env, or use fallback in dev."""
    raw = os.environ.get(env_var)
    if raw:
        key = base64.b64decode(raw)
        if len(key) != 32:
            raise ValueError(f"{env_var} must decode to exactly 32 bytes, got {len(key)}")
        return key
    if os.environ.get("APP_ENV") == "production":
        raise RuntimeError(f"Missing required env var {env_var} in production mode.")
    return fallback  # dev/test only

TIER_KEYS = {
    0: _load_key("TIER0_KEY", b"TIER0KEY_EMERGENCY_PLAIN_NO_ENCR"),
    1: _load_key("TIER1_KEY", b"TIER1KEY_ASHA_WORKER_32BYTES!!!X"),
    2: _load_key("TIER2_KEY", b"TIER2KEY_PHARMACIST_32BYTES!!!!X"),
    3: _load_key("TIER3_KEY", b"TIER3KEY_DOCTOR_FULL_ACCESS!!!!X"),
}

BASE_DIR      = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATABASE_PATH = os.path.join(BASE_DIR, "database", "medichain.db")
DATABASE_URL  = os.environ.get("DATABASE_URL", f"sqlite:///{DATABASE_PATH}")

QR_OUTPUT_DIR = os.path.join(BASE_DIR, "qr_codes")
os.makedirs(QR_OUTPUT_DIR, exist_ok=True)