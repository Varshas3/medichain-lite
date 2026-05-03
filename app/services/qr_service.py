import json, os
import qrcode
from qrcode.constants import ERROR_CORRECT_H
from PIL import Image, ImageDraw, ImageFont
from app.config import QR_OUTPUT_DIR
from app.services.encryption import build_encrypted_payload

def generate_qr(patient_data: dict) -> str:
    payload    = build_encrypted_payload(patient_data)
    qr_content = json.dumps({
        "v": 1, "uid": payload["patient_uid"],
        "t0": payload["tier0"], "t1": payload["tier1"],
        "t2": payload["tier2"], "t3": payload["tier3"],
    }, separators=(",", ":"))
    qr = qrcode.QRCode(version=None, error_correction=ERROR_CORRECT_H, box_size=8, border=4)
    qr.add_data(qr_content)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white").convert("RGB")
    img = _add_label(img, patient_data)
    save_path = os.path.join(QR_OUTPUT_DIR, f"{patient_data['patient_uid']}.png")
    img.save(save_path)
    print(f"[QR] Saved → {save_path}")
    return save_path

def _add_label(img: Image.Image, patient_data: dict) -> Image.Image:
    strip_h = 50
    new_img = Image.new("RGB", (img.width, img.height + strip_h), "white")
    new_img.paste(img, (0, 0))
    draw  = ImageDraw.Draw(new_img)
    name  = patient_data.get("tier0", {}).get("name", patient_data.get("patient_uid", ""))
    bg    = patient_data.get("tier0", {}).get("blood_group", "")
    uid   = patient_data.get("patient_uid", "")
    label = f"{name}  |  {uid}  |  Blood: {bg}"
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 14)
    except Exception:
        font = ImageFont.load_default()
    bbox   = draw.textbbox((0, 0), label, font=font)
    text_w = bbox[2] - bbox[0]
    draw.text(((new_img.width - text_w) // 2, img.height + 10), label, fill="black", font=font)
    return new_img

def decode_qr_payload(raw_json: str) -> dict:
    try:
        payload = json.loads(raw_json)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid QR payload — not valid JSON: {e}")
    missing = {"v", "uid", "t0", "t1", "t2", "t3"} - payload.keys()
    if missing:
        raise ValueError(f"QR payload missing fields: {missing}")
    return {"patient_uid": payload["uid"], "tier0": payload["t0"], "tier1": payload["t1"],
            "tier2": payload["t2"], "tier3": payload["t3"]}