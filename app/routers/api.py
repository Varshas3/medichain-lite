from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

from app.utils.database import get_db
from app.models.db_models import Provider, Patient
from app.services.encryption import build_encrypted_payload, decrypt_up_to_tier
from app.services.qr_service import generate_qr, decode_qr_payload
from app.services.access_control import verify_provider, hash_license_key, describe_tier_access
from app.services.drug_interaction import check_interactions, check_full_list
from app.services.audit import log_event, get_audit_trail, verify_audit_chain

router = APIRouter()

class PatientRegisterRequest(BaseModel):
    patient_uid: str
    name:        str
    age:         int
    blood_group: str
    phone:       str
    tier0:       dict
    tier1:       dict
    tier2:       dict
    tier3:       dict

class ProviderRegisterRequest(BaseModel):
    provider_id: str
    name:        str
    role:        str
    tier_level:  int
    license_key: str

class QRScanRequest(BaseModel):
    qr_raw_json: str
    provider_id: str
    license_key: str

class DrugCheckRequest(BaseModel):
    new_drug:             str
    existing_medications: list[str]
    provider_id:          str
    patient_uid:          Optional[str] = None

class FullRegimenCheckRequest(BaseModel):
    medications: list[str]

@router.post("/patients/register", tags=["Patients"])
def register_patient(body: PatientRegisterRequest, db: Session = Depends(get_db)):
    if db.query(Patient).filter(Patient.patient_uid == body.patient_uid).first():
        raise HTTPException(400, f"Patient {body.patient_uid} already registered.")
    patient_data = body.model_dump()
    payload  = build_encrypted_payload(patient_data)
    qr_path  = generate_qr(patient_data)
    db.add(Patient(patient_uid=body.patient_uid, name=body.name, age=body.age,
                   blood_group=body.blood_group, phone=body.phone,
                   tier0_blob=payload["tier0"], tier1_blob=payload["tier1"],
                   tier2_blob=payload["tier2"], tier3_blob=payload["tier3"],
                   qr_image_path=qr_path))
    db.commit()
    return {"message": "Patient registered.", "patient_uid": body.patient_uid, "qr_path": qr_path}

@router.post("/providers/register", tags=["Providers"])
def register_provider(body: ProviderRegisterRequest, db: Session = Depends(get_db)):
    if db.query(Provider).filter(Provider.provider_id == body.provider_id).first():
        raise HTTPException(400, f"Provider {body.provider_id} already registered.")
    db.add(Provider(provider_id=body.provider_id, name=body.name, role=body.role,
                    tier_level=body.tier_level, license_hash=hash_license_key(body.license_key)))
    db.commit()
    return {"message": "Provider registered.", "provider_id": body.provider_id}

@router.post("/qr/scan", tags=["QR"])
def scan_qr(body: QRScanRequest, request: Request, db: Session = Depends(get_db)):
    provider = verify_provider(body.provider_id, body.license_key, db)
    if not provider:
        raise HTTPException(401, "Invalid provider credentials.")
    try:
        qr_payload = decode_qr_payload(body.qr_raw_json)
    except ValueError as e:
        raise HTTPException(400, str(e))
    decrypted = decrypt_up_to_tier(qr_payload, provider.tier_level)
    log_event(db=db, patient_uid=qr_payload["patient_uid"], provider_id=body.provider_id,
              action="scan", tier_accessed=provider.tier_level, details={"role": provider.role},
              ip_address=request.client.host if request.client else None)
    return {"patient_uid": qr_payload["patient_uid"], "tier_accessed": provider.tier_level,
            "provider_role": provider.role, "data": decrypted}

@router.post("/drugs/check", tags=["Drug Interactions"])
def drug_interaction_check(body: DrugCheckRequest, db: Session = Depends(get_db)):
    result = check_interactions(body.new_drug, body.existing_medications, db)
    if body.patient_uid:
        log_event(db=db, patient_uid=body.patient_uid, provider_id=body.provider_id,
                  action="interaction_check", tier_accessed=2,
                  details={"new_drug": body.new_drug, "interactions": result["interactions_found"],
                           "safe": result["safe_to_dispense"]})
    return result

@router.post("/drugs/check-regimen", tags=["Drug Interactions"])
def regimen_check(body: FullRegimenCheckRequest, db: Session = Depends(get_db)):
    return check_full_list(body.medications, db)

@router.get("/audit/{patient_uid}", tags=["Audit"])
def get_patient_audit(patient_uid: str, db: Session = Depends(get_db)):
    return {"patient_uid": patient_uid, "audit_trail": get_audit_trail(patient_uid, db)}

@router.get("/audit/{patient_uid}/verify", tags=["Audit"])
def verify_patient_audit(patient_uid: str, db: Session = Depends(get_db)):
    return verify_audit_chain(patient_uid, db)

@router.get("/tiers/{tier_level}", tags=["Utility"])
def tier_info(tier_level: int):
    if tier_level not in range(4):
        raise HTTPException(400, "Tier must be 0, 1, 2, or 3.")
    return describe_tier_access(tier_level)

@router.get("/health", tags=["Utility"])
def health_check():
    return {"status": "ok", "system": "MediChain Lite"}