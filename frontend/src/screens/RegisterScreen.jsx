import React, { useState } from 'react';
import { Lock, ArrowRight, CheckCircle2, Shield } from 'lucide-react';
import { useApi } from '../hooks/useApi';
import TierBadge from '../components/TierBadge';
import Spinner from '../components/Spinner';

export default function RegisterScreen({ setPatient, setQrPayload, onNavigate, showToast }) {
  const [step, setStep] = useState(1);
  const [loading, setLoading] = useState(false);
  const [successMode, setSuccessMode] = useState(false);
  const [flash, setFlash] = useState(false);
  
  const api = useApi();

  const [formData, setFormData] = useState({
    name: '', age: '', gender: 'Other', blood_group: 'O+', phone: '',
    ec_name: '', ec_phone: '', allergies: '',
    medications: '', diagnoses: ''
  });

  const handleChange = (e) => setFormData(p => ({ ...p, [e.target.name]: e.target.value }));

  const loadDemo = async () => {
    try {
      const demo = await api.getDemoPatient();
      setFormData({
        name: demo.name,
        age: demo.age,
        gender: 'Female', // Demo default
        blood_group: demo.blood_group,
        phone: demo.phone,
        ec_name: 'Rahul Sharma', // Fake data
        ec_phone: demo.tier0.emergency_contact,
        allergies: demo.tier0.allergies.join(', '),
        diagnoses: demo.tier1.chronic_conditions.join(', '),
        medications: demo.tier1.current_medications.join(', ')
      });
      setFlash(true);
      setTimeout(() => setFlash(false), 800);
      setTimeout(() => setStep(4), 1000);
      showToast('Demo data loaded successfully', 'success');
    } catch (e) {
      showToast('Failed to load demo data', 'error');
    }
  };

  const nextStep = () => {
    if (step === 1 && (!formData.name || !formData.age || !formData.phone)) {
      return showToast("Please fill all required fields", 'error');
    }
    setStep(s => Math.min(s + 1, 4));
  };
  const prevStep = () => setStep(s => Math.max(s - 1, 1));

  const handleSubmit = async () => {
    setLoading(true);
    try {
      const payload = {
        patient_uid: `PAT-${Math.floor(Math.random() * 90000) + 10000}`,
        name: formData.name,
        age: parseInt(formData.age),
        blood_group: formData.blood_group,
        phone: formData.phone,
        tier0: {
          name: formData.name, blood_group: formData.blood_group, 
          allergies: formData.allergies.split(',').map(s=>s.trim()).filter(Boolean), 
          emergency_contact: formData.ec_phone
        },
        tier1: {
          chronic_conditions: formData.diagnoses.split(',').map(s=>s.trim()).filter(Boolean),
          current_medications: formData.medications.split(',').map(s=>s.trim()).filter(Boolean)
        },
        tier2: { prescriptions: [], refill_history: [], last_dispensed: null },
        tier3: { full_history: "Initial registration.", lab_results: "", doctor_notes: "", adverse_reactions: "" }
      };

      const res = await api.registerPatient(payload);
      
      setPatient(payload);
      setQrPayload(res.qr_payload);
      
      setSuccessMode(true);
      setTimeout(() => {
        setSuccessMode(false);
        onNavigate('dashboard');
      }, 1500);

    } catch (e) {
      showToast(e.detail || "Registration failed", 'error');
    } finally {
      setLoading(false);
    }
  };

  if (successMode) {
    return (
      <div style={{ height: '100%', display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'center' }}>
        <Shield size={64} color="var(--primary)" style={{ animation: 'pulseOnce 0.5s ease' }} />
        <h2 style={{ marginTop: 16, color: 'var(--primary)' }}>Encrypted & Registered</h2>
      </div>
    );
  }

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
        <h2>Registration</h2>
        <button className="btn-ghost text-sm" onClick={loadDemo} style={{ width: 'auto', padding: 0 }}>
          Load Demo Patient
        </button>
      </div>

      <div style={{ height: 6, background: 'var(--border)', borderRadius: 3, marginBottom: 24, overflow: 'hidden' }}>
        <div style={{ 
          height: '100%', background: 'var(--primary)', 
          width: `${(step / 4) * 100}%`, transition: 'width 0.3s ease' 
        }} />
      </div>

      <div className="card">
        {step === 1 && (
          <div className="animate-fadeIn">
            <h3>Personal Details</h3>
            <label>Full Name *</label>
            <input className={flash ? 'input-flash' : ''} name="name" value={formData.name} onChange={handleChange} />
            <div className="grid-2">
              <div>
                <label>Age *</label>
                <input className={flash ? 'input-flash' : ''} type="number" name="age" value={formData.age} onChange={handleChange} />
              </div>
              <div>
                <label>Blood Group *</label>
                <select className={flash ? 'input-flash' : ''} name="blood_group" value={formData.blood_group} onChange={handleChange}>
                  {['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-'].map(bg => <option key={bg}>{bg}</option>)}
                </select>
              </div>
            </div>
            <label>Phone Number *</label>
            <input className={flash ? 'input-flash' : ''} type="tel" name="phone" value={formData.phone} onChange={handleChange} />
          </div>
        )}

        {step === 2 && (
          <div className="animate-fadeIn">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
              <h3>Emergency Info</h3>
              <TierBadge tier={1} />
            </div>
            <p className="text-muted text-sm" style={{ marginBottom: 16 }}>Available to ASHA workers and paramedics.</p>
            <label>Emergency Contact Name</label>
            <input name="ec_name" value={formData.ec_name} onChange={handleChange} />
            <label>Emergency Contact Phone</label>
            <input type="tel" name="ec_phone" value={formData.ec_phone} onChange={handleChange} />
            <label>Allergies (comma separated)</label>
            <input name="allergies" value={formData.allergies} onChange={handleChange} placeholder="e.g. Penicillin, Peanuts" />
          </div>
        )}

        {step === 3 && (
          <div className="animate-fadeIn">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
              <h3>Clinical Record</h3>
              <TierBadge tier={2} />
            </div>
            <p className="text-muted text-sm" style={{ marginBottom: 16 }}>Available to Pharmacists and Doctors.</p>
            <label>Diagnoses / Chronic Conditions (comma separated)</label>
            <input name="diagnoses" value={formData.diagnoses} onChange={handleChange} placeholder="e.g. Type 2 Diabetes" />
            <label>Current Medications (comma separated)</label>
            <input name="medications" value={formData.medications} onChange={handleChange} placeholder="e.g. Metformin 500mg" />
          </div>
        )}

        {step === 4 && (
          <div className="animate-fadeIn">
            <h3>Confirm & Encrypt</h3>
            <p className="text-muted text-sm" style={{ marginBottom: 16 }}>Review your tiered access structure.</p>
            
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8, marginBottom: 24 }}>
              <div style={{ background: 'var(--tier3)', color: 'white', padding: 8, borderRadius: '4px 4px 0 0', textAlign: 'center', fontWeight: 'bold' }} title="Doctors Only (OTP Required)">T3: Full History</div>
              <div style={{ background: 'var(--tier2)', color: 'white', padding: 8, borderRadius: 2, textAlign: 'center', margin: '0 8px', fontWeight: 'bold' }} title="Pharmacists: Prescriptions">T2: Clinical</div>
              <div style={{ background: 'var(--tier1)', color: 'white', padding: 8, borderRadius: 2, textAlign: 'center', margin: '0 16px', fontWeight: 'bold' }} title="ASHA: Meds & Diagnoses">T1: Basic Health</div>
              <div style={{ background: 'var(--tier0)', color: 'white', padding: 8, borderRadius: '0 0 4px 4px', textAlign: 'center', margin: '0 24px', fontWeight: 'bold' }} title="Public: Demographics & Emergency">T0: Public ID</div>
            </div>

            <div style={{ background: 'var(--bg-surface)', padding: 12, borderRadius: 8, fontSize: '0.875rem' }}>
              <strong>Name:</strong> {formData.name} <br/>
              <strong>Blood:</strong> {formData.blood_group} <br/>
              <strong>Meds:</strong> {formData.medications || 'None'}
            </div>
          </div>
        )}
      </div>

      <div style={{ display: 'flex', gap: 12, marginTop: 16 }}>
        {step > 1 && <button className="btn btn-outline" onClick={prevStep}>Back</button>}
        {step < 4 ? (
          <button className="btn btn-primary" onClick={nextStep}>Next <ArrowRight size={18}/></button>
        ) : (
          <button className="btn btn-primary" onClick={handleSubmit} disabled={loading}>
            {loading ? <Spinner size={20} /> : <><Lock size={18}/> Encrypt & Save</>}
          </button>
        )}
      </div>
    </div>
  );
}
