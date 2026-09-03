'use client';

import Link from 'next/link';
import { useLanguage } from '@/context/LanguageContext';

export default function NotFound() {
  const { t } = useLanguage();

  return (
    <main className="flex min-h-screen flex-col items-center justify-center gap-6 bg-gray-50 px-4 text-center">
      <div className="flex h-24 w-24 items-center justify-center rounded-full bg-emerald-50">
        <span className="text-5xl font-bold text-emerald-800">4</span>
        <span className="text-5xl font-bold text-emerald-400">0</span>
        <span className="text-5xl font-bold text-emerald-800">4</span>
      </div>

      <div className="max-w-md">
        <h1 className="mb-2 text-3xl font-bold text-gray-800">{t('pages.notFound.title', 'Page Not Found')}</h1>
        <p className="text-gray-500">
          {t('pages.notFound.message', "The page you're looking for doesn't exist or may have been moved.")}
        </p>
      </div>

      <div className="flex flex-col gap-3 sm:flex-row">
        <Link
          href="/customer"
          className="rounded-xl bg-emerald-800 px-6 py-2.5 font-semibold text-white transition hover:bg-emerald-900"
        >
          {t('common.viewAll', 'Browse Products')}
        </Link>
        <Link
          href="/"
          className="rounded-xl border border-gray-300 bg-white px-6 py-2.5 font-semibold text-gray-700 transition hover:bg-gray-50"
        >
          {t('pages.notFound.goHome', 'Go to Home')}
        </Link>
      </div>

      <p className="text-sm text-gray-400">
        {t('support.howHelp', 'Looking for something specific?')}
        <br />
        <Link href="/support" className="text-emerald-700 underline hover:text-emerald-900">
          {t('support.submitTicket', 'Contact support')}
        </Link>
      </p>
    </main>
  );
}
