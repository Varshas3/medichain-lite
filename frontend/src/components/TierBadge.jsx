import React from 'react';

export default function TierBadge({ tier }) {
  const tiers = {
    0: { label: 'Public', color: 'var(--tier0)', bg: '#eff6ff' },
    1: { label: 'Basic', color: 'var(--tier1)', bg: '#ecfdf5' },
    2: { label: 'Clinical', color: 'var(--tier2)', bg: '#fffbeb' },
    3: { label: 'Full', color: 'var(--tier3)', bg: '#fef2f2' }
  };
  
  const t = tiers[tier] || tiers[0];
  
  return (
    <span style={{
      display: 'inline-flex',
      alignItems: 'center',
      padding: '2px 8px',
      borderRadius: '12px',
      fontSize: '0.75rem',
      fontWeight: '600',
      backgroundColor: t.bg,
      color: t.color,
      border: `1px solid ${t.color}33`
    }}>
      T{tier} {t.label}
    </span>
  );
}
