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
  // Source information for transparency
  sourceInfo?: SourceInformation
}

export interface SourceInformation {
  totalSources: number
  marketingExamples: number
  complianceRules: number
  searchStrategy: 'vector' | 'hybrid' | 'text'
  fallbackUsed: boolean
}

// Content extraction from Warren responses
export interface ExtractedContent {
  marketingContent: string | null
  conversationalResponse: string
  hasMarketingContent: boolean
  title?: string
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
  text_results_found?: number
  total_knowledge_sources?: number
  fallback_used?: boolean
  context_quality_score?: number
  // Additional source breakdown (if available from backend)
  marketing_examples_count?: number
  compliance_rules_count?: number
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

// Advisor Workflow Types - matching backend API responses
export interface AdvisorSession {
  session_id: string
  advisor_id: string
  title: string
  created_at: string
  updated_at: string
  message_count?: number
}

export interface AdvisorMessage {
  id: string
  session_id: string
  message_type: 'user' | 'warren'
  content: string
  metadata?: any
  created_at: string
}

export interface AdvisorContent {
  id: string
  advisor_id: string
  title: string
  content_text: string
  content_type: string
  audience_type: string
  status: 'draft' | 'submitted' | 'approved' | 'rejected' | 'distributed' | 'archived'
  source_session_id?: string
  source_message_id?: string
  advisor_notes?: string
  intended_channels: string[]
  source_metadata?: any
  created_at: string
  updated_at: string
}

export interface AdvisorStatistics {
  total_content: number
  total_sessions: number
  content_by_status: Record<string, number>
  content_by_type: Record<string, number>
  recent_activity_count: number
}

// Audience Management Types - matching backend API responses
export interface Contact {
  id: number  // Backend uses int IDs
  advisor_id: string
  first_name: string
  last_name: string
  email?: string
  phone?: string
  company?: string
  title?: string
  status: string  // Backend uses string, not enum
  notes?: string
  created_at: string  // ISO datetime string
  updated_at: string
}

export interface Audience {
  id: number  // Backend uses int IDs
  advisor_id: string
  name: string
  description?: string
  characteristics?: string
  occupation?: string
  relationship_type?: string
  contact_count?: number  // From backend response
  created_at: string
  updated_at: string
  contacts?: Contact[]  // When populated with contacts
}

export interface AudienceStatistics {
  advisor_id: string
  total_contacts: number
  total_audiences: number
  total_relationships: number
  avg_contacts_per_audience: number
}

// Document Management Types (SCRUM-46)
export interface DocumentUploadResult {
  filename: string
  index: number
  status: 'success' | 'failed'
  document_id?: string
  title?: string
  processing_results?: {
    text_extracted: boolean
    word_count: number
    images_detected: number
    tables_detected: number
    visual_summary: string
    processing_time_ms: number
    summary_generated?: boolean
    summary_tokens?: number
    summary_preview?: string
  }
  error?: string
  error_type?: string
}

export interface BatchUploadResponse {
  status: 'success' | 'partial_success' | 'failed'
  message: string
  batch_results: {
    total_files: number
    successful_count: number
    failed_count: number
    success_rate: number
    successful_uploads: DocumentUploadResult[]
    failed_uploads: DocumentUploadResult[]
  }
}

export interface SessionDocument {
  document_id: string
  title: string
  content_type: string
  original_filename: string
  file_size_bytes: number
  word_count: number
  upload_timestamp: string
  processing_status: 'pending' | 'processed' | 'failed'
  summary?: string
  summary_tokens?: number
  metadata: any
}