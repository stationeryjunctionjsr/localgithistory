import { permanentRedirect } from 'next/navigation';

/**
 * Legacy route: /brand/[name]
 * Permanently redirected to /brands/[name] via next.config.js redirects.
 * This server component is a safety fallback.
 */
export default function LegacyBrandRedirect({ params }: { params: { name: string } }) {
  permanentRedirect(`/brands/${encodeURIComponent(params.name)}`);
}
