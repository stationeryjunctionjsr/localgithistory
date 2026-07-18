'use client';

/**
 * ConsentBasedTracking
 *
 * Loads tracking scripts ONLY after the user explicitly accepts cookies.
 * Listens for the 'cookie-consent-changed' custom event from PrivacyConsent.tsx
 * so tracking activates immediately on accept without a page reload.
 *
 * Scripts loaded (when env vars present):
 *  - Google Tag Manager  (NEXT_PUBLIC_GTM_ID)
 *  - Google Analytics 4  (NEXT_PUBLIC_GA_ID)
 *  - Google Ads gtag     (NEXT_PUBLIC_GOOGLE_ADS_ID)
 *  - Microsoft Clarity   (NEXT_PUBLIC_CLARITY_ID)
 *  - Meta (Facebook) Pixel (NEXT_PUBLIC_META_PIXEL_ID)
 */

import { useEffect, useState } from 'react';
import Script from 'next/script';

const GTM_ID = process.env.NEXT_PUBLIC_GTM_ID || '';
const GA_ID = process.env.NEXT_PUBLIC_GA_ID || '';
const CLARITY_ID = process.env.NEXT_PUBLIC_CLARITY_ID || '';
const GOOGLE_ADS_ID = process.env.NEXT_PUBLIC_GOOGLE_ADS_ID || '';
const META_PIXEL_ID = process.env.NEXT_PUBLIC_META_PIXEL_ID || '';

export default function ConsentBasedTracking() {
  const [consentGiven, setConsentGiven] = useState(false);

  useEffect(() => {
    if (localStorage.getItem('cookieConsent') === 'accepted') {
      setConsentGiven(true);
    }

    const handler = (e: Event) => {
      const decision = (e as CustomEvent<string>).detail;
      setConsentGiven(decision === 'accepted');
    };
    window.addEventListener('cookie-consent-changed', handler);
    return () => window.removeEventListener('cookie-consent-changed', handler);
  }, []);

  if (!consentGiven) return null;

  return (
    <>
      {/* ── Google Tag Manager ── */}
      {GTM_ID && (
        <>
          <noscript>
            <iframe
              src={`https://www.googletagmanager.com/ns.html?id=${GTM_ID}`}
              height="0"
              width="0"
              style={{ display: 'none', visibility: 'hidden' }}
            />
          </noscript>
          <Script id="gtm-script" strategy="afterInteractive">
            {`(function(w,d,s,l,i){w[l]=w[l]||[];w[l].push({'gtm.start':
            new Date().getTime(),event:'gtm.js'});var f=d.getElementsByTagName(s)[0],
            j=d.createElement(s),dl=l!='dataLayer'?'&l='+l:'';j.async=true;j.src=
            'https://www.googletagmanager.com/gtm.js?id='+i+dl;f.parentNode.insertBefore(j,f);
            })(window,document,'script','dataLayer','${GTM_ID}');`}
          </Script>
        </>
      )}

      {/* ── Google Analytics 4 ── */}
      {GA_ID && (
        <>
          <Script
            src={`https://www.googletagmanager.com/gtag/js?id=${GA_ID}`}
            strategy="afterInteractive"
          />
          <Script id="ga-script" strategy="afterInteractive">
            {`window.dataLayer = window.dataLayer || [];
            function gtag(){dataLayer.push(arguments);}
            gtag('js', new Date());
            gtag('config', '${GA_ID}', { send_page_view: true });`}
          </Script>
        </>
      )}

      {/* ── Google Ads conversion tracking ── */}
      {GOOGLE_ADS_ID && !GA_ID && (
        // Only load standalone gTag if GA4 is NOT already loaded
        // (if GA4 is present, Google Ads should be configured through GTM / linked account)
        <>
          <Script
            src={`https://www.googletagmanager.com/gtag/js?id=${GOOGLE_ADS_ID}`}
            strategy="afterInteractive"
          />
          <Script id="google-ads-script" strategy="afterInteractive">
            {`window.dataLayer = window.dataLayer || [];
            function gtag(){dataLayer.push(arguments);}
            gtag('js', new Date());
            gtag('config', '${GOOGLE_ADS_ID}');`}
          </Script>
        </>
      )}
      {GOOGLE_ADS_ID && GA_ID && (
        // GA4 already loaded – just add the Ads ID to the same gtag config
        <Script id="google-ads-config" strategy="afterInteractive">
          {`if(typeof gtag === 'function'){ gtag('config', '${GOOGLE_ADS_ID}'); }`}
        </Script>
      )}

      {/* ── Microsoft Clarity ── */}
      {CLARITY_ID && (
        <Script id="clarity-script" strategy="afterInteractive">
          {`(function(c,l,a,r,i,t,y){
              c[a]=c[a]||function(){(c[a].q=c[a].q||[]).push(arguments)};
              t=l.createElement(r);t.async=1;t.src="https://www.clarity.ms/tag/"+i;
              y=l.getElementsByTagName(r)[0];y.parentNode.insertBefore(t,y);
          })(window, document, "clarity", "script", "${CLARITY_ID}");`}
        </Script>
      )}

      {/* ── Meta (Facebook) Pixel ── */}
      {META_PIXEL_ID && (
        <Script id="meta-pixel-script" strategy="afterInteractive">
          {`!function(f,b,e,v,n,t,s)
          {if(f.fbq)return;n=f.fbq=function(){n.callMethod?
          n.callMethod.apply(n,arguments):n.queue.push(arguments)};
          if(!f._fbq)f._fbq=n;n.push=n;n.loaded=!0;n.version='2.0';
          n.queue=[];t=b.createElement(e);t.async=!0;
          t.src=v;s=b.getElementsByTagName(e)[0];
          s.parentNode.insertBefore(t,s)}(window, document,'script',
          'https://connect.facebook.net/en_US/fbevents.js');
          fbq('init', '${META_PIXEL_ID}');
          fbq('track', 'PageView');`}
        </Script>
      )}
    </>
  );
}
