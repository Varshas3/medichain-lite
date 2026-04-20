# scripts/seed_db.py
# ─────────────────────────────────────────────────────────────
# Seeds the SQLite database with:
#   1. Drug interaction pairs (based on NLEM 2022 / WHO data)
#   2. Sample healthcare providers for testing
# Run once:  python scripts/seed_db.py
# ─────────────────────────────────────────────────────────────

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.utils.database import init_db, SessionLocal
from app.models.db_models import DrugInteraction, Provider
from app.services.access_control import hash_license_key

# ── Drug interaction pairs ────────────────────────────────────
DRUG_INTERACTIONS = [
    # CRITICAL
    ("warfarin",    "aspirin",        "critical",
     "Both inhibit platelet function / clotting cascade; combined use dramatically increases bleeding risk.",
     "Do NOT co-dispense. Consult prescribing doctor immediately.", "WHO 2023"),
    ("warfarin",    "ibuprofen",      "critical",
     "NSAIDs inhibit platelet aggregation and displace warfarin from plasma proteins, potentiating anticoagulation.",
     "Do NOT dispense. Refer patient to physician.", "NLEM 2022"),
    ("methotrexate","ibuprofen",      "critical",
     "NSAIDs reduce renal clearance of methotrexate causing toxic accumulation.",
     "Do NOT co-dispense. Risk of severe methotrexate toxicity.", "WHO 2023"),
    ("ssri",        "tramadol",       "critical",
     "Combined serotonergic activity can precipitate serotonin syndrome.",
     "Do NOT co-dispense. Seek alternative analgesic.", "WHO 2023"),
    ("digoxin",     "amiodarone",     "critical",
     "Amiodarone inhibits P-glycoprotein, markedly increasing digoxin plasma levels.",
     "Do NOT co-dispense without cardiology review and digoxin dose adjustment.", "NLEM 2022"),
    ("sildenafil",  "nitrates",       "critical",
     "Both cause vasodilation; combined effect can cause life-threatening hypotension.",
     "Absolute contraindication. Do NOT dispense together.", "NLEM 2022"),

    # MAJOR
    ("metformin",   "alcohol",        "major",
     "Alcohol potentiates lactic acidosis risk with metformin.",
     "Counsel patient to avoid alcohol. Monitor renal function.", "NLEM 2022"),
    ("ciprofloxacin","antacids",      "major",
     "Antacids chelate ciprofloxacin reducing absorption by up to 90%.",
     "Separate doses by at least 2 hours.", "NLEM 2022"),
    ("atorvastatin", "clarithromycin","major",
     "Clarithromycin inhibits CYP3A4, significantly raising atorvastatin levels and myopathy risk.",
     "Temporarily suspend atorvastatin during antibiotic course.", "WHO 2023"),
    ("lithium",      "ibuprofen",     "major",
     "NSAIDs reduce renal lithium clearance; plasma levels can rise to toxic range.",
     "Avoid. Use paracetamol as alternative if analgesia needed.", "WHO 2023"),
    ("clopidogrel",  "omeprazole",    "major",
     "Omeprazole inhibits CYP2C19 reducing conversion of clopidogrel to active metabolite.",
     "Switch to pantoprazole if PPI therapy is required.", "NLEM 2022"),
    ("amlodipine",   "simvastatin",   "major",
     "Amlodipine inhibits CYP3A4 raising simvastatin AUC; increased myopathy risk.",
     "Do not exceed simvastatin 20mg/day. Consider alternative statin.", "NLEM 2022"),

    # MODERATE
    ("metformin",    "contrast dye",  "moderate",
     "Iodinated contrast media can transiently impair renal function causing metformin accumulation.",
     "Hold metformin 48h before and after contrast procedure.", "NLEM 2022"),
    ("amlodipine",   "grapefruit",    "moderate",
     "Grapefruit inhibits intestinal CYP3A4 increasing amlodipine bioavailability.",
     "Advise patient to avoid grapefruit juice.", "WHO 2023"),
    ("paracetamol",  "alcohol",       "moderate",
     "Chronic alcohol use induces CYP2E1, increasing hepatotoxic metabolite of paracetamol.",
     "Limit paracetamol to <2g/day in patients with regular alcohol use.", "NLEM 2022"),
    ("tetracycline", "milk",          "moderate",
     "Calcium in dairy chelates tetracycline, reducing absorption.",
     "Take tetracycline 1 hour before or 2 hours after dairy products.", "NLEM 2022"),
    ("levothyroxine","iron",          "moderate",
     "Iron reduces absorption of levothyroxine.",
     "Separate doses by at least 4 hours.", "NLEM 2022"),

    # MINOR
    ("cetirizine",   "alcohol",       "minor",
     "Additive CNS depression possible.",
     "Counsel patient on drowsiness risk. Generally safe.", "NLEM 2022"),
    ("metronidazole","milk",          "minor",
     "Dairy can slightly reduce metronidazole peak plasma levels.",
     "Take on empty stomach where possible. Clinically minor.", "NLEM 2022"),
]

# ── Sample providers for testing ──────────────────────────────
SAMPLE_PROVIDERS = [
    {"provider_id": "DOC-KA-00001", "name": "Dr. Ananya Sharma",   "role": "doctor",      "tier_level": 3, "license_key": "DOCTOR_KEY_001"},
    {"provider_id": "PHR-KA-00001", "name": "Rajan Pillai",        "role": "pharmacist",  "tier_level": 2, "license_key": "PHARMA_KEY_001"},
    {"provider_id": "ASH-KA-00001", "name": "Meena Devi",          "role": "asha",        "tier_level": 1, "license_key": "ASHA_KEY_00001"},
]


def seed():
    init_db()
    db = SessionLocal()

    # Seed drug interactions
    existing_count = db.query(DrugInteraction).count()
    if existing_count == 0:
        for drug_a, drug_b, severity, mechanism, recommendation, source in DRUG_INTERACTIONS:
            db.add(DrugInteraction(
                drug_a         = drug_a.lower(),
                drug_b         = drug_b.lower(),
                severity       = severity,
                mechanism      = mechanism,
                recommendation = recommendation,
                source         = source,
            ))
        db.commit()
        print(f"[SEED] {len(DRUG_INTERACTIONS)} drug interactions inserted.")
    else:
        print(f"[SEED] Drug interactions already seeded ({existing_count} rows). Skipping.")

    # Seed providers
    for p in SAMPLE_PROVIDERS:
        exists = db.query(Provider).filter(Provider.provider_id == p["provider_id"]).first()
        if not exists:
            db.add(Provider(
                provider_id  = p["provider_id"],
                name         = p["name"],
                role         = p["role"],
                tier_level   = p["tier_level"],
                license_hash = hash_license_key(p["license_key"]),
            ))
    db.commit()
    print(f"[SEED] {len(SAMPLE_PROVIDERS)} sample providers seeded.")
    print("\n[SEED] Test credentials:")
    for p in SAMPLE_PROVIDERS:
        print(f"  {p['role']:12} | id={p['provider_id']} | key={p['license_key']}")

    db.close()


if __name__ == "__main__":
    seed()