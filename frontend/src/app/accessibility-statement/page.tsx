'use client';

import { useLanguage } from '@/context/LanguageContext';
import Link from 'next/link';

export default function AccessibilityStatementPage() {
  const { t } = useLanguage();

  return (
    <div className="max-w-4xl mx-auto px-4 py-12">
      <h1 className="text-3xl font-bold mb-2">{t('pages.accessibilityStatement.title', 'Accessibility Statement')}</h1>
      <p className="text-gray-500 mb-8">{t('pages.accessibilityStatement.subtitle', 'Our commitment to digital accessibility for all users.')}</p>

      <div className="prose prose-green max-w-none space-y-8">

        <section aria-labelledby="commitment-heading">
          <h2 id="commitment-heading" className="text-xl font-semibold mb-3">Our Commitment</h2>
          <p>
            Stationery Junction is committed to ensuring digital accessibility for people with disabilities.
            We are continually improving the user experience for everyone and applying relevant accessibility standards.
          </p>
        </section>

        <section aria-labelledby="standards-heading">
          <h2 id="standards-heading" className="text-xl font-semibold mb-3">Conformance Status</h2>
          <p>
            We aim to conform to the{' '}
            <a
              href="https://www.w3.org/TR/WCAG21/"
              target="_blank"
              rel="noopener noreferrer"
              className="text-green-700 underline"
            >
              Web Content Accessibility Guidelines (WCAG) 2.1 Level AA
            </a>
            . We also follow the{' '}
            <a
              href="https://guidelines.india.gov.in/"
              target="_blank"
              rel="noopener noreferrer"
              className="text-green-700 underline"
            >
              Guidelines for Indian Government Websites (GIGW) 3.0
            </a>
            .
          </p>
          <p className="mt-2">
            <strong>Current status:</strong> Partially conformant. Some content may not yet fully meet all WCAG 2.1 AA success criteria.
          </p>
        </section>

        <section aria-labelledby="features-heading">
          <h2 id="features-heading" className="text-xl font-semibold mb-3">Accessibility Features</h2>
          <ul className="list-disc list-inside space-y-1">
            <li>Support for all 12 major Indian languages via the Language Switcher</li>
            <li>High-contrast display mode</li>
            <li>Adjustable font size (large text mode)</li>
            <li>Dyslexia-friendly font option</li>
            <li>Reduced motion mode</li>
            <li>Always-visible focus rings for keyboard navigation</li>
            <li>Skip-to-main-content link at the top of every page</li>
            <li>Semantic HTML with ARIA landmarks and labels throughout</li>
            <li>Compatible with screen readers (VoiceOver, NVDA, JAWS)</li>
            <li>Minimum 4.5:1 colour contrast ratio in default mode</li>
          </ul>
        </section>

        <section aria-labelledby="known-issues-heading">
          <h2 id="known-issues-heading" className="text-xl font-semibold mb-3">Known Limitations</h2>
          <p>
            We are aware of the following areas that are still being improved:
          </p>
          <ul className="list-disc list-inside space-y-1">
            <li>Some third-party embeds (payment gateways) may not be fully accessible</li>
            <li>Certain complex data tables may lack full ARIA markup</li>
            <li>PDF documents are not yet screen-reader optimised</li>
          </ul>
          <p className="mt-2">
            We are actively working to address these issues in upcoming releases.
          </p>
        </section>

        <section aria-labelledby="technical-heading">
          <h2 id="technical-heading" className="text-xl font-semibold mb-3">Technical Specifications</h2>
          <p>
            This website relies on the following technologies for conformance with WCAG 2.1:
          </p>
          <ul className="list-disc list-inside space-y-1">
            <li>HTML5</li>
            <li>CSS3</li>
            <li>JavaScript / React</li>
            <li>WAI-ARIA 1.2</li>
          </ul>
          <p className="mt-2">
            Accessibility was tested using NVDA, VoiceOver (macOS/iOS), and automated tools including axe DevTools and Lighthouse.
          </p>
        </section>

        <section aria-labelledby="feedback-heading">
          <h2 id="feedback-heading" className="text-xl font-semibold mb-3">Feedback & Contact</h2>
          <p>
            We welcome your feedback on the accessibility of Stationery Junction. If you experience barriers or have suggestions:
          </p>
          <ul className="list-disc list-inside space-y-1">
            <li>
              <strong>Submit a support ticket:</strong>{' '}
              <Link href="/support" className="text-green-700 underline">
                Customer Support
              </Link>
            </li>
            <li>
              <strong>Email:</strong>{' '}
              <a href={`mailto:${process.env.NEXT_PUBLIC_SUPPORT_EMAIL || 'support@stationeryjunction.com'}`} className="text-green-700 underline">
                {process.env.NEXT_PUBLIC_SUPPORT_EMAIL || 'support@stationeryjunction.com'}
              </a>
            </li>
          </ul>
          <p className="mt-2">
            We aim to respond to accessibility feedback within 2 business days.
          </p>
        </section>

        <section aria-labelledby="enforcement-heading">
          <h2 id="enforcement-heading" className="text-xl font-semibold mb-3">Formal Complaints</h2>
          <p>
            If you are not satisfied with our response to your accessibility feedback, you may contact the{' '}
            <a
              href="https://www.meity.gov.in/"
              target="_blank"
              rel="noopener noreferrer"
              className="text-green-700 underline"
            >
              Ministry of Electronics and Information Technology (MeitY)
            </a>
            .
          </p>
        </section>

        <section aria-labelledby="date-heading">
          <h2 id="date-heading" className="text-xl font-semibold mb-3">Review & Update</h2>
          <p>
            This statement was last reviewed on{' '}
            <time dateTime="2026-09-02">2 September 2026</time>.
            We review this statement every six months.
          </p>
        </section>

      </div>
    </div>
  );
}
