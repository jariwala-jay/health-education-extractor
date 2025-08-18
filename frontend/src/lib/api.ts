import axios from "axios";

// API Configuration
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// Create axios instance
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

// Export the apiClient for direct use
export { apiClient };

// Add request interceptor to include auth token
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem("auth_token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Add response interceptor to handle auth errors
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Token expired or invalid, redirect to login
      localStorage.removeItem("auth_token");
      window.location.href = "/login";
    }
    return Promise.reject(error);
  }
);

// Types for API responses
export interface PDFDocument {
  id: string;
  filename: string;
  file_size_bytes: number;
  processing_status:
    | "uploaded"
    | "parsing"
    | "chunking"
    | "processing"
    | "completed"
    | "failed";
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
  official_sources?: string[];
  learn_more_url?: string;
  processing_status:
    | "draft"
    | "reviewed"
    | "approved"
    | "uploaded"
    | "rejected";
  reading_level_score?: number;
  source_pdf_id?: string;
  created_at: string;
  updated_at: string;
}

export interface ExportSummary {
  total_articles: number;
  ready_to_upload: number;
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

export interface UploadResult {
  message: string;
  uploaded_at: string;
  total_articles: number;
  uploaded_articles: number;
  failed_articles: number;
  filters_applied: {
    category?: string;
    tags?: string[];
    source_pdf_id?: string;
  };
  failed_details?: Array<{
    title: string;
    reason: string;
  }>;
}

// API Functions

// Health Check
export const healthCheck = async (): Promise<{
  status: string;
  service: string;
}> => {
  const response = await apiClient.get("/health");
  return response.data;
};

// PDF Processing APIs
export const uploadPDF = async (file: File): Promise<PDFDocument> => {
  const formData = new FormData();
  formData.append("file", file);

  const response = await apiClient.post("/api/v1/pdf/upload", formData, {
    headers: {
      "Content-Type": "multipart/form-data",
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
  const params: Record<string, string | number> = { page, per_page: perPage };
  if (status) params.status = status;

  const response = await apiClient.get("/api/v1/pdf/list", { params });
  return response.data;
};

export const deletePDF = async (
  pdfId: string
): Promise<{ message: string }> => {
  const response = await apiClient.delete(`/api/v1/pdf/${pdfId}`);
  return response.data;
};

export const downloadPDF = async (
  pdfId: string,
  filename: string
): Promise<void> => {
  const response = await apiClient.get(`/api/v1/pdf/${pdfId}/download`, {
    responseType: "blob",
  });

  downloadBlob(response.data, filename);
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
  const params: Record<string, string | number | string[]> = {
    page,
    per_page: perPage,
  };
  if (category) params.category = category;
  if (status) params.status = status;
  if (search) params.search = search;
  if (tags && tags.length > 0) params.tags = tags;

  const response = await apiClient.get("/api/v1/articles/", { params });
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
  const response = await apiClient.put(
    `/api/v1/articles/${articleId}`,
    updates
  );
  return response.data;
};

export const deleteArticle = async (
  articleId: string
): Promise<{ message: string }> => {
  const response = await apiClient.delete(`/api/v1/articles/${articleId}`);
  return response.data;
};

export const approveArticle = async (
  articleId: string
): Promise<{ message: string }> => {
  const response = await apiClient.post(
    `/api/v1/articles/${articleId}/approve`
  );
  return response.data;
};

export const rejectArticle = async (
  articleId: string,
  reason?: string
): Promise<{ message: string }> => {
  const response = await apiClient.post(
    `/api/v1/articles/${articleId}/reject`,
    { reason }
  );
  return response.data;
};

export const findSimilarArticles = async (
  articleId: string,
  limit: number = 5
): Promise<HealthArticle[]> => {
  const response = await apiClient.get(
    `/api/v1/articles/search/similar/${articleId}`,
    {
      params: { limit },
    }
  );
  return response.data;
};

// Upload APIs
export const uploadArticlesToAppDatabase = async (
  category?: string,
  tags?: string[],
  sourcePdfId?: string
): Promise<UploadResult> => {
  const params = new URLSearchParams();
  if (category) params.append("category", category);
  if (tags && tags.length > 0) {
    tags.forEach((tag) => params.append("tags", tag));
  }
  if (sourcePdfId) params.append("source_pdf_id", sourcePdfId);

  const response = await apiClient.post(
    `/api/v1/articles/upload-to-app-database?${params.toString()}`
  );
  return response.data;
};

export const getExportSummary = async (
  sourcePdfId?: string
): Promise<ExportSummary> => {
  const params = new URLSearchParams();
  if (sourcePdfId) params.append("source_pdf_id", sourcePdfId);

  const response = await apiClient.get(
    `/api/v1/articles/export/summary?${params.toString()}`
  );
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
  const response = await apiClient.get(
    `/api/v1/articles/by-pdf/${pdfId}?page=${page}&per_page=${perPage}`
  );
  return response.data;
};

// Utility functions
export const downloadBlob = (blob: Blob, filename: string) => {
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.style.display = "none";
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  window.URL.revokeObjectURL(url);
  document.body.removeChild(a);
};

export const isAPIError = (
  error: unknown
): error is { response: { data: { detail: string } } } => {
  return Boolean(
    error &&
      typeof error === "object" &&
      "response" in error &&
      error.response &&
      typeof error.response === "object" &&
      "data" in error.response &&
      error.response.data &&
      typeof error.response.data === "object" &&
      "detail" in error.response.data
  );
};

export const getErrorMessage = (error: unknown): string => {
  if (isAPIError(error)) {
    return error.response.data.detail;
  }
  if (
    error &&
    typeof error === "object" &&
    "message" in error &&
    typeof error.message === "string"
  ) {
    return error.message;
  }
  return "An unexpected error occurred";
};

// Recipe Types
export interface RecipeOriginal {
  id: string;
  source_id?: string;
  title: string;
  image_url?: string;
  ready_in_minutes?: number;
  servings?: number;
  instructions: string[];
  cuisines: string[];
  dish_types: string[];
  diets: string[];
  vegetarian?: boolean;
  vegan?: boolean;
  gluten_free?: boolean;
  dairy_free?: boolean;
  health_score?: number;
  spoonacular_score?: number;
  normalized_ingredients: Array<{
    original?: string;
    name_raw?: string;
    quantity?: number;
    unit?: string;
    availability: "used" | "missed" | "unused";
  }>;
  created_at: string;
  updated_at: string;
  coverage_score?: number;
  eligible?: boolean;
  pantry_matches?: number;
  missing_count?: number;
  substitutions_count?: number;
}

export interface CuratedIngredient {
  name: string;
  quantity?: number;
  unit?: string;
  notes?: string;
}

export interface SubstitutionSuggestion {
  original: string;
  mapped_to?: string;
  reason?: string;
  confidence?: number;
}

export interface RecipeCurated {
  id: string;
  original_recipe_id: string;
  title: string;
  ingredients: CuratedIngredient[];
  instructions: string[];
  servings?: number;
  time_minutes?: number;
  curation_status: "draft" | "reviewed" | "approved" | "uploaded" | "rejected";
  coverage_score?: number;
  missing_ingredients: string[];
  substitution_suggestions: SubstitutionSuggestion[];
  reading_level_score?: number;
  reviewer_notes?: string;
  created_at: string;
  updated_at: string;
}

export interface RecipeAnalysis {
  recipe: {
    id: string;
    title: string;
  };
  coverage_score: number;
  eligible: boolean;
  pantry_matches: string[];
  missing: string[];
  substitutions: Array<{
    original: string;
    mapped_to: string;
    notes?: string;
    strength?: number;
  }>;
  params: {
    allow_substitutions: boolean;
    max_missing: number;
  };
}

// Recipe API Functions
export const listRecipes = async (
  page: number = 1,
  perPage: number = 20,
  search?: string,
  eligibleOnly: boolean = false,
  allowSubstitutions?: boolean,
  maxMissing?: number
): Promise<RecipeOriginal[]> => {
  const params: Record<string, string | number | boolean> = {
    page,
    per_page: perPage,
  };
  if (search) params.search = search;
  if (eligibleOnly) params.eligible_only = eligibleOnly;
  if (allowSubstitutions !== undefined)
    params.allow_substitutions = allowSubstitutions;
  if (maxMissing !== undefined) params.max_missing = maxMissing;

  const response = await apiClient.get("/api/v1/recipes/", { params });
  return response.data;
};

export const analyzeRecipe = async (
  recipeId: string,
  allowSubstitutions?: boolean,
  maxMissing?: number
): Promise<RecipeAnalysis> => {
  const params: Record<string, boolean | number> = {};
  if (allowSubstitutions !== undefined)
    params.allow_substitutions = allowSubstitutions;
  if (maxMissing !== undefined) params.max_missing = maxMissing;

  const response = await apiClient.get(`/api/v1/recipes/${recipeId}/analyze`, {
    params,
  });
  return response.data;
};

export const curateRecipe = async (
  recipeId: string,
  allowSubstitutions: boolean = true,
  maxMissing: number = 2,
  targetServings?: number
): Promise<{
  message: string;
  curated_id: string;
  original_id: string;
  title: string;
  coverage_score: number;
  ingredients_count: number;
  instructions_count: number;
  substitutions_applied: number;
  validation_errors: string[];
  confidence_score?: number;
  status: string;
}> => {
  const params: Record<string, boolean | number> = {
    allow_substitutions: allowSubstitutions,
    max_missing: maxMissing,
  };
  if (targetServings !== undefined) params.target_servings = targetServings;

  const response = await apiClient.post(
    `/api/v1/recipes/${recipeId}/curate`,
    null,
    { params }
  );
  return response.data;
};

export const listCuratedRecipes = async (
  page: number = 1,
  perPage: number = 20,
  status?: string
): Promise<
  Array<{
    id: string;
    original_recipe_id: string;
    title: string;
    curation_status: string;
    coverage_score?: number;
    ingredients_count: number;
    instructions_count: number;
    substitutions_count: number;
    created_at: string;
    updated_at: string;
  }>
> => {
  const params: Record<string, string | number> = {
    page,
    per_page: perPage,
  };
  if (status) params.status = status;

  const response = await apiClient.get("/api/v1/recipes/curated", { params });
  return response.data;
};

export const getCuratedRecipe = async (
  curatedId: string
): Promise<{
  curated: RecipeCurated;
  original?: {
    id: string;
    title: string;
    normalized_ingredients: Array<{
      original?: string;
      name_raw?: string;
      quantity?: number;
      unit?: string;
      availability: string;
    }>;
  };
}> => {
  const response = await apiClient.get(`/api/v1/recipes/curated/${curatedId}`);
  return response.data;
};

export const updateCuratedRecipe = async (
  curatedId: string,
  updates: Partial<RecipeCurated>
): Promise<{
  message: string;
  id: string;
  title: string;
  updated_at: string;
}> => {
  const response = await apiClient.put(
    `/api/v1/recipes/curated/${curatedId}`,
    updates
  );
  return response.data;
};

export const approveCuratedRecipe = async (
  curatedId: string
): Promise<{
  message: string;
  status: string;
}> => {
  const response = await apiClient.post(
    `/api/v1/recipes/curated/${curatedId}/approve`
  );
  return response.data;
};

export const rejectCuratedRecipe = async (
  curatedId: string,
  reason?: string
): Promise<{
  message: string;
  status: string;
}> => {
  const response = await apiClient.post(
    `/api/v1/recipes/curated/${curatedId}/reject`,
    {
      reason,
    }
  );
  return response.data;
};

// Full Spoonacular Recipe Format Interface
export interface SpoonacularRecipe {
  id: number;
  title: string;
  image?: string;
  imageType?: string;
  readyInMinutes?: number;
  servings?: number;
  sourceUrl?: string;
  vegetarian?: boolean;
  vegan?: boolean;
  glutenFree?: boolean;
  dairyFree?: boolean;
  veryHealthy?: boolean;
  cheap?: boolean;
  veryPopular?: boolean;
  sustainable?: boolean;
  lowFodmap?: boolean;
  weightWatcherSmartPoints?: number;
  gaps?: string;
  preparationMinutes?: number;
  cookingMinutes?: number;
  aggregateLikes?: number;
  healthScore?: number;
  creditsText?: string;
  license?: string;
  sourceName?: string;
  pricePerServing?: number;
  extendedIngredients?: Array<{
    id: number;
    aisle: string;
    image: string;
    consistency: string;
    name: string;
    nameClean: string;
    original: string;
    originalName: string;
    amount: number;
    unit: string;
    meta: string[];
    measures: {
      us: { amount: number; unitShort: string; unitLong: string };
      metric: { amount: number; unitShort: string; unitLong: string };
    };
  }>;
  summary?: string;
  cuisines?: string[];
  dishTypes?: string[];
  diets?: string[];
  occasions?: string[];
  analyzedInstructions?: Array<{
    name: string;
    steps: Array<{
      number: number;
      step: string;
      ingredients?: Array<{
        id: number;
        name: string;
        localizedName: string;
        image: string;
      }>;
      equipment?: Array<{
        id: number;
        name: string;
        localizedName: string;
        image: string;
        temperature?: { number: number; unit: string };
      }>;
      length?: { number: number; unit: string };
    }>;
  }>;
  spoonacularScore?: number;
  spoonacularSourceUrl?: string;
  usedIngredientCount?: number;
  missedIngredientCount?: number;
  likes?: number;
  missedIngredients?: Array<{
    id: number;
    amount: number;
    unit: string;
    unitLong: string;
    unitShort: string;
    aisle: string;
    name: string;
    original: string;
    originalName: string;
    meta: string[];
    extendedName?: string;
    image: string;
  }>;
  usedIngredients?: Array<{
    id: number;
    amount: number;
    unit: string;
    unitLong: string;
    unitShort: string;
    aisle: string;
    name: string;
    original: string;
    originalName: string;
    meta: string[];
    extendedName?: string;
    image: string;
  }>;
  unusedIngredients?: Array<{
    id: number;
    amount: number;
    unit: string;
    unitLong: string;
    unitShort: string;
    aisle: string;
    name: string;
    original: string;
    originalName: string;
    meta: string[];
    image: string;
  }>;
  nutrition?: {
    nutrients: Array<{
      name: string;
      amount: number;
      unit: string;
    }>;
  };
}

export const ingestRecipes = async (recipeData: {
  results: SpoonacularRecipe[];
  offset?: number;
  number?: number;
  totalResults?: number;
}): Promise<{
  message: string;
  created: number;
}> => {
  const response = await apiClient.post("/api/v1/recipes/ingest", recipeData);
  return response.data;
};
