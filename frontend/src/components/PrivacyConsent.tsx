'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { useAuth } from '@/context/AuthContext';
import styles from './PrivacyConsent.module.css';

export default function PrivacyConsent() {
  const { user } = useAuth();
  const [showConsent, setShowConsent] = useState(false);

  useEffect(() => {
    const consentGiven = localStorage.getItem('cookieConsent');
    if (!consentGiven && !user) {
      setShowConsent(true);
    } else if (user) {
      setShowConsent(false);
    }
  }, [user]);

  const handleAcceptCookies = () => {
    localStorage.setItem('cookieConsent', 'accepted');
    localStorage.setItem('cookieConsentDate', new Date().toISOString());
    window.dispatchEvent(new CustomEvent('cookie-consent-changed', { detail: 'accepted' }));
    setShowConsent(false);
  };

  const handleRejectCookies = () => {
    localStorage.setItem('cookieConsent', 'rejected');
    window.dispatchEvent(new CustomEvent('cookie-consent-changed', { detail: 'rejected' }));
    setShowConsent(false);
  };

  if (!showConsent) return null;

  return (
    <>
      {/* Cookie Consent Banner */}
      <div className={styles.cookieConsentBanner}>
        <div className={styles.cookieConsentContent}>
          <div className={styles.cookieConsentText}>
            <h4>Cookie Consent</h4>
            <p>
              We use cookies to enhance your browsing experience, analyze site traffic, and
              personalize content. By clicking &quot;Accept&quot;, you consent to our use of cookies.
              <Link href="/privacy-policy" className={styles.privacyLink}>
                Learn more about our Privacy Policy
              </Link>
            </p>
          </div>
          <div className={styles.cookieConsentActions}>
            <button
              onClick={handleRejectCookies}
              className={`${styles.consentButton} ${styles.rejectButton}`}
            >
              Reject
            </button>
            <button
              onClick={handleAcceptCookies}
              className={`${styles.consentButton} ${styles.acceptButton}`}
            >
              Accept All
            </button>
          </div>
        </div>
      </div>
    </>
  );
}

