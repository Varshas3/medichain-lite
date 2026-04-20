# app/services/access_control.py
# ─────────────────────────────────────────────────────────────
# Tiered Access Control + Credential Verification
#
# TIER MODEL
# ──────────
#  Tier 0 → No credential needed  → sees: name, blood group, allergies, emergency contact
#  Tier 1 → ASHA / Paramedic      → sees: + chronic conditions, current medications (names only)
#  Tier 2 → Pharmacist            → sees: + full prescriptions, dosages, refill history
#  Tier 3 → Doctor (NMC)          → sees: + complete history, lab results, doctor notes
# ─────────────────────────────────────────────────────────────

import bcrypt
from sqlalchemy.orm import Session
from app.models.db_models import Provider
from app.services.encryption import decrypt_up_to_tier


# ── Role → default tier mapping ───────────────────────────────
ROLE_TIER_MAP = {
    "asha":        1,
    "paramedic":   1,
    "pharmacist":  2,
    "doctor":      3,
    "specialist":  3,
    "admin":       3,
}


# ── Credential verification ───────────────────────────────────

def verify_provider(provider_id: str, license_key: str, db: Session) -> Provider | None:
    """
    Look up provider_id in the DB and verify their license key via bcrypt.
    Returns the Provider ORM object on success, None on failure.
    """
    provider = db.query(Provider).filter(
        Provider.provider_id == provider_id,
        Provider.is_active   == True
    ).first()

    if not provider:
        return None

    # bcrypt comparison (constant-time, safe against timing attacks)
    key_matches = bcrypt.checkpw(
        license_key.encode("utf-8"),
        provider.license_hash.encode("utf-8")
    )
    return provider if key_matches else None


def hash_license_key(raw_key: str) -> str:
    """Hash a provider's license key with bcrypt for safe storage."""
    return bcrypt.hashpw(raw_key.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


# ── Tiered data access ────────────────────────────────────────

def access_patient_data(qr_payload: dict, provider: Provider) -> dict:
    """
    Given a decoded QR payload and a verified provider,
    return only the data that the provider's tier permits.

    Args:
        qr_payload: dict with keys tier0..tier3 (encrypted blobs)
        provider:   verified Provider ORM object

    Returns:
        {
            "patient_uid": ...,
            "tier_accessed": 2,
            "data": { "tier0": {...}, "tier1": {...}, "tier2": {...} }
        }
    """
    max_tier = provider.tier_level
    decrypted = decrypt_up_to_tier(qr_payload, max_tier)

    return {
        "patient_uid":  qr_payload["patient_uid"],
        "tier_accessed": max_tier,
        "provider_role": provider.role,
        "data":          decrypted,
    }


# ── What each tier can SEE (display schema for frontend) ──────

TIER_FIELD_SCOPE = {
    0: ["name", "blood_group", "allergies", "emergency_contact"],
    1: ["chronic_conditions", "current_medications"],
    2: ["prescriptions", "dosages", "refill_history", "last_dispensed"],
    3: ["full_history", "lab_results", "doctor_notes", "adverse_reactions"],
}


def describe_tier_access(tier: int) -> dict:
    """Return a human-readable summary of what a given tier can access."""
    fields = []
    for t in range(tier + 1):
        fields.extend(TIER_FIELD_SCOPE.get(t, []))
    return {
        "tier": tier,
        "accessible_fields": fields,
        "description": _tier_description(tier),
    }


def _tier_description(tier: int) -> str:
    descriptions = {
        0: "Emergency responder — name, blood group, allergies, emergency contact only.",
        1: "ASHA worker / Paramedic — adds chronic conditions and current medication names.",
        2: "Pharmacist — adds full prescriptions, dosages, and refill history.",
        3: "Doctor — full medical history, lab results, and clinical notes.",
    }
    return descriptions.get(tier, "Unknown tier.")