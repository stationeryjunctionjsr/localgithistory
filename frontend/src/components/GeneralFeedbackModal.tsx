'use client';

import { useState } from 'react';
import api from '@/utils/api';
import { toast } from 'react-toastify';
import { useTheme } from '@/context/ThemeContext';

interface GeneralFeedbackModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export default function GeneralFeedbackModal({ isOpen, onClose }: GeneralFeedbackModalProps) {
  const { theme } = useTheme();
  const [rating, setRating] = useState(0);
  const [hoverRating, setHoverRating] = useState(0);
  const [comment, setComment] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (rating === 0) {
      toast.error('Please select a star rating');
      return;
    }

    setIsSubmitting(true);
    try {
      await api.post('/order-feedback/', {
        rating,
        comment,
        feedbackType: 'general',
      });
      toast.success('Thank you for your valuable feedback!');
      setRating(0);
      setComment('');
      onClose();
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Failed to submit feedback. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-[9999] flex animate-fade-in items-center justify-center bg-black/60 px-4 backdrop-blur-sm">
      <div
        className="animate-scale-up w-full max-w-lg transform overflow-hidden rounded-3xl bg-white shadow-2xl transition-all"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="relative">
          <div className="h-2 w-full" style={{ backgroundColor: theme.primary }} />
          <button
            onClick={onClose}
            className="absolute right-4 top-4 rounded-full p-2 text-gray-400 transition-all hover:bg-gray-100 hover:text-gray-600"
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

          <div className="p-10">
            <div className="mb-10 text-center">
              <div className="mx-auto mb-6 flex h-20 w-20 rotate-3 items-center justify-center rounded-2xl bg-indigo-50">
                <svg
                  className="h-10 w-10 text-indigo-600"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth="2"
                    d="M11 5.882V19.24a1.76 1.76 0 01-3.417.592l-2.147-6.15M18 13a3 3 0 100-6M5.436 13.683A4.001 4.001 0 017 6h1.832c4.1 0 7.625-1.234 9.168-3v14c-1.543-1.766-5.067-3-9.168-3H7a3.988 3.988 0 01-1.564-.317z"
                  />
                </svg>
              </div>
              <h3 className="mb-2 text-3xl font-black text-gray-900">Share Your Thoughts</h3>
              <p className="font-medium text-gray-500">
                Your feedback helps us create a better experience for everyone.
              </p>
            </div>

            <form onSubmit={handleSubmit} className="space-y-8">
              <div>
                <label className="mb-4 block text-center text-sm font-black uppercase tracking-widest text-gray-400">
                  Overall Experience
                </label>
                <div className="flex justify-center gap-3">
                  {[1, 2, 3, 4, 5].map((star) => (
                    <button
                      key={star}
                      type="button"
                      onMouseEnter={() => setHoverRating(star)}
                      onMouseLeave={() => setHoverRating(0)}
                      onClick={() => setRating(star)}
                      className="transform transition-all duration-200 focus:outline-none active:scale-90"
                    >
                      <svg
                        className={`h-12 w-12 transition-colors duration-200 ${
                          star <= (hoverRating || rating)
                            ? 'text-yellow-400 drop-shadow-sm'
                            : 'text-gray-300 hover:text-yellow-400'
                        }`}
                        fill="currentColor"
                        viewBox="0 0 20 20"
                      >
                        <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                      </svg>
                    </button>
                  ))}
                </div>
              </div>

              <div>
                <label className="mb-3 ml-1 block text-sm font-bold text-gray-700">
                  Tell us more
                </label>
                <textarea
                  value={comment}
                  onChange={(e) => setComment(e.target.value)}
                  rows={4}
                  className="w-full resize-none rounded-2xl border border-gray-200 bg-gray-50 p-4 text-sm shadow-inner outline-none transition-all focus:border-transparent focus:ring-2"
                  style={{ '--tw-ring-color': theme.primary } as any}
                  placeholder="What do you love? What can we improve? We're listening..."
                />
              </div>

              <div className="flex gap-4 pt-2">
                <button
                  type="button"
                  onClick={onClose}
                  className="flex-1 rounded-2xl px-6 py-4 text-sm font-bold text-gray-500 transition-all hover:bg-gray-100 hover:text-gray-700"
                >
                  Maybe Later
                </button>
                <button
                  type="submit"
                  disabled={isSubmitting || rating === 0}
                  className={`flex flex-[2] items-center justify-center rounded-2xl px-6 py-4 text-sm font-black text-white shadow-xl transition-all active:scale-95 ${
                    rating === 0
                      ? 'cursor-not-allowed bg-gray-200 opacity-50 shadow-none'
                      : 'shadow-indigo-200 hover:opacity-90'
                  }`}
                  style={{ backgroundColor: rating > 0 ? theme.primary : undefined }}
                >
                  {isSubmitting ? (
                    <div className="h-5 w-5 animate-spin rounded-full border-2 border-white border-t-transparent"></div>
                  ) : (
                    'Submit Feedback'
                  )}
                </button>
              </div>
            </form>
          </div>
        </div>
      </div>
    </div>
  );
}
