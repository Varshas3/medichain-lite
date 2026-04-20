# app/services/drug_interaction.py
# ─────────────────────────────────────────────────────────────
# Offline Drug Interaction Checking Engine
#
# Checks a new drug against a patient's existing medication list.
# All lookups hit the local SQLite DB — no internet required.
#
# Severity levels (descending danger):
#   critical  → Do NOT dispense. Alert immediately.
#   major     → Avoid combination. Consult doctor.
#   moderate  → Use with caution. Monitor patient.
#   minor     → Noted. Generally safe to dispense.
# ─────────────────────────────────────────────────────────────

from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
from app.models.db_models import DrugInteraction
from typing import Optional


SEVERITY_ORDER = {"critical": 4, "major": 3, "moderate": 2, "minor": 1}
SEVERITY_COLORS = {
    "critical": "🔴",
    "major":    "🟠",
    "moderate": "🟡",
    "minor":    "🟢",
}


def _normalise(drug_name: str) -> str:
    """Lowercase and strip whitespace for consistent matching."""
    return drug_name.strip().lower()


def check_interactions(
    new_drug: str,
    existing_medications: list[str],
    db: Session,
    min_severity: Optional[str] = None
) -> dict:
    """
    Check if new_drug interacts with any drug in existing_medications.

    Args:
        new_drug:             Name of the drug being newly prescribed/dispensed.
        existing_medications: List of drugs the patient is currently on.
        db:                   Active SQLAlchemy session.
        min_severity:         Optional filter — only return alerts at/above this level.
                              e.g. "moderate" will suppress "minor" alerts.

    Returns:
        {
            "new_drug": "warfarin",
            "interactions_found": 2,
            "alerts": [
                {
                    "drug_a": "warfarin",
                    "drug_b": "aspirin",
                    "severity": "major",
                    "severity_icon": "🟠",
                    "mechanism": "...",
                    "recommendation": "..."
                },
                ...
            ],
            "safe_to_dispense": False   ← False if any critical alert exists
        }
    """
    normalised_new   = _normalise(new_drug)
    normalised_exist = [_normalise(m) for m in existing_medications]

    alerts = []
    for existing in normalised_exist:
        # Query: find rows where (drug_a=new AND drug_b=existing) OR (drug_a=existing AND drug_b=new)
        rows = db.query(DrugInteraction).filter(
            or_(
                and_(DrugInteraction.drug_a == normalised_new,
                     DrugInteraction.drug_b == existing),
                and_(DrugInteraction.drug_a == existing,
                     DrugInteraction.drug_b == normalised_new),
            )
        ).all()

        for row in rows:
            # Apply minimum severity filter
            if min_severity and SEVERITY_ORDER.get(row.severity, 0) < SEVERITY_ORDER.get(min_severity, 0):
                continue
            alerts.append({
                "drug_a":         row.drug_a,
                "drug_b":         row.drug_b,
                "severity":       row.severity,
                "severity_icon":  SEVERITY_COLORS.get(row.severity, "⚪"),
                "mechanism":      row.mechanism,
                "recommendation": row.recommendation,
                "source":         row.source,
            })

    # Sort by severity descending so critical shows first
    alerts.sort(key=lambda a: SEVERITY_ORDER.get(a["severity"], 0), reverse=True)

    has_critical     = any(a["severity"] == "critical" for a in alerts)
    safe_to_dispense = not has_critical

    return {
        "new_drug":           new_drug,
        "checked_against":    existing_medications,
        "interactions_found": len(alerts),
        "safe_to_dispense":   safe_to_dispense,
        "alerts":             alerts,
    }


def check_full_list(medications: list[str], db: Session) -> dict:
    """
    Check all pairwise interactions within a medication list.
    Useful when reviewing a patient's entire current regimen.
    """
    all_alerts = []
    seen_pairs = set()

    for i, drug in enumerate(medications):
        others = medications[:i] + medications[i+1:]
        result = check_interactions(drug, others, db)
        for alert in result["alerts"]:
            pair = tuple(sorted([alert["drug_a"], alert["drug_b"]]))
            if pair not in seen_pairs:
                seen_pairs.add(pair)
                all_alerts.append(alert)

    all_alerts.sort(key=lambda a: SEVERITY_ORDER.get(a["severity"], 0), reverse=True)
    has_critical = any(a["severity"] == "critical" for a in all_alerts)

    return {
        "medications_checked": medications,
        "total_interactions":  len(all_alerts),
        "safe_regimen":        not has_critical,
        "alerts":              all_alerts,
    }