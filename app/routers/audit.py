from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.utils.database import get_db
from app.services.audit import get_audit_trail, verify_audit_chain

router = APIRouter()

@router.get("/audit/{patient_uid}", tags=["Audit"])
def get_patient_audit(patient_uid: str, db: Session = Depends(get_db)):
    return {"patient_uid": patient_uid, "audit_trail": get_audit_trail(patient_uid, db)}

@router.get("/audit/{patient_uid}/verify", tags=["Audit"])
def verify_patient_audit(patient_uid: str, db: Session = Depends(get_db)):
    return verify_audit_chain(patient_uid, db)
