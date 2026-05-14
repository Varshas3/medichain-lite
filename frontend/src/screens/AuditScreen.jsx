import React, { useState, useEffect } from 'react';
import { ShieldCheck, ShieldAlert, Lock, Unlock, Link, Clock, AlertTriangle } from 'lucide-react';
import { useApi } from '../hooks/useApi';
import Spinner from '../components/Spinner';
import TierBadge from '../components/TierBadge';

export default function AuditScreen({ patient, auditTrail, setAuditTrail, showToast }) {
  const [verifying, setVerifying] = useState(false);
  const [verifyStatus, setVerifyStatus] = useState(null); // { valid: bool, message: str, count: int }
  
  const [toggles, setToggles] = useState({ 1: true, 2: true, 3: true });
  const api = useApi();

  const patientUid = patient?.patient_uid || "PAT-XXXX";

  useEffect(() => {
    // Fetch audit trail on mount if patient exists
    if (patient) {
      api.getAudit(patientUid)
        .then(res => setAuditTrail(res.audit_trail))
        .catch(err => console.error("Failed to load audit trail", err));
    }
  }, [patient]);

  const handleVerify = async () => {
    setVerifying(true);
    setVerifyStatus(null);
    try {
      const res = await api.verifyChain(patientUid);
      setVerifyStatus({
        valid: res.is_valid,
        count: res.total_logs,
        message: res.is_valid ? `All ${res.total_logs} entries intact.` : "Tampering detected in chain!"
      });
    } catch (e) {
      showToast("Verification failed", 'error');
    } finally {
      setVerifying(false);
    }
  };

  const timeAgo = (dateStr) => {
    const seconds = Math.floor((new Date() - new Date(dateStr + "Z")) / 1000);
    if (seconds < 60) return "Just now";
    const minutes = Math.floor(seconds / 60);
    if (minutes < 60) return `${minutes} min ago`;
    const hours = Math.floor(minutes / 60);
    if (hours < 24) return `${hours} hr ago`;
    return `${Math.floor(hours / 24)} days ago`;
  };

  const ToggleSwitch = ({ checked, onChange, disabled }) => (
    <div 
      onClick={() => !disabled && onChange(!checked)}
      style={{
        width: 44, height: 24, borderRadius: 12,
        background: disabled ? 'var(--border)' : (checked ? 'var(--primary)' : '#cbd5e1'),
        position: 'relative', cursor: disabled ? 'not-allowed' : 'pointer',
        transition: 'background 0.3s'
      }}
    >
      <div style={{
        width: 20, height: 20, borderRadius: '50%', background: 'white',
        position: 'absolute', top: 2, left: checked ? 22 : 2,
        transition: 'left 0.3s ease', boxShadow: '0 1px 3px rgba(0,0,0,0.2)'
      }} />
    </div>
  );

  return (
    <div className="animate-fadeIn">
      
      {/* SECTION 1: Consent & Tier Controls */}
      <h3 style={{ marginBottom: 12, display: 'flex', alignItems: 'center', gap: 8 }}>
        <Lock size={18} /> Privacy Controls
      </h3>
      
      <div className="card" style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', opacity: 0.6 }}>
          <div>
            <div style={{ fontWeight: 600 }}>Tier 0: Public</div>
            <div className="text-xs text-muted">Always public — cannot be disabled</div>
          </div>
          <ToggleSwitch checked={true} disabled={true} />
        </div>
        
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <div style={{ fontWeight: 600, color: 'var(--tier1)' }}>Tier 1: Basic Health</div>
            <div className="text-xs text-muted">ASHA workers & paramedics</div>
          </div>
          <ToggleSwitch checked={toggles[1]} onChange={(v) => setToggles({...toggles, 1: v})} />
        </div>

        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <div style={{ fontWeight: 600, color: 'var(--tier2)' }}>Tier 2: Clinical</div>
            <div className="text-xs text-muted">Pharmacists (prescriptions)</div>
          </div>
          <ToggleSwitch checked={toggles[2]} onChange={(v) => setToggles({...toggles, 2: v})} />
        </div>

        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', background: '#fef2f2', padding: 8, margin: '0 -8px', borderRadius: 8 }}>
          <div>
            <div style={{ fontWeight: 600, color: 'var(--tier3)' }}>Tier 3: Full History</div>
            <div className="text-xs text-muted" style={{ color: 'var(--danger)' }}>Requires OTP consent per session</div>
          </div>
          <ToggleSwitch checked={toggles[3]} onChange={(v) => setToggles({...toggles, 3: v})} />
        </div>
      </div>

      {/* SECTION 2: Audit Timeline */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end', marginTop: 24, marginBottom: 16 }}>
        <h3 style={{ display: 'flex', alignItems: 'center', gap: 8, margin: 0 }}>
          <ShieldAlert size={18} /> Audit Timeline
        </h3>
        <button className="btn btn-outline text-xs" style={{ width: 'auto', padding: '6px 12px' }} onClick={handleVerify} disabled={verifying}>
          {verifying ? <Spinner size={14} /> : <><Link size={14} /> Verify Chain</>}
        </button>
      </div>

      {verifyStatus && (
        <div style={{ 
          background: verifyStatus.valid ? 'var(--primary-light)' : '#fee2e2', 
          color: verifyStatus.valid ? 'var(--primary-dark)' : 'var(--danger)', 
          padding: '12px 16px', borderRadius: 8, marginBottom: 16, display: 'flex', alignItems: 'center', gap: 8,
          animation: 'pulseOnce 0.5s ease'
        }}>
          {verifyStatus.valid ? <ShieldCheck size={20} /> : <AlertTriangle size={20} />}
          <span style={{ fontWeight: 500, fontSize: '0.875rem' }}>{verifyStatus.message}</span>
        </div>
      )}

      <div className="card" style={{ position: 'relative' }}>
        {(!auditTrail || auditTrail.length === 0) ? (
          <div style={{ textAlign: 'center', padding: '32px 16px', opacity: 0.6 }}>
            <Clock size={48} style={{ margin: '0 auto 16px auto' }} />
            <p>Scan your QR to generate your first audit entry</p>
          </div>
        ) : (
          <div style={{ paddingLeft: 12 }}>
            <div style={{ position: 'absolute', left: 23, top: 24, bottom: 24, width: 2, background: 'var(--border)', zIndex: 0 }} />
            
            {[...auditTrail].reverse().map((log, index) => (
              <div key={log.id} style={{ position: 'relative', zIndex: 1, marginBottom: 24, paddingLeft: 24 }}>
                <div style={{ 
                  position: 'absolute', left: -15, top: 4, width: 12, height: 12, borderRadius: '50%', 
                  background: log.action === 'scan' ? 'var(--success)' : 'var(--warning)', 
                  border: '2px solid white', boxShadow: '0 0 0 1px var(--border)' 
                }} />
                
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 4 }}>
                  <div style={{ fontWeight: 600, fontSize: '0.9rem' }}>{log.provider_id}</div>
                  <div className="text-xs text-muted" title={new Date(log.timestamp + "Z").toLocaleString()}>
                    {timeAgo(log.timestamp)}
                  </div>
                </div>
                
                <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
                  <span className="chip" style={{ margin: 0, textTransform: 'capitalize' }}>
                    {log.action.replace('_', ' ')}
                  </span>
                  <TierBadge tier={log.tier_accessed} />
                </div>
                
                {log.details && (
                  <div className="text-xs text-muted" style={{ marginTop: 8, background: 'var(--bg-surface)', padding: 8, borderRadius: 4, fontFamily: 'monospace' }}>
                    {JSON.stringify(JSON.parse(log.details))}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

    </div>
  );
}
