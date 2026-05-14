import React, { useState, useEffect } from 'react';
import Shell from './components/Shell';
import { ToastProvider, useToast } from './hooks/useToast';
import { useConsent } from './hooks/useConsent';
import OTPModal from './components/OTPModal';
import { HelpCircle, X } from 'lucide-react';

import RegisterScreen from './screens/RegisterScreen';
import DashboardScreen from './screens/DashboardScreen';
import QRScreen from './screens/QRScreen';
import ScanScreen from './screens/ScanScreen';
import ProviderScreen from './screens/ProviderScreen';
import AuditScreen from './screens/AuditScreen';

function HelpModal({ onClose }) {
  const steps = [
    { num: 1, title: 'Register', desc: 'Create a tiered patient record.' },
    { num: 2, title: 'View QR', desc: 'See your encrypted offline QR.' },
    { num: 3, title: 'Scan as ASHA', desc: 'Simulate Tier 1 decryption.' },
    { num: 4, title: 'Scan as Doctor', desc: 'Triggers Tier 3 OTP consent.' },
    { num: 5, title: 'Check Audit', desc: 'Verify the access blockchain.' }
  ];

  return (
    <div className="modal-overlay" style={{ zIndex: 1000 }}>
      <div className="modal-content" style={{ paddingBottom: 40 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
          <h2>Demo Walkthrough</h2>
          <button className="btn-ghost" onClick={onClose} style={{ padding: 4, width: 'auto' }}><X size={24} /></button>
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
          {steps.map(s => (
            <div key={s.num} className="card" style={{ marginBottom: 0, padding: '12px 16px', display: 'flex', alignItems: 'center', gap: 12 }}>
              <div style={{ background: 'var(--primary)', color: 'white', width: 24, height: 24, borderRadius: '50%', display: 'flex', justifyContent: 'center', alignItems: 'center', fontWeight: 'bold' }}>{s.num}</div>
              <div>
                <div style={{ fontWeight: 600 }}>{s.title}</div>
                <div className="text-xs text-muted">{s.desc}</div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

function AppContent() {
  const [currentScreen, setCurrentScreen] = useState('register');
  const [patient, setPatient] = useState(null);
  const [qrPayload, setQrPayload] = useState(null);
  const [scanResult, setScanResult] = useState(null);
  const [auditTrail, setAuditTrail] = useState(null);
  const [showHelp, setShowHelp] = useState(false);

  const { showToast } = useToast();
  const consentParams = useConsent();

  // SW Registration
  useEffect(() => {
    if ('serviceWorker' in navigator) {
      import('virtual:pwa-register').then(({ registerSW }) => {
        registerSW({
          onOfflineReady() {
            showToast('App ready for offline use', 'success');
          },
        });
      }).catch(console.error);
    }
  }, [showToast]);

  const handleNavigate = (screen) => setCurrentScreen(screen);

  const screenProps = {
    patient, setPatient,
    qrPayload, setQrPayload,
    scanResult, setScanResult,
    auditTrail, setAuditTrail,
    onNavigate: handleNavigate,
    showToast,
    triggerConsent: consentParams.triggerConsent
  };

  return (
    <Shell currentScreen={currentScreen} onNavigate={handleNavigate}>
      {currentScreen === 'register' && <RegisterScreen {...screenProps} />}
      {currentScreen === 'dashboard' && <DashboardScreen {...screenProps} />}
      {currentScreen === 'qr' && <QRScreen {...screenProps} />}
      {currentScreen === 'scan' && <ScanScreen {...screenProps} />}
      {currentScreen === 'provider' && <ProviderScreen {...screenProps} />}
      {currentScreen === 'audit' && <AuditScreen {...screenProps} />}
      
      {consentParams.isConsentModalOpen && (
        <OTPModal 
          consentData={consentParams.consentData} 
          onClose={consentParams.closeConsent} 
        />
      )}

      {showHelp && <HelpModal onClose={() => setShowHelp(false)} />}
      
      <button 
        onClick={() => setShowHelp(true)}
        style={{
          position: 'absolute', bottom: 90, right: 16, width: 48, height: 48,
          borderRadius: '50%', background: 'var(--primary)', color: 'white',
          display: 'flex', justifyContent: 'center', alignItems: 'center',
          border: 'none', boxShadow: '0 4px 12px rgba(13, 148, 136, 0.4)',
          cursor: 'pointer', zIndex: 50
        }}
      >
        <HelpCircle size={24} />
      </button>
    </Shell>
  );
}

export default function App() {
  return (
    <ToastProvider>
      <AppContent />
    </ToastProvider>
  );
}
