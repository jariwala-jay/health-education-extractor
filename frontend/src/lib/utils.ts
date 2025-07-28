/**
 * Utility functions for the Health Education Extractor frontend
 */

/**
 * Parse a timestamp from the backend as UTC and return a proper Date object
 * The backend sends timestamps without timezone info, but they are actually UTC
 */
export function parseUTCTimestamp(timestamp: string): Date {
  // If the timestamp doesn't end with 'Z', add it to indicate UTC
  if (!timestamp.endsWith('Z') && !timestamp.includes('+')) {
    return new Date(timestamp + 'Z');
  }
  return new Date(timestamp);
}

/**
 * Format a timestamp for display using date-fns with proper timezone handling
 */
export function formatTimestamp<T extends Record<string, unknown>>(
  timestamp: string, 
  formatFn: (date: Date, options?: T) => string, 
  options?: T
): string {
  const date = parseUTCTimestamp(timestamp);
  return formatFn(date, options);
} 