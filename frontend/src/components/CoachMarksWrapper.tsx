'use client';

import { useState, useEffect } from 'react';
import { useAuth } from '@/context/AuthContext';
import { useCoachMarks } from '@/hooks/useCoachMarks';
import api from '@/utils/api';
import { logger } from '@/utils/logger';

interface CoachMarksWrapperProps {
  pageId: string;
}

export default function CoachMarksWrapper({ pageId }: CoachMarksWrapperProps) {
  const { user } = useAuth();
  const [steps, setSteps] = useState<any[]>([]);
  // eslint-disable-next-line unused-imports/no-unused-vars
  // eslint-disable-next-line unused-imports/no-unused-vars
  // eslint-disable-next-line unused-imports/no-unused-vars
  const { showCoachMarks, markAsCompleted, skipCoachMarks } = useCoachMarks(pageId, steps);

  useEffect(() => {
    const fetchCoachMarks = async () => {
      if (!user) return;

      const role = user.role;
      const guestRole = !user ? 'guest' : null;

      try {
        const response = await api.get(`/coach-marks/${role || guestRole}/${pageId}`);
        if (response.data?.steps) {
          setSteps(response.data.steps);
        }
      } catch (error) {
        logger.error('Failed to fetch coach marks:', error);
      }
    };

    fetchCoachMarks();
  }, [user, pageId]);

  // Coach marks are currently disabled/commented out
  /*
  if (!showCoachMarks || steps.length === 0) {
    return null;
  }

  return <CoachMarks steps={steps} onComplete={markAsCompleted} onSkip={skipCoachMarks} />;
  */
  return null;
}
