import { permanentRedirect } from 'next/navigation';

/**
 * Legacy route: /brand/[name]
 * Permanently redirected to /brands/[name] via next.config.js redirects.
 * This server component is a safety fallback.
 */
export default async function LegacyBrandRedirect({ params }: { params: Promise<{ name: string }> }) {
  const { name } = await params;
  permanentRedirect(`/brands/${encodeURIComponent(name)}`);
}
