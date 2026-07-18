/**
 * Date/time utilities – always IST (Asia/Kolkata).
 *
 * Every user-facing timestamp in the application MUST use these helpers
 * so that times are consistently displayed in Indian Standard Time.
 */

const IST_TIMEZONE = 'Asia/Kolkata';
const IST_LOCALE = 'en-IN';

/**
 * Parses a date string robustly, ensuring naive UTC strings (without timezone suffix)
 * are parsed as UTC instead of local timezone.
 */
function parseDate(dateString: string | undefined | null): Date {
  if (!dateString) return new Date(NaN);
  let normalized = dateString.trim();
  // Replace space between date and time with 'T' if present (e.g. "2026-06-03 12:00:00")
  if (/^\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}/.test(normalized)) {
    normalized = normalized.replace(/\s+/, 'T');
  }
  // If it contains a time component (has ':') and lacks timezone info, append 'Z'
  if (normalized.includes(':') && !normalized.endsWith('Z') && !/[+-]\d{2}(:?\d{2})?$/.test(normalized)) {
    normalized += 'Z';
  }
  return new Date(normalized);
}

/**
 * Format a date string to IST date + time.
 * Example output: "25/02/2026, 09:07 pm"
 */
export function formatDateTimeIST(dateString: string | undefined | null): string {
  if (!dateString) return 'N/A';
  try {
    const date = parseDate(dateString);
    if (isNaN(date.getTime())) return 'N/A';
    return date.toLocaleString(IST_LOCALE, {
      timeZone: IST_TIMEZONE,
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      hour12: true,
    });
  } catch {
    return 'N/A';
  }
}

/**
 * Format a date string to IST date only.
 * Example output: "25/02/2026"
 */
export function formatDateIST(dateString: string | undefined | null): string {
  if (!dateString) return 'N/A';
  try {
    const date = parseDate(dateString);
    if (isNaN(date.getTime())) return 'N/A';
    return date.toLocaleDateString(IST_LOCALE, {
      timeZone: IST_TIMEZONE,
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
    });
  } catch {
    return 'N/A';
  }
}

/**
 * Format a date string to IST time only.
 * Example output: "09:07 pm"
 */
export function formatTimeIST(dateString: string | undefined | null): string {
  if (!dateString) return 'N/A';
  try {
    const date = parseDate(dateString);
    if (isNaN(date.getTime())) return 'N/A';
    return date.toLocaleTimeString(IST_LOCALE, {
      timeZone: IST_TIMEZONE,
      hour: '2-digit',
      minute: '2-digit',
      hour12: true,
    });
  } catch {
    return 'N/A';
  }
}

