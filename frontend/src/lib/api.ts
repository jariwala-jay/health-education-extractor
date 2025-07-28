import axios from 'axios';

// API Configuration
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// Create axios instance
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Types for API responses
export interface PDFDocument {
  id: string;
  filename: string;
  file_size_bytes: number;
  processing_status: 'uploaded' | 'parsing' | 'chunking' | 'processing' | 'completed' | 'failed';
  uploaded_at: string;
  total_pages?: number;
  total_chunks?: number;
  total_articles_generated?: number;
  processing_started_at?: string;
  processing_completed_at?: string;
  error_message?: string;
}

export interface HealthArticle {
  id: string;
  title: string;
  category: string;
  image_url?: string;
  medical_condition_tags: string[];
  content: string;
  processing_status: 'draft' | 'reviewed' | 'approved' | 'rejected';
  reading_level_score?: number;
  source_pdf_id?: string;
  created_at: string;
  updated_at: string;
}

export interface ExportSummary {
  total_articles: number;
  status_breakdown: Record<string, number>;
  category_breakdown: Record<string, number>;
  recent_articles: Array<{
    id: string;
    title: string;
    category: string;
    status: string;
    created_at: string;
  }>;
}

// API Functions

// Health Check
export const healthCheck = async (): Promise<{ status: string; service: string }> => {
  const response = await apiClient.get('/health');
  return response.data;
};

// PDF Processing APIs
export const uploadPDF = async (file: File): Promise<PDFDocument> => {
  const formData = new FormData();
  formData.append('file', file);
  
  const response = await apiClient.post('/api/v1/pdf/upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
  return response.data;
};

export const getPDFStatus = async (pdfId: string): Promise<PDFDocument> => {
  const response = await apiClient.get(`/api/v1/pdf/status/${pdfId}`);
  return response.data;
};

export const listPDFs = async (
  page: number = 1,
  perPage: number = 10,
  status?: string
): Promise<{
  documents: PDFDocument[];
  total: number;
  page: number;
  per_page: number;
}> => {
  const params: any = { page, per_page: perPage };
  if (status) params.status = status;
  
  const response = await apiClient.get('/api/v1/pdf/list', { params });
  return response.data;
};

export const deletePDF = async (pdfId: string): Promise<{ message: string }> => {
  const response = await apiClient.delete(`/api/v1/pdf/${pdfId}`);
  return response.data;
};

// Health Articles APIs
export const listArticles = async (
  page: number = 1,
  perPage: number = 10,
  category?: string,
  status?: string,
  search?: string,
  tags?: string[]
): Promise<HealthArticle[]> => {
  const params: any = { page, per_page: perPage };
  if (category) params.category = category;
  if (status) params.status = status;
  if (search) params.search = search;
  if (tags && tags.length > 0) params.tags = tags;
  
  const response = await apiClient.get('/api/v1/articles/', { params });
  return response.data;
};

export const getArticle = async (articleId: string): Promise<HealthArticle> => {
  const response = await apiClient.get(`/api/v1/articles/${articleId}`);
  return response.data;
};

export const updateArticle = async (
  articleId: string,
  updates: Partial<HealthArticle>
): Promise<HealthArticle> => {
  const response = await apiClient.put(`/api/v1/articles/${articleId}`, updates);
  return response.data;
};

export const deleteArticle = async (articleId: string): Promise<{ message: string }> => {
  const response = await apiClient.delete(`/api/v1/articles/${articleId}`);
  return response.data;
};

export const approveArticle = async (articleId: string): Promise<{ message: string }> => {
  const response = await apiClient.post(`/api/v1/articles/${articleId}/approve`);
  return response.data;
};

export const rejectArticle = async (
  articleId: string,
  reason?: string
): Promise<{ message: string }> => {
  const response = await apiClient.post(`/api/v1/articles/${articleId}/reject`, { reason });
  return response.data;
};

export const findSimilarArticles = async (
  articleId: string,
  limit: number = 5
): Promise<HealthArticle[]> => {
  const response = await apiClient.get(`/api/v1/articles/search/similar/${articleId}`, {
    params: { limit },
  });
  return response.data;
};

// Export APIs
export const exportArticlesJSON = async (
  category?: string,
  status?: string,
  tags?: string[],
  approvedOnly: boolean = true,
  sourcePdfId?: string
): Promise<Blob> => {
  const params = new URLSearchParams();
  if (category) params.append('category', category);
  if (status) params.append('status', status);
  if (tags && tags.length > 0) {
    tags.forEach(tag => params.append('tags', tag));
  }
  params.append('approved_only', approvedOnly.toString());
  if (sourcePdfId) params.append('source_pdf_id', sourcePdfId);

  const response = await apiClient.get(`/api/v1/articles/export/json?${params.toString()}`, {
    responseType: 'blob'
  });
  return response.data;
};

export const getExportSummary = async (sourcePdfId?: string): Promise<ExportSummary> => {
  const params = new URLSearchParams();
  if (sourcePdfId) params.append('source_pdf_id', sourcePdfId);
  
  const response = await apiClient.get(`/api/v1/articles/export/summary?${params.toString()}`);
  return response.data;
};

// PDF-specific article functions
export const getArticlesByPdf = async (
  pdfId: string,
  page: number = 1,
  perPage: number = 50
): Promise<{
  articles: HealthArticle[];
  pagination: {
    page: number;
    per_page: number;
    total: number;
    pages: number;
  };
  pdf_id: string;
}> => {
  const response = await apiClient.get(`/api/v1/articles/by-pdf/${pdfId}?page=${page}&per_page=${perPage}`);
  return response.data;
};

// Utility functions
export const downloadBlob = (blob: Blob, filename: string) => {
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.style.display = 'none';
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  window.URL.revokeObjectURL(url);
  document.body.removeChild(a);
};

export const isAPIError = (error: any): error is { response: { data: { detail: string } } } => {
  return error?.response?.data?.detail;
};

export const getErrorMessage = (error: any): string => {
  if (isAPIError(error)) {
    return error.response.data.detail;
  }
  return error?.message || 'An unexpected error occurred';
}; 