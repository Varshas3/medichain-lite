export const MOCK_PATIENT = {
  patient_uid: "PAT-KA-8899",
  name: "Priya Sharma",
  age: 45,
  blood_group: "B+",
  phone: "+919876543210",
  tier0: {
      name: "Priya Sharma",
      blood_group: "B+",
      allergies: ["Penicillin"],
      emergency_contact: "+919988776655"
  },
  tier1: {
      chronic_conditions: ["Type 2 Diabetes", "Hypertension", "Dyslipidemia"],
      current_medications: ["Metformin", "Amlodipine", "Atorvastatin"]
  },
  tier2: {
      prescriptions: [
          {"drug": "Metformin", "dosage": "500mg OD"},
          {"drug": "Amlodipine", "dosage": "5mg OD"},
          {"drug": "Atorvastatin", "dosage": "10mg HS"}
      ],
      refill_history: ["2023-09-01", "2023-10-01"],
      last_dispensed: "2023-10-01"
  },
  tier3: {
      full_history: "Diagnosed with T2DM in 2018. Hypertension noted in 2020.",
      lab_results: "HbA1c 7.2% (Oct 2023). Lipid panel shows elevated LDL.",
      doctor_notes: "Patient advised on diet and exercise. Continue current medication.",
      adverse_reactions: "Mild GI upset initially with Metformin, now resolved."
  }
};

export const MOCK_QR_PAYLOAD = {
  "v": 1,
  "uid": "PAT-KA-8899",
  "t0": "base64_demo_t0_payload_xyz==",
  "t1": "base64_demo_t1_payload_xyz==",
  "t2": "base64_demo_t2_payload_xyz==",
  "t3": "base64_demo_t3_payload_xyz=="
};

export const MOCK_SCAN_RESULT_DOCTOR = {
  patient_uid: "PAT-KA-8899",
  tier_accessed: 3,
  provider_role: "doctor",
  data: {
    tier0: MOCK_PATIENT.tier0,
    tier1: MOCK_PATIENT.tier1,
    tier2: MOCK_PATIENT.tier2,
    tier3: MOCK_PATIENT.tier3
  }
};

export const MOCK_SCAN_RESULT_PHARMACIST = {
  patient_uid: "PAT-KA-8899",
  tier_accessed: 2,
  provider_role: "pharmacist",
  data: {
    tier0: MOCK_PATIENT.tier0,
    tier1: MOCK_PATIENT.tier1,
    tier2: MOCK_PATIENT.tier2
  }
};

export const MOCK_SCAN_RESULT_ASHA = {
  patient_uid: "PAT-KA-8899",
  tier_accessed: 1,
  provider_role: "asha",
  data: {
    tier0: MOCK_PATIENT.tier0,
    tier1: MOCK_PATIENT.tier1
  }
};

export const MOCK_DRUG_RESULT_CRITICAL = {
  safe_to_dispense: false,
  interactions_found: [
    { severity: "critical", mechanism: "Increased risk of severe bleeding." }
  ]
};

export const MOCK_DRUG_RESULT_SAFE = {
  safe_to_dispense: true,
  interactions_found: []
};
