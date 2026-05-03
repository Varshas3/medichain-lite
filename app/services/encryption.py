import json, base64, os
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
from app.config import TIER_KEYS

def _aes_encrypt(plaintext: str, key: bytes) -> str:
    iv        = os.urandom(16)
    cipher    = AES.new(key, AES.MODE_CBC, iv)
    padded    = pad(plaintext.encode("utf-8"), AES.block_size)
    encrypted = cipher.encrypt(padded)
    return base64.b64encode(iv + encrypted).decode("utf-8")

def _aes_decrypt(blob: str, key: bytes) -> str:
    raw        = base64.b64decode(blob.encode("utf-8"))
    iv         = raw[:16]
    ciphertext = raw[16:]
    cipher     = AES.new(key, AES.MODE_CBC, iv)
    try:
        plaintext = unpad(cipher.decrypt(ciphertext), AES.block_size)
    except (ValueError, KeyError):
        raise ValueError("Decryption failed — wrong key or tampered data.")
    return plaintext.decode("utf-8")

def encrypt_tier(data: dict, tier: int) -> str:
    json_str = json.dumps(data)
    if tier == 0:
        return json_str
    key = TIER_KEYS.get(tier)
    if key is None:
        raise ValueError(f"Unknown tier: {tier}")
    return _aes_encrypt(json_str, key)

def decrypt_tier(blob: str, tier: int) -> dict:
    if tier == 0:
        return json.loads(blob)
    key = TIER_KEYS.get(tier)
    if key is None:
        raise ValueError(f"Unknown tier: {tier}")
    return json.loads(_aes_decrypt(blob, key))

def build_encrypted_payload(patient_data: dict) -> dict:
    return {
        "patient_uid": patient_data["patient_uid"],
        "tier0": encrypt_tier(patient_data.get("tier0", {}), tier=0),
        "tier1": encrypt_tier(patient_data.get("tier1", {}), tier=1),
        "tier2": encrypt_tier(patient_data.get("tier2", {}), tier=2),
        "tier3": encrypt_tier(patient_data.get("tier3", {}), tier=3),
    }

def decrypt_up_to_tier(payload: dict, max_tier: int) -> dict:
    result = {}
    for t in range(max_tier + 1):
        key_name = f"tier{t}"
        if key_name in payload and payload[key_name]:
            try:
                result[f"tier{t}"] = decrypt_tier(payload[key_name], tier=t)
            except ValueError:
                result[f"tier{t}"] = {"error": "Decryption failed for this tier."}
    return result