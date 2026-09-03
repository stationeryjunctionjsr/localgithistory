'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import styles from './PrivacyConsent.module.css';
import { useLanguage } from '@/context/LanguageContext';

export default function PrivacyConsent() {
  const { t } = useLanguage();
  const [showConsent, setShowConsent] = useState(false);

  useEffect(() => {
    // Show the banner to ALL visitors (including logged-in users) if consent has not yet been given.
    // Previously this was gated on `!user`, which meant logged-in users never saw the banner — GIGW non-compliant.
    const consentGiven = localStorage.getItem('cookieConsent');
    if (!consentGiven) {
      setShowConsent(true);
    }
  }, []);

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
      <div className={styles.cookieConsentBanner} role="dialog" aria-modal="false" aria-label={t('cookie.title', 'Cookie Consent')}>
        <div className={styles.cookieConsentContent}>
          <div className={styles.cookieConsentText}>
            <h4>{t('cookie.title', 'Cookie Consent')}</h4>
            <p>
              {t('cookie.message', 'We use cookies to enhance your browsing experience, analyze site traffic, and personalize content. By clicking "Accept", you consent to our use of cookies.')}{' '}
              <Link href="/privacy-policy" className={styles.privacyLink}>
                {t('cookie.learnMore', 'Learn more about our Privacy Policy')}
              </Link>
            </p>
          </div>
          <div className={styles.cookieConsentActions}>
            <button
              onClick={handleRejectCookies}
              className={`${styles.consentButton} ${styles.rejectButton}`}
            >
              {t('cookie.reject', 'Reject')}
            </button>
            <button
              onClick={handleAcceptCookies}
              className={`${styles.consentButton} ${styles.acceptButton}`}
            >
              {t('cookie.accept', 'Accept All')}
            </button>
          </div>
        </div>
      </div>
    </>
  );
}
