import React, { useEffect, useRef, useState } from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  Modal,
  Animated,
  Dimensions,
  StyleSheet,
} from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { colors, shadows } from '../theme';
import { useCoachMarkContext } from '../context/CoachMarkContext';

const { width: SCREEN_WIDTH, height: SCREEN_HEIGHT } = Dimensions.get('window');

interface CoachMarkProps {
  id: string;
  title: string;
  description: string;
  targetPosition?: { x: number; y: number; width: number; height: number };
  onDismiss: () => void;
  onNext?: () => void;
  isLast?: boolean;
}

const STORAGE_KEY = 'coach_marks_shown';

export const useCoachMarks = (markIds: string[]) => {
  const [currentIndex, setCurrentIndex] = useState(-1);
  const [shownMarks, setShownMarks] = useState<Set<string>>(new Set());
  const [isReady, setIsReady] = useState(false);

  useEffect(() => {
    loadShownMarks();
  }, []);

  const loadShownMarks = async () => {
    try {
      const stored = await AsyncStorage.getItem(STORAGE_KEY);
      if (stored) {
        setShownMarks(new Set(JSON.parse(stored)));
      }
      setIsReady(true);
    } catch (e) {
      if (__DEV__) console.warn('[CoachMark] load shown marks failed', e);
      setIsReady(true);
    }
  };

  const startTour = () => {
    const firstUnshown = markIds.findIndex((id) => !shownMarks.has(id));
    if (firstUnshown !== -1) {
      setCurrentIndex(firstUnshown);
    }
  };

  const markAsShown = async (id: string) => {
    const newShown = new Set(shownMarks);
    newShown.add(id);
    setShownMarks(newShown);
    try {
      await AsyncStorage.setItem(STORAGE_KEY, JSON.stringify([...newShown]));
    } catch (e) {
      if (__DEV__) console.warn('[CoachMark] persist mark failed', e);
    }
  };

  const next = () => {
    if (currentIndex >= 0 && currentIndex < markIds.length) {
      markAsShown(markIds[currentIndex]);
    }
    if (currentIndex < markIds.length - 1) {
      setCurrentIndex(currentIndex + 1);
    } else {
      setCurrentIndex(-1);
    }
  };

  const dismiss = () => {
    if (currentIndex >= 0 && currentIndex < markIds.length) {
      markAsShown(markIds[currentIndex]);
    }
    setCurrentIndex(-1);
  };

  const resetAll = async () => {
    setShownMarks(new Set());
    try {
      await AsyncStorage.removeItem(STORAGE_KEY);
    } catch (e) {
      if (__DEV__) console.warn('[CoachMark] reset storage failed', e);
    }
  };

  const currentMarkId = currentIndex >= 0 ? markIds[currentIndex] : null;
  const isActive = currentIndex >= 0;

  return {
    isReady,
    isActive,
    currentMarkId,
    currentIndex,
    totalMarks: markIds.length,
    startTour,
    next,
    dismiss,
    resetAll,
    hasSeenMark: (id: string) => shownMarks.has(id),
  };
};

export const CoachMark: React.FC<CoachMarkProps> = ({
  id,
  title,
  description,
  targetPosition,
  onDismiss,
  onNext,
  isLast = false,
}) => {
  const { anchors } = useCoachMarkContext();
  const fadeAnim = useRef(new Animated.Value(0)).current;
  const scaleAnim = useRef(new Animated.Value(0.9)).current;

  // Prefer anchor layout if available, otherwise fall back to prop
  const layout = anchors[id] || targetPosition;

  useEffect(() => {
    Animated.parallel([
      Animated.timing(fadeAnim, {
        toValue: 1,
        duration: 200,
        useNativeDriver: true,
      }),
      Animated.spring(scaleAnim, {
        toValue: 1,
        friction: 8,
        tension: 100,
        useNativeDriver: true,
      }),
    ]).start();
  }, [fadeAnim, scaleAnim]);

  const tooltipStyle = layout
    ? {
        top: layout.y + layout.height + 12,
        left: Math.max(16, Math.min(layout.x, SCREEN_WIDTH - 280)),
      }
    : {
        top: SCREEN_HEIGHT / 2 - 60,
        left: (SCREEN_WIDTH - 280) / 2,
      };

  return (
    <Modal transparent visible animationType="none">
      <Animated.View style={[styles.overlay, { opacity: fadeAnim }]}>
        {/* Semi-transparent backdrop */}
        <View style={styles.backdrop} />

        {/* Spotlight on target (if position provided) */}
        {layout && (
          <View
            style={[
              styles.spotlight,
              {
                top: layout.y - 8,
                left: layout.x - 8,
                width: layout.width + 16,
                height: layout.height + 16,
                borderRadius: 12,
              },
            ]}
          />
        )}

        {/* Tooltip */}
        <Animated.View
          style={[
            styles.tooltip,
            tooltipStyle,
            {
              transform: [{ scale: scaleAnim }],
            },
          ]}
        >
          <Text style={styles.title}>{title}</Text>
          <Text style={styles.description}>{description}</Text>

          <View style={styles.actions}>
            <TouchableOpacity onPress={onDismiss} style={styles.skipBtn}>
              <Text style={styles.skipText}>Skip</Text>
            </TouchableOpacity>
            <TouchableOpacity onPress={onNext || onDismiss} style={styles.nextBtn}>
              <Text style={styles.nextText}>{isLast ? 'Got it' : 'Next'}</Text>
            </TouchableOpacity>
          </View>
        </Animated.View>
      </Animated.View>
    </Modal>
  );
};

const styles = StyleSheet.create({
  overlay: {
    flex: 1,
    position: 'relative',
  },
  backdrop: {
    ...StyleSheet.absoluteFillObject,
    backgroundColor: 'rgba(0, 0, 0, 0.6)',
  },
  spotlight: {
    position: 'absolute',
    backgroundColor: 'transparent',
    borderWidth: 2,
    borderColor: 'rgba(255, 255, 255, 0.8)',
  },
  tooltip: {
    position: 'absolute',
    width: 280,
    backgroundColor: colors.surface,
    borderRadius: 16,
    padding: 20,
    ...shadows.lg,
  },
  title: {
    fontSize: 17,
    fontWeight: '600',
    color: colors.textPrimary,
    marginBottom: 8,
  },
  description: {
    fontSize: 14,
    color: colors.textSecondary,
    lineHeight: 20,
    marginBottom: 20,
  },
  actions: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  skipBtn: {
    paddingVertical: 8,
    paddingHorizontal: 12,
  },
  skipText: {
    fontSize: 14,
    color: colors.textMuted,
  },
  nextBtn: {
    backgroundColor: colors.accent,
    paddingVertical: 10,
    paddingHorizontal: 20,
    borderRadius: 10,
  },
  nextText: {
    fontSize: 14,
    fontWeight: '600',
    color: colors.textOnAccent,
  },
});

export default CoachMark;
