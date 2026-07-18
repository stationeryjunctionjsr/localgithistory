import Link from 'next/link';
import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: '404 – Page Not Found | Stationery Junction',
  description: 'The page you are looking for could not be found.',
};

export default function NotFound() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center gap-6 bg-gray-50 px-4 text-center">
      <div className="flex h-24 w-24 items-center justify-center rounded-full bg-emerald-50">
        <span className="text-5xl font-bold text-emerald-800">4</span>
        <span className="text-5xl font-bold text-emerald-400">0</span>
        <span className="text-5xl font-bold text-emerald-800">4</span>
      </div>

      <div className="max-w-md">
        <h1 className="mb-2 text-3xl font-bold text-gray-800">Page Not Found</h1>
        <p className="text-gray-500">
          The page you&apos;re looking for doesn&apos;t exist or may have been moved.
        </p>
      </div>

      <div className="flex flex-col gap-3 sm:flex-row">
        <Link
          href="/customer"
          className="rounded-xl bg-emerald-800 px-6 py-2.5 font-semibold text-white transition hover:bg-emerald-900"
        >
          Browse Products
        </Link>
        <Link
          href="/"
          className="rounded-xl border border-gray-300 bg-white px-6 py-2.5 font-semibold text-gray-700 transition hover:bg-gray-50"
        >
          Go to Home
        </Link>
      </div>

      <p className="text-sm text-gray-400">
        Looking for something specific?{' '}
        <Link href="/customer/support" className="text-emerald-700 underline hover:text-emerald-900">
          Contact support
        </Link>
      </p>
    </main>
  );
}
