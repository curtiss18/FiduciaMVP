import axios from 'axios';
import {
  ContentReviewResponse,
  ReviewSubmission,
  ReviewSubmissionResponse,
  ViolationAnalysisRequest,
  ViolationAnalysisResponse,
  APIResponse,
  APIError
} from './types';

// Base API client for compliance portal
const api = axios.create({
  baseURL: 'http://localhost:8000/api/v1',
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000, // 30 second timeout
  withCredentials: false, // Disable credentials for CORS
});

// API response interceptor for error handling
api.interceptors.response.use(
  (response: any) => response,
  (error: { response: { data: any; }; message: any; code: string; }) => {
    console.error('Compliance API Error:', error.response?.data || error.message);
    if (error.code === 'ERR_NETWORK') {
      console.error('Network error - check if backend is running on localhost:8000');
    }
    return Promise.reject(error);
  }
);

// Lite Version API - Token-based access
export const complianceLiteApi = {
  // Get content for review using token
  getContentForReview: async (token: string): Promise<ContentReviewResponse> => {
    const response = await api.get(`/compliance/content/${token}`);
    return response.data;
  },

  // Submit review decision and feedback
  submitReview: async (reviewData: ReviewSubmission): Promise<ReviewSubmissionResponse> => {
    const response = await api.post('/compliance/review/submit', reviewData);
    return response.data;
  },

  // Get AI assistance for violation analysis
  analyzeViolation: async (analysisData: ViolationAnalysisRequest): Promise<ViolationAnalysisResponse> => {
    const response = await api.post('/compliance/ai/analyze-violation', analysisData);
    return response.data;
  },

  // Get upgrade information
  getUpgradeInfo: async (token: string) => {
    const response = await api.get('/compliance/upgrade/info', {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    });
    return response.data;
  }
};

// Full Version API - Account-based access (for future implementation)
export const complianceFullApi = {
  // Authentication endpoints
  login: async (email: string, password: string, mfaCode?: string) => {
    const response = await api.post('/compliance/auth/login', {
      email,
      password,
      mfaCode
    });
    return response.data;
  },

  logout: async (allDevices: boolean = false) => {
    const response = await api.post('/compliance/auth/logout', { allDevices });
    return response.data;
  },

  // Dashboard and analytics
  getDashboard: async (timeRange: string = '7d') => {
    const response = await api.get('/compliance/dashboard', {
      params: { timeRange }
    });
    return response.data;
  },

  // Advisor management
  getAdvisors: async (page: number = 1, limit: number = 25) => {
    const response = await api.get('/compliance/advisors', {
      params: { page, limit }
    });
    return response.data;
  },

  // Review history
  getReviewHistory: async (page: number = 1, limit: number = 25) => {
    const response = await api.get('/compliance/reviews/history', {
      params: { page, limit }
    });
    return response.data;
  }
};

// Error handling utility
export const handleApiError = (error: any): string => {
  if (error.response?.data?.error?.message) {
    return error.response.data.error.message;
  }
  if (error.response?.status === 401) {
    return 'Invalid or expired review token';
  }
  if (error.response?.status === 404) {
    return 'Content not found or no longer available';
  }
  if (error.response?.status === 410) {
    return 'This content has already been reviewed';
  }
  if (error.code === 'ERR_NETWORK') {
    return 'Unable to connect to server. Please check your internet connection.';
  }
  return 'An unexpected error occurred. Please try again.';
};

// Token validation utility
export const validateToken = (token: string): boolean => {
  if (!token || typeof token !== 'string') return false;
  
  // Basic token format validation (should have signature)
  const parts = token.split('.');
  return parts.length === 2 && parts[0].length > 0 && parts[1].length > 0;
};

export default api;
