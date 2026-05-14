from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from datetime import datetime

from app.utils.database import get_db
from app.services.consent_service import create_consent_session, verify_otp
from app.models.db_models import ConsentSession

router = APIRouter()

class ConsentRequest(BaseModel):
    patient_uid: str
    provider_id: str
    phone_number: str

class VerifyRequest(BaseModel):
    session_id: str
    otp: str

@router.post("/consent/request", tags=["Consent"])
def request_consent(body: ConsentRequest, db: Session = Depends(get_db)):
    session_id, otp = create_consent_session(
        patient_uid=body.patient_uid,
        provider_id=body.provider_id,
        phone=body.phone_number,
        tier=3, # Tier 3 is the only one needing explicit consent in this flow
        db=db
    )
    
    return {
        "session_id": session_id,
        "message": "Consent OTP sent to patient.",
        "demo_otp": otp, # Only for non-production demo
        "expires_in_seconds": 600
    }

@router.post("/consent/verify", tags=["Consent"])
def verify_consent(body: VerifyRequest, db: Session = Depends(get_db)):
    approved = verify_otp(body.session_id, body.otp, db)
    if approved:
        return {"approved": True, "message": "Consent approved successfully."}
    else:
        return {"approved": False, "message": "Invalid or expired OTP."}

@router.get("/consent/status/{patient_uid}/{provider_id}", tags=["Consent"])
def get_consent_status(patient_uid: str, provider_id: str, db: Session = Depends(get_db)):
    session = db.query(ConsentSession).filter(
        ConsentSession.patient_uid == patient_uid,
        ConsentSession.provider_id == provider_id,
        ConsentSession.tier_requested == 3,
        ConsentSession.status == "approved",
        ConsentSession.expires_at > datetime.utcnow()
    ).order_by(ConsentSession.created_at.desc()).first()
    
    if session:
        return {"has_active_consent": True, "expires_at": session.expires_at}
    return {"has_active_consent": False, "expires_at": None}
