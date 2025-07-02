import axios from 'axios';
import { WarrenResponse, ContentType, AudienceType, Contact, Audience } from './types';

// Base API client for communicating with FastAPI backend
const api = axios.create({
  baseURL: 'http://localhost:8000/api/v1',
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000, // 30 second timeout for Warren generations
  withCredentials: false, // Disable credentials for CORS
});

// API response interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('API Error:', error.response?.data || error.message);
    if (error.code === 'ERR_NETWORK') {
      console.error('Network error - check if backend is running on localhost:8000');
    }
    return Promise.reject(error);
  }
);

// Warren Chat API - Main interface for advisor portal
export const warrenChatApi = {
  // Send message to Warren in conversational format
  sendMessage: async (
    message: string, 
    conversationId: string,
    context?: any
  ): Promise<WarrenResponse> => {
    const response = await api.post('/warren/generate-v3', {
      request: message,
      content_type: context?.contentType || 'linkedin_post',
      audience_type: context?.audience || 'general_education',
      conversation_id: conversationId,
      previous_context: context,
      current_content: context?.current_content,
      is_refinement: context?.is_refinement || false,
      youtube_url: context?.youtube_url
    });
    return response.data;
  },

  // Generate content with specific parameters
  generateContent: async (
    request: string,
    contentType: ContentType = 'linkedin_post',
    audienceType: AudienceType = 'general_education'
  ): Promise<WarrenResponse> => {
    const response = await api.post('/warren/generate-v3', {
      request,
      content_type: contentType,
      audience_type: audienceType,
    });
    return response.data;
  },

  // Test Warren connection
  testConnection: async () => {
    const response = await api.get('/health');
    return response.data;
  }
};

// System API for health checks
export const systemApi = {
  getHealth: () => api.get('/health'),
  getStatus: () => api.get('/status'),
};

// Advisor Workflow API - Complete session and content management
export const advisorApi = {
  // Session Management
  createSession: async (advisorId: string, title?: string) => {
    const response = await api.post('/advisor/sessions/create', {
      advisor_id: advisorId,
      title: title || 'Warren Chat Session'
    });
    return response.data;
  },

  saveMessage: async (sessionId: string, messageType: 'user' | 'warren', content: string, metadata?: any) => {
    const response = await api.post('/advisor/sessions/messages/save', {
      session_id: sessionId,
      message_type: messageType,
      content,
      metadata
    });
    return response.data;
  },

  getSessionMessages: async (sessionId: string, advisorId: string) => {
    const response = await api.get(`/advisor/sessions/${sessionId}/messages`, {
      params: { advisor_id: advisorId }
    });
    return response.data;
  },

  // Content Management
  saveContent: async (contentData: {
    advisorId: string;
    title: string;
    contentText: string;
    contentType: string;
    audienceType: string;
    sourceSessionId?: string;
    sourceMessageId?: string;
    advisorNotes?: string;
    intendedChannels?: string[];
    sourceMetadata?: any;
  }) => {
    const response = await api.post('/advisor/content/save', {
      advisor_id: contentData.advisorId,
      title: contentData.title,
      content_text: contentData.contentText,
      content_type: contentData.contentType,
      audience_type: contentData.audienceType,
      source_session_id: contentData.sourceSessionId,
      source_message_id: contentData.sourceMessageId,
      advisor_notes: contentData.advisorNotes,
      intended_channels: contentData.intendedChannels || [],
      source_metadata: contentData.sourceMetadata
    });
    return response.data;
  },

  getContentLibrary: async (advisorId: string, filters?: any) => {
    const response = await api.get('/advisor/content/library', {
      params: { advisor_id: advisorId, ...filters }
    });
    return response.data;
  },

  updateContentStatus: async (contentId: string, advisorId: string, newStatus: string, notes?: string) => {
    const response = await api.put(`/advisor/content/${contentId}/status`, {
      new_status: newStatus,
      advisor_notes: notes
    }, {
      params: { advisor_id: advisorId }
    });
    return response.data;
  },

  // Update full content (for session updates)
  updateContent: async (contentId: string, advisorId: string, updateData: {
    title?: string;
    contentText?: string;
    advisorNotes?: string;
  }) => {
    const params: any = { advisor_id: advisorId };
    
    if (updateData.title) params.title = updateData.title;
    if (updateData.contentText) params.content_text = updateData.contentText;
    if (updateData.advisorNotes) params.advisor_notes = updateData.advisorNotes;
    // Note: source_metadata removed as advisor_content table doesn't have this column

    const response = await api.put(`/advisor/content/${contentId}`, null, { params });
    return response.data;
  },

  // Analytics
  getStatistics: async (advisorId: string) => {
    const response = await api.get('/advisor/content/statistics', {
      params: { advisor_id: advisorId }
    });
    return response.data;
  },

  // Archive/Restore functionality
  archiveContent: async (contentId: string, advisorId: string) => {
    return advisorApi.updateContentStatus(contentId, advisorId, 'archived', 'Content archived by user');
  },

  restoreContent: async (contentId: string, advisorId: string) => {
    return advisorApi.updateContentStatus(contentId, advisorId, 'draft', 'Content restored from archive');
  }
};

