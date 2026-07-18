import React, { useRef } from 'react';
import { View, ViewProps } from 'react-native';
import { useCoachMarkContext } from '../context/CoachMarkContext';

interface CoachMarkAnchorProps extends ViewProps {
  id: string;
  children: React.ReactNode;
}

export const CoachMarkAnchor: React.FC<CoachMarkAnchorProps> = ({
  id,
  children,
  style,
  ...props
}) => {
  const { registerAnchor } = useCoachMarkContext();
  const viewRef = useRef<View>(null);

  // We need to measure periodically or on layout to get absolute coordinates
  const measure = () => {
    viewRef.current?.measureInWindow((x, y, width, height) => {
      if (width && height) {
        registerAnchor(id, { x, y, width, height });
      }
    });
  };

  return (
    <View
      ref={viewRef}
      collapsable={false} // Important for measurement
      onLayout={measure}
      style={style}
      {...props}
    >
      {children}
    </View>
  );
};
