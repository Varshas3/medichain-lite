import uuid
import random
import bcrypt
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.models.db_models import ConsentSession

def create_consent_session(patient_uid: str, provider_id: str, phone: str, tier: int, db: Session):
    session_id = str(uuid.uuid4())
    # Generate 6-digit OTP
    otp = f"{random.randint(0, 999999):06d}"
    
    # Hash OTP
    otp_hash = bcrypt.hashpw(otp.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    
    expires_at = datetime.utcnow() + timedelta(minutes=10)
    
    session = ConsentSession(
        session_id=session_id,
        patient_uid=patient_uid,
        provider_id=provider_id,
        otp_hash=otp_hash,
        phone_number=phone,
        tier_requested=tier,
        status="pending",
        expires_at=expires_at
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    
    # In demo mode, print OTP to console
    print(f"[DEMO OTP] For session {session_id}, OTP is: {otp}")
    
    # In production: call send_sms(phone, otp)
    # TODO: Implement actual SMS gateway integration here
    
    return session_id, otp

def verify_otp(session_id: str, otp_entered: str, db: Session) -> bool:
    session = db.query(ConsentSession).filter(ConsentSession.session_id == session_id).first()
    if not session:
        return False
        
    if session.status != "pending":
        return False
        
    if datetime.utcnow() > session.expires_at:
        session.status = "expired"
        db.commit()
        return False
        
    if bcrypt.checkpw(otp_entered.encode("utf-8"), session.otp_hash.encode("utf-8")):
        session.status = "approved"
        session.approved_at = datetime.utcnow()
        db.commit()
        return True
        
    return False

def is_tier3_consented(patient_uid: str, provider_id: str, db: Session) -> bool:
    session = db.query(ConsentSession).filter(
        ConsentSession.patient_uid == patient_uid,
        ConsentSession.provider_id == provider_id,
        ConsentSession.tier_requested == 3,
        ConsentSession.status == "approved",
        ConsentSession.expires_at > datetime.utcnow()
    ).first()
    
    return session is not None
