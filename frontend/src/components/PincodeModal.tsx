'use client';

import React, { useState, useEffect, useRef } from 'react';
import { usePincode } from '@/context/PincodeContext';
import { useAuth } from '@/context/AuthContext';

/* ─── Floating stationery silhouette ─────────────────────────────────────── */
function FloatingDecor({
  className,
  driftClass,
  children,
}: {
  className: string;
  driftClass: string;
  children: React.ReactNode;
}) {
  return (
    <div
      className={`pointer-events-none absolute text-white/[0.06] ${driftClass} ${className}`}
      aria-hidden
    >
      {children}
    </div>
  );
}

/* ─── SVG icon helpers ────────────────────────────────────────────────────── */
const PencilIcon = () => (
  <svg viewBox="0 0 24 24" fill="currentColor" className="h-full w-full">
    <path d="M3 17.25V21h3.75L17.81 9.94l-3.75-3.75L3 17.25zM20.71 7.04a1 1 0 000-1.41l-2.34-2.34a1 1 0 00-1.41 0l-1.83 1.83 3.75 3.75 1.83-1.83z" />
  </svg>
);

const NotebookIcon = () => (
  <svg viewBox="0 0 24 24" fill="currentColor" className="h-full w-full">
    <path d="M18 2H6c-1.1 0-2 .9-2 2v16c0 1.1.9 2 2 2h12c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zm0 18H6V4h2v8l2.5-1.5L13 12V4h5v16z" />
  </svg>
);

const RulerIcon = () => (
  <svg viewBox="0 0 24 24" fill="currentColor" className="h-full w-full">
    <path d="M21.71 3.29l-1-1c-.39-.39-1.02-.39-1.41 0L2.29 19.29c-.39.39-.39 1.02 0 1.41l1 1c.39.39 1.02.39 1.41 0L21.71 4.71c.39-.39.39-1.02 0-1.42zM5.5 15.5l1-1 1.5 1.5-1 1-1.5-1.5zm3-3l1-1 1.5 1.5-1 1-1.5-1.5zm3-3l1-1 1.5 1.5-1 1-1.5-1.5zm3-3l1-1 1.5 1.5-1 1-1.5-1.5z" />
  </svg>
);

const StarIcon = () => (
  <svg viewBox="0 0 24 24" fill="currentColor" className="h-full w-full">
    <path d="M12 1L9.5 8.5H2l6 4.5-2.3 7.5L12 16l6.3 4.5L16 12.9l6-4.5H14.5L12 1z" />
  </svg>
);

const ScissorsIcon = () => (
  <svg viewBox="0 0 24 24" fill="currentColor" className="h-full w-full">
    <path d="M9.64 7.64c.23-.5.36-1.05.36-1.64 0-2.21-1.79-4-4-4S2 3.79 2 6s1.79 4 4 4c.59 0 1.14-.13 1.64-.36L10 12l-2.36 2.36C7.14 14.13 6.59 14 6 14c-2.21 0-4 1.79-4 4s1.79 4 4 4 4-1.79 4-4c0-.59-.13-1.14-.36-1.64L12 14l7 7h3v-1L9.64 7.64zM6 8c-1.1 0-2-.89-2-2s.9-2 2-2 2 .89 2 2-.9 2-2 2zm0 12c-1.1 0-2-.89-2-2s.9-2 2-2 2 .89 2 2-.9 2-2 2zm6-7.5c-.28 0-.5-.22-.5-.5s.22-.5.5-.5.5.22.5.5-.22.5-.5.5zM19 3l-6 6 2 2 7-7V3h-3z" />
  </svg>
);

/* ─── Trust feature item ──────────────────────────────────────────────────── */
function TrustItem({ icon, label }: { icon: React.ReactNode; label: string }) {
  return (
    <div className="flex items-center gap-1.5 text-[11px] font-medium text-white/40">
      <span className="text-white/30">{icon}</span>
      <span>{label}</span>
    </div>
  );
}

