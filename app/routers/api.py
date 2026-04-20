# app/routers/api.py
# ─────────────────────────────────────────────────────────────
# FastAPI route definitions for MediChain Lite backend
# ─────────────────────────────────────────────────────────────

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


# ══════════════════════════════════════════════════════════════
# PYDANTIC SCHEMAS  (request/response models)
# ══════════════════════════════════════════════════════════════

class PatientRegisterRequest(BaseModel):
    patient_uid:    str
    name:           str
    age:            int
    blood_group:    str
    phone:          str
    tier0:          dict    # emergency info
    tier1:          dict    # ASHA-level data
    tier2:          dict    # pharmacist-level data
    tier3:          dict    # doctor-level data

class ProviderRegisterRequest(BaseModel):
    provider_id:    str
    name:           str
    role:           str         # doctor / pharmacist / asha
    tier_level:     int         # 0–3
    license_key:    str         # raw key — will be hashed before storage

class QRScanRequest(BaseModel):
    qr_raw_json:    str         # JSON string from the scanned QR
    provider_id:    str
    license_key:    str

class DrugCheckRequest(BaseModel):
    new_drug:               str
    existing_medications:   list[str]
    provider_id:            str
    patient_uid:            Optional[str] = None

class FullRegimenCheckRequest(BaseModel):
    medications:    list[str]


# ══════════════════════════════════════════════════════════════
# PATIENT ENDPOINTS
# ══════════════════════════════════════════════════════════════

@router.post("/patients/register", tags=["Patients"])
def register_patient(body: PatientRegisterRequest, db: Session = Depends(get_db)):
    """
    Register a new patient, encrypt their tier data, generate the QR code.
    Returns the QR image path.
    """
    # Check duplicate
    exists = db.query(Patient).filter(Patient.patient_uid == body.patient_uid).first()
    if exists:
        raise HTTPException(400, f"Patient {body.patient_uid} already registered.")

    patient_data = body.model_dump()

    # Generate encrypted payload + QR
    payload   = build_encrypted_payload(patient_data)
    qr_path   = generate_qr(patient_data)

    # Persist to DB
    patient = Patient(
        patient_uid   = body.patient_uid,
        name          = body.name,
        age           = body.age,
        blood_group   = body.blood_group,
        phone         = body.phone,
        tier0_blob    = payload["tier0"],
        tier1_blob    = payload["tier1"],
        tier2_blob    = payload["tier2"],
        tier3_blob    = payload["tier3"],
        qr_image_path = qr_path,
    )
    db.add(patient)
    db.commit()

    return {"message": "Patient registered.", "patient_uid": body.patient_uid, "qr_path": qr_path}


# ══════════════════════════════════════════════════════════════
# PROVIDER ENDPOINTS
# ══════════════════════════════════════════════════════════════

@router.post("/providers/register", tags=["Providers"])
def register_provider(body: ProviderRegisterRequest, db: Session = Depends(get_db)):
    """Register a new healthcare provider with hashed credentials."""
    exists = db.query(Provider).filter(Provider.provider_id == body.provider_id).first()
    if exists:
        raise HTTPException(400, f"Provider {body.provider_id} already registered.")

    provider = Provider(
        provider_id  = body.provider_id,
        name         = body.name,
        role         = body.role,
        tier_level   = body.tier_level,
        license_hash = hash_license_key(body.license_key),
    )
    db.add(provider)
    db.commit()
    return {"message": "Provider registered.", "provider_id": body.provider_id}


# ══════════════════════════════════════════════════════════════
# QR SCAN ENDPOINT (core workflow)
# ══════════════════════════════════════════════════════════════

@router.post("/qr/scan", tags=["QR"])
def scan_qr(body: QRScanRequest, request: Request, db: Session = Depends(get_db)):
    """
    Main scan endpoint.
    1. Verifies provider credentials.
    2. Decodes + decrypts QR data up to provider's tier.
    3. Logs the access event to the audit trail.
    Returns decrypted patient data for that provider's tier.
    """
    # 1. Verify provider
    provider = verify_provider(body.provider_id, body.license_key, db)
    if not provider:
        raise HTTPException(401, "Invalid provider credentials.")

    # 2. Decode QR
    try:
        qr_payload = decode_qr_payload(body.qr_raw_json)
    except ValueError as e:
        raise HTTPException(400, str(e))

    # 3. Decrypt up to tier
    decrypted = decrypt_up_to_tier(qr_payload, provider.tier_level)

    # 4. Audit log
    log_event(
        db           = db,
        patient_uid  = qr_payload["patient_uid"],
        provider_id  = body.provider_id,
        action       = "scan",
        tier_accessed = provider.tier_level,
        details      = {"role": provider.role},
        ip_address   = request.client.host if request.client else None,
    )

    return {
        "patient_uid":   qr_payload["patient_uid"],
        "tier_accessed": provider.tier_level,
        "provider_role": provider.role,
        "data":          decrypted,
    }


# ══════════════════════════════════════════════════════════════
# DRUG INTERACTION ENDPOINTS
# ══════════════════════════════════════════════════════════════

@router.post("/drugs/check", tags=["Drug Interactions"])
def drug_interaction_check(body: DrugCheckRequest, db: Session = Depends(get_db)):
    """
    Check a new drug against a patient's existing medication list.
    Logs the check to the audit trail if patient_uid is provided.
    """
    result = check_interactions(body.new_drug, body.existing_medications, db)

    if body.patient_uid:
        log_event(
            db            = db,
            patient_uid   = body.patient_uid,
            provider_id   = body.provider_id,
            action        = "interaction_check",
            tier_accessed = 2,
            details       = {
                "new_drug":     body.new_drug,
                "interactions": result["interactions_found"],
                "safe":         result["safe_to_dispense"],
            },
        )
    return result


@router.post("/drugs/check-regimen", tags=["Drug Interactions"])
def regimen_check(body: FullRegimenCheckRequest, db: Session = Depends(get_db)):
    """Check all pairwise interactions within a patient's full medication list."""
    return check_full_list(body.medications, db)


# ══════════════════════════════════════════════════════════════
# AUDIT TRAIL ENDPOINTS
# ══════════════════════════════════════════════════════════════

@router.get("/audit/{patient_uid}", tags=["Audit"])
def get_patient_audit(patient_uid: str, db: Session = Depends(get_db)):
    """Return the complete audit trail for a patient."""
    return {"patient_uid": patient_uid, "audit_trail": get_audit_trail(patient_uid, db)}


@router.get("/audit/{patient_uid}/verify", tags=["Audit"])
def verify_patient_audit(patient_uid: str, db: Session = Depends(get_db)):
    """Verify the tamper-evident chain integrity for a patient's audit trail."""
    return verify_audit_chain(patient_uid, db)


# ══════════════════════════════════════════════════════════════
# UTILITY ENDPOINTS
# ══════════════════════════════════════════════════════════════

@router.get("/tiers/{tier_level}", tags=["Utility"])
def tier_info(tier_level: int):
    """Return what a given tier level can access."""
    if tier_level not in range(4):
        raise HTTPException(400, "Tier must be 0, 1, 2, or 3.")
    return describe_tier_access(tier_level)


@router.get("/health", tags=["Utility"])
def health_check():
    return {"status": "ok", "system": "MediChain Lite"}