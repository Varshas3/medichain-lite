from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

from app.utils.database import get_db
from app.models.db_models import Patient, AuditLog
from app.services.encryption import build_encrypted_payload
from app.services.qr_service import generate_qr

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

@router.post("/patients/register", tags=["Patients"])
def register_patient(body: PatientRegisterRequest, db: Session = Depends(get_db)):
    """
    Register patient, encrypt tier data, generate QR.
    Returns the encrypted blobs so the frontend can build a real scannable QR payload.
    """
    existing = db.query(Patient).filter(Patient.patient_uid == body.patient_uid).first()
    if existing:
        db.delete(existing)
        db.commit()

    patient_data = body.model_dump()
    payload  = build_encrypted_payload(patient_data)
    qr_path  = generate_qr(patient_data)

    db.add(Patient(
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
    ))
    db.commit()

    return {
        "message":     "Patient registered.",
        "patient_uid": body.patient_uid,
        "qr_path":     qr_path,
        "qr_payload": {
            "v":   1,
            "uid": payload["patient_uid"],
            "t0":  payload["tier0"],
            "t1":  payload["tier1"],
            "t2":  payload["tier2"],
            "t3":  payload["tier3"],
        }
    }

@router.get("/patients/search", tags=["Patients"])
def search_patients(q: str, db: Session = Depends(get_db)):
    """Searches by partial name or UID, returns list of {patient_uid, name, blood_group, audit_count}"""
    patients = db.query(Patient).filter(
        (Patient.name.ilike(f"%{q}%")) | (Patient.patient_uid.ilike(f"%{q}%"))
    ).all()
    
    results = []
    for p in patients:
        audit_count = db.query(AuditLog).filter(AuditLog.patient_uid == p.patient_uid).count()
        results.append({
            "patient_uid": p.patient_uid,
            "name": p.name,
            "blood_group": p.blood_group,
            "audit_count": audit_count
        })
    return results

@router.get("/patients/{uid}", tags=["Patients"])
def get_patient(uid: str, db: Session = Depends(get_db)):
    """Returns Tier 0 public info + audit event count"""
    patient = db.query(Patient).filter(Patient.patient_uid == uid).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
        
    audit_count = db.query(AuditLog).filter(AuditLog.patient_uid == uid).count()
    
    # We could decrypt tier0_blob, but we just return basic DB info since it's "public" Tier 0 equivalent
    return {
        "patient_uid": patient.patient_uid,
        "name": patient.name,
        "age": patient.age,
        "blood_group": patient.blood_group,
        "phone": patient.phone,
        "audit_count": audit_count
    }

@router.get("/demo/patient", tags=["Demo"])
def get_demo_patient():
    """Returns a fully built demo patient payload for frontend testing."""
    return {
        "patient_uid": "PAT-KA-8899",
        "name": "Priya Sharma",
        "age": 45,
        "blood_group": "B+",
        "phone": "+919876543210",
        "tier0": {
            "name": "Priya Sharma",
            "blood_group": "B+",
            "allergies": ["Penicillin"],
            "emergency_contact": "+919988776655"
        },
        "tier1": {
            "chronic_conditions": ["Type 2 Diabetes", "Hypertension", "Dyslipidemia"],
            "current_medications": ["Metformin", "Amlodipine", "Atorvastatin"]
        },
        "tier2": {
            "prescriptions": [
                {"drug": "Metformin", "dosage": "500mg OD"},
                {"drug": "Amlodipine", "dosage": "5mg OD"},
                {"drug": "Atorvastatin", "dosage": "10mg HS"}
            ],
            "refill_history": ["2023-09-01", "2023-10-01"],
            "last_dispensed": "2023-10-01"
        },
        "tier3": {
            "full_history": "Diagnosed with T2DM in 2018. Hypertension noted in 2020.",
            "lab_results": "HbA1c 7.2% (Oct 2023). Lipid panel shows elevated LDL.",
            "doctor_notes": "Patient advised on diet and exercise. Continue current medication.",
            "adverse_reactions": "Mild GI upset initially with Metformin, now resolved."
        }
    }

@router.delete("/demo/reset/{patient_uid}", tags=["Demo"])
def demo_reset_patient(patient_uid: str, db: Session = Depends(get_db)):
    """Delete a patient + their audit trail — useful for live demo resets."""
    logs = db.query(AuditLog).filter(AuditLog.patient_uid == patient_uid).all()
    for log in logs:
        db.delete(log)
    patient = db.query(Patient).filter(Patient.patient_uid == patient_uid).first()
    if patient:
        db.delete(patient)
    db.commit()
    return {"message": f"Demo reset complete for {patient_uid}"}