/* ═══════════════════════════════════════════════════════════════════════════ */
export default function PincodeModal() {
  const {
    isPincodeModalOpen,
    isMandatory,
    pincode: currentPincode,
    city: currentCity,
    isLoading,
    error,
    checkAndSetPincode,
    closePincodeModal,
  } = usePincode();

  const { user } = useAuth();
  const isWholesaler = (user as any)?.role === 'wholesaler';

  const [enteredPin, setEnteredPin] = useState('');
  const [localError, setLocalError] = useState<string | null>(null);
  const [successInfo, setSuccessInfo] = useState<{
    city?: string | null;
    state?: string | null;
    pincode?: string;
  } | null>(null);

  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (isPincodeModalOpen) {
      setEnteredPin(currentPincode || '');
      setLocalError(null);
      setSuccessInfo(null);
      setTimeout(() => inputRef.current?.focus(), 120);
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = 'unset';
    }
    return () => { document.body.style.overflow = 'unset'; };
  }, [isPincodeModalOpen, currentPincode]);

  if (!isPincodeModalOpen) return null;

  /* ── handlers ─────────────────────────────────────────────────────────── */
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
        pincode: clean,
      });
    } else {
      setLocalError(
        result.message ||
          `Sorry, we don't service pincode ${clean} yet. Please try a different one.`
      );
    }
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const val = e.target.value.replace(/\D/g, '').slice(0, 6);
    setEnteredPin(val);
    setLocalError(null);
    setSuccessInfo(null);
  };

  /* ── render ───────────────────────────────────────────────────────────── */
  return (
    <div
      className="fixed inset-0 z-[9999] overflow-hidden"
      role="dialog"
      aria-modal="true"
      aria-labelledby="pincode-modal-title"
    >
      {/* ── Branded full-screen backdrop ────────────────────────────────── */}
      <div
        className="absolute inset-0 animate-fade-in"
        style={{
          background:
            'linear-gradient(150deg, #051209 0%, #0d2b1d 28%, #1a4d33 55%, #0d2b1d 78%, #051209 100%)',
        }}
        onClick={() => { if (!isMandatory) closePincodeModal(); }}
      />

      {/* ── Ambient glowing orbs (depth) ────────────────────────────────── */}
      <div className="pointer-events-none absolute inset-0 overflow-hidden" aria-hidden>
        {/* top-left emerald bloom */}
        <div className="absolute -left-32 -top-32 h-[480px] w-[480px] rounded-full bg-emerald-500/20 blur-3xl" />
        {/* right-center gold accent */}
        <div className="absolute -right-20 top-1/3 h-80 w-80 rounded-full bg-[#D4AF37]/12 blur-3xl" />
        {/* bottom emerald glow */}
        <div className="absolute -bottom-16 left-1/3 h-96 w-96 rounded-full bg-emerald-700/20 blur-3xl" />
        {/* near-modal warm accent */}
        <div className="absolute left-1/2 top-1/2 h-[600px] w-[600px] -translate-x-1/2 -translate-y-1/2 rounded-full bg-emerald-400/[0.07] blur-3xl" />

        {/* Dot-grid texture */}
        <div
          className="absolute inset-0 opacity-[0.045]"
          style={{
            backgroundImage: 'radial-gradient(circle, #ffffff 1px, transparent 1px)',
            backgroundSize: '28px 28px',
          }}
        />
      </div>

      {/* ── Floating stationery silhouettes ─────────────────────────────── */}
      {/* Pencil — top right */}
      <FloatingDecor className="right-12 top-12 h-28 w-28 rotate-[-22deg]" driftClass="animate-drift-1">
        <PencilIcon />
      </FloatingDecor>

      {/* Notebook — top left */}
      <FloatingDecor className="left-10 top-16 h-24 w-24 rotate-[18deg]" driftClass="animate-drift-2">
        <NotebookIcon />
      </FloatingDecor>

      {/* Ruler — bottom right */}
      <FloatingDecor className="bottom-20 right-14 h-28 w-28 rotate-[-40deg]" driftClass="animate-drift-3">
        <RulerIcon />
      </FloatingDecor>

      {/* Scissors — bottom left */}
      <FloatingDecor className="bottom-16 left-16 h-20 w-20 rotate-[25deg]" driftClass="animate-drift-1">
        <ScissorsIcon />
      </FloatingDecor>

      {/* Star — mid left */}
      <FloatingDecor className="left-6 top-1/2 h-14 w-14 -translate-y-1/2 rotate-[10deg]" driftClass="animate-drift-2">
        <StarIcon />
      </FloatingDecor>

      {/* Star — mid right */}
      <FloatingDecor className="right-8 top-1/2 h-10 w-10 translate-y-8" driftClass="animate-drift-3">
        <StarIcon />
      </FloatingDecor>

      {/* ── Main column ─────────────────────────────────────────────────── */}
      <div className="relative flex h-full flex-col items-center justify-center px-4 py-8">

        {/* Brand header */}
        <div
          className="mb-7 text-center animate-fade-in"
          style={{ animationDelay: '120ms', animationFillMode: 'both' }}
        >
          {/* Logo mark */}
          <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-white/10 ring-1 ring-white/20 backdrop-blur-sm">
            <svg className="h-8 w-8 text-[#D4AF37]" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.6}
                d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.6}
                d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
            </svg>
          </div>
          <p className="mb-0.5 text-[10px] font-bold uppercase tracking-[0.35em] text-[#D4AF37]">
            Welcome to
          </p>
          <h1 className="text-2xl font-extrabold tracking-tight text-white sm:text-3xl">
            Stationery Junction
          </h1>
          <p className="mt-1.5 text-xs text-white/45">
            Premium stationery · delivered hyperlocally
          </p>
        </div>

        {/* ── Modal card ──────────────────────────────────────────────────── */}
        <div
          className="relative w-full max-w-sm overflow-hidden rounded-2xl bg-white shadow-2xl shadow-black/50 animate-scale-up"
          onClick={(e) => e.stopPropagation()}
        >
          {/* Gradient top accent bar */}
          <div className="h-1.5 w-full bg-gradient-to-r from-emerald-700 via-[#D4AF37] to-emerald-700" />

          {/* Close button — only when voluntary + pin already set + not in success flow */}
          {!isMandatory && currentPincode && !successInfo && (
            <button
              onClick={closePincodeModal}
              className="absolute right-4 top-5 z-10 flex h-8 w-8 items-center justify-center rounded-full bg-gray-100 text-gray-400 transition-colors hover:bg-gray-200 hover:text-gray-700"
              aria-label="Close"
            >
              <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          )}

          <div className="p-6 sm:p-7">
            {/* Card header */}
            <div className="flex flex-col items-center text-center">
              <div className="mb-3.5 flex h-13 w-13 items-center justify-center rounded-full bg-emerald-50 text-emerald-700 ring-8 ring-emerald-50/50">
                <svg className="h-7 w-7" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.8}
                    d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.8}
                    d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
                </svg>
              </div>
              <h2
                id="pincode-modal-title"
                className="text-lg font-bold tracking-tight text-gray-900 sm:text-xl"
              >
                {isMandatory ? 'Select Your Delivery Location' : 'Change Delivery Location'}
              </h2>
              <p className="mt-1.5 max-w-xs text-xs leading-relaxed text-gray-500 sm:text-sm">
                {isWholesaler
                  ? 'Enter your 6-digit PIN code to confirm serviceability to your business location.'
                  : 'We deliver hyperlocally from nearby sellers. Enter your PIN code to discover what\'s available near you.'}
              </p>
            </div>

            {/* Form */}
            <form onSubmit={handleSubmit} className="mt-5 space-y-3.5" noValidate>

              {/* PIN input */}
              <div>
                <label
                  htmlFor="pincode-input"
                  className="mb-1.5 block text-[10px] font-bold uppercase tracking-wider text-gray-500"
                >
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
                    className="w-full rounded-xl border border-gray-200 px-4 py-3.5 text-center text-2xl font-bold tracking-[0.28em] text-gray-900 placeholder:text-gray-300 placeholder:tracking-normal transition-all focus:border-emerald-600 focus:outline-none focus:ring-4 focus:ring-emerald-500/10"
                    autoComplete="postal-code"
                  />
                  {enteredPin.length > 0 && (
                    <button
                      type="button"
                      onClick={() => { setEnteredPin(''); setLocalError(null); inputRef.current?.focus(); }}
                      className="absolute right-3 top-1/2 -translate-y-1/2 rounded-full p-1 text-gray-400 hover:text-gray-600"
                      aria-label="Clear"
                    >
                      <svg className="h-4 w-4" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                      </svg>
                    </button>
                  )}
                </div>

                {/* 6-segment progress bar */}
                <div className="mt-2 flex gap-1">
                  {[...Array(6)].map((_, i) => (
                    <div
                      key={i}
                      className={`h-[3px] flex-1 rounded-full transition-all duration-200 ${
                        i < enteredPin.length ? 'bg-emerald-600' : 'bg-gray-100'
                      }`}
                    />
                  ))}
                </div>
              </div>

              {/* Error message */}
              {(localError || error) && (
                <div key={localError || error} className="animate-shake rounded-xl border border-red-200/80 bg-red-50 p-3">
                  <div className="flex items-start gap-2 text-xs text-red-700">
                    <svg className="mt-0.5 h-4 w-4 shrink-0 text-red-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                        d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    <span className="font-medium leading-relaxed">{localError || error}</span>
                  </div>
                </div>
              )}

              {/* Success card */}
              {successInfo && (
                <div className="animate-fade-in rounded-xl border border-emerald-200 bg-emerald-50 p-3.5">
                  <div className="flex items-center gap-2.5 text-xs font-medium text-emerald-800">
                    <svg className="h-5 w-5 shrink-0 text-emerald-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    <div>
                      <span className="font-bold">Confirmed! </span>
                      {successInfo.city || successInfo.state
                        ? `Delivering to ${[successInfo.city, successInfo.state].filter(Boolean).join(', ')} (${successInfo.pincode})`
                        : `Delivering to PIN ${successInfo.pincode}`}
                    </div>
                  </div>
                </div>
              )}

              {/* Submit button */}
              <button
                type="submit"
                disabled={isLoading || enteredPin.length !== 6}
                className="w-full flex items-center justify-center gap-2 rounded-xl bg-emerald-800 px-4 py-3.5 text-sm font-bold text-white shadow-lg shadow-emerald-900/20 transition-all hover:bg-emerald-900 active:scale-[0.98] disabled:cursor-not-allowed disabled:opacity-50"
              >
                {isLoading ? (
                  <>
                    <svg className="h-4 w-4 animate-spin" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v4l3-3-3-3V4a10 10 0 100 20v-4l-3 3 3 3v-4a8 8 0 01-8-8z" />
                    </svg>
                    <span>Checking Serviceability…</span>
                  </>
                ) : (
                  <span>Check &amp; Continue →</span>
                )}
              </button>
            </form>

            {/* Current location reminder (voluntary mode) */}
            {currentPincode && !isMandatory && (
              <p className="mt-4 text-center text-[11px] text-gray-400">
                Currently delivering to{' '}
                <span className="font-semibold text-gray-600">
                  {currentCity ? `${currentCity} (${currentPincode})` : currentPincode}
                </span>
              </p>
            )}
          </div>
        </div>

        {/* ── Trust / feature strip ────────────────────────────────────────── */}
        <div
          className="mt-7 flex items-center gap-4 sm:gap-5 animate-fade-in"
          style={{ animationDelay: '280ms', animationFillMode: 'both' }}
        >
          <TrustItem
            label="Hyperlocal delivery"
            icon={
              <svg className="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                  d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
              </svg>
            }
          />
          <div className="h-3 w-px bg-white/15" />
          <TrustItem
            label="Local sellers"
            icon={
              <svg className="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                  d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0z" />
              </svg>
            }
          />
          <div className="h-3 w-px bg-white/15" />
          <TrustItem
            label="Fast service"
            icon={
              <svg className="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                  d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
            }
          />
        </div>

      </div>
    </div>
  );
}
