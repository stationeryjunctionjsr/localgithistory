import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import AsyncStorage from '@react-native-async-storage/async-storage';
import api from '../api/client';

export interface ServiceableSeller {
  id: string;
  name: string;
  companyName: string;
  city?: string;
  allowUrgentDelivery?: boolean;
  allowDeliverySlots?: boolean;
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
  isModalOpen: boolean;
  isMandatory: boolean;
  isLoading: boolean;
  error: string | null;
  checkAndSetPincode: (
    pin: string,
    role?: string
  ) => Promise<{ success: boolean; isServiceable: boolean; message?: string; data?: PincodeData }>;
  openModal: (mandatory?: boolean) => void;
  closeModal: () => void;
  clearPincode: () => void;
}

const STORAGE_KEY = '@sj_mobile_pincode_data';

const PincodeContext = createContext<PincodeContextType | undefined>(undefined);

export const PincodeProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [pincodeData, setPincodeData] = useState<PincodeData | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [isMandatory, setIsMandatory] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const loadSavedPincode = async () => {
      try {
        const saved = await AsyncStorage.getItem(STORAGE_KEY);
        if (saved) {
          const parsed: PincodeData = JSON.parse(saved);
          if (parsed && parsed.pincode && parsed.isServiceable) {
            setPincodeData(parsed);
            return;
          }
        }
      } catch {
        // Ignore read errors
      }

      // If no valid serviceable pincode is stored, open non-dismissable modal
      setIsMandatory(true);
      setIsModalOpen(true);
    };

    loadSavedPincode();
  }, []);

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
        const msg = 'Please enter a valid 6-digit PIN code.';
        setError(msg);
        return { success: false, isServiceable: false, message: msg };
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
        };

        if (isServ) {
          setPincodeData(newPincodeData);
          await AsyncStorage.setItem(STORAGE_KEY, JSON.stringify(newPincodeData));
          setIsMandatory(false);
          setIsModalOpen(false);
          setError(null);
          return { success: true, isServiceable: true, data: newPincodeData };
        } else {
          const errMsg = `Delivery is currently not available to pincode ${cleanPin}. Please try another pincode.`;
          setError(errMsg);
          return { success: true, isServiceable: false, message: errMsg, data: newPincodeData };
        }
      } catch (err: any) {
        const fallbackMsg =
          err?.response?.data?.detail || 'Unable to verify pincode serviceability. Please try again.';
        setError(fallbackMsg);
        return { success: false, isServiceable: false, message: fallbackMsg };
      } finally {
        setIsLoading(false);
      }
    },
    []
  );

  const openModal = useCallback((mandatory = false) => {
    setIsMandatory(mandatory);
    setError(null);
    setIsModalOpen(true);
  }, []);

  const closeModal = useCallback(() => {
    if (!isMandatory && pincodeData?.isServiceable) {
      setIsModalOpen(false);
      setError(null);
    }
  }, [isMandatory, pincodeData]);

  const clearPincode = useCallback(async () => {
    setPincodeData(null);
    await AsyncStorage.removeItem(STORAGE_KEY);
    setIsMandatory(true);
    setIsModalOpen(true);
  }, []);

  const value: PincodeContextType = {
    pincode: pincodeData?.pincode || null,
    city: pincodeData?.city || null,
    state: pincodeData?.state || null,
    district: pincodeData?.district || null,
    isServiceable: pincodeData ? pincodeData.isServiceable : null,
    sellerCount: pincodeData?.sellerCount || 0,
    serviceableSellers: pincodeData?.serviceableSellers || [],
    pincodeData,
    isModalOpen,
    isMandatory,
    isLoading,
    error,
    checkAndSetPincode,
    openModal,
    closeModal,
    clearPincode,
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
