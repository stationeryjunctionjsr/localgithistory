'use client';

import { useLanguage } from '@/context/LanguageContext';
import Link from 'next/link';

export default function TermsOfUsePage() {
  const { t } = useLanguage();

  return (
    <div className="max-w-4xl mx-auto px-4 py-12">
      <h1 className="text-3xl font-bold mb-2">{t('pages.terms.title', 'Terms of Use')}</h1>
      <p className="text-gray-500 mb-2">{t('pages.terms.subtitle', 'Please read these terms carefully before using our services.')}</p>
      <p className="text-sm text-gray-400 mb-8">
        Last updated: <time dateTime="2026-09-02">2 September 2026</time>
      </p>

      <div className="prose prose-green max-w-none space-y-8">

        <section aria-labelledby="acceptance-heading">
          <h2 id="acceptance-heading" className="text-xl font-semibold mb-3">1. Acceptance of Terms</h2>
          <p>
            By accessing or using the Stationery Junction website and mobile application (collectively, the &quot;Platform&quot;),
            you agree to be bound by these Terms of Use and our{' '}
            <Link href="/privacy-policy" className="text-green-700 underline">Privacy Policy</Link>.
            If you do not agree with any part of these terms, please do not use the Platform.
          </p>
        </section>

        <section aria-labelledby="eligibility-heading">
          <h2 id="eligibility-heading" className="text-xl font-semibold mb-3">2. Eligibility</h2>
          <p>
            The Platform is intended for use by businesses and individuals aged 18 years or older.
            By using the Platform, you represent and warrant that you meet these eligibility requirements.
          </p>
        </section>

        <section aria-labelledby="account-heading">
          <h2 id="account-heading" className="text-xl font-semibold mb-3">3. Account Registration</h2>
          <ul className="list-disc list-inside space-y-1">
            <li>You are responsible for maintaining the confidentiality of your account credentials.</li>
            <li>You are responsible for all activities that occur under your account.</li>
            <li>You must notify us immediately if you suspect unauthorised use of your account.</li>
            <li>We reserve the right to suspend or terminate accounts that violate these terms.</li>
          </ul>
        </section>

        <section aria-labelledby="products-heading">
          <h2 id="products-heading" className="text-xl font-semibold mb-3">4. Products and Orders</h2>
          <ul className="list-disc list-inside space-y-1">
            <li>All product listings are subject to availability.</li>
            <li>Prices are subject to change without prior notice.</li>
            <li>We reserve the right to refuse or cancel any order at our discretion.</li>
            <li>Product images are for illustrative purposes; actual products may vary slightly.</li>
          </ul>
        </section>

        <section aria-labelledby="payments-heading">
          <h2 id="payments-heading" className="text-xl font-semibold mb-3">5. Payments</h2>
          <p>
            Payments are processed through secure third-party payment gateways. We do not store your
            full payment card details. By completing a purchase, you confirm that you have the right
            to use the payment method provided.
          </p>
        </section>

        <section aria-labelledby="returns-heading">
          <h2 id="returns-heading" className="text-xl font-semibold mb-3">6. Returns and Refunds</h2>
          <p>
            Our return and refund policy is described on the product pages and in our order confirmation
            emails. Wholesale orders may have different return terms as agreed at the time of purchase.
          </p>
        </section>

        <section aria-labelledby="ip-heading">
          <h2 id="ip-heading" className="text-xl font-semibold mb-3">7. Intellectual Property</h2>
          <p>
            All content on the Platform, including text, graphics, logos, and software, is the property
            of Stationery Junction or its content suppliers and is protected by applicable Indian and
            international intellectual property laws. You may not reproduce, distribute, or create
            derivative works without our express written consent.
          </p>
        </section>

        <section aria-labelledby="prohibited-heading">
          <h2 id="prohibited-heading" className="text-xl font-semibold mb-3">8. Prohibited Activities</h2>
          <p>You agree not to:</p>
          <ul className="list-disc list-inside space-y-1">
            <li>Use the Platform for any unlawful purpose</li>
            <li>Attempt to gain unauthorised access to any part of the Platform</li>
            <li>Transmit malicious code or interfere with Platform operations</li>
            <li>Scrape, crawl, or harvest data without written permission</li>
            <li>Impersonate any person or entity</li>
          </ul>
        </section>

        <section aria-labelledby="liability-heading">
          <h2 id="liability-heading" className="text-xl font-semibold mb-3">9. Limitation of Liability</h2>
          <p>
            To the maximum extent permitted by law, Stationery Junction shall not be liable for any
            indirect, incidental, special, consequential, or punitive damages arising from your use of
            the Platform.
          </p>
        </section>

        <section aria-labelledby="governing-heading">
          <h2 id="governing-heading" className="text-xl font-semibold mb-3">10. Governing Law</h2>
          <p>
            These Terms of Use shall be governed by and construed in accordance with the laws of India.
            Any disputes arising from these terms shall be subject to the exclusive jurisdiction of the
            courts in Jharkhand, India.
          </p>
        </section>

        <section aria-labelledby="changes-heading">
          <h2 id="changes-heading" className="text-xl font-semibold mb-3">11. Changes to These Terms</h2>
          <p>
            We reserve the right to modify these Terms of Use at any time. Continued use of the Platform
            after changes are posted constitutes your acceptance of the revised terms. We will notify
            registered users of material changes via email.
          </p>
        </section>

        <section aria-labelledby="contact-heading">
          <h2 id="contact-heading" className="text-xl font-semibold mb-3">12. Contact Us</h2>
          <p>
            For questions about these Terms of Use, please contact us via our{' '}
            <Link href="/support" className="text-green-700 underline">Customer Support</Link> page
            or email us at{' '}
            <a
              href={`mailto:${process.env.NEXT_PUBLIC_SUPPORT_EMAIL || 'legal@stationeryjunction.com'}`}
              className="text-green-700 underline"
            >
              {process.env.NEXT_PUBLIC_SUPPORT_EMAIL || 'legal@stationeryjunction.com'}
            </a>
            .
          </p>
        </section>

      </div>
    </div>
  );
}
