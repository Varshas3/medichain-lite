import React from 'react';
import { Home, QrCode, ScanLine, UserSquare2, ShieldAlert } from 'lucide-react';

export default function TabBar({ currentScreen, onNavigate }) {
  const tabs = [
    { id: 'dashboard', label: 'Home', icon: Home },
    { id: 'qr', label: 'My QR', icon: QrCode },
    { id: 'scan', label: 'Scan', icon: ScanLine },
    { id: 'provider', label: 'Provider', icon: UserSquare2 },
    { id: 'audit', label: 'Audit', icon: ShieldAlert },
  ];

  return (
    <div style={{
      position: 'absolute',
      bottom: 0,
      left: 0,
      right: 0,
      height: '65px',
      backgroundColor: 'var(--bg-card)',
      borderTop: '1px solid var(--border)',
      display: 'flex',
      justifyContent: 'space-around',
      alignItems: 'center',
      paddingBottom: 'safe-area-inset-bottom'
    }} className="tab-bar no-print">
      {tabs.map(tab => {
        const Icon = tab.icon;
        const isActive = currentScreen === tab.id;
        return (
          <button
            key={tab.id}
            onClick={() => onNavigate(tab.id)}
            style={{
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              background: 'none',
              border: 'none',
              color: isActive ? 'var(--primary)' : 'var(--text-muted)',
              cursor: 'pointer',
              transition: 'color 0.2s',
              width: '20%'
            }}
          >
            <Icon size={24} style={{ marginBottom: 4 }} />
            <span style={{ fontSize: '0.65rem', fontWeight: isActive ? '600' : '500' }}>
              {tab.label}
            </span>
          </button>
        );
      })}
    </div>
  );
}
