'use client';

import { usePincode } from '@/context/PincodeContext';

/**
 * ModeSwitchToggle — rendered in the Header and MobileNavBar when a pincode supports
 * both Hyperlocal (zone-based valet delivery) and Pan-India (3PL courier) fulfillment.
 * Only visible when availableModes.length === 2.
 */
export default function ModeSwitchToggle() {
  const { availableModes, activeMode, setActiveMode } = usePincode();

  // Only show when both modes are available for the active pincode
  if (!availableModes.includes('hyperlocal') || !availableModes.includes('pan_india')) {
    return null;
  }

  return (
    <div
      className="flex items-center rounded-full border border-gray-200 bg-white p-0.5 shadow-sm"
      role="group"
      aria-label="Shopping mode"
    >
      <button
        onClick={() => setActiveMode('hyperlocal')}
        aria-pressed={activeMode === 'hyperlocal'}
        className={`flex items-center gap-1.5 rounded-full px-3 py-1 text-xs font-semibold transition-all ${
          activeMode === 'hyperlocal'
            ? 'bg-[#1a4d33] text-white shadow-sm'
            : 'text-gray-500 hover:text-gray-700'
        }`}
      >
        <span className="text-[10px]" aria-hidden="true">🟢</span>
        <span className="hidden sm:inline">Shop for your area</span>
        <span className="sm:hidden">Local</span>
      </button>
      <button
        onClick={() => setActiveMode('pan_india')}
        aria-pressed={activeMode === 'pan_india'}
        className={`flex items-center gap-1.5 rounded-full px-3 py-1 text-xs font-semibold transition-all ${
          activeMode === 'pan_india'
            ? 'bg-blue-600 text-white shadow-sm'
            : 'text-gray-500 hover:text-gray-700'
        }`}
      >
        <span className="text-[10px]" aria-hidden="true">🇮🇳</span>
        <span className="hidden sm:inline">Shop from India</span>
        <span className="sm:hidden">India</span>
      </button>
    </div>
  );
}
