import React, { useState, useEffect, useCallback } from 'react';
import { Pill, ShieldAlert, History, Activity, AlertTriangle, CheckCircle, Search, QrCode } from 'lucide-react';
import { useApi } from '../hooks/useApi';
import Spinner from '../components/Spinner';

export default function DashboardScreen({ patient, auditTrail, onNavigate, showToast }) {
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [isSearching, setIsSearching] = useState(false);
  
  const [drugInput, setDrugInput] = useState('');
  const [interactionResult, setInteractionResult] = useState(null);
  const [checkingDrug, setCheckingDrug] = useState(false);

  const api = useApi();

  // Fallback to demo data safely if patient state is somehow null
  const activePatient = patient || {
    name: 'Guest User',
    patient_uid: 'PAT-XXXX',
    blood_group: 'Unknown',
    tier0: { allergies: [] },
    tier1: { current_medications: [] }
  };

  const meds = activePatient.tier1?.current_medications || [];
  const allergies = activePatient.tier0?.allergies || [];

  // Search debounce
  useEffect(() => {
    if (!searchQuery) {
      setSearchResults([]);
      return;
    }
    const timer = setTimeout(async () => {
      setIsSearching(true);
      try {
        const results = await api.searchPatients(searchQuery);
        setSearchResults(results);
      } catch (e) {
        console.error(e);
      } finally {
        setIsSearching(false);
      }
    }, 400);
    return () => clearTimeout(timer);
  }, [searchQuery, api]);

  const checkDrug = async (drugA, drugB) => {
    setCheckingDrug(true);
    setInteractionResult(null);
    try {
      const existing = drugB ? [drugB] : meds;
      const result = await api.checkDrugs({
        new_drug: drugA,
        existing_medications: existing,
        provider_id: "DOC-KA-00001", // Demo context
        patient_uid: activePatient.patient_uid
      });
      setInteractionResult(result);
    } catch (e) {
      showToast("Failed to check interaction", 'error');
    } finally {
      setCheckingDrug(false);
    }
  };

  return (
    <div>
      <div className="card hero-card animate-fadeIn">
        <h2>{activePatient.name}</h2>
        <p className="font-mono" style={{ opacity: 0.8, marginBottom: 12 }}>{activePatient.patient_uid}</p>
        
        <div>
          <span className="chip" style={{ background: 'rgba(255,255,255,0.2)', border: 'none', color: 'white' }}>🩸 {activePatient.blood_group}</span>
          {allergies.length > 0 && (
            <span className="chip" style={{ background: 'rgba(239, 68, 68, 0.2)', border: 'none', color: 'white' }}>⚠️ {allergies.length} Allergies</span>
          )}
          <span className="chip" style={{ background: 'rgba(255,255,255,0.2)', border: 'none', color: 'white' }}>💊 {meds.length} Meds</span>
        </div>
      </div>

      <div className="grid-2 animate-fadeIn" style={{ animationDelay: '0.1s' }}>
        <div className="card" style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
          <Pill size={24} color="var(--primary)" style={{ marginBottom: 8 }}/>
          <h3>{meds.length}</h3>
          <span className="text-xs text-muted">Active Meds</span>
        </div>
        <div className="card" style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
          <ShieldAlert size={24} color="var(--tier2)" style={{ marginBottom: 8 }}/>
          <h3>4</h3>
          <span className="text-xs text-muted">Encrypted Tiers</span>
        </div>
        <div className="card" style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
          <History size={24} color="var(--tier0)" style={{ marginBottom: 8 }}/>
          <h3>{auditTrail?.length || 0}</h3>
          <span className="text-xs text-muted">Access Events</span>
        </div>
        <div className="card" style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
          <Activity size={24} color="var(--success)" style={{ marginBottom: 8 }}/>
          <h3 style={{ color: 'var(--success)' }}>Valid</h3>
          <span className="text-xs text-muted">Chain Status</span>
        </div>
      </div>

      <button className="btn btn-primary animate-fadeIn" style={{ marginBottom: 16, animationDelay: '0.2s' }} onClick={() => onNavigate('qr')}>
        <QrCode size={20} /> Show My QR
      </button>

      <div className="card animate-fadeIn" style={{ animationDelay: '0.3s' }}>
        <h3 style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 12 }}>
          <Search size={18} /> Patient Search
        </h3>
        <input 
          placeholder="Search by name or UID..." 
          value={searchQuery}
          onChange={e => setSearchQuery(e.target.value)}
        />
        {isSearching && <div style={{ textAlign: 'center', padding: 8 }}><Spinner size={20} /></div>}
        
        {searchResults.length > 0 && (
          <div style={{ marginTop: 8, display: 'flex', flexDirection: 'column', gap: 8 }}>
            {searchResults.map(r => (
              <div key={r.patient_uid} style={{ padding: 8, border: '1px solid var(--border)', borderRadius: 8, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div>
                  <div style={{ fontWeight: 600, fontSize: '0.9rem' }}>{r.name}</div>
                  <div className="text-xs text-muted font-mono">{r.patient_uid}</div>
                </div>
                <button className="btn-outline text-xs" style={{ padding: '4px 8px', width: 'auto', borderRadius: 4 }}>Load</button>
              </div>
            ))}
          </div>
        )}
      </div>

      <div className="card animate-fadeIn" style={{ animationDelay: '0.4s' }}>
        <h3>Drug Interaction Checker</h3>
        <p className="text-xs text-muted" style={{ marginBottom: 12 }}>Check against: {meds.join(', ') || 'None'}</p>
        
        <div style={{ display: 'flex', gap: 8, marginBottom: 12 }}>
          <input 
            placeholder="New drug name" 
            value={drugInput}
            onChange={e => setDrugInput(e.target.value)}
            style={{ margin: 0 }}
          />
          <button className="btn btn-primary" style={{ width: 'auto' }} onClick={() => checkDrug(drugInput)} disabled={!drugInput || checkingDrug}>
            {checkingDrug ? <Spinner size={18} /> : 'Check'}
          </button>
        </div>

        <div style={{ display: 'flex', gap: 8, overflowX: 'auto', paddingBottom: 8, margin: '0 -16px', padding: '0 16px' }}>
          <button className="btn btn-outline text-xs" style={{ whiteSpace: 'nowrap', padding: '4px 8px', borderRadius: 16 }} onClick={() => { setDrugInput('Warfarin'); checkDrug('Warfarin', 'Aspirin'); }}>
            ⚠️ Warfarin+Aspirin
          </button>
          <button className="btn btn-outline text-xs" style={{ whiteSpace: 'nowrap', padding: '4px 8px', borderRadius: 16 }} onClick={() => { setDrugInput('Paracetamol'); checkDrug('Paracetamol', 'Metformin'); }}>
            ✅ Para+Metformin
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
              {interactionResult.safe_to_dispense ? 'Safe to Dispense' : 'Interaction Detected'}
            </div>
            {!interactionResult.safe_to_dispense && interactionResult.interactions_found.map((int, i) => (
              <div key={i} className="text-sm" style={{ marginTop: 8 }}>
                <strong>{int.severity.toUpperCase()}</strong>: {int.mechanism}
              </div>
            ))}
          </div>
        )}
      </div>

    </div>
  );
}
