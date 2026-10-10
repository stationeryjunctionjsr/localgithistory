'use client';

import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { usePathname } from 'next/navigation';
import api from '@/utils/api';
import { logger } from '@/utils/logger';

export interface ServiceableSeller {
  id: string;
  name: string;
  companyName: string;
  city?: string;
  allowUrgentDelivery?: boolean;
}

export interface PincodeData {
  pincode: string;
  city?: string | null;
  state?: string | null;
  district?: string | null;
  isServiceable: boolean;
  sellerCount: number;
  serviceableSellers: ServiceableSeller[];
  urgentDeliveryAvailable?: boolean;
  slotBookingAvailable?: boolean;
  showSellerCount?: boolean;  // false for wholesalers — marketplace model does not apply
  zoneCustomerType?: string;  // "retail" | "business" | "both"
  hasZone?: boolean;         // pincode maps to a hyperlocal delivery zone
  hasPanIndia?: boolean;     // pincode is within Pan-India courier serviceability
  allowedModes?: ('hyperlocal' | 'pan_india')[];  // modes available for this pincode
  defaultMode?: 'hyperlocal' | 'pan_india';        // API-recommended default mode
}

interface PincodeContextType {
  pincode: string | null;
  city: string | null;
  state: string | null;
  district: string | null;
  isServiceable: boolean | null;
  sellerCount: number;
  serviceableSellers: ServiceableSeller[];
  pincodeData: PincodeData | null;
  isPincodeModalOpen: boolean;
  isMandatory: boolean;
  isLoading: boolean;
  error: string | null;
  checkAndSetPincode: (
    pin: string,
    role?: string
  ) => Promise<{ success: boolean; isServiceable: boolean; message?: string; data?: PincodeData }>;
  openPincodeModal: (mandatory?: boolean) => void;
  closePincodeModal: () => void;
  clearPincode: () => void;
  activeMode: 'hyperlocal' | 'pan_india';
  availableModes: ('hyperlocal' | 'pan_india')[];
  setActiveMode: (mode: 'hyperlocal' | 'pan_india') => void;
}

const STORAGE_KEY = 'sj_pincode_data';
const PINCODE_ONLY_KEY = 'sj_user_pincode';

const PincodeContext = createContext<PincodeContextType | undefined>(undefined);

