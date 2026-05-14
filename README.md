# MediChain

A role-based encrypted QR health system for offline patient records. 
Privacy is enforced at the cryptographic layer using AES-256-CBC encryption.

## 🚀 One-Command Demo Setup

Run this single command from the `frontend` folder to start both the Python backend and the React frontend simultaneously:

```bash
cd frontend
npm run demo
```

## 🔒 Tiered Encryption System

| Tier | Role / Provider | Data Accessible | Security / Encryption |
|------|-----------------|-----------------|------------------------|
| **0** | **Public** | Demographics, Blood Group, Allergies | Plain JSON inside QR |
| **1** | **ASHA Worker** | Tier 0 + Diagnoses, Current Meds | AES Encrypted (Tier 1 Key) |
| **2** | **Pharmacist** | Tier 1 + Prescriptions, Refills | AES Encrypted (Tier 2 Key) |
| **3** | **Doctor** | Tier 2 + Full History, Notes | AES Encrypted (Tier 3 Key) |

## 🔑 Offline Demo Credentials

If the backend database is empty, you can use these offline fallback credentials in the provider login/scan simulation:

| Role | License ID | License Key |
|------|------------|-------------|
| **Doctor** | `DOC-KA-00001` | `DOCTOR_KEY_001` |
| **Pharmacist** | `PHR-KA-00001` | `PHARMA_KEY_001` |
| **ASHA Worker** | `ASH-KA-00001` | `ASHA_KEY_00001` |

## 📱 Tier 3 OTP Consent Flow

1. The Doctor scans the QR code and requests Tier 3 decryption.
2. The payload is sent to the backend. The backend recognizes the Tier 3 request and checks the active `ConsentSession` table.
3. If no active consent is found, the backend returns a `403 consent_required` error.
4. The frontend intercepts this, triggering the OTP Consent Modal.
5. An OTP is sent (simulated in demo) to the patient.
6. Once the 6-digit OTP is verified, the session is marked approved, and the frontend automatically retries the scan.

## 📱 PWA Support

MediChain is built as a Progressive Web App (PWA).
- **Service Workers**: NetworkFirst for API calls, CacheFirst for static assets.
- **Installable**: The app can be added to the home screen of any mobile device, enabling it to act like a native app.
- **Offline Capable**: Provider QR scans and tier decryption workflows continue to function even without cell service (when using the cached PWA shell).

## 📸 Screenshots

*(Replace with actual screenshots of your hackathon project)*
- [Registration Flow Screenshot]
- [Dashboard View Screenshot]
- [QR Code Screen Screenshot]
- [Scan & Decrypt Screen Screenshot]
