import axios from 'axios';

// Base API client for communicating with FastAPI backend
const api = axios.create({
  baseURL: 'http://localhost:8000/api/v1',
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000, // 30 second timeout
});

// API response interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('API Error:', error.response?.data || error.message);
    return Promise.reject(error);
  }
);

// Content Management API (CRUD)
export const contentApi = {
  // Get all content pieces
  getContent: (params?: any) => api.get('/content', { params }),
  
  // Get content enums for form dropdowns
  getContentEnums: () => api.get('/content/enums'),
  
  // Get content statistics
  getContentStatistics: () => api.get('/content/statistics'),
  
  // Get specific content by ID
  getContentById: (id: number) => api.get(`/content/${id}`),
  
  // Create new content
  createContent: (content: any) => api.post('/content', content),
  
  // Update existing content
  updateContent: (id: number, content: any) => api.put(`/content/${id}`, content),
  
  // Delete content
  deleteContent: (id: number) => api.delete(`/content/${id}`),
};

// Vector Search API
export const vectorApi = {
  // Test vector search
  testSearch: (query: string, limit = 5) => 
    api.post('/vector-search/test', { query, limit }),
  
  // Get vector search stats
  getStats: () => api.get('/vector-search/stats'),
  
  // Check readiness
  getReadiness: () => api.get('/vector-search/readiness'),
};

// Embeddings API
export const embeddingsApi = {
  // Get embedding status
  getStatus: () => api.get('/embeddings/status'),
  
  // Test embeddings
  test: () => api.post('/embeddings/test'),
  
  // Vectorize content
  vectorizeContent: (contentIds: string[]) => 
    api.post('/embeddings/vectorize-content', { content_ids: contentIds }),
  
  // Cost estimation
  getCostEstimate: () => api.get('/embeddings/cost-estimate'),
};

// Warren API
export const warrenApi = {
  // Generate content with Warren V3
  generateV3: (request: string, contentType: string, audienceType?: string) =>
    api.post('/warren/generate-v3', {
      request,
      content_type: contentType,
      audience_type: audienceType,
    }),
};

// System API
export const systemApi = {
  // Health check
  getHealth: () => api.get('/health'),
  
  // System status
  getStatus: () => api.get('/status'),
};

export default api;