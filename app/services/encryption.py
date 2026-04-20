# app/services/encryption.py
# ─────────────────────────────────────────────────────────────
# AES-256-CBC encryption for tiered QR payload
#
# HOW TIERS WORK
# ──────────────
#  Tier 0 → Stored as plain JSON  (emergency info, no key needed)
#  Tier 1 → AES-256 encrypted with TIER1_KEY  (ASHA workers)
#  Tier 2 → AES-256 encrypted with TIER2_KEY  (Pharmacists)
#  Tier 3 → AES-256 encrypted with TIER3_KEY  (Doctors)
#
# Each encrypted blob = base64( IV [16 bytes] + ciphertext )
# Stored as a UTF-8 string so it embeds cleanly in JSON / QR.
# ─────────────────────────────────────────────────────────────

import json
import base64
import os
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
from app.config import TIER_KEYS


# ── Low-level AES helpers ─────────────────────────────────────

def _aes_encrypt(plaintext: str, key: bytes) -> str:
    """
    Encrypt a UTF-8 string with AES-256-CBC.
    Returns a base64 string:  base64(IV + ciphertext)
    """
    iv        = os.urandom(16)                          # random 16-byte IV every time
    cipher    = AES.new(key, AES.MODE_CBC, iv)
    padded    = pad(plaintext.encode("utf-8"), AES.block_size)
    encrypted = cipher.encrypt(padded)
    blob      = base64.b64encode(iv + encrypted).decode("utf-8")
    return blob


def _aes_decrypt(blob: str, key: bytes) -> str:
    """
    Decrypt a base64 blob produced by _aes_encrypt.
    Raises ValueError if the key is wrong or data is tampered.
    """
    raw       = base64.b64decode(blob.encode("utf-8"))
    iv        = raw[:16]
    ciphertext = raw[16:]
    cipher    = AES.new(key, AES.MODE_CBC, iv)
    try:
        plaintext = unpad(cipher.decrypt(ciphertext), AES.block_size)
    except (ValueError, KeyError):
        raise ValueError("Decryption failed — wrong key or tampered data.")
    return plaintext.decode("utf-8")


# ── Tier-level helpers ────────────────────────────────────────

def encrypt_tier(data: dict, tier: int) -> str:
    """
    Encrypt a dict for the given tier.
    Tier 0 is stored as plain JSON (public emergency info).
    """
    json_str = json.dumps(data)
    if tier == 0:
        return json_str                                 # no encryption for emergency tier
    key = TIER_KEYS.get(tier)
    if key is None:
        raise ValueError(f"Unknown tier: {tier}")
    return _aes_encrypt(json_str, key)


def decrypt_tier(blob: str, tier: int) -> dict:
    """
    Decrypt a blob for the given tier and return a dict.
    Raises ValueError on wrong key / tampered data.
    """
    if tier == 0:
        return json.loads(blob)                         # plain JSON for tier 0
    key = TIER_KEYS.get(tier)
    if key is None:
        raise ValueError(f"Unknown tier: {tier}")
    json_str = _aes_decrypt(blob, key)
    return json.loads(json_str)


# ── Full patient payload builder ──────────────────────────────

def build_encrypted_payload(patient_data: dict) -> dict:
    """
    Given a complete patient dict (all tiers), returns a dict of
    encrypted blobs ready to embed into the QR code.

    patient_data structure expected:
    {
        "patient_uid": "PAT-2024-00001",
        "tier0": { "name": ..., "blood_group": ..., "emergency_contact": ..., "allergies": ... },
        "tier1": { "chronic_conditions": [...], "current_medications": [...] },
        "tier2": { "prescriptions": [...], "lab_results": [...] },
        "tier3": { "full_history": [...], "doctor_notes": [...] }
    }
    """
    return {
        "patient_uid": patient_data["patient_uid"],
        "tier0": encrypt_tier(patient_data.get("tier0", {}), tier=0),
        "tier1": encrypt_tier(patient_data.get("tier1", {}), tier=1),
        "tier2": encrypt_tier(patient_data.get("tier2", {}), tier=2),
        "tier3": encrypt_tier(patient_data.get("tier3", {}), tier=3),
    }


def decrypt_up_to_tier(payload: dict, max_tier: int) -> dict:
    """
    Decrypt all tiers from 0 up to max_tier (inclusive).
    Returns a merged dict of all accessible data.
    Used when a provider scans a QR — they get everything up to their tier.
    """
    result = {}
    for t in range(max_tier + 1):
        key_name = f"tier{t}"
        if key_name in payload and payload[key_name]:
            try:
                result[f"tier{t}"] = decrypt_tier(payload[key_name], tier=t)
            except ValueError:
                result[f"tier{t}"] = {"error": "Decryption failed for this tier."}
    return result