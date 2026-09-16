'use client';

import { useState, useEffect, useRef, useCallback, useId } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/context/AuthContext';
import { toast } from 'react-hot-toast';
import api from '@/utils/api';
import { logger } from '@/utils/logger';

interface AuthModalProps {
  isOpen: boolean;
  onClose: () => void;
  initialMode?: 'login' | 'register';
  onSuccess?: () => void;
  redirectOnSuccess?: boolean;
}

export default function AuthModal({
  isOpen,
  onClose,
  initialMode = 'login',
  onSuccess,
  redirectOnSuccess = true,
}: AuthModalProps) {
  const [isLogin, setIsLogin] = useState(initialMode === 'login');
  const [formData, setFormData] = useState({
    emailOrPhone: '',
    email: '',
    password: '',
    name: '',
    confirmPassword: '',
    phone: '',
  });
  const [otp, setOtp] = useState('');
  const [otpSent, setOtpSent] = useState(false);
  const [sendingOTP, setSendingOTP] = useState(false);
  const [verifyingOTP, setVerifyingOTP] = useState(false);
  const [otpVerified, setOtpVerified] = useState(false);
  const [loading, setLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [showForgotPassword, setShowForgotPassword] = useState(false);
  const [forgotPasswordData, setForgotPasswordData] = useState({
    phone: '',
    newPassword: '',
    confirmPassword: '',
    otp: '',
  });
  const [forgotPasswordOTPSent, setForgotPasswordOTPSent] = useState(false);
  const [sendingForgotPasswordOTP, setSendingForgotPasswordOTP] = useState(false);
  const [verifyingForgotPasswordOTP, setVerifyingForgotPasswordOTP] = useState(false);
  const [forgotPasswordOTPVerified, setForgotPasswordOTPVerified] = useState(false);
  const [canResend, setCanResend] = useState(false);
  const [forgotPasswordCanResend, setForgotPasswordCanResend] = useState(false);
  const [msg91Token, setMsg91Token] = useState('');
  const [forgotPasswordMsg91Token, setForgotPasswordMsg91Token] = useState('');
  const [timer, setTimer] = useState(0);
  const [forgotPasswordTimer, setForgotPasswordTimer] = useState(0);
  // eslint-disable-next-line unused-imports/no-unused-vars
  const { login, register, user } = useAuth();
  const router = useRouter();

  // ── Accessibility ──
  const modalRef = useRef<HTMLDivElement>(null);
  const previousFocusRef = useRef<HTMLElement | null>(null);
  const dialogTitleId = useId();
  const [statusMsg, setStatusMsg] = useState('');

  const FOCUSABLE = 'a[href], button:not([disabled]), textarea, input:not([disabled]), select, [tabindex]:not([tabindex="-1"])';

  const handleTab = useCallback((e: KeyboardEvent) => {
    if (!modalRef.current) return;
    const focusable = Array.from(modalRef.current.querySelectorAll<HTMLElement>(FOCUSABLE)).filter(
      (el) => el.offsetParent !== null
    );
    if (!focusable.length) return;
    const first = focusable[0];
    const last = focusable[focusable.length - 1];
    if (e.shiftKey ? document.activeElement === first : document.activeElement === last) {
      e.preventDefault();
      (e.shiftKey ? last : first).focus();
    }
  }, []);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
      if (e.key === 'Tab') handleTab(e);
    };
    if (isOpen) {
      previousFocusRef.current = document.activeElement as HTMLElement;
      document.addEventListener('keydown', handleKeyDown);
      document.body.style.overflow = 'hidden';
      requestAnimationFrame(() => {
        modalRef.current?.querySelector<HTMLElement>(FOCUSABLE)?.focus();
      });
    }
    return () => {
      document.removeEventListener('keydown', handleKeyDown);
      document.body.style.overflow = 'unset';
      if (!isOpen) previousFocusRef.current?.focus();
    };
  }, [isOpen, onClose, handleTab]);

  useEffect(() => {
    let interval: NodeJS.Timeout;
    if (timer > 0) {
      interval = setInterval(() => {
        setTimer((prev) => prev - 1);
      }, 1000);
    } else {
      setCanResend(true);
    }
    return () => clearInterval(interval);
  }, [timer]);

  useEffect(() => {
    let interval: NodeJS.Timeout;
    if (forgotPasswordTimer > 0) {
      interval = setInterval(() => {
        setForgotPasswordTimer((prev) => prev - 1);
      }, 1000);
    } else {
      setForgotPasswordCanResend(true);
    }
    return () => clearInterval(interval);
  }, [forgotPasswordTimer]);

  useEffect(() => {
    if (isOpen) {
      setIsLogin(initialMode === 'login');
      resetForm();
    }
  }, [isOpen, initialMode]);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    if (name === 'phone') {
      const cleanValue = value.replace(/\D/g, '').slice(0, 10);
      setFormData({ ...formData, [name]: cleanValue });
      return;
    }
    setFormData({ ...formData, [name]: value });
  };

  const handleForgotPasswordChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    if (name === 'phone') {
      const cleanValue = value.replace(/\D/g, '').slice(0, 10);
      setForgotPasswordData({ ...forgotPasswordData, [name]: cleanValue });
      return;
    }
    setForgotPasswordData({ ...forgotPasswordData, [name]: value });
  };

  const handleSendOTP = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!formData.phone) {
      toast.error('Please enter phone number');
      return;
    }

    let cleanPhone = formData.phone.replace(/\D/g, '');
    if (cleanPhone.length > 10 && cleanPhone.startsWith('91')) {
      cleanPhone = cleanPhone.slice(-10);
    }
    if (cleanPhone.length !== 10) {
      toast.error('Please enter a valid 10-digit phone number');
      return;
    }

    setSendingOTP(true);
    try {
      if (typeof window !== 'undefined' && (window as any).sendOtp && !(window as any).disableMSG91) {
        try {
          (window as any).sendOtp(
            '91' + cleanPhone,
            // eslint-disable-next-line unused-imports/no-unused-vars
            (data: any) => {
              setOtpSent(true);
              setCanResend(false);
              setTimer(30);
              toast.success('OTP sent');
              setSendingOTP(false);
            },
            async (error: any) => {
              logger.warn('MSG91 Frontend Error, falling back to backend:', error);
              // Fallback to backend API
              try {
                // eslint-disable-next-line unused-imports/no-unused-vars
                const response = await api.post('/auth/send-otp', {
                  phone: cleanPhone,
                  purpose: 'register',
                });
                setOtpSent(true);
                setCanResend(false);
                setTimer(30);
                toast.success('OTP sent to your phone');
                setSendingOTP(false);
              } catch (fallbackError: any) {
                toast.error(fallbackError.response?.data?.detail || 'Failed to send OTP');
                setSendingOTP(false);
              }
            }
          );
        } catch (sdkError: any) {
          logger.warn('MSG91 SDK threw error, falling back to backend:', sdkError);
          // eslint-disable-next-line unused-imports/no-unused-vars
          const response = await api.post('/auth/send-otp', {
            phone: cleanPhone,
            purpose: 'register',
          });
          setOtpSent(true);
          setCanResend(false);
          setTimer(30);
          toast.success('OTP sent to your phone');
          setSendingOTP(false);
        }
      } else {
        const response = await api.post('/auth/send-otp', {
          phone: cleanPhone,
          purpose: 'register',
        });
        setOtpSent(true);
        setCanResend(false);
        setTimer(30);
        toast.success('OTP sent to your phone');
        if (response.data.otp && process.env.NODE_ENV !== 'production') {
          console.log('OTP (Development):', response.data.otp);
          toast(`OTP (Dev): ${response.data.otp}`, { duration: 2000 });
        }
        setSendingOTP(false);
      }
    } catch (error: any) {
      const errorMessage =
        error.response?.data?.detail ||
        error.response?.data?.message ||
        error.message ||
        'Failed to send OTP. Please check your connection and try again.';
      toast.error(errorMessage);
      setSendingOTP(false);
    }
  };

  const handleRetryOTP = () => {
    if (typeof window !== 'undefined' && (window as any).retryOtp && !(window as any).disableMSG91) {
      setSendingOTP(true);
      (window as any).retryOtp(
        11,
        // eslint-disable-next-line unused-imports/no-unused-vars
        (data: any) => {
          setCanResend(false);
          setTimer(30);
          toast('OTP resent');
          setSendingOTP(false);
        },
        // eslint-disable-next-line unused-imports/no-unused-vars
        (error: any) => {
          toast.error('Failed to resend');
          setSendingOTP(false);
        }
      );
    } else {
      handleSendOTP({ preventDefault: () => {} } as any);
    }
  };

  const handleVerifyOTP = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!otp) {
      toast.error('Please enter OTP');
      return;
    }

    setVerifyingOTP(true);
    try {
      if (typeof window !== 'undefined' && (window as any).verifyOtp && !(window as any).disableMSG91) {
        try {
          (window as any).verifyOtp(
            otp,
            (data: any) => {
              const token =
                typeof data === 'string'
                  ? data
                  : data?.token || data?.jwt_token || data?.message;
              setOtpVerified(true);
              setMsg91Token(token || '');
              if (process.env.NODE_ENV !== 'production') {
                console.log('MSG91 verifyOtp success data:', data, 'extracted token:', token);
              }
              toast.success('Phone verified');
              setVerifyingOTP(false);
            },
            // eslint-disable-next-line unused-imports/no-unused-vars
            async (error: any) => {
              logger.warn('MSG91 Verification error, trying backend...');
              try {
                const clean = formData.phone.replace(/\D/g, '').slice(-10);
                await api.post('/auth/verify-otp', { phone: clean, otp });
                setOtpVerified(true);
                toast.success('Phone number verified');
                setVerifyingOTP(false);
              // eslint-disable-next-line unused-imports/no-unused-vars
              } catch (fallbackError: any) {
                toast.error('Invalid OTP');
                setVerifyingOTP(false);
              }
            }
          );
        // eslint-disable-next-line unused-imports/no-unused-vars
        } catch (e: any) {
          logger.warn('SDK Verify error, falling back...');
          await api.post('/auth/verify-otp', { phone: formData.phone, otp });
          setOtpVerified(true);
          toast.success('Phone number verified');
          setVerifyingOTP(false);
        }
      } else {
        await api.post('/auth/verify-otp', { phone: formData.phone, otp });
        setOtpVerified(true);
        toast.success('Phone number verified');
        setVerifyingOTP(false);
      }
    } catch (error: any) {
      toast.error(error.response?.data?.detail || error.response?.data?.message || 'Invalid OTP');
      setVerifyingOTP(false);
    }
  };

  const handleSendForgotPasswordOTP = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!forgotPasswordData.phone) {
      toast.error('Please enter phone number');
      return;
    }

    let cleanPhone = forgotPasswordData.phone.replace(/\D/g, '');
    if (cleanPhone.length > 10 && cleanPhone.startsWith('91')) {
      cleanPhone = cleanPhone.slice(-10);
    }
    if (cleanPhone.length !== 10) {
      toast.error('Please enter a valid 10-digit phone number');
      return;
    }

    setSendingForgotPasswordOTP(true);
    try {
      if (typeof window !== 'undefined' && (window as any).sendOtp && !(window as any).disableMSG91) {
        try {
          (window as any).sendOtp(
            '91' + cleanPhone,
            // eslint-disable-next-line unused-imports/no-unused-vars
            (data: any) => {
              setForgotPasswordOTPSent(true);
              setForgotPasswordCanResend(false);
              setForgotPasswordTimer(30);
              toast.success('OTP sent');
              setSendingForgotPasswordOTP(false);
            },
            // eslint-disable-next-line unused-imports/no-unused-vars
            async (error: any) => {
              try {
                // eslint-disable-next-line unused-imports/no-unused-vars
                const response = await api.post('/auth/send-otp', {
                  phone: cleanPhone,
                  purpose: 'forgot_password',
                });
                setForgotPasswordOTPSent(true);
                setForgotPasswordCanResend(false);
                setForgotPasswordTimer(30);
                toast.success('OTP sent to your phone');
                setSendingForgotPasswordOTP(false);
              // eslint-disable-next-line unused-imports/no-unused-vars
              } catch (e: any) {
                toast.error('Failed to send OTP');
                setSendingForgotPasswordOTP(false);
              }
            }
          );
        // eslint-disable-next-line unused-imports/no-unused-vars
        } catch (sdkError: any) {
          const response = await api.post('/auth/send-otp', {
            phone: cleanPhone,
            purpose: 'forgot_password',
          });
          setForgotPasswordOTPSent(true);
          setForgotPasswordCanResend(false);
          setForgotPasswordTimer(30);
          toast.success('OTP sent to your phone');
          if (response.data.otp) {
            if (process.env.NODE_ENV !== 'production') {
              console.log('OTP (Development):', response.data.otp);
            }
          }
          setSendingForgotPasswordOTP(false);
        }
      } else {
        const response = await api.post('/auth/send-otp', {
          phone: cleanPhone,
          purpose: 'forgot_password',
        });
        setForgotPasswordOTPSent(true);
        setForgotPasswordCanResend(false);
        setForgotPasswordTimer(30);
        toast.success('OTP sent to your phone');
        if (response.data.otp && process.env.NODE_ENV !== 'production') {
          console.log('OTP (Development):', response.data.otp);
          toast(`OTP (Dev): ${response.data.otp}`, { duration: 2000 });
        }
        setSendingForgotPasswordOTP(false);
      }
    } catch (error: any) {
      toast.error(
        error.response?.data?.detail || error.response?.data?.message || 'Failed to send OTP'
      );
      setSendingForgotPasswordOTP(false);
    }
  };

  const handleRetryForgotPasswordOTP = () => {
    if (typeof window !== 'undefined' && (window as any).retryOtp && !(window as any).disableMSG91) {
      setSendingForgotPasswordOTP(true);
      (window as any).retryOtp(
        11,
        // eslint-disable-next-line unused-imports/no-unused-vars
        (data: any) => {
          setForgotPasswordCanResend(false);
          setForgotPasswordTimer(30);
          toast('OTP resent');
          setSendingForgotPasswordOTP(false);
        },
        // eslint-disable-next-line unused-imports/no-unused-vars
        (error: any) => {
          toast.error('Failed to resend');
          setSendingForgotPasswordOTP(false);
        }
      );
    } else {
      handleSendForgotPasswordOTP({ preventDefault: () => {} } as any);
    }
  };

  const handleVerifyForgotPasswordOTP = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!forgotPasswordData.otp) {
      toast.error('Please enter OTP');
      return;
    }

    setVerifyingForgotPasswordOTP(true);
    try {
      if (typeof window !== 'undefined' && (window as any).verifyOtp && !(window as any).disableMSG91) {
        try {
          (window as any).verifyOtp(
            forgotPasswordData.otp,
            (data: any) => {
              const token =
                typeof data === 'string'
                  ? data
                  : data?.token || data?.jwt_token || data?.message;
              setForgotPasswordOTPVerified(true);
              setForgotPasswordMsg91Token(token || '');
              toast.success('OTP verified');
              setVerifyingForgotPasswordOTP(false);
            },
            // eslint-disable-next-line unused-imports/no-unused-vars
            async (error: any) => {
              try {
                const clean = forgotPasswordData.phone.replace(/\D/g, '').slice(-10);
                await api.post('/auth/verify-otp', { phone: clean, otp: forgotPasswordData.otp });
                setForgotPasswordOTPVerified(true);
                toast.success('OTP verified');
                setVerifyingForgotPasswordOTP(false);
              // eslint-disable-next-line unused-imports/no-unused-vars
              } catch (e: any) {
                toast.error('Invalid OTP');
                setVerifyingForgotPasswordOTP(false);
              }
            }
          );
        // eslint-disable-next-line unused-imports/no-unused-vars
        } catch (e: any) {
          await api.post('/auth/verify-otp', {
            phone: forgotPasswordData.phone,
            otp: forgotPasswordData.otp,
          });
          setForgotPasswordOTPVerified(true);
          toast.success('OTP verified');
          setVerifyingForgotPasswordOTP(false);
        }
      } else {
        await api.post('/auth/verify-otp', {
          phone: forgotPasswordData.phone,
          otp: forgotPasswordData.otp,
        });
        setForgotPasswordOTPVerified(true);
        toast.success('OTP verified');
        setVerifyingForgotPasswordOTP(false);
      }
    } catch (error: any) {
      toast.error(error.response?.data?.detail || error.response?.data?.message || 'Invalid OTP');
      setVerifyingForgotPasswordOTP(false);
    }
  };

  const handleForgotPassword = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!forgotPasswordOTPVerified) {
      toast.error('Please verify OTP first');
      return;
    }

    if (forgotPasswordData.newPassword !== forgotPasswordData.confirmPassword) {
      toast.error('Passwords do not match');
      return;
    }

    if (forgotPasswordData.newPassword.length < 6) {
      toast.error('Password must be at least 6 characters');
      return;
    }

    setLoading(true);
    try {
      await api.post('/auth/forgot-password', {
        phone: forgotPasswordData.phone,
        newPassword: forgotPasswordData.newPassword,
        otp: forgotPasswordData.otp,
        msg91Token: forgotPasswordMsg91Token,
      });
      toast.success('Password reset successful! Please login with your new password.');
      setShowForgotPassword(false);
      setForgotPasswordData({ phone: '', newPassword: '', confirmPassword: '', otp: '' });
      setForgotPasswordOTPSent(false);
      setForgotPasswordOTPVerified(false);
      setIsLogin(true);
    } catch (error: any) {
      toast.error(
        error.response?.data?.detail || error.response?.data?.message || 'Failed to reset password'
      );
    } finally {
      setLoading(false);
    }
  };

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!formData.emailOrPhone || !formData.emailOrPhone.trim()) {
      toast.error('Please enter email or phone number');
      return;
    }

    if (!formData.password || !formData.password.trim()) {
      toast.error('Please enter password');
      return;
    }

    setLoading(true);

    try {
      const emailOrPhone = formData.emailOrPhone.trim();
      const processedEmailOrPhone = emailOrPhone.includes('@')
        ? emailOrPhone
        : emailOrPhone.replace(/\D/g, '');

      if (!processedEmailOrPhone) {
        toast.error('Please enter a valid email or phone number');
        setLoading(false);
        return;
      }

      // Call login which sets token/user state and returns user data
      const userData = await login(processedEmailOrPhone, formData.password);

      onClose();
      resetForm();

      if (onSuccess) {
        onSuccess();
      }

      if (redirectOnSuccess) {
        // Use effectiveRole if available, otherwise use role
        const userRole = userData.effectiveRole || userData.role;

        // Redirect to role-specific dashboard using user data from login
        switch (userRole) {
          case 'super_admin':
            router.replace('/admin');
            break;
          case 'wholesaler':
            router.replace('/wholesaler');
            break;
          case 'customer':
            router.replace('/customer');
            break;
          case 'valet':
            router.replace('/valet');
            break;
          default:
            logger.warn('Unknown role:', userRole, 'User data:', userData);
            router.replace('/');
        }
      }
    } catch (error: any) {
      logger.error('Login error in AuthModal:', error);
      // Error is already handled by AuthContext with toast
    } finally {
      setLoading(false);
    }
  };

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!otpVerified) {
      toast.error('Please verify your phone number first');
      return;
    }

    if (formData.password !== formData.confirmPassword) {
      toast.error('Passwords do not match');
      return;
    }

    setLoading(true);

    try {
      // eslint-disable-next-line unused-imports/no-unused-vars
      // eslint-disable-next-line unused-imports/no-unused-vars
      const { confirmPassword, emailOrPhone, ...restData } = formData;
      const registerData = {
        ...restData,
        role: 'customer' as const,
        msg91Token: msg91Token,
        otp,
      };
      await register(registerData);
      onClose();
      resetForm();
      
      if (onSuccess) {
        onSuccess();
      }
    // eslint-disable-next-line unused-imports/no-unused-vars
    } catch (e) { logger.warn("Silent catch block:", e); /* Error handled by AuthContext */ } finally {
      setLoading(false);
    }
  };

  const resetForm = () => {
    setFormData({
      emailOrPhone: '',
      email: '',
      password: '',
      name: '',
      confirmPassword: '',
      phone: '',
    });
    setOtp('');
    setOtpSent(false);
    setOtpVerified(false);
    setMsg91Token('');
    setShowPassword(false);
    setShowConfirmPassword(false);
    setShowForgotPassword(false);
    setForgotPasswordData({ phone: '', newPassword: '', confirmPassword: '', otp: '' });
    setForgotPasswordOTPSent(false);
    setForgotPasswordOTPVerified(false);
    setForgotPasswordMsg91Token('');
    setCanResend(false);
    setForgotPasswordCanResend(false);
    setTimer(0);
    setForgotPasswordTimer(0);
  };

  const switchMode = (mode: boolean) => {
    setIsLogin(mode);
    resetForm();
    setShowForgotPassword(false);
  };

  if (!isOpen) return null;

  // aria-live status announcement helper
  const announce = (msg: string) => setStatusMsg(msg);

  if (showForgotPassword) {
    return (
      <div
        className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-60 p-4"
        aria-hidden="true"
        onClick={onClose}
      >
        {/* aria-live status region */}
        <div aria-live="polite" aria-atomic="true" className="sr-only">
          {statusMsg}
        </div>
        <div
          ref={modalRef}
          role="dialog"
          aria-modal="true"
          aria-labelledby={`${dialogTitleId}-forgot`}
          className="relative max-h-[90vh] w-full max-w-md overflow-y-auto rounded-2xl bg-white p-8 shadow-2xl"
          onClick={(e) => e.stopPropagation()}
          aria-hidden="false"
        >
          <button
            className="absolute right-4 top-4 text-2xl text-gray-600 hover:text-red-600"
            onClick={onClose}
            aria-label="Close forgot password dialog"
          >
            ×
          </button>
          <h2 id={`${dialogTitleId}-forgot`} className="mb-4 text-2xl font-bold text-red-600">Forgot Password</h2>
          <button
            onClick={() => setShowForgotPassword(false)}
            className="mb-4 text-sm text-red-600 underline hover:text-red-800"
          >
            ← Back to Login
          </button>
          <form className="space-y-4" onSubmit={handleForgotPassword}>
            <div className="space-y-4">
              <div>
                <label htmlFor="fp-phone" className="mb-1 block text-sm font-medium text-gray-700">
                  Phone Number *
                </label>
                <div className="flex gap-2">
                  <input
                    id="fp-phone"
                    name="phone"
                    type="tel"
                    value={forgotPasswordData.phone}
                    onChange={handleForgotPasswordChange}
                   
                    disabled={forgotPasswordOTPSent && forgotPasswordOTPVerified}
                    placeholder="Enter 10-digit phone number"
                    maxLength={10}
                    className="flex-1 rounded-lg border-2 border-gray-300 px-3 py-2 focus:border-red-500 focus:outline-none disabled:bg-gray-100"
                  />
                  <button
                    type="button"
                    onClick={
                      !forgotPasswordOTPSent
                        ? handleSendForgotPasswordOTP
                        : handleRetryForgotPasswordOTP
                    }
                    disabled={
                      sendingForgotPasswordOTP ||
                      !forgotPasswordData.phone ||
                      (forgotPasswordOTPSent && !forgotPasswordCanResend) ||
                      forgotPasswordOTPVerified
                    }
                    className="min-w-[100px] whitespace-nowrap rounded-lg px-4 py-2 text-sm font-semibold text-white shadow-md transition-all disabled:opacity-50"
                    style={{ background: 'linear-gradient(135deg, #d63031 0%, #e17055 100%)' }}
                  >
                    {!forgotPasswordOTPSent
                      ? sendingForgotPasswordOTP
                        ? 'Sending...'
                        : 'Send OTP'
                      : forgotPasswordCanResend
                        ? 'Resend'
                        : `${forgotPasswordTimer}s`}
                  </button>
                </div>
              </div>

              {forgotPasswordOTPSent && !forgotPasswordOTPVerified && (
                <div>
                  <label htmlFor="fp-otp" className="mb-1 block text-sm font-medium text-gray-700">
                    Enter OTP *
                  </label>
                  <div className="flex gap-2">
                    <input
                      id="fp-otp"
                      type="text"
                      name="otp"
                      value={forgotPasswordData.otp}
                      onChange={handleForgotPasswordChange}
                      placeholder="6-digit OTP"
                      maxLength={6}
                      autoComplete="one-time-code"
                      inputMode="numeric"
                      className="flex-1 rounded-lg border-2 border-gray-300 px-3 py-2 focus:border-red-500 focus:outline-none"
                    />
                    <button
                      type="button"
                      onClick={handleVerifyForgotPasswordOTP}
                      disabled={
                        verifyingForgotPasswordOTP ||
                        !forgotPasswordData.otp ||
                        forgotPasswordData.otp.length !== 6
                      }
                      className="min-w-[100px] rounded-lg px-6 py-2 text-sm font-semibold text-white shadow-md transition-all disabled:opacity-50"
                      style={{ background: 'linear-gradient(135deg, #d63031 0%, #e17055 100%)' }}
                    >
                      {verifyingForgotPasswordOTP ? '...' : 'Verify'}
                    </button>
                  </div>
                </div>
              )}
            </div>
            {forgotPasswordOTPVerified && (
              <>
                <div>
                  <label htmlFor="fp-new-password" className="mb-1 block text-sm font-medium text-gray-700">
                    New Password *
                  </label>
                  <input
                    id="fp-new-password"
                    name="newPassword"
                    type="password"
                    value={forgotPasswordData.newPassword}
                    onChange={handleForgotPasswordChange}
                   
                    minLength={6}
                    placeholder="Enter new password"
                    className="w-full rounded-lg border-2 border-gray-300 px-3 py-2 focus:border-red-500 focus:outline-none"
                  />
                </div>
                <div>
                  <label htmlFor="fp-confirm-password" className="mb-1 block text-sm font-medium text-gray-700">
                    Confirm New Password *
                  </label>
                  <input
                    id="fp-confirm-password"
                    name="confirmPassword"
                    type="password"
                    value={forgotPasswordData.confirmPassword}
                    onChange={handleForgotPasswordChange}
                   
                    minLength={6}
                    placeholder="Confirm new password"
                    className="w-full rounded-lg border-2 border-gray-300 px-3 py-2 focus:border-red-500 focus:outline-none"
                  />
                </div>
                <button
                  type="submit"
                  disabled={loading}
                  className="w-full rounded-lg py-3 font-medium text-white disabled:opacity-50"
                  style={{ background: 'linear-gradient(135deg, #d63031 0%, #e17055 100%)' }}
                >
                  {loading ? 'Resetting...' : 'Reset Password'}
                </button>
              </>
            )}
          </form>
        </div>
      </div>
    );
  }

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-60 p-4"
      aria-hidden="true"
      onClick={onClose}
    >
      {/* aria-live status region */}
      <div aria-live="polite" aria-atomic="true" className="sr-only">
        {statusMsg}
      </div>
      <div
        ref={modalRef}
        role="dialog"
        aria-modal="true"
        aria-labelledby={dialogTitleId}
        className="relative max-h-[90vh] w-full max-w-md overflow-y-auto rounded-2xl bg-white p-8 shadow-2xl"
        onClick={(e) => e.stopPropagation()}
        aria-hidden="false"
      >
        <button
          className="absolute right-4 top-4 text-2xl text-gray-600 hover:text-red-600"
          onClick={onClose}
          aria-label="Close dialog"
        >
          ×
        </button>

        {/* Visually hidden title for screen readers */}
        <h2 id={dialogTitleId} className="sr-only">
          {isLogin ? 'Sign in to your account' : 'Create a new account'}
        </h2>

        <div className="mb-6 flex border-b-2 border-gray-200">
          <button
            type="button"
            onClick={() => switchMode(true)}
            className={`flex-1 px-4 py-3 text-center font-semibold transition-all ${
              isLogin
                ? 'border-b-3 border-red-600 bg-red-50 text-red-600'
                : 'text-gray-600 hover:text-red-600'
            }`}
            style={isLogin ? { borderBottomWidth: '3px' } : {}}
          >
            Login
          </button>
          <button
            type="button"
            onClick={() => switchMode(false)}
            className={`flex-1 px-4 py-3 text-center font-semibold transition-all ${
              !isLogin
                ? 'border-b-3 border-red-600 bg-red-50 text-red-600'
                : 'text-gray-600 hover:text-red-600'
            }`}
            style={!isLogin ? { borderBottomWidth: '3px' } : {}}
          >
            Register
          </button>
        </div>

        {isLogin ? (
          <form className="space-y-4" onSubmit={handleLogin}>
            <div>
              <label htmlFor="login-email-phone" className="mb-1 block text-sm font-medium text-gray-700">
                Email or Phone *
              </label>
              <input
                id="login-email-phone"
                name="emailOrPhone"
                type="text"
               
                autoComplete="username"
                className="w-full rounded-lg border-2 border-gray-300 px-3 py-2 focus:border-red-500 focus:outline-none"
                placeholder="Enter email or phone number"
                value={formData.emailOrPhone}
                onChange={handleChange}
              />
            </div>

            <div>
              <label htmlFor="login-password" className="mb-1 block text-sm font-medium text-gray-700">Password *</label>
              <div className="relative">
                <input
                  id="login-password"
                  name="password"
                  type={showPassword ? 'text' : 'password'}
                 
                  autoComplete="current-password"
                  className="w-full rounded-lg border-2 border-gray-300 px-3 py-2 pr-10 focus:border-red-500 focus:outline-none"
                  placeholder="Password"
                  value={formData.password}
                  onChange={handleChange}
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  aria-label={showPassword ? 'Hide password' : 'Show password'}
                  aria-pressed={showPassword}
                  className="absolute right-3 top-1/2 -translate-y-1/2 transform text-gray-500 hover:text-red-600"
                >
                  {showPassword ? '👁️' : '👁️‍🗨️'}
                </button>
              </div>
            </div>

            <div className="text-right">
              <button
                type="button"
                onClick={() => setShowForgotPassword(true)}
                className="text-sm text-red-600 underline hover:text-red-800"
              >
                Forgot Password?
              </button>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full rounded-lg py-3 font-medium text-white disabled:opacity-50"
              style={{ background: 'linear-gradient(135deg, #d63031 0%, #e17055 100%)' }}
            >
              {loading ? 'Signing in...' : 'Sign in'}
            </button>
          </form>
        ) : (
          <form className="space-y-4" onSubmit={handleRegister}>
            <div>
              <label htmlFor="reg-name" className="mb-1 block text-sm font-medium text-gray-700">Name *</label>
              <input
                id="reg-name" required
                name="name"
                type="text"
               
                autoComplete="name"
                className="w-full rounded-lg border-2 border-gray-300 px-3 py-2 focus:border-red-500 focus:outline-none"
                value={formData.name}
                onChange={handleChange}
              />
            </div>

            <div>
              <label htmlFor="reg-email" className="mb-1 block text-sm font-medium text-gray-700">Email *</label>
              <input
                id="reg-email" required
                name="email"
                type="email"
               
                autoComplete="email"
                className="w-full rounded-lg border-2 border-gray-300 px-3 py-2 focus:border-red-500 focus:outline-none"
                value={formData.email}
                onChange={handleChange}
              />
            </div>

            <div>
              <label htmlFor="reg-password" className="mb-1 block text-sm font-medium text-gray-700">Password *</label>
              <div className="relative">
                <input
                  id="reg-password" required
                  name="password"
                  type={showPassword ? 'text' : 'password'}
                 
                  minLength={6}
                  autoComplete="new-password"
                  aria-describedby="reg-password-hint"
                  className="w-full rounded-lg border-2 border-gray-300 px-3 py-2 pr-10 focus:border-red-500 focus:outline-none"
                  value={formData.password}
                  onChange={handleChange}
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  aria-label={showPassword ? 'Hide password' : 'Show password'}
                  aria-pressed={showPassword}
                  className="absolute right-3 top-1/2 -translate-y-1/2 transform text-gray-500 hover:text-red-600"
                >
                  {showPassword ? '👁️' : '👁️‍🗨️'}
                </button>
              </div>
              <p id="reg-password-hint" className="mt-1 text-xs text-gray-500">Must be at least 6 characters</p>
            </div>

            <div>
              <label htmlFor="reg-confirm-password" className="mb-1 block text-sm font-medium text-gray-700">
                Confirm Password *
              </label>
              <div className="relative">
                <input
                  id="reg-confirm-password" required
                  name="confirmPassword"
                  type={showConfirmPassword ? 'text' : 'password'}
                 
                  autoComplete="new-password"
                  className="w-full rounded-lg border-2 border-gray-300 px-3 py-2 pr-10 focus:border-red-500 focus:outline-none"
                  value={formData.confirmPassword}
                  onChange={handleChange}
                />
                <button
                  type="button"
                  onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                  aria-label={showConfirmPassword ? 'Hide confirm password' : 'Show confirm password'}
                  aria-pressed={showConfirmPassword}
                  className="absolute right-3 top-1/2 -translate-y-1/2 transform text-gray-500 hover:text-red-600"
                >
                  {showConfirmPassword ? '👁️' : '👁️‍🗨️'}
                </button>
              </div>
            </div>

            <div className="space-y-4">
              <div>
                <label htmlFor="reg-phone" className="mb-1 block text-sm font-medium text-gray-700">Phone *</label>
                <div className="flex gap-2">
                  <input
                    id="reg-phone"
                    name="phone"
                    type="tel"
                   
                    disabled={otpVerified}
                    autoComplete="tel"
                    inputMode="numeric"
                    className="flex-1 rounded-lg border-2 border-gray-300 px-3 py-2 focus:border-red-500 focus:outline-none disabled:bg-gray-100"
                    placeholder="Enter 10-digit phone number"
                    maxLength={10}
                    value={formData.phone}
                    onChange={handleChange}
                  />
                  <button
                    type="button"
                    onClick={!otpSent ? handleSendOTP : handleRetryOTP}
                    disabled={
                      sendingOTP || !formData.phone || (otpSent && !canResend) || otpVerified
                    }
                    className="min-w-[100px] whitespace-nowrap rounded-lg px-4 py-2 text-sm font-semibold text-white shadow-md transition-all disabled:opacity-50"
                    style={{ background: 'linear-gradient(135deg, #d63031 0%, #e17055 100%)' }}
                  >
                    {!otpSent
                      ? sendingOTP
                        ? 'Sending...'
                        : 'Send OTP'
                      : canResend
                        ? 'Resend'
                        : `${timer}s`}
                  </button>
                </div>
              </div>

              {otpSent && !otpVerified && (
                <div>
                  <label htmlFor="reg-otp" className="mb-1 block text-sm font-medium text-gray-700">
                    Enter OTP *
                  </label>
                  <div className="flex gap-2">
                    <input
                      id="reg-otp"
                      type="text"
                      value={otp}
                      onChange={(e) => setOtp(e.target.value)}
                      placeholder="6-digit OTP"
                      maxLength={6}
                      autoComplete="one-time-code"
                      inputMode="numeric"
                      className="flex-1 rounded-lg border-2 border-gray-300 px-3 py-2 focus:border-red-500 focus:outline-none"
                    />
                    <button
                      type="button"
                      onClick={handleVerifyOTP}
                      disabled={verifyingOTP || !otp || otp.length !== 6}
                      className="min-w-[100px] rounded-lg px-6 py-2 text-sm font-semibold text-white shadow-md transition-all disabled:opacity-50"
                      style={{ background: 'linear-gradient(135deg, #d63031 0%, #e17055 100%)' }}
                    >
                      {verifyingOTP ? '...' : 'Verify'}
                    </button>
                  </div>
                </div>
              )}
            </div>

              {otpVerified && (
                <div
                  role="status"
                  aria-live="polite"
                  className="rounded-lg bg-green-50 p-3 text-center font-medium text-green-800"
                >
                  ✓ Phone number verified
                </div>
              )}

            <button
              type="submit"
              disabled={loading || !otpVerified}
              className="w-full rounded-lg py-3 font-medium text-white disabled:opacity-50"
              style={{ background: 'linear-gradient(135deg, #d63031 0%, #e17055 100%)' }}
            >
              {loading ? 'Registering...' : 'Register'}
            </button>
          </form>
        )}
      </div>
    </div>
  );
}

