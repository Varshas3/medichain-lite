import { useState, useCallback } from 'react';

export function useConsent() {
  const [isConsentModalOpen, setIsConsentModalOpen] = useState(false);
  const [consentData, setConsentData] = useState(null);
  
  const triggerConsent = useCallback((data) => {
    setConsentData(data); // { patient_uid, provider_id, phone_number, onComplete }
    setIsConsentModalOpen(true);
  }, []);

  const closeConsent = useCallback(() => {
    setIsConsentModalOpen(false);
    setConsentData(null);
  }, []);

  return {
    isConsentModalOpen,
    consentData,
    triggerConsent,
    closeConsent
  };
}
