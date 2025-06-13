export interface ContentItem {
  id: number
  title: string
  content_text: string
  content_type: string
  audience_type: string
  approval_status: string
  tags: string
  source: string
  compliance_notes: string
  created_at: string
  updated_at: string
  is_vectorized: boolean
}

export interface ContentStats {
  total_content: number
  by_type: Record<string, number>
  by_status: Record<string, number>
  vectorization_stats: {
    vectorized: number
    total: number
    percentage: number
  }
}

export interface EditContentModalProps {
  isOpen: boolean
  onClose: () => void
  onSuccess: () => void
  content: ContentItem | null
}