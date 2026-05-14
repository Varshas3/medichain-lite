import React, { useState } from 'react';
import { UserSquare2, ChevronDown, ChevronUp, Pill, AlertTriangle, CheckCircle, Search } from 'lucide-react';
import { useApi } from '../hooks/useApi';
import Spinner from '../components/Spinner';

const PROVIDERS = [
  { id: 'DOC-KA-00001', role: 'Doctor', tier: 3 },
  { id: 'PHR-KA-00001', role: 'Pharmacist', tier: 2 },
  { id: 'ASH-KA-00001', role: 'ASHA Worker', tier: 1 }
];

export default function ProviderScreen({ scanResult, onNavigate, showToast }) {
  const [selectedProvider, setSelectedProvider] = useState(PROVIDERS[0].id);
  const [expandedTiers, setExpandedTiers] = useState({ 0: true, 1: true, 2: true, 3: true });
  
  const [drugInput, setDrugInput] = useState('');
  const [interactionResult, setInteractionResult] = useState(null);
  const [checkingDrug, setCheckingDrug] = useState(false);
  const api = useApi();

  const toggleTier = (t) => setExpandedTiers(prev => ({ ...prev, [t]: !prev[t] }));

  const humanize = (str) => {
    return str.split('_').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ');
  };

  const getPatientMeds = () => {
    if (!scanResult || scanResult.tier_accessed < 2) return [];
    // tier2 prescriptions is array of {drug, dosage}
    const rx = scanResult.data.tier2?.prescriptions || [];
    return rx.map(r => r.drug);
  };

  const checkDrug = async () => {
    if (!drugInput) return;
    setCheckingDrug(true);
    setInteractionResult(null);
    try {
      const result = await api.checkDrugs({
        new_drug: drugInput,
        existing_medications: getPatientMeds(),
        provider_id: selectedProvider,
        patient_uid: scanResult.patient_uid
      });
      setInteractionResult(result);
    } catch (e) {
      showToast("Failed to check interaction", 'error');
    } finally {
      setCheckingDrug(false);
    }
  };

  return (
    <div className="animate-fadeIn">
      <div style={{ background: '#4c1d95', color: '#ede9fe', padding: '12px 16px', borderRadius: 8, fontSize: '0.875rem', display: 'flex', alignItems: 'center', gap: 8, marginBottom: 16 }}>
        <UserSquare2 size={18} /> This view simulates a provider-facing app
      </div>

      <div className="card" style={{ marginBottom: 16 }}>
        <label>Active Provider Session</label>
        <select value={selectedProvider} onChange={e => setSelectedProvider(e.target.value)}>
          {PROVIDERS.map(p => <option key={p.id} value={p.id}>🩺 {p.role} ({p.id})</option>)}
        </select>
      </div>

      {!scanResult ? (
        <div style={{ textAlign: 'center', marginTop: 60 }}>
          <p className="text-muted" style={{ marginBottom: 16 }}>No patient scanned yet.</p>
          <button className="btn btn-primary" style={{ margin: '0 auto', width: 'auto', padding: '12px 24px' }} onClick={() => onNavigate('scan')}>
            Go to Scan Tab
          </button>
        </div>
      ) : (
        <>
          <div className="card" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div>
              <h2 style={{ fontSize: '1.25rem', marginBottom: 4 }}>{scanResult.data.tier0?.name || 'Unknown Patient'}</h2>
              <div className="font-mono text-muted text-sm">{scanResult.patient_uid}</div>
            </div>
            <div className="chip" style={{ background: '#fef2f2', color: 'var(--danger)', border: '1px solid #fecaca', margin: 0 }}>
              🩸 {scanResult.data.tier0?.blood_group || 'N/A'}
            </div>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: 12, marginBottom: 16 }}>
            {[0, 1, 2, 3].map(t => {
              const data = scanResult.data[`tier${t}`];
              if (!data) return null;
              const isExpanded = expandedTiers[t];

              return (
                <div key={t} style={{ border: `1px solid var(--tier${t})`, borderRadius: 8, overflow: 'hidden' }}>
                  <div 
                    style={{ background: `var(--tier${t})`, color: 'white', padding: '12px 16px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', cursor: 'pointer' }}
                    onClick={() => toggleTier(t)}
                  >
                    <span style={{ fontWeight: 600 }}>Tier {t} Data</span>
                    {isExpanded ? <ChevronUp size={18} /> : <ChevronDown size={18} />}
                  </div>
                  
                  {isExpanded && (
                    <div style={{ padding: 16, background: 'white' }}>
                      <table style={{ width: '100%', fontSize: '0.875rem' }}>
                        <tbody>
                          {Object.entries(data).map(([key, val]) => (
                            <tr key={key}>
                              <td style={{ color: 'var(--text-muted)', paddingBottom: 8, width: '40%', verticalAlign: 'top' }}>{humanize(key)}</td>
                              <td style={{ fontWeight: 500, paddingBottom: 8 }}>
                                {Array.isArray(val) ? (
                                  typeof val[0] === 'object' ? (
                                    <ul style={{ paddingLeft: 16, margin: 0 }}>
                                      {val.map((obj, i) => (
                                        <li key={i}>{Object.values(obj).join(' - ')}</li>
                                      ))}
                                    </ul>
                                  ) : (
                                    val.join(', ') || 'None'
                                  )
                                ) : (val || 'N/A')}
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  )}
                </div>
              );
            })}
          </div>

          {scanResult.tier_accessed >= 2 && (
            <div className="card animate-fadeIn">
              <h3 style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 12 }}>
                <Pill size={18} color="var(--primary)" /> Clinical Safety Check
              </h3>
              <p className="text-xs text-muted" style={{ marginBottom: 12 }}>Checking against current prescriptions: {getPatientMeds().join(', ') || 'None'}</p>
              
              <div style={{ display: 'flex', gap: 8, marginBottom: 12 }}>
                <input 
                  placeholder="New drug to prescribe" 
                  value={drugInput}
                  onChange={e => setDrugInput(e.target.value)}
                  style={{ margin: 0 }}
                />
                <button className="btn btn-primary" style={{ width: 'auto' }} onClick={checkDrug} disabled={!drugInput || checkingDrug}>
                  {checkingDrug ? <Spinner size={18} /> : <Search size={18} />}
                </button>
              </div>

              {interactionResult && (
                <div style={{ 
                  marginTop: 16, padding: 12, borderRadius: 8,
                  background: interactionResult.safe_to_dispense ? 'var(--primary-light)' : '#fee2e2',
                  border: `1px solid ${interactionResult.safe_to_dispense ? 'var(--primary)' : 'var(--danger)'}`,
                  animation: !interactionResult.safe_to_dispense ? 'pulseOnce 0.5s ease' : 'none'
                }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4, color: interactionResult.safe_to_dispense ? 'var(--primary-dark)' : 'var(--danger)', fontWeight: 600 }}>
                    {interactionResult.safe_to_dispense ? <CheckCircle size={18} /> : <AlertTriangle size={18} />}
                    {interactionResult.safe_to_dispense ? 'Safe to Prescribe' : 'Clinical Warning'}
                  </div>
                  {!interactionResult.safe_to_dispense && interactionResult.interactions_found.map((int, i) => (
                    <div key={i} className="text-sm" style={{ marginTop: 8 }}>
                      <strong>{int.severity.toUpperCase()}</strong>: {int.mechanism}
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </>
      )}
    </div>
  );
}
