from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
from app.models.db_models import DrugInteraction
from typing import Optional

SEVERITY_ORDER  = {"critical": 4, "major": 3, "moderate": 2, "minor": 1}
SEVERITY_COLORS = {"critical": "🔴", "major": "🟠", "moderate": "🟡", "minor": "🟢"}

def _normalise(drug_name: str) -> str:
    return drug_name.strip().lower()

def check_interactions(new_drug: str, existing_medications: list, db: Session,
                       min_severity: Optional[str] = None) -> dict:
    normalised_new   = _normalise(new_drug)
    normalised_exist = [_normalise(m) for m in existing_medications]
    alerts = []
    for existing in normalised_exist:
        rows = db.query(DrugInteraction).filter(
            or_(
                and_(DrugInteraction.drug_a == normalised_new, DrugInteraction.drug_b == existing),
                and_(DrugInteraction.drug_a == existing,       DrugInteraction.drug_b == normalised_new),
            )
        ).all()
        for row in rows:
            if min_severity and SEVERITY_ORDER.get(row.severity, 0) < SEVERITY_ORDER.get(min_severity, 0):
                continue
            alerts.append({"drug_a": row.drug_a, "drug_b": row.drug_b, "severity": row.severity,
                            "severity_icon": SEVERITY_COLORS.get(row.severity, "⚪"),
                            "mechanism": row.mechanism, "recommendation": row.recommendation,
                            "source": row.source})
    alerts.sort(key=lambda a: SEVERITY_ORDER.get(a["severity"], 0), reverse=True)
    has_critical = any(a["severity"] == "critical" for a in alerts)
    return {"new_drug": new_drug, "checked_against": existing_medications,
            "interactions_found": len(alerts), "safe_to_dispense": not has_critical, "alerts": alerts}

def check_full_list(medications: list, db: Session) -> dict:
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
    return {"medications_checked": medications, "total_interactions": len(all_alerts),
            "safe_regimen": not has_critical, "alerts": all_alerts}