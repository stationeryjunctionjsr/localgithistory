'use client';

import React, { useState, useEffect, useRef } from 'react';
import { usePincode } from '@/context/PincodeContext';
import { useAuth } from '@/context/AuthContext';

export default function PincodeModal() {
  const {
    isPincodeModalOpen,
    isMandatory,
    pincode: currentPincode,
    city: currentCity,
    state: currentState,
    sellerCount,
    isLoading,
    error,
    checkAndSetPincode,
    closePincodeModal,
  } = usePincode();

  const { user } = useAuth();
  const [enteredPin, setEnteredPin] = useState('');
  const [localError, setLocalError] = useState<string | null>(null);
  const [successInfo, setSuccessInfo] = useState<{
    city?: string | null;
    state?: string | null;
    sellerCount?: number;
    pincode?: string;
  } | null>(null);

  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (isPincodeModalOpen) {
      setEnteredPin(currentPincode || '');
      setLocalError(null);
      setSuccessInfo(null);
      // Auto-focus input when modal opens
      setTimeout(() => {
        inputRef.current?.focus();
      }, 100);

      // Lock body scroll
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = 'unset';
    }

    return () => {
      document.body.style.overflow = 'unset';
    };
  }, [isPincodeModalOpen, currentPincode]);

  if (!isPincodeModalOpen) return null;

  const handleSubmit = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    setLocalError(null);
    setSuccessInfo(null);

    const clean = enteredPin.replace(/\D/g, '').slice(0, 6);
    if (clean.length !== 6) {
      setLocalError('Please enter a valid 6-digit Indian PIN code.');
      return;
    }

    const role = (user as any)?.role || 'customer';
    const result = await checkAndSetPincode(clean, role);

    if (result.success && result.isServiceable) {
      setSuccessInfo({
        city: result.data?.city,
        state: result.data?.state,
        sellerCount: result.data?.sellerCount,
        pincode: clean,
      });
    } else {
      setLocalError(
        result.message ||
          `Sorry, we do not currently service pincode ${clean}. Please try a different pincode.`
      );
    }
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const val = e.target.value.replace(/\D/g, '').slice(0, 6);
    setEnteredPin(val);
    setLocalError(null);
    setSuccessInfo(null);
  };

  return (
    <div
      className="fixed inset-0 z-[9999] flex items-center justify-center bg-black/70 p-4 backdrop-blur-sm animate-fade-in"
      onClick={() => {
        if (!isMandatory) {
          closePincodeModal();
        }
      }}
      role="dialog"
      aria-modal="true"
      aria-labelledby="pincode-modal-title"
    >
      <div
        className="relative w-full max-w-md overflow-hidden rounded-2xl bg-white shadow-2xl transition-all animate-scale-up"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Top Decorative Header Accent */}
        <div className="h-2 w-full bg-gradient-to-r from-emerald-600 via-teal-500 to-emerald-700" />

        {/* Close button (only visible when voluntary / already set) */}
        {!isMandatory && currentPincode && (
          <button
            onClick={closePincodeModal}
            className="absolute right-4 top-5 z-10 flex h-8 w-8 items-center justify-center rounded-full bg-gray-100 text-gray-400 hover:bg-gray-200 hover:text-gray-700 transition-colors"
            aria-label="Close modal"
          >
            <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        )}

        <div className="p-6 sm:p-8">
          {/* Header Icon & Title */}
          <div className="flex flex-col items-center text-center">
            <div className="mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-emerald-50 text-emerald-700 ring-8 ring-emerald-50/50">
              <svg className="h-8 w-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={1.8}
                  d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z"
                />
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={1.8}
                  d="M15 11a3 3 0 11-6 0 3 3 0 016 0z"
                />
              </svg>
            </div>

            <h2 id="pincode-modal-title" className="text-xl sm:text-2xl font-bold tracking-tight text-gray-900">
              {isMandatory ? 'Select Delivery Location' : 'Change Delivery Location'}
            </h2>
            <p className="mt-1.5 text-xs sm:text-sm text-gray-500 leading-relaxed max-w-sm">
              We operate hyperlocally to deliver the freshest deals and fastest service from local sellers. Please enter your 6-digit PIN code.
            </p>
          </div>

          {/* Form */}
          <form onSubmit={handleSubmit} className="mt-6 space-y-4">
            <div>
              <label htmlFor="pincode-input" className="block text-xs font-semibold uppercase tracking-wider text-gray-600 mb-1.5">
                Delivery Pincode <span className="text-red-500">*</span>
              </label>
              <div className="relative">
                <input
                  ref={inputRef}
                  id="pincode-input"
                  type="text"
                  inputMode="numeric"
                  pattern="[0-9]*"
                  maxLength={6}
                  value={enteredPin}
                  onChange={handleInputChange}
                  placeholder="e.g. 831001"
                  className="w-full rounded-xl border border-gray-300 px-4 py-3.5 text-center text-2xl font-bold tracking-[0.25em] text-gray-900 placeholder:text-gray-300 placeholder:tracking-normal focus:border-emerald-600 focus:outline-none focus:ring-4 focus:ring-emerald-500/10 transition-all"
                  autoComplete="postal-code"
                />
                {enteredPin.length > 0 && (
                  <button
                    type="button"
                    onClick={() => {
                      setEnteredPin('');
                      setLocalError(null);
                      inputRef.current?.focus();
                    }}
                    className="absolute right-3 top-1/2 -translate-y-1/2 rounded-full p-1 text-gray-400 hover:text-gray-600"
                  >
                    <svg className="h-4 w-4" fill="currentColor" viewBox="0 0 20 20">
                      <path
                        fillRule="evenodd"
                        d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
                        clipRule="evenodd"
                      />
                    </svg>
                  </button>
                )}
              </div>
            </div>

            {/* Error Message */}
            {(localError || error) && (
              <div className="rounded-xl bg-red-50 p-3.5 border border-red-200/80 animate-shake">
                <div className="flex items-start gap-2.5 text-xs text-red-700">
                  <svg className="h-4 w-4 shrink-0 text-red-500 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  <div className="flex-1 font-medium leading-relaxed">
                    {localError || error}
                  </div>
                </div>
              </div>
            )}

            {/* Success Card */}
            {successInfo && (
              <div className="rounded-xl bg-emerald-50 p-3.5 border border-emerald-200 animate-fade-in">
                <div className="flex items-center gap-2.5 text-xs text-emerald-800 font-medium">
                  <svg className="h-5 w-5 text-emerald-600 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  <div>
                    <span className="font-bold">Serviceable Area: </span>
                    {successInfo.city || successInfo.state
                      ? `${successInfo.city || ''}${successInfo.city && successInfo.state ? ', ' : ''}${successInfo.state || ''} (${successInfo.pincode})`
                      : `PIN Code ${successInfo.pincode}`}
                    <div className="text-[11px] text-emerald-700 mt-0.5">
                      {successInfo.sellerCount && successInfo.sellerCount > 0
                        ? `🎉 ${successInfo.sellerCount} seller(s) available in your location!`
                        : '🎉 Platform delivery available to your location!'}
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Submit Button */}
            <button
              type="submit"
              disabled={isLoading || enteredPin.length !== 6}
              className="w-full flex items-center justify-center gap-2 rounded-xl bg-emerald-800 py-3.5 px-4 text-sm font-bold text-white shadow-lg shadow-emerald-900/20 hover:bg-emerald-900 disabled:opacity-50 disabled:cursor-not-allowed transition-all active:scale-[0.98]"
            >
              {isLoading ? (
                <>
                  <svg className="h-4 w-4 animate-spin text-white" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v4l3-3-3-3V4a10 10 0 100 20v-4l-3 3 3 3v-4a8 8 0 01-8-8z" />
                  </svg>
                  <span>Checking Serviceability...</span>
                </>
              ) : (
                <span>Check & Continue</span>
              )}
            </button>
          </form>

          {/* Current location if set */}
          {currentPincode && !isMandatory && (
            <div className="mt-4 text-center">
              <span className="text-[11px] text-gray-500">
                Currently delivering to:{' '}
                <span className="font-semibold text-gray-700">
                  {currentCity ? `${currentCity} (${currentPincode})` : currentPincode}
                </span>
              </span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
