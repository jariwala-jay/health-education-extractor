/**
 * Centralized constants for the Health Education Extractor application
 */

// Health article categories - keep in sync with backend CategoryEnum
export const HEALTH_CATEGORIES = [
  'Hypertension',
  'Diabetes',
  'Kidney Health',
  'Nutrition',
  'Physical Activity',
  'Obesity',
  'General Health'
] as const;

// Type for category values
export type HealthCategory = typeof HEALTH_CATEGORIES[number];

// Processing status options
export const PROCESSING_STATUSES = [
  'draft',
  'reviewed',
  'approved',
  'rejected'
] as const;

export type ProcessingStatus = typeof PROCESSING_STATUSES[number];

// Category colors for UI display
export const CATEGORY_COLORS: Record<HealthCategory, string> = {
  'Hypertension': 'bg-red-100 text-red-800',
  'Diabetes': 'bg-purple-100 text-purple-800',
  'Kidney Health': 'bg-blue-100 text-blue-800',
  'Nutrition': 'bg-green-100 text-green-800',
  'Physical Activity': 'bg-orange-100 text-orange-800',
  'Obesity': 'bg-yellow-100 text-yellow-800',
  'General Health': 'bg-gray-100 text-gray-800',
};

// Status colors for UI display
export const STATUS_COLORS: Record<ProcessingStatus, string> = {
  'approved': 'text-green-600 bg-green-100',
  'reviewed': 'text-blue-600 bg-blue-100',
  'rejected': 'text-red-600 bg-red-100',
  'draft': 'text-yellow-600 bg-yellow-100',
};

// Export utility function to get category color
export const getCategoryColor = (category: string): string => {
  return CATEGORY_COLORS[category as HealthCategory] || 'bg-gray-100 text-gray-800';
};

// Export utility function to get status color
export const getStatusColor = (status: string): string => {
  return STATUS_COLORS[status as ProcessingStatus] || 'text-gray-600 bg-gray-100';
}; 