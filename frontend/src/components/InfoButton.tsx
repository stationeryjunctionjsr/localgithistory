'use client';

import { useState } from 'react';

interface InfoButtonProps {
  info?: string | null;
  position?: 'top' | 'bottom' | 'left' | 'right';
  children?: React.ReactNode;
  forceTooltip?: boolean;
}

export default function InfoButton({
  info,
  position = 'top',
  children,
  forceTooltip = false,
}: InfoButtonProps) {
  const [showTooltip, setShowTooltip] = useState(false);
  const [showModal, setShowModal] = useState(false);
  const [tooltipPos, setTooltipPos] = useState({ top: 0, left: 0 });

  const handleClick = (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (!info) return;
    if (info.length > 100 && !forceTooltip) {
      setShowModal(true);
    } else {
      setShowTooltip(!showTooltip);
    }
  };

  const tooltipClasses = `fixed z-[99999] bg-gray-800 text-white px-3 py-2 rounded text-xs max-w-[250px] whitespace-normal leading-relaxed shadow-xl pointer-events-none normal-case font-normal`;

  if (!info && !children) return null;

  // If there are children, wrap them
  if (children) {
    if (!info) {
      return <>{children}</>;
    }

    return (
      <span
        className="group relative inline-block cursor-help"
        onMouseEnter={(e) => {
          if (info.length <= 100 || forceTooltip) {
            const rect = e.currentTarget.getBoundingClientRect();
            setTooltipPos({
              top: position === 'top' ? rect.top - 10 : rect.bottom + 10,
              left: rect.left + rect.width / 2,
            });
            setShowTooltip(true);
          }
        }}
        onMouseLeave={() => setShowTooltip(false)}
        onClick={(e) => {
          if (info.length > 100 && !forceTooltip) {
            e.preventDefault();
            e.stopPropagation();
            setShowModal(true);
          }
        }}
      >
        <span className="border-b-[1.5px] border-dotted border-gray-400">{children}</span>

        {showTooltip && (info.length <= 100 || forceTooltip) && (
          <div
            className={tooltipClasses}
            style={{
              top: `${tooltipPos.top}px`,
              left: `${tooltipPos.left}px`,
              transform: 'translate(-50%, -100%)',
              marginTop: position === 'top' ? '-10px' : '10px',
            }}
          >
            {info}
            <div
              className={`absolute left-1/2 h-0 w-0 -translate-x-1/2 transform ${
                position === 'top'
                  ? 'top-full border-l-4 border-r-4 border-t-4 border-l-transparent border-r-transparent border-t-gray-800'
                  : 'bottom-full border-b-4 border-l-4 border-r-4 border-b-gray-800 border-l-transparent border-r-transparent'
              }`}
            />
          </div>
        )}

        {showModal && !forceTooltip && (
          <div
            className="fixed inset-0 z-50 flex cursor-auto items-center justify-center bg-black bg-opacity-50"
            onClick={(e) => {
              e.stopPropagation();
              setShowModal(false);
            }}
          >
            <div
              className="relative max-h-[80vh] max-w-md overflow-y-auto rounded-lg bg-white p-6"
              onClick={(e) => e.stopPropagation()}
            >
              <button
                type="button"
                onClick={(e) => {
                  e.stopPropagation();
                  setShowModal(false);
                }}
                className="absolute right-2 top-2 text-2xl leading-none text-gray-500 hover:text-gray-700"
              >
                ×
              </button>
              <h3 className="mb-4 mt-0 text-lg font-normal normal-case">Information</h3>
              <p className="m-0 whitespace-pre-wrap font-normal normal-case leading-relaxed text-gray-700">
                {info}
              </p>
            </div>
          </div>
        )}
      </span>
    );
  }

  // Backup behavior in case there is no children (self closing tag)
  return (
    <>
      <button
        type="button"
        onClick={handleClick}
        onMouseEnter={(e) => {
          if (info && (info.length <= 100 || forceTooltip)) {
            const rect = e.currentTarget.getBoundingClientRect();
            setTooltipPos({
              top: position === 'top' ? rect.top - 10 : rect.bottom + 10,
              left: rect.left + rect.width / 2,
            });
            setShowTooltip(true);
          }
        }}
        onMouseLeave={() => setShowTooltip(false)}
        className="relative z-10 ml-1 inline-flex cursor-pointer items-center justify-center text-gray-500 opacity-70 transition-opacity hover:text-gray-700 hover:opacity-100"
        title=""
      >
        <span className="inline-flex h-3.5 w-3.5 items-center justify-center rounded-full bg-gray-400 text-[9px] font-bold italic text-white shadow-sm transition-colors hover:bg-gray-500">
          i
        </span>
      </button>

      {showTooltip && info && (info.length <= 100 || forceTooltip) && (
        <div
          className={tooltipClasses}
          style={{
            top: `${tooltipPos.top}px`,
            left: `${tooltipPos.left}px`,
            transform: 'translate(-50%, -100%)',
            marginTop: position === 'top' ? '-10px' : '10px',
          }}
        >
          {info}
          <div
            className={`absolute left-1/2 h-0 w-0 -translate-x-1/2 transform ${
              position === 'top'
                ? 'top-full border-l-4 border-r-4 border-t-4 border-l-transparent border-r-transparent border-t-gray-800'
                : 'bottom-full border-b-4 border-l-4 border-r-4 border-b-gray-800 border-l-transparent border-r-transparent'
            }`}
          />
        </div>
      )}

      {showModal && !forceTooltip && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50"
          onClick={() => setShowModal(false)}
        >
          <div
            className="relative max-h-[80vh] max-w-md overflow-y-auto rounded-lg bg-white p-6"
            onClick={(e) => e.stopPropagation()}
          >
            <button
              type="button"
              onClick={() => setShowModal(false)}
              className="absolute right-2 top-2 text-2xl leading-none text-gray-500 hover:text-gray-700"
            >
              ×
            </button>
            <h3 className="mb-4 mt-0 text-lg font-normal normal-case">Information</h3>
            <p className="m-0 whitespace-pre-wrap font-normal normal-case leading-relaxed text-gray-700">
              {info}
            </p>
          </div>
        </div>
      )}
    </>
  );
}
