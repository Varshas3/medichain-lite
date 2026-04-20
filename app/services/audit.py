# app/services/audit.py
# ─────────────────────────────────────────────────────────────
# Tamper-Evident Audit Trail
#
# Every access / prescription / QR update is logged here.
# Rows are INSERT-ONLY — never updated or deleted.
# A chain hash links each entry to the previous one,
# making silent tampering detectable.
# ─────────────────────────────────────────────────────────────

import json
import hashlib
from datetime import datetime
from sqlalchemy.orm import Session
from app.models.db_models import AuditLog


# ── Log an event ──────────────────────────────────────────────

def log_event(
    db:           Session,
    patient_uid:  str,
    provider_id:  str,
    action:       str,      # "scan" | "prescribe" | "update_qr" | "interaction_check"
    tier_accessed: int,
    details:      dict  = None,
    ip_address:   str   = None,
) -> AuditLog:
    """
    Write one audit row.  Computes a chain_hash over:
        previous_hash + patient_uid + provider_id + action + timestamp
    so any deletion or row reordering breaks the chain.
    """
    details_json = json.dumps(details or {})
    timestamp    = datetime.utcnow()

    # Fetch previous hash in the chain for this patient
    prev = (
        db.query(AuditLog)
        .filter(AuditLog.patient_uid == patient_uid)
        .order_by(AuditLog.id.desc())
        .first()
    )
    prev_hash = _row_hash(prev) if prev else "GENESIS"

    # Compute this entry's hash
    raw = f"{prev_hash}|{patient_uid}|{provider_id}|{action}|{timestamp.isoformat()}"
    chain_hash = hashlib.sha256(raw.encode()).hexdigest()

    # Inject hash into details so it's stored alongside the record
    details_with_hash = {**(details or {}), "_chain_hash": chain_hash}

    entry = AuditLog(
        patient_uid   = patient_uid,
        provider_id   = provider_id,
        action        = action,
        tier_accessed = tier_accessed,
        details       = json.dumps(details_with_hash),
        timestamp     = timestamp,
        ip_address    = ip_address,
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    print(f"[AUDIT] {action} | patient={patient_uid} | provider={provider_id} | tier={tier_accessed}")
    return entry


# ── Retrieve audit trail ──────────────────────────────────────

def get_audit_trail(patient_uid: str, db: Session) -> list[dict]:
    """Return the full audit trail for a patient (chronological)."""
    logs = (
        db.query(AuditLog)
        .filter(AuditLog.patient_uid == patient_uid)
        .order_by(AuditLog.timestamp.asc())
        .all()
    )
    return [_log_to_dict(log) for log in logs]


def verify_audit_chain(patient_uid: str, db: Session) -> dict:
    """
    Walk the audit chain and verify integrity.
    Returns a report indicating whether the chain is intact.
    """
    logs = (
        db.query(AuditLog)
        .filter(AuditLog.patient_uid == patient_uid)
        .order_by(AuditLog.id.asc())
        .all()
    )

    if not logs:
        return {"status": "empty", "message": "No audit entries found.", "broken_at": None}

    prev_hash = "GENESIS"
    for i, log in enumerate(logs):
        details_dict = json.loads(log.details or "{}")
        stored_hash  = details_dict.get("_chain_hash", "")

        raw      = f"{prev_hash}|{log.patient_uid}|{log.provider_id}|{log.action}|{log.timestamp.isoformat()}"
        expected = hashlib.sha256(raw.encode()).hexdigest()

        if stored_hash != expected:
            return {
                "status":     "TAMPERED",
                "message":    f"Chain broken at entry #{i+1} (id={log.id})",
                "broken_at":  log.id,
            }
        prev_hash = stored_hash

    return {
        "status":    "intact",
        "message":   f"All {len(logs)} entries verified.",
        "broken_at": None,
    }


# ── Helpers ───────────────────────────────────────────────────

def _row_hash(log: AuditLog) -> str:
    """Extract stored chain_hash from a log row's details JSON."""
    try:
        return json.loads(log.details).get("_chain_hash", "")
    except Exception:
        return ""


def _log_to_dict(log: AuditLog) -> dict:
    return {
        "id":           log.id,
        "patient_uid":  log.patient_uid,
        "provider_id":  log.provider_id,
        "action":       log.action,
        "tier_accessed": log.tier_accessed,
        "details":      json.loads(log.details or "{}"),
        "timestamp":    log.timestamp.isoformat(),
        "ip_address":   log.ip_address,
    }