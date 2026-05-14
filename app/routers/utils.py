from fastapi import APIRouter, HTTPException

from app.services.access_control import describe_tier_access

router = APIRouter()

@router.get("/tiers/{tier_level}", tags=["Utility"])
def tier_info(tier_level: int):
    if tier_level not in range(4):
        raise HTTPException(400, "Tier must be 0, 1, 2, or 3.")
    return describe_tier_access(tier_level)

@router.get("/health", tags=["Utility"])
def health_check():
    return {"status": "ok", "system": "MediChain Lite"}
