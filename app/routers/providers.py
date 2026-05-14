from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.utils.database import get_db
from app.models.db_models import Provider
from app.services.access_control import hash_license_key

router = APIRouter()

class ProviderRegisterRequest(BaseModel):
    provider_id: str
    name:        str
    role:        str
    tier_level:  int
    license_key: str

@router.post("/providers/register", tags=["Providers"])
def register_provider(body: ProviderRegisterRequest, db: Session = Depends(get_db)):
    if db.query(Provider).filter(Provider.provider_id == body.provider_id).first():
        raise HTTPException(400, f"Provider {body.provider_id} already registered.")
    db.add(Provider(
        provider_id  = body.provider_id,
        name         = body.name,
        role         = body.role,
        tier_level   = body.tier_level,
        license_hash = hash_license_key(body.license_key),
    ))
    db.commit()
    return {"message": "Provider registered.", "provider_id": body.provider_id}
