import { 
  MOCK_PATIENT, MOCK_QR_PAYLOAD, 
  MOCK_SCAN_RESULT_DOCTOR, MOCK_SCAN_RESULT_PHARMACIST, MOCK_SCAN_RESULT_ASHA,
  MOCK_DRUG_RESULT_CRITICAL, MOCK_DRUG_RESULT_SAFE 
} from '../mockData';

const API_BASE = "http://localhost:8000/api/v1";

export function useApi() {
  const fetcher = async (endpoint, options = {}, mockFallback = null) => {
    try {
      const res = await fetch(`${API_BASE}${endpoint}`, {
        ...options,
        headers: {
          "Content-Type": "application/json",
          ...options.headers,
        },
      });
      const data = await res.json();
      if (!res.ok) throw data;
      return data;
    } catch (e) {
      // If there's no response from server (offline) or it's a TypeError
      if (!e.status && mockFallback !== undefined) {
        console.log(`[OFFLINE DEMO MODE] Returning mock for ${endpoint}`);
        return mockFallback;
      }
      throw e;
    }
  };

  return {
    health: () => fetcher("/health"),
    getDemoPatient: () => fetcher("/demo/patient", {}, MOCK_PATIENT),
    registerPatient: (body) => fetcher("/patients/register", { method: "POST", body: JSON.stringify(body) }, { qr_payload: MOCK_QR_PAYLOAD }),
    searchPatients: (q) => fetcher(`/patients/search?q=${encodeURIComponent(q)}`, {}, [{ patient_uid: MOCK_PATIENT.patient_uid, name: MOCK_PATIENT.name, blood_group: MOCK_PATIENT.blood_group, audit_count: 5 }]),
    getPatient: (uid) => fetcher(`/patients/${uid}`, {}, MOCK_PATIENT),
    scanQR: (payload) => {
      // Return specific mock based on role
      let mock = MOCK_SCAN_RESULT_DOCTOR;
      if (payload.provider_id.includes('PHR')) mock = MOCK_SCAN_RESULT_PHARMACIST;
      if (payload.provider_id.includes('ASH')) mock = MOCK_SCAN_RESULT_ASHA;
      return fetcher("/qr/scan", { method: "POST", body: JSON.stringify(payload) }, mock);
    },
    checkDrugs: (body) => {
      let mock = MOCK_DRUG_RESULT_SAFE;
      if (body.new_drug.toLowerCase().includes('warfarin')) mock = MOCK_DRUG_RESULT_CRITICAL;
      return fetcher("/drugs/check", { method: "POST", body: JSON.stringify(body) }, mock);
    },
    getAudit: (uid) => fetcher(`/audit/${uid}`, {}, { audit_trail: [] }),
    verifyChain: (uid) => fetcher(`/audit/${uid}/verify`, {}, { is_valid: true, total_logs: 5 }),
    requestConsent: (body) => fetcher("/consent/request", { method: "POST", body: JSON.stringify(body) }, { session_id: "demo-sess", message: "Demo OTP sent", demo_otp: "123456" }),
    verifyOTP: (body) => fetcher("/consent/verify", { method: "POST", body: JSON.stringify(body) }, { approved: body.otp === "123456", message: body.otp === "123456" ? "Approved" : "Invalid OTP" }),
    getConsentStatus: (uid, providerId) => fetcher(`/consent/status/${uid}/${providerId}`, {}, { has_active_consent: false, expires_at: null }),
  };
}
