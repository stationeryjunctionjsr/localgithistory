import { permanentRedirect } from 'next/navigation';

/**
 * /landingpage is permanently redirected to / via next.config.js redirects.
 * This server component is a safety fallback.
 */
export default function LandingPage() {
  permanentRedirect('/');
}
