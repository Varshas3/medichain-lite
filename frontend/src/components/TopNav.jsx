import React, { useState, useEffect } from 'react';
import { Cross, User } from 'lucide-react';
import { useApi } from '../hooks/useApi';

export default function TopNav() {
  const [apiStatus, setApiStatus] = useState('checking'); // checking, online, offline
  const api = useApi();

  useEffect(() => {
    let mounted = true;
    const checkHealth = async () => {
      try {
        await api.health();
        if (mounted) setApiStatus('online');
      } catch (e) {
        if (mounted) setApiStatus('offline');
      }
    };
    checkHealth();
    const interval = setInterval(checkHealth, 30000); // Check every 30s
    return () => { mounted = false; clearInterval(interval); };
  }, []);

  const getStatusColor = () => {
    if (apiStatus === 'checking') return '#f59e0b';
    if (apiStatus === 'online') return '#10b981';
    return '#ef4444';
  };

  return (
    <div style={{
      height: '60px',
      backgroundColor: 'var(--primary)',
      color: 'white',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      padding: '0 16px',
      boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
      zIndex: 10
    }} className="top-nav no-print">
      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
        <div style={{ background: 'white', borderRadius: '50%', padding: 4 }}>
          <Cross size={20} color="var(--primary)" fill="var(--primary)" />
        </div>
        <h1 style={{ fontSize: '1.2rem', margin: 0, color: 'white', fontWeight: 700 }}>MediChain</h1>
        <div style={{ display: 'flex', alignItems: 'center', gap: 4, marginLeft: 4 }}>
          <span style={{ 
            width: 8, height: 8, borderRadius: '50%', 
            backgroundColor: getStatusColor(),
            boxShadow: `0 0 0 2px ${getStatusColor()}40`,
            animation: apiStatus === 'online' ? 'pulse 2s infinite' : 'none'
          }} title={`API ${apiStatus}`}></span>
          {apiStatus === 'offline' && <span style={{ fontSize: '0.65rem', background: 'rgba(255,255,255,0.2)', padding: '2px 6px', borderRadius: 8 }}>Demo Mode</span>}
        </div>
      </div>
      
      <div style={{ 
        width: 36, height: 36, borderRadius: '50%', 
        backgroundColor: 'rgba(255,255,255,0.2)',
        display: 'flex', justifyContent: 'center', alignItems: 'center'
      }}>
        <User size={20} />
      </div>
    </div>
  );
}
