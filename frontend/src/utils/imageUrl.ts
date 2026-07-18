/** Inline SVG data URI — no third-party placeholder host. */
export const IMAGE_PLACEHOLDER_DATA_URI =
  "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='200' height='200' viewBox='0 0 200 200'%3E%3Crect width='200' height='200' fill='%23f3f4f6'/%3E%3Ctext x='50%25' y='50%25' dominant-baseline='middle' text-anchor='middle' font-size='14' fill='%239ca3af'%3ENo Image%3C/text%3E%3C/svg%3E";

/**
 * Constructs a full image URL from a relative path
 * Handles both absolute URLs and relative paths
 * Strips /api from base URL for static file serving
 *
 * @param {string} imagePath - The image path (can be absolute URL or relative path like /uploads/...)
 * @returns {string | null} - Full URL to the image or null if path is empty
 */
export const getImageUrl = (imagePath: string | null | undefined): string | null => {
  if (!imagePath) return null;

  // If already a full URL, return as is (intercepting via.placeholder.com)
  if (imagePath.startsWith('http')) {
    if (imagePath.includes('via.placeholder.com')) {
      try {
        const url = new URL(imagePath);
        const textParam = url.searchParams.get('text') || 'Stationery Product';
        return `/placeholder?text=${encodeURIComponent(textParam)}`;
      } catch (_) {
        return '/placeholder?text=Stationery%20Product';
      }
    }
    return imagePath;
  }

  // Default host aligns with local FastAPI (8000); set NEXT_PUBLIC_API_URL in env for other setups.
  const baseUrl = (process.env.NEXT_PUBLIC_API_URL || '').replace('/api', '');

  // Ensure path starts with /
  const path = imagePath.startsWith('/') ? imagePath : '/' + imagePath;

  return `${baseUrl}${path}`;
};

/**
 * Constructs image URL with fallback placeholder
 *
 * @param {string} imagePath - The image path
 * @param {string} placeholder - Placeholder URL (default: inline SVG)
 * @returns {string} - Full URL to the image or placeholder
 */
export const getImageUrlWithFallback = (
  imagePath: string | null | undefined,
  placeholder: string = IMAGE_PLACEHOLDER_DATA_URI
): string => {
  return getImageUrl(imagePath) || placeholder;
};
