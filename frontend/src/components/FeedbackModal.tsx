'use client';

import { useState, useEffect } from 'react';
import { useAuth } from '@/context/AuthContext';
import { usePathname } from 'next/navigation';
import api from '@/utils/api';
import { toast } from 'react-toastify';
import { logger } from '@/utils/logger';

export default function FeedbackModal() {
  const { user } = useAuth();
  const pathname = usePathname();
  const [eligibleOrderId, setEligibleOrderId] = useState<string | null>(null);
  const [isOpen, setIsOpen] = useState(false);
  const [rating, setRating] = useState(0);
  const [hoverRating, setHoverRating] = useState(0);
  const [comment, setComment] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    if (!user || user.role === 'super_admin' || user.role === 'wholesaler' || user.role === 'valet')
      return;

    // Don't show in admin paths
    if (pathname?.startsWith('/admin')) return;

    const checkEligibility = async () => {
      try {
        const response = await api.get('/order-feedback/eligible');
        const orderId = response.data.eligibleOrderId;

        if (orderId) {
          // Check if closed in this session
          const closedKey = `feedbackClosed_${orderId}`;
          if (!sessionStorage.getItem(closedKey)) {
            setEligibleOrderId(orderId);
            setIsOpen(true);
          }
        }
      } catch (error) {
        logger.error('Failed to check feedback eligibility', error);
      }
    };

    checkEligibility();
  }, [user, pathname]);

  const handleClose = () => {
    if (eligibleOrderId) {
      sessionStorage.setItem(`feedbackClosed_${eligibleOrderId}`, 'true');
    }
    setIsOpen(false);
  };

  const handleSubmit = async () => {
    if (rating === 0) {
      toast.error('Please select a star rating');
      return;
    }

    if (!eligibleOrderId) return;

    setIsSubmitting(true);
    try {
      await api.post('/order-feedback/', {
        orderId: eligibleOrderId,
        rating,
        comment,
      });
      toast.success('Thank you for your feedback!');
      setIsOpen(false);
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Failed to submit feedback');
    } finally {
      setIsSubmitting(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-[9999] flex items-center justify-center bg-black/50 px-4 backdrop-blur-sm">
      <div className="animate-fade-in-up w-full max-w-md transform overflow-hidden rounded-2xl bg-white shadow-2xl transition-all">
        <div className="p-6">
          <div className="mb-4 flex items-start justify-between">
            <h3 className="text-xl font-bold text-gray-900">How did we do?</h3>
            <button
              onClick={handleClose}
              className="text-gray-400 transition-colors hover:text-gray-600"
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
          </div>

          <p className="mb-6 text-sm text-gray-600">
            We&apos;d love to hear about your experience with your recent order.
          </p>

          <div className="mb-6 flex justify-center gap-2">
            {[1, 2, 3, 4, 5].map((star) => (
              <button
                key={star}
                type="button"
                onMouseEnter={() => setHoverRating(star)}
                onMouseLeave={() => setHoverRating(0)}
                onClick={() => setRating(star)}
                className="transform transition-transform hover:scale-110 focus:outline-none"
              >
                <svg
                  className={`h-10 w-10 transition-colors duration-200 ${star <= (hoverRating || rating) ? 'text-yellow-400' : 'text-gray-300 hover:text-yellow-400'}`}
                  fill="currentColor"
                  viewBox="0 0 20 20"
                >
                  <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                </svg>
              </button>
            ))}
          </div>

          <div className="mb-6">
            <label className="mb-2 block text-sm font-medium text-gray-700">
              Any additional comments? (Optional)
            </label>
            <textarea
              value={comment}
              onChange={(e) => setComment(e.target.value)}
              rows={3}
              className="w-full resize-none rounded-xl border border-gray-300 p-3 text-sm shadow-sm outline-none focus:border-indigo-500 focus:ring-indigo-500"
              placeholder="Tell us what you liked or how we can improve..."
            />
          </div>

          <button
            onClick={handleSubmit}
            disabled={isSubmitting || rating === 0}
            className={`flex w-full items-center justify-center rounded-xl px-4 py-3 text-sm font-bold text-white ${
              rating === 0
                ? 'cursor-not-allowed bg-gray-300'
                : 'bg-indigo-600 shadow-lg shadow-indigo-600/30 hover:bg-indigo-700'
            } transition-all`}
          >
            {isSubmitting ? (
              <div className="h-5 w-5 animate-spin rounded-full border-2 border-white border-t-transparent"></div>
            ) : (
              'Submit Feedback'
            )}
          </button>
        </div>
      </div>
    </div>
  );
}
