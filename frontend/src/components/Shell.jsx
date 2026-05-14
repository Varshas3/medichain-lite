import React from 'react';
import TopNav from './TopNav';
import TabBar from './TabBar';

export default function Shell({ children, currentScreen, onNavigate }) {
  // Only show tab bar if not on register screen
  const showTabs = currentScreen !== 'register';

  return (
    <div className="shell">
      <TopNav />
      <div className="screen-container" style={{ paddingBottom: showTabs ? '80px' : '16px' }}>
        {children}
      </div>
      {showTabs && <TabBar currentScreen={currentScreen} onNavigate={onNavigate} />}
    </div>
  );
}
