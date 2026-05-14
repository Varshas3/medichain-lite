import React, { useState, useEffect, useRef } from 'react';
import { Lock, ShieldCheck, X } from 'lucide-react';
import Spinner from './Spinner';
import { useApi } from '../hooks/useApi';
import { useToast } from '../hooks/useToast';

export default function OTPModal({ consentData, onClose }) {
  const [step, setStep] = useState(1);
  const [loading, setLoading] = useState(false);
  const [sessionId, setSessionId] = useState(null);
  const [otp, setOtp] = useState(['', '', '', '', '', '']);
  const [timeLeft, setTimeLeft] = useState(600);
  const inputsRef = useRef([]);
  
  const api = useApi();
  const { showToast } = useToast();

  useEffect(() => {
    let timer;
    if (step === 2 && timeLeft > 0) {
      timer = setInterval(() => setTimeLeft(t => t - 1), 1000);
    }
    return () => clearInterval(timer);
  }, [step, timeLeft]);

  const handleSendOTP = async () => {
    setLoading(true);
    try {
      const res = await api.requestConsent({
        patient_uid: consentData.patient_uid,
        provider_id: consentData.provider_id,
        phone_number: consentData.phone_number || "+91XXXXXX1234"
      });
      setSessionId(res.session_id);
      setStep(2);
      showToast(res.message, 'success');
      if (res.demo_otp) {
        showToast(`DEMO OTP: ${res.demo_otp}`, 'info');
      }
    } catch (err) {
      showToast(err.detail || "Failed to request OTP", 'error');
    } finally {
      setLoading(false);
    }
  };

  const handleOtpChange = (index, value) => {
    if (!/^[0-9]*$/.test(value)) return;
    
    const newOtp = [...otp];
    newOtp[index] = value;
    setOtp(newOtp);

    // Auto-advance
    if (value && index < 5) {
      inputsRef.current[index + 1].focus();
    }
  };

  const handleKeyDown = (index, e) => {
    if (e.key === 'Backspace' && !otp[index] && index > 0) {
      inputsRef.current[index - 1].focus();
    }
  };

  const verifyOTP = async () => {
    const fullOtp = otp.join('');
    if (fullOtp.length !== 6) return;
    
    setLoading(true);
    try {
      const res = await api.verifyOTP({
        session_id: sessionId,
        otp: fullOtp
      });
      if (res.approved) {
        setStep(3);
        setTimeout(() => {
          if (consentData.onComplete) consentData.onComplete();
          onClose();
        }, 1500);
      } else {
        showToast(res.message, 'error');
        setOtp(['', '', '', '', '', '']);
        inputsRef.current[0].focus();
      }
    } catch (err) {
      showToast("Verification failed", 'error');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (step === 2 && otp.every(v => v !== '')) {
      verifyOTP();
    }
  }, [otp]);

  const formatTime = (s) => `${Math.floor(s / 60)}:${(s % 60).toString().padStart(2, '0')}`;

  return (
    <div className="modal-overlay">
      <div className="modal-content">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
          <h2 style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <Lock size={20} color="var(--primary)" /> 
            Tier 3 Consent
          </h2>
          {step !== 3 && <button className="btn-ghost" onClick={onClose} style={{ padding: 4, width: 'auto' }}><X size={24} /></button>}
        </div>

        {step === 1 && (
          <div>
            <p className="text-muted" style={{ marginBottom: 24 }}>
              The provider requires your approval to decrypt Tier 3 medical history. An OTP will be sent to your registered phone.
            </p>
            <button className="btn btn-primary" onClick={handleSendOTP} disabled={loading}>
              {loading ? <Spinner size={20} /> : "Send OTP via SMS"}
            </button>
          </div>
        )}

        {step === 2 && (
          <div>
            <p className="text-muted" style={{ textAlign: 'center', marginBottom: 8 }}>
              Enter 6-digit code sent to your phone
            </p>
            <div className="otp-inputs" style={{ display: 'flex', justifyContent: 'center' }}>
              {otp.map((digit, i) => (
                <input
                  key={i}
                  ref={el => inputsRef.current[i] = el}
                  type="text"
                  maxLength="1"
                  value={digit}
                  onChange={e => handleOtpChange(i, e.target.value)}
                  onKeyDown={e => handleKeyDown(i, e)}
                  style={{ width: '40px', height: '50px', textAlign: 'center', fontSize: '1.2rem', margin: '0 4px', borderRadius: '8px', border: '1px solid var(--border)' }}
                />
              ))}
            </div>
            <p className="text-xs text-muted" style={{ textAlign: 'center', marginBottom: 24 }}>
              Time remaining: {formatTime(timeLeft)}
            </p>
            {loading && <div style={{ display: 'flex', justifyContent: 'center' }}><Spinner size={24} /></div>}
          </div>
        )}

        {step === 3 && (
          <div style={{ textAlign: 'center', padding: '24px 0' }}>
            <ShieldCheck size={64} color="var(--success)" style={{ margin: '0 auto 16px auto', animation: 'pulseOnce 0.5s ease' }} />
            <h3 style={{ color: 'var(--success)' }}>Access Approved</h3>
            <p className="text-muted text-sm">Decrypting Tier 3 payload...</p>
          </div>
        )}
      </div>
    </div>
  );
}
