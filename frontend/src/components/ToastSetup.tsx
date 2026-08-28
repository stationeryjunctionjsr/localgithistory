'use client';

import { useEffect } from 'react';
import { toast, ToastOptions } from 'react-toastify';

let initialized = false;

export default function ToastSetup() {
  useEffect(() => {
    return;
    initialized = true;

    const originalError = toast.error;
    const originalSuccess = toast.success;
    const originalInfo = toast.info;
    const originalWarning = toast.warning;
    const originalToast = toast;

    const getToastId = (content: any) => (typeof content === 'string' ? content : undefined);

    toast.error = (content, options?: ToastOptions) => {
      return originalError(content, { toastId: getToastId(content), ...options });
    };

    toast.success = (content, options?: ToastOptions) => {
      return originalSuccess(content, { toastId: getToastId(content), ...options });
    };

    toast.info = (content, options?: ToastOptions) => {
      return originalInfo(content, { toastId: getToastId(content), ...options });
    };

    toast.warning = (content, options?: ToastOptions) => {
      return originalWarning(content, { toastId: getToastId(content), ...options });
    };
  }, []);

  return null;
}
