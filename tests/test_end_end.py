import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.utils.database import init_db, SessionLocal
from app.services.encryption import encrypt_tier, decrypt_tier, build_encrypted_payload, decrypt_up_to_tier
from app.services.qr_service import generate_qr, decode_qr_payload
from app.services.access_control import verify_provider, describe_tier_access
from app.services.drug_interaction import check_interactions, check_full_list
from app.services.audit import log_event, get_audit_trail, verify_audit_chain
from scripts.seed_db import seed

PASS = "✅ PASS"
FAIL = "❌ FAIL"

def test_encryption():
    print("\n── TEST: AES Encryption / Decryption ─────────────────")
    sample = {"name": "Priya Menon", "blood_group": "O+", "allergies": ["penicillin"]}
    for tier in range(4):
        blob      = encrypt_tier(sample, tier)
        recovered = decrypt_tier(blob, tier)
        print(f"  Tier {tier}: {PASS if recovered == sample else FAIL}")
    blob = encrypt_tier(sample, tier=2)
    try:
        decrypt_tier(blob, tier=3)
        print(f"  Wrong-key test: {FAIL} (should have raised)")
    except ValueError:
        print(f"  Wrong-key raises ValueError: {PASS}")

def test_qr_generation():
    print("\n── TEST: QR Code Generation & Decode ─────────────────")
    patient_data = {
        "patient_uid": "PAT-TEST-001",
        "tier0": {"name": "Priya Menon", "blood_group": "O+", "allergies": ["penicillin"], "emergency_contact": "9876543210"},
        "tier1": {"chronic_conditions": ["Hypertension"], "current_medications": ["amlodipine"]},
        "tier2": {"prescriptions": [{"drug": "amlodipine", "dose": "5mg", "frequency": "OD"}], "refill_history": []},
        "tier3": {"full_history": ["BP diagnosed 2020"], "lab_results": [], "doctor_notes": ""},
    }
    path = generate_qr(patient_data)
    print(f"  QR generated at {path}: {PASS if os.path.exists(path) else FAIL}")
    payload = build_encrypted_payload(patient_data)
    qr_json = json.dumps({"v":1,"uid":payload["patient_uid"],"t0":payload["tier0"],
                           "t1":payload["tier1"],"t2":payload["tier2"],"t3":payload["tier3"]}, separators=(",",":"))
    decoded = decode_qr_payload(qr_json)
    print(f"  QR decode preserves uid: {PASS if decoded['patient_uid']=='PAT-TEST-001' else FAIL}")

def test_access_control():
    print("\n── TEST: Tiered Access Control ────────────────────────")
    db = SessionLocal()
    provider = verify_provider("DOC-KA-00001", "DOCTOR_KEY_001", db)
    print(f"  Doctor credential verify: {PASS if provider and provider.tier_level==3 else FAIL}")
    provider = verify_provider("PHR-KA-00001", "PHARMA_KEY_001", db)
    print(f"  Pharmacist credential verify: {PASS if provider and provider.tier_level==2 else FAIL}")
    provider = verify_provider("DOC-KA-00001", "WRONG_KEY", db)
    print(f"  Wrong key rejected: {PASS if provider is None else FAIL}")
    info = describe_tier_access(2)
    print(f"  Tier 2 scope has prescriptions: {PASS if 'prescriptions' in info['accessible_fields'] else FAIL}")
    db.close()

def test_drug_interactions():
    print("\n── TEST: Drug Interaction Engine ──────────────────────")
    db = SessionLocal()
    result = check_interactions("warfarin", ["aspirin", "metformin"], db)
    print(f"  Warfarin+Aspirin → critical alert: {PASS if result['interactions_found'] > 0 and not result['safe_to_dispense'] else FAIL}")
    result = check_interactions("paracetamol", ["metformin"], db)
    print(f"  Paracetamol+Metformin → safe: {PASS if result['safe_to_dispense'] and result['interactions_found']==0 else FAIL}")
    result = check_interactions("Warfarin", ["Aspirin"], db)
    print(f"  Case-insensitive match: {PASS if result['interactions_found'] > 0 else FAIL}")
    result = check_full_list(["warfarin", "aspirin", "metformin", "ibuprofen"], db)
    print(f"  Full regimen check finds >=2 interactions: {PASS if result['total_interactions']>=2 else FAIL}")
    db.close()

def test_audit_trail():
    print("\n── TEST: Tamper-Evident Audit Trail ───────────────────")
    db  = SessionLocal()
    uid = "PAT-AUDIT-TEST"
    for action in ["scan", "interaction_check", "prescribe"]:
        log_event(db, uid, "DOC-KA-00001", action, tier_accessed=3, details={"test": True})
    trail = get_audit_trail(uid, db)
    print(f"  3 entries logged: {PASS if len(trail)==3 else FAIL}")
    report = verify_audit_chain(uid, db)
    print(f"  Chain intact: {PASS if report['status']=='intact' else FAIL}")
    db.close()

if __name__ == "__main__":
    print("=" * 55)
    print("  MediChain Lite — End-to-End Test Suite")
    print("=" * 55)
    init_db()
    seed()
    test_encryption()
    test_qr_generation()
    test_access_control()
    test_drug_interactions()
    test_audit_trail()
    print("\n" + "=" * 55)
    print("  All tests complete.")
    print("=" * 55)