// Audience & Contact Management API - Uses existing backend endpoints
export const audienceApi = {
  // Contact Management - using existing /api/v1/contacts endpoints
  getContacts: async (advisorId: string = 'demo_advisor_001', searchTerm?: string, statusFilter?: string) => {
    const params: any = { advisor_id: advisorId };
    if (searchTerm) params.search = searchTerm;
    if (statusFilter && statusFilter !== 'all') params.status = statusFilter;
    
    const response = await api.get('/contacts', { params });
    return { contacts: response.data || [] };
  },

  createContact: async (contactData: {
    advisorId: string;
    firstName: string;
    lastName: string;
    email?: string;
    phone?: string;
    company?: string;
    title?: string;
    status: string;
    notes?: string;
  }) => {
    const response = await api.post('/contacts', {
      advisor_id: contactData.advisorId,
      first_name: contactData.firstName,
      last_name: contactData.lastName,
      email: contactData.email,
      phone: contactData.phone,
      company: contactData.company,
      title: contactData.title,
      status: contactData.status,
      notes: contactData.notes
    });
    return response.data;
  },

  getContact: async (contactId: string, advisorId: string = 'demo_advisor_001') => {
    const response = await api.get(`/contacts/${contactId}`, {
      params: { advisor_id: advisorId }
    });
    return response.data;
  },

  updateContact: async (contactId: string, advisorId: string, contactData: any) => {
    // Map frontend field names to backend field names
    const mappedData = {
      first_name: contactData.firstName,
      last_name: contactData.lastName,
      email: contactData.email,
      phone: contactData.phone,
      company: contactData.company,
      title: contactData.title,
      status: contactData.status,
      notes: contactData.notes
    };
    
    const response = await api.put(`/contacts/${contactId}`, mappedData, {
      params: { advisor_id: advisorId }
    });
    return response.data;
  },

  deleteContact: async (contactId: string, advisorId: string = 'demo_advisor_001') => {
    const response = await api.delete(`/contacts/${contactId}`, {
      params: { advisor_id: advisorId }
    });
    return response.data;
  },

  // Audience Management - using existing /api/v1/audiences endpoints
  getAudiences: async (advisorId: string = 'demo_advisor_001') => {
    const response = await api.get('/audiences', {
      params: { advisor_id: advisorId }
    });
    return { audiences: response.data || [] };
  },

  createAudience: async (audienceData: {
    advisorId: string;
    name: string;
    description?: string;
    characteristics?: string;
    occupation?: string;
    relationshipType?: string;
  }) => {
    const response = await api.post('/audiences', {
      advisor_id: audienceData.advisorId,
      name: audienceData.name,
      description: audienceData.description,
      characteristics: audienceData.characteristics,
      occupation: audienceData.occupation,
      relationship_type: audienceData.relationshipType
    });
    return response.data;
  },

  getAudience: async (audienceId: string, advisorId: string = 'demo_advisor_001') => {
    const response = await api.get(`/audiences/${audienceId}`, {
      params: { advisor_id: advisorId }
    });
    return response.data;
  },

  updateAudience: async (audienceId: string, advisorId: string, audienceData: any) => {
    const response = await api.put(`/audiences/${audienceId}`, audienceData, {
      params: { advisor_id: advisorId }
    });
    return response.data;
  },

  deleteAudience: async (audienceId: string, advisorId: string = 'demo_advisor_001') => {
    const response = await api.delete(`/audiences/${audienceId}`, {
      params: { advisor_id: advisorId }
    });
    return response.data;
  },

  // Statistics - using existing /api/v1/statistics endpoint
  getAudienceStatistics: async (advisorId: string = 'demo_advisor_001') => {
    const response = await api.get('/statistics', {
      params: { advisor_id: advisorId }
    });
    return response.data;
  }
};

export default api;