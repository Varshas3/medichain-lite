import React, { useState, useEffect } from 'react';
import { ScanLine, Unlock, Lock, AlertCircle, RefreshCcw } from 'lucide-react';
import { useApi } from '../hooks/useApi';
import Spinner from '../components/Spinner';

const PROVIDERS = [
  { id: 'DOC-KA-00001', role: 'Doctor', key: 'DOCTOR_KEY_001', tier: 3 },
  { id: 'PHR-KA-00001', role: 'Pharmacist', key: 'PHARMA_KEY_001', tier: 2 },
  { id: 'ASH-KA-00001', role: 'ASHA Worker', key: 'ASHA_KEY_00001', tier: 1 }
];

export default function ScanScreen({ qrPayload, scanResult, setScanResult, triggerConsent, showToast }) {
  const [selectedProvider, setSelectedProvider] = useState(PROVIDERS[0]);
  const [licenseKey, setLicenseKey] = useState(PROVIDERS[0].key);
  const [payloadInput, setPayloadInput] = useState('');
  const [loading, setLoading] = useState(false);
  
  const api = useApi();

  useEffect(() => {
    if (qrPayload) {
      setPayloadInput(JSON.stringify(qrPayload, null, 2));
    }
  }, [qrPayload]);

  const handleProviderChange = (e) => {
    const p = PROVIDERS.find(p => p.id === e.target.value);
    setSelectedProvider(p);
    setLicenseKey(p.key);
  };

  const humanize = (str) => {
    return str.split('_').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ');
  };

  const performScan = async () => {
    if (!payloadInput) return showToast("No QR payload to scan", 'error');
    setLoading(true);
    setScanResult(null);

    try {
      const res = await api.scanQR({
        qr_raw_json: payloadInput,
        provider_id: selectedProvider.id,
        license_key: licenseKey
      });
      
      setScanResult(res);
      showToast("Decryption successful", 'success');
      
    } catch (err) {
      if (err.detail && err.detail.error === "consent_required") {
        // Trigger OTP Modal
        triggerConsent({
          patient_uid: err.detail.patient_uid,
          provider_id: err.detail.provider_id,
          phone_number: "+919876543210", // Mocked for demo
          onComplete: () => performScan() // Retry automatically
        });
      } else {
        showToast(err.detail || "Scan failed", 'error');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="animate-fadeIn">
      <div style={{ background: '#e0e7ff', color: '#4338ca', padding: '12px 16px', borderRadius: 8, fontSize: '0.875rem', display: 'flex', alignItems: 'center', gap: 8, marginBottom: 16 }}>
        <ScanLine size={18} /> Simulating provider scan device
      </div>

      <div className="card">
        <h3>Provider Authentication</h3>
        <label>Select Role</label>
        <select value={selectedProvider.id} onChange={handleProviderChange}>
          {PROVIDERS.map(p => <option key={p.id} value={p.id}>🩺 {p.role} ({p.id})</option>)}
        </select>
        
        <label>License Key</label>
        <input value={licenseKey} onChange={e => setLicenseKey(e.target.value)} />
      </div>

      <div className="card">
        <h3>Scanned QR Data</h3>
        <textarea 
          style={{ width: '100%', height: 120, fontFamily: 'monospace', fontSize: '0.75rem', padding: 8, borderRadius: 8, border: '1px solid var(--border)', resize: 'none', marginBottom: 12 }}
          value={payloadInput}
          onChange={e => setPayloadInput(e.target.value)}
          placeholder='{"v":1,"uid":"..."}'
        />
        <button className="btn btn-primary" onClick={performScan} disabled={loading || !payloadInput}>
          {loading ? <Spinner size={20} /> : <><Unlock size={18} /> Scan & Decrypt</>}
        </button>
      </div>

      {scanResult && (
        <div className="animate-fadeIn">
          <div style={{ textAlign: 'center', margin: '24px 0' }}>
            <Unlock size={48} color="var(--success)" style={{ animation: 'pulseOnce 0.5s ease', marginBottom: 8, margin: '0 auto' }} />
            <h3 style={{ color: 'var(--success)' }}>Access Granted — Tier {scanResult.tier_accessed}</h3>
            <p className="text-muted text-sm">{scanResult.provider_role.toUpperCase()}</p>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
            {[0, 1, 2, 3].map(t => {
              const data = scanResult.data[`tier${t}`];
              if (!data) return null;
              return (
                <div key={t} className="card" style={{ borderLeft: `4px solid var(--tier${t})`, padding: 12 }}>
                  <h4 style={{ marginBottom: 8, color: `var(--tier${t})` }}>Tier {t} Data</h4>
                  <table style={{ width: '100%', fontSize: '0.875rem' }}>
                    <tbody>
                      {Object.entries(data).map(([key, val]) => (
                        <tr key={key}>
                          <td style={{ color: 'var(--text-muted)', paddingBottom: 4, width: '40%' }}>{humanize(key)}</td>
                          <td style={{ fontWeight: 500, paddingBottom: 4 }}>
                            {Array.isArray(val) ? val.join(', ') || 'None' : (val || 'N/A')}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              );
            })}
          </div>

          {scanResult.tier_accessed < 3 && (
            <div style={{ background: '#fef2f2', color: 'var(--danger)', padding: '12px', borderRadius: 8, display: 'flex', gap: 8, marginTop: 16, fontSize: '0.875rem' }}>
              <Lock size={18} /> Tiers above {scanResult.tier_accessed} remain AES-encrypted.
            </div>
          )}
        </div>
      )}
    </div>
  );
}
