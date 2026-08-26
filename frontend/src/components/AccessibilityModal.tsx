'use client';

import React from 'react';
import AccessibilityPanel from './AccessibilityPanel';
import { useTheme } from '@/context/ThemeContext';

interface AccessibilityModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export default function AccessibilityModal({ isOpen, onClose }: AccessibilityModalProps) {
  const { theme } = useTheme();

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-[10000] flex animate-fade-in items-center justify-center bg-black/60 px-4 backdrop-blur-sm">
      <div
        className="animate-scale-up w-full max-w-sm transform overflow-hidden rounded-3xl bg-white shadow-2xl transition-all"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="relative">
          <div className="h-2 w-full" style={{ backgroundColor: theme.primary }} />
          <button
            onClick={onClose}
            className="absolute right-4 top-4 rounded-full p-2 text-gray-400 transition-all hover:bg-gray-100 hover:text-gray-600 z-10"
          >
            <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M6 18L18 6M6 6l12 12"
              />
            </svg>
          </button>

          <div className="p-6 pt-10">
            <AccessibilityPanel />
          </div>
        </div>
      </div>
    </div>
  );
}
