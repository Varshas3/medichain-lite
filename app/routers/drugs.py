from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

from app.utils.database import get_db
from app.services.drug_interaction import check_interactions, check_full_list
from app.services.audit import log_event

router = APIRouter()

class DrugCheckRequest(BaseModel):
    new_drug:             str
    existing_medications: list[str]
    provider_id:          str
    patient_uid:          Optional[str] = None

class FullRegimenCheckRequest(BaseModel):
    medications: list[str]

@router.post("/drugs/check", tags=["Drug Interactions"])
def drug_interaction_check(body: DrugCheckRequest, db: Session = Depends(get_db)):
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
    return check_full_list(body.medications, db)
