'use client';

import { useState, useEffect } from 'react';

interface CoachMarkStep {
  selector: string;
  title: string;
  content: string;
  position: 'top' | 'bottom' | 'left' | 'right';
}

interface CoachMarksProps {
  steps: CoachMarkStep[];
  onComplete?: () => void;
  onSkip?: () => void;
}

export default function CoachMarks({ steps, onComplete, onSkip }: CoachMarksProps) {
  const [currentStep, setCurrentStep] = useState(0);
  const [targetElement, setTargetElement] = useState<HTMLElement | null>(null);
  const [position, setPosition] = useState({ top: 0, left: 0, width: 0, height: 0 });

  useEffect(() => {
    if (steps && steps.length > 0 && currentStep < steps.length) {
      const step = steps[currentStep];
      const element = document.querySelector(step.selector) as HTMLElement;

      if (element) {
        setTargetElement(element);
        const rect = element.getBoundingClientRect();
        setPosition({
          top: rect.top + window.scrollY,
          left: rect.left + window.scrollX,
          width: rect.width,
          height: rect.height,
        });
      } else {
        if (currentStep < steps.length - 1) {
          setCurrentStep(currentStep + 1);
        } else {
          onComplete?.();
        }
      }
    }
  }, [currentStep, steps, onComplete]);

  if (!steps || steps.length === 0 || currentStep >= steps.length) {
    return null;
  }

  const step = steps[currentStep];
  const tooltipPosition =
    step.position === 'top'
      ? { bottom: window.innerHeight - position.top + 10, left: position.left }
      : step.position === 'bottom'
        ? { top: position.top + position.height + 10, left: position.left }
        : step.position === 'left'
          ? { top: position.top, right: window.innerWidth - position.left + 10 }
          : { top: position.top, left: position.left + position.width + 10 };

  const handleNext = () => {
    if (currentStep < steps.length - 1) {
      setCurrentStep(currentStep + 1);
    } else {
      onComplete?.();
    }
  };

  const handleSkip = () => {
    onSkip?.();
    onComplete?.();
  };

  return (
    <>
      <div className="fixed inset-0 z-[9998] bg-black/70" onClick={handleNext} />
      {targetElement && (
        <div
          className="pointer-events-none fixed z-[9999] rounded border-4 border-blue-500 shadow-lg"
          style={{
            top: position.top,
            left: position.left,
            width: position.width,
            height: position.height,
            boxShadow: '0 0 0 9999px rgba(0, 0, 0, 0.7)',
          }}
        />
      )}
      <div
        className="fixed z-[10000] max-w-[350px] rounded-lg bg-white p-5 shadow-xl"
        style={tooltipPosition}
      >
        <div className="mb-2.5">
          <strong className="mb-2 block text-base">{step.title}</strong>
          <p className="m-0 leading-relaxed text-gray-600">{step.content}</p>
        </div>
        <div className="mt-4 flex items-center justify-between">
          <button
            type="button"
            onClick={handleSkip}
            className="cursor-pointer border-none bg-transparent px-2.5 py-1.5 text-gray-600 hover:text-gray-800"
          >
            Skip
          </button>
          <div className="flex items-center gap-2">
            <span className="text-xs leading-7 text-gray-400">
              {currentStep + 1} of {steps.length}
            </span>
            <button
              type="button"
              onClick={handleNext}
              className="cursor-pointer rounded border-none bg-blue-500 px-4 py-1.5 text-white hover:bg-blue-600"
            >
              {currentStep < steps.length - 1 ? 'Next' : 'Got it'}
            </button>
          </div>
        </div>
      </div>
    </>
  );
}
