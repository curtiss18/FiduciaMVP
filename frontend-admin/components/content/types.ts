export interface ContentItem {
  id: number
  title: string
  content_text: string
  content_type: string
  audience_type: string
  approval_status: string
  tags: string | string[]
  source?: string
  compliance_notes?: string
  created_at: string
  updated_at: string
  has_embedding: boolean  // Updated to match API response
  // Additional fields for enhanced content management
  tone?: string
  topic_focus?: string
  target_demographics?: string
  original_source?: string
  compliance_score?: number
  source_type?: string
  usage_count?: number
  effectiveness_score?: number
}

export interface ContentStats {
  total_content: number
  vectorized_content: number
  vectorization_percentage: number
  content_by_type: Record<string, number>
  content_by_source: Record<string, number>
  content_by_approval: Record<string, number>
  // Legacy compatibility - computed properties
  by_type?: Record<string, number>
  by_status?: Record<string, number>
  vectorization_stats?: {
    vectorized: number
    total: number
    percentage: number
  }
}

export interface ContentModalProps {
  mode: 'create' | 'edit'
  isOpen: boolean
  onClose: () => void
  onSuccess: () => void
  content?: ContentItem | null
}

export interface EditContentModalProps {
  isOpen: boolean
  onClose: () => void
  onSuccess: () => void
  content: ContentItem | null
}