import React, { useEffect, useRef, useState } from 'react';
import QRCode from 'qrcode';
import { RefreshCw, Copy, Printer, WifiOff, Shield } from 'lucide-react';
import TierBadge from '../components/TierBadge';

export default function QRScreen({ patient, qrPayload, onNavigate, showToast }) {
  const canvasRef = useRef(null);
  const [renderCount, setRenderCount] = useState(0);

  const activePatient = patient || { name: 'Guest User', patient_uid: 'PAT-XXXX', blood_group: 'Unknown', tier0: {allergies:[]} };
  
  useEffect(() => {
    if (qrPayload && canvasRef.current) {
      QRCode.toCanvas(canvasRef.current, JSON.stringify(qrPayload), {
        width: 250,
        margin: 2,
        color: { dark: '#0f172a', light: '#ffffff' }
      }, (error) => {
        if (error) console.error(error);
      });
    }
  }, [qrPayload, renderCount]);

  const handleCopy = () => {
    if (!qrPayload) return showToast("No QR data available", "error");
    navigator.clipboard.writeText(JSON.stringify(qrPayload));
    showToast("Payload copied to clipboard", "success");
    onNavigate('scan');
  };

  const handlePrint = () => {
    window.print();
  };

  if (!qrPayload) {
    return (
      <div style={{ textAlign: 'center', marginTop: 40 }}>
        <p className="text-muted">No QR payload generated.</p>
        <button className="btn btn-primary" style={{ marginTop: 16 }} onClick={() => onNavigate('register')}>Go to Registration</button>
      </div>
    );
  }

  return (
    <div className="animate-fadeIn">
      <div className="no-print" style={{ background: '#fef2f2', color: 'var(--danger)', padding: '8px 16px', borderRadius: 8, fontSize: '0.875rem', display: 'flex', alignItems: 'center', gap: 8, marginBottom: 16 }}>
        <WifiOff size={16} /> Data is embedded in QR. Works fully offline.
      </div>

      <div className="card" style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', padding: '24px 16px' }}>
        <h2 style={{ marginBottom: 4 }}>{activePatient.name}</h2>
        <div className="font-mono text-muted" style={{ marginBottom: 16 }}>{activePatient.patient_uid}</div>
        
        <div style={{ background: 'white', padding: 8, borderRadius: 16, border: '2px solid var(--primary)', marginBottom: 16 }}>
          <canvas ref={canvasRef} style={{ display: 'block', borderRadius: 8 }} />
        </div>

        <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', justifyContent: 'center', marginBottom: 12 }}>
          <TierBadge tier={0} />
          <TierBadge tier={1} />
          <TierBadge tier={2} />
          <TierBadge tier={3} />
        </div>

        <div className="text-xs text-muted" style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
          <Shield size={14} /> AES-256-CBC Encrypted
        </div>
      </div>

      <div className="grid-2 no-print" style={{ marginBottom: 16 }}>
        <button className="btn btn-outline text-sm" onClick={() => setRenderCount(c => c + 1)}>
          <RefreshCw size={16} /> Refresh
        </button>
        <button className="btn btn-outline text-sm" onClick={handleCopy}>
          <Copy size={16} /> Copy JSON
        </button>
      </div>
      
      <button className="btn btn-primary no-print" style={{ marginBottom: 24 }} onClick={handlePrint}>
        <Printer size={18} /> Export Health Card
      </button>

      <div className="card no-print">
        <h3 style={{ fontSize: '1rem', marginBottom: 12 }}>Access Control Map</h3>
        <div style={{ fontSize: '0.8rem', display: 'flex', flexDirection: 'column', gap: 8 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid var(--border)', paddingBottom: 4 }}>
            <strong>T0 (Public)</strong> <span className="text-muted">Demographics, Allergies</span>
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid var(--border)', paddingBottom: 4 }}>
            <strong>T1 (ASHA)</strong> <span className="text-muted">+ Current Meds, Diagnoses</span>
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid var(--border)', paddingBottom: 4 }}>
            <strong>T2 (Pharma)</strong> <span className="text-muted">+ Prescriptions, Refills</span>
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between', paddingBottom: 4 }}>
            <strong>T3 (Doctor)</strong> <span className="text-muted">+ Full History (OTP Req)</span>
          </div>
        </div>
      </div>
    </div>
  );
}
