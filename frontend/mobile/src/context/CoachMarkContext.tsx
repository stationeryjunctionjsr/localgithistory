import React, { createContext, useContext, useState, useCallback, ReactNode } from 'react';
import { LayoutRectangle } from 'react-native';

interface AnchorLayout extends LayoutRectangle {
  // We can extend this if we need more info (e.g. scroll offset)
}

interface CoachMarkContextType {
  anchors: Record<string, AnchorLayout>;
  registerAnchor: (id: string, layout: AnchorLayout) => void;
  unregisterAnchor: (id: string) => void;
}

const CoachMarkContext = createContext<CoachMarkContextType | undefined>(undefined);

export const CoachMarkProvider = ({ children }: { children: ReactNode }) => {
  const [anchors, setAnchors] = useState<Record<string, AnchorLayout>>({});

  const registerAnchor = useCallback((id: string, layout: AnchorLayout) => {
    setAnchors((prev) => {
      // Only update if changed to avoid renders
      const existing = prev[id];
      if (
        existing &&
        existing.x === layout.x &&
        existing.y === layout.y &&
        existing.width === layout.width &&
        existing.height === layout.height
      ) {
        return prev;
      }
      return { ...prev, [id]: layout };
    });
  }, []);

  const unregisterAnchor = useCallback((id: string) => {
    setAnchors((prev) => {
      const { [id]: _, ...rest } = prev;
      return rest;
    });
  }, []);

  return (
    <CoachMarkContext.Provider value={{ anchors, registerAnchor, unregisterAnchor }}>
      {children}
    </CoachMarkContext.Provider>
  );
};

export const useCoachMarkContext = () => {
  const context = useContext(CoachMarkContext);
  if (!context) {
    throw new Error('useCoachMarkContext must be used within a CoachMarkProvider');
  }
  return context;
};
