from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.utils.database import get_db
from app.services.encryption import decrypt_up_to_tier
from app.services.qr_service import decode_qr_payload
from app.services.access_control import verify_provider
from app.services.audit import log_event
from app.services.consent_service import is_tier3_consented

router = APIRouter()

class QRScanRequest(BaseModel):
    qr_raw_json: str
    provider_id: str
    license_key: str

@router.post("/qr/scan", tags=["QR"])
def scan_qr(body: QRScanRequest, request: Request, db: Session = Depends(get_db)):
    """
    Verify provider credentials, decrypt QR up to their tier, log the access.
    """
    provider = verify_provider(body.provider_id, body.license_key, db)
    if not provider:
        raise HTTPException(401, "Invalid provider credentials.")

    try:
        qr_payload = decode_qr_payload(body.qr_raw_json)
    except ValueError as e:
        raise HTTPException(400, str(e))
        
    patient_uid = qr_payload["patient_uid"]

    if provider.tier_level == 3:
        if not is_tier3_consented(patient_uid, provider.provider_id, db):
            raise HTTPException(
                status_code=403, 
                detail={
                    "error": "consent_required",
                    "message": "Patient OTP consent required for Tier 3 access.",
                    "patient_uid": patient_uid,
                    "provider_id": provider.provider_id
                }
            )

    decrypted = decrypt_up_to_tier(qr_payload, provider.tier_level)

    log_event(
        db            = db,
        patient_uid   = patient_uid,
        provider_id   = body.provider_id,
        action        = "scan",
        tier_accessed = provider.tier_level,
        details       = {"role": provider.role},
        ip_address    = request.client.host if request.client else None,
    )

    return {
        "patient_uid":   patient_uid,
        "tier_accessed": provider.tier_level,
        "provider_role": provider.role,
        "data":          decrypted,
    }
