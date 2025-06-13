// Chat and conversation types
export interface Message {
  id: string
  role: 'advisor' | 'warren'
  content: string
  timestamp: Date
  type: 'text' | 'content_preview' | 'file_upload' | 'error'
  metadata?: {
    contentType?: string
    audience?: string
    platform?: string
    isGenerating?: boolean
  }
}

export interface Conversation {
  id: string
  messages: Message[]
  status: 'active' | 'content_ready' | 'saved' | 'submitted'
  generatedContent?: GeneratedContent
  context?: ConversationContext
}

export interface GeneratedContent {
  title: string
  content: string
  contentType: string
  audience: string
  platform: string
  complianceScore?: number
  disclaimers?: string[]
}

export interface ConversationContext {
  audience?: string
  purpose?: string
  contentType?: string
  platform?: string
  topic?: string
  complianceSensitivity?: 'low' | 'medium' | 'high'
  uploadedFiles?: UploadedFile[]
}

export interface UploadedFile {
  id: string
  name: string
  type: string
  size: number
  content?: string
  uploadedAt: Date
}

// Warren response types
export interface WarrenResponse {
  status: 'success' | 'error'
  content?: string
  error?: string
  search_strategy?: 'vector' | 'hybrid' | 'text'
  vector_results_found?: number
  total_knowledge_sources?: number
  fallback_used?: boolean
  context_quality_score?: number
  metadata?: {
    contentType?: string
    audience?: string
    platform?: string
  }
}

// Content types from backend
export type ContentType = 
  | 'linkedin_post'
  | 'email_template'
  | 'website_content'
  | 'newsletter'
  | 'social_media'
  | 'blog_post'
  | 'general'

export type AudienceType = 
  | 'general_education'
  | 'high_net_worth'
  | 'retirees'
  | 'young_professionals'
  | 'institutional'
  | 'prospects'

// API response types
export interface ApiResponse<T = any> {
  status: 'success' | 'error'
  data?: T
  error?: string
  message?: string
}