export const PincodeProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const pathname = usePathname() || '';

  const [pincodeData, setPincodeData] = useState<PincodeData | null>(null);
  const [isPincodeModalOpen, setIsPincodeModalOpen] = useState(false);
  const [isMandatory, setIsMandatory] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [hasInitialized, setHasInitialized] = useState(false);
  const [activeMode, setActiveModeInternal] = useState<'hyperlocal' | 'pan_india'>(() => {
    if (typeof window !== 'undefined') {
      return (localStorage.getItem('sj_active_mode') as 'hyperlocal' | 'pan_india') || 'hyperlocal';
    }
    return 'hyperlocal';
  });

  // Exempt routes where store delivery pincode modal should not block user actions
  const isExemptRoute =
    pathname.startsWith('/admin') ||
    pathname.startsWith('/seller-admin') ||
    pathname.startsWith('/valet');

  // Load persisted pincode on initial mount
  useEffect(() => {
    try {
      const savedDataStr = localStorage.getItem(STORAGE_KEY);
      if (savedDataStr) {
        const parsed: PincodeData = JSON.parse(savedDataStr);
        if (parsed && parsed.pincode) {
          setPincodeData(parsed);
          setHasInitialized(true);
          return;
        }
      }
    } catch (e) { logger.warn("Silent catch block:", e); /* Fallback */ }

    // If not stored and not on an exempt admin route, prompt non-dismissable modal
    if (!isExemptRoute) {
      setIsMandatory(true);
      setIsPincodeModalOpen(true);
    }
    setHasInitialized(true);
  }, [isExemptRoute]);

  // If user navigates from an exempt route to a customer route without a pincode, prompt
  useEffect(() => {
    if (hasInitialized && !isExemptRoute && !pincodeData) {
      setIsMandatory(false);  // Never block browsing — just invite the user to set a pincode
      setIsPincodeModalOpen(true);
    }
  }, [pathname, hasInitialized, isExemptRoute, pincodeData]);

  // Sync activeMode to the API-recommended default when pincode data loads or changes
  useEffect(() => {
    if (pincodeData?.defaultMode) {
      setActiveModeInternal(pincodeData.defaultMode);
    }
  }, [pincodeData?.defaultMode]);

  const checkAndSetPincode = useCallback(
    async (
      pin: string,
      role = 'customer'
    ): Promise<{
      success: boolean;
      isServiceable: boolean;
      message?: string;
      data?: PincodeData;
    }> => {
      const cleanPin = (pin || '').toString().replace(/\D/g, '').slice(0, 6);
      if (cleanPin.length !== 6) {
        setError('Please enter a valid 6-digit Indian PIN code.');
        return {
          success: false,
          isServiceable: false,
          message: 'Please enter a valid 6-digit Indian PIN code.',
        };
      }

      setIsLoading(true);
      setError(null);

      try {
        const res = await api.get('/delivery-charges/check-serviceability', {
          params: { pincode: cleanPin, userRole: role },
        });

        const data = res.data || {};
        const isServ = Boolean(data.isServiceable);

        const newPincodeData: PincodeData = {
          pincode: cleanPin,
          city: data.city || null,
          state: data.state || null,
          district: data.district || null,
          isServiceable: isServ,
          sellerCount: data.sellerCount || (data.serviceableSellers ? data.serviceableSellers.length : 0),
          serviceableSellers: data.serviceableSellers || [],
          urgentDeliveryAvailable: Boolean(data.urgentDeliveryAvailable),
          slotBookingAvailable: Boolean(data.slotBookingAvailable),
          showSellerCount: data.showSellerCount !== false, // default true; false only when API explicitly says so
          zoneCustomerType: data.zoneCustomerType || 'retail',
          hasZone: Boolean(data.hasZone),
          hasPanIndia: Boolean(data.hasPanIndia),
          allowedModes: data.allowedModes || (data.hasZone ? ['hyperlocal'] : ['pan_india']),
          defaultMode: data.defaultMode || (data.hasZone ? 'hyperlocal' : 'pan_india'),
        };

        if (isServ) {
          setPincodeData(newPincodeData);
          localStorage.setItem(STORAGE_KEY, JSON.stringify(newPincodeData));
          localStorage.setItem(PINCODE_ONLY_KEY, cleanPin);
          setIsMandatory(false);  // Immediately lift the blur gate so page starts revealing
          setError(null);
          // Keep modal up briefly so the success card animates while the page reveals behind it
          setTimeout(() => setIsPincodeModalOpen(false), 900);
          return { success: true, isServiceable: true, data: newPincodeData };
        } else {
          // Unmapped pincode — store the data so user can browse, but note it's not serviceable
          setPincodeData(newPincodeData);
          localStorage.setItem(STORAGE_KEY, JSON.stringify(newPincodeData));
          localStorage.setItem(PINCODE_ONLY_KEY, cleanPin);
          setIsMandatory(false);  // Never block browsing for unmapped pincodes
          setTimeout(() => setIsPincodeModalOpen(false), 900);
          const errMsg = `Delivery is not yet available to PIN ${cleanPin}. You can browse our catalog.`;
          setError(errMsg);
          return { success: true, isServiceable: false, message: errMsg, data: newPincodeData };
        }
      } catch (err: any) {
        const fallbackMsg =
          err?.response?.data?.detail || 'Unable to check pincode serviceability. Please try again.';
        setError(fallbackMsg);
        return { success: false, isServiceable: false, message: fallbackMsg };
      } finally {
        setIsLoading(false);
      }
    },
    []
  );

  const setActiveMode = useCallback((mode: 'hyperlocal' | 'pan_india') => {
    setActiveModeInternal(mode);
    if (typeof window !== 'undefined') {
      localStorage.setItem('sj_active_mode', mode);
    }
  }, []);

  const openPincodeModal = useCallback((mandatory = false) => {
    setIsMandatory(mandatory);
    setError(null);
    setIsPincodeModalOpen(true);
  }, []);

  const closePincodeModal = useCallback(() => {
    // Allow dismissal in all cases — unmapped users should be able to browse freely
    setIsPincodeModalOpen(false);
    setError(null);
  }, []);

  const clearPincode = useCallback(() => {
    setPincodeData(null);
    localStorage.removeItem(STORAGE_KEY);
    localStorage.removeItem(PINCODE_ONLY_KEY);
    if (!isExemptRoute) {
      setIsMandatory(true);
      setIsPincodeModalOpen(true);
    }
  }, [isExemptRoute]);

  const value: PincodeContextType = {
    pincode: pincodeData?.pincode || null,
    city: pincodeData?.city || null,
    state: pincodeData?.state || null,
    district: pincodeData?.district || null,
    isServiceable: pincodeData ? pincodeData.isServiceable : null,
    sellerCount: pincodeData?.sellerCount || 0,
    serviceableSellers: pincodeData?.serviceableSellers || [],
    pincodeData,
    isPincodeModalOpen,
    isMandatory,
    isLoading,
    error,
    checkAndSetPincode,
    openPincodeModal,
    closePincodeModal,
    clearPincode,
    activeMode,
    availableModes: pincodeData?.allowedModes || (pincodeData?.hasZone ? ['hyperlocal'] : pincodeData?.hasPanIndia ? ['pan_india'] : []),
    setActiveMode,
  };

  return <PincodeContext.Provider value={value}>{children}</PincodeContext.Provider>;
};

export const usePincode = (): PincodeContextType => {
  const context = useContext(PincodeContext);
  if (!context) {
    throw new Error('usePincode must be used within a PincodeProvider');
  }
  return context;
};

export default PincodeContext;
