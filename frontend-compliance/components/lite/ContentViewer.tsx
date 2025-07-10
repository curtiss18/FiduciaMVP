import { ContentForReview, AdvisorInfo } from '@/lib/types'
import { formatDate, formatRelativeTime, getWordCount, getEstimatedReadTime } from '@/lib/utils'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Clock, FileText, Target, Users } from 'lucide-react'

interface ContentViewerProps {
  content: ContentForReview
  advisor: AdvisorInfo
  onTextSelection: (selectedText: string, startPos: number, endPos: number) => void
}

export function ContentViewer({ content, advisor, onTextSelection }: ContentViewerProps) {
  const handleTextSelect = () => {
    const selection = window.getSelection()
    if (selection && selection.toString().trim()) {
      const selectedText = selection.toString()
      // For now, we'll just log the selection
      // In a full implementation, this would calculate positions
      onTextSelection(selectedText, 0, selectedText.length)
    }
  }

  return (
    <div className="space-y-6">
      {/* Content Card */}
      <Card className="content-viewer">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <FileText className="h-5 w-5" />
            {content.title || 'Marketing Content'}
          </CardTitle>
          <div className="flex flex-wrap gap-4 text-sm text-gray-500">
            <span className="flex items-center gap-1">
              <Target className="h-4 w-4" />
              {content.platform}
            </span>
            <span className="flex items-center gap-1">
              <Users className="h-4 w-4" />
              {content.audience}
            </span>
            <span className="flex items-center gap-1">
              <Clock className="h-4 w-4" />
              {getEstimatedReadTime(content.content)} min read
            </span>
          </div>
        </CardHeader>
        <CardContent>
          <div 
            className="prose max-w-none whitespace-pre-wrap text-gray-900 leading-relaxed"
            onMouseUp={handleTextSelect}
            style={{ userSelect: 'text' }}
          >
            {content.content}
          </div>
          
          <div className="mt-6 pt-4 border-t flex justify-between text-sm text-gray-500">
            <span>{getWordCount(content.content)} words</span>
            <span>Created {formatRelativeTime(content.createdAt)}</span>
          </div>
        </CardContent>
      </Card>

      {/* Content Metadata */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Content Details</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <span className="font-medium text-gray-700">Type:</span>
              <span className="ml-2 text-gray-900">{content.contentType.replace('_', ' ')}</span>
            </div>
            <div>
              <span className="font-medium text-gray-700">Platform:</span>
              <span className="ml-2 text-gray-900">{content.platform}</span>
            </div>
            <div>
              <span className="font-medium text-gray-700">Audience:</span>
              <span className="ml-2 text-gray-900">{content.audience}</span>
            </div>
            <div>
              <span className="font-medium text-gray-700">Created:</span>
              <span className="ml-2 text-gray-900">{formatDate(content.createdAt)}</span>
            </div>
          </div>
          
          {content.metadata.tags.length > 0 && (
            <div>
              <span className="font-medium text-gray-700">Tags:</span>
              <div className="mt-1 flex flex-wrap gap-2">
                {content.metadata.tags.map((tag, index) => (
                  <span 
                    key={index}
                    className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800"
                  >
                    {tag}
                  </span>
                ))}
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
