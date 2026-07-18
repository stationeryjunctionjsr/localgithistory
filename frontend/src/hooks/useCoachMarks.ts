import { useState, useEffect } from 'react';

const COACH_MARKS_STORAGE_KEY = 'coachMarksCompleted';

export const useCoachMarks = (pageId: string, steps: any[]) => {
  const [showCoachMarks, setShowCoachMarks] = useState(false);
  const [completedMarks, setCompletedMarks] = useState<string[]>([]);

  useEffect(() => {
    // Coach marks are currently disabled/commented out
    /*
    const stored = localStorage.getItem(COACH_MARKS_STORAGE_KEY);
    if (stored) {
      try {
        const completed = JSON.parse(stored);
        setCompletedMarks(completed);

        if (!completed.includes(pageId) && steps && steps.length > 0) {
          setShowCoachMarks(true);
        }
      } catch (error) {
        console.error('Error loading coach marks:', error);
      }
    } else if (steps && steps.length > 0) {
      setShowCoachMarks(true);
    }
    */
    setShowCoachMarks(false);
  }, [pageId, steps]);

  const markAsCompleted = () => {
    const updated = [...completedMarks, pageId];
    setCompletedMarks(updated);
    localStorage.setItem(COACH_MARKS_STORAGE_KEY, JSON.stringify(updated));
    setShowCoachMarks(false);
  };

  const skipCoachMarks = () => {
    markAsCompleted();
  };

  const resetCoachMarks = () => {
    const updated = completedMarks.filter((id) => id !== pageId);
    setCompletedMarks(updated);
    localStorage.setItem(COACH_MARKS_STORAGE_KEY, JSON.stringify(updated));
    setShowCoachMarks(true);
  };

  return {
    showCoachMarks,
    markAsCompleted,
    skipCoachMarks,
    resetCoachMarks,
  };
};
