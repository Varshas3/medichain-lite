# app/services/qr_service.py
# ─────────────────────────────────────────────────────────────
# QR Code generation and decoding for MediChain Lite
#
# The QR code embeds a JSON string with four encrypted tier blobs.
# Format stored inside QR:
# {
#   "v": 1,                          ← schema version
#   "uid": "PAT-2024-00001",
#   "t0": "<plain JSON>",            ← Tier 0 (no encryption)
#   "t1": "<AES base64 blob>",       ← Tier 1
#   "t2": "<AES base64 blob>",       ← Tier 2
#   "t3": "<AES base64 blob>"        ← Tier 3
# }
# ─────────────────────────────────────────────────────────────

import json
import os
import qrcode
from qrcode.constants import ERROR_CORRECT_H
from PIL import Image, ImageDraw, ImageFont
from app.config import QR_OUTPUT_DIR
from app.services.encryption import build_encrypted_payload


def generate_qr(patient_data: dict) -> str:
    """
    Build the encrypted payload and render it as a QR code PNG.

    Args:
        patient_data: full patient dict (see build_encrypted_payload docstring)

    Returns:
        Absolute path to the saved QR code PNG.
    """
    # 1. Build encrypted tier blobs
    payload = build_encrypted_payload(patient_data)

    # 2. Compact JSON → embed in QR
    qr_content = json.dumps({
        "v":   1,
        "uid": payload["patient_uid"],
        "t0":  payload["tier0"],
        "t1":  payload["tier1"],
        "t2":  payload["tier2"],
        "t3":  payload["tier3"],
    }, separators=(",", ":"))   # compact — saves QR modules

    # 3. Generate QR image (high error correction so it still scans if printed)
    qr = qrcode.QRCode(
        version=None,                   # auto-size
        error_correction=ERROR_CORRECT_H,
        box_size=8,
        border=4,
    )
    qr.add_data(qr_content)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white").convert("RGB")

    # 4. Add a small label strip at the bottom
    img = _add_label(img, patient_data)

    # 5. Save
    uid       = patient_data["patient_uid"]
    filename  = f"{uid}.png"
    save_path = os.path.join(QR_OUTPUT_DIR, filename)
    img.save(save_path)
    print(f"[QR] Saved → {save_path}")
    return save_path


def _add_label(img: Image.Image, patient_data: dict) -> Image.Image:
    """Append a white strip below the QR with name + UID + blood group."""
    strip_h = 50
    new_img = Image.new("RGB", (img.width, img.height + strip_h), "white")
    new_img.paste(img, (0, 0))

    draw = ImageDraw.Draw(new_img)
    name    = patient_data.get("tier0", {}).get("name", patient_data.get("patient_uid", ""))
    bg      = patient_data.get("tier0", {}).get("blood_group", "")
    uid     = patient_data.get("patient_uid", "")
    label   = f"{name}  |  {uid}  |  Blood: {bg}"

    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 14)
    except Exception:
        font = ImageFont.load_default()

    # Centre the text
    bbox = draw.textbbox((0, 0), label, font=font)
    text_w = bbox[2] - bbox[0]
    x = (new_img.width - text_w) // 2
    y = img.height + 10
    draw.text((x, y), label, fill="black", font=font)
    return new_img


def decode_qr_payload(raw_json: str) -> dict:
    """
    Parse the raw JSON string extracted from a scanned QR code.
    Returns the payload dict with tier blobs intact (still encrypted).
    """
    try:
        payload = json.loads(raw_json)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid QR payload — not valid JSON: {e}")

    required = {"v", "uid", "t0", "t1", "t2", "t3"}
    missing  = required - payload.keys()
    if missing:
        raise ValueError(f"QR payload missing fields: {missing}")

    # Normalise keys to what the rest of the system expects
    return {
        "patient_uid": payload["uid"],
        "tier0": payload["t0"],
        "tier1": payload["t1"],
        "tier2": payload["t2"],
        "tier3": payload["t3"],
    }