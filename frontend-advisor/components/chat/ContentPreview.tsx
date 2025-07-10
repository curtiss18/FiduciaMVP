import React from 'react'
import { GeneratedContent } from '@/lib/types'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Copy, Download, Save, Send } from 'lucide-react'
import { cn } from '@/lib/utils'

interface ContentPreviewProps {
  content: GeneratedContent | null
  onCopy?: () => void
  onSave?: () => void
  onSubmitForReview?: () => void
  onRegenerate?: () => void
}

export const ContentPreview: React.FC<ContentPreviewProps> = ({
  content,
  onCopy,
  onSave,
  onSubmitForReview,
  onRegenerate
}) => {
  if (!content) return null

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(content.content)
      onCopy?.()
    } catch (err) {
      console.error('Failed to copy content:', err)
    }
  }

  const getPlatformIcon = (platform: string) => {
    switch (platform.toLowerCase()) {
      case 'linkedin': return '💼'
      case 'twitter': case 'x': return '🐦'
      case 'email': return '📧'
      case 'website': return '🌐'
      case 'newsletter': return '📰'
      default: return '📄'
    }
  }

  const getAudienceLabel = (audience: string) => {
    return audience.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())
  }

  return (
    <div className="border-t bg-background p-4">
      <div className="max-w-4xl mx-auto">
        <Card className="bg-green-50 border-green-200 dark:bg-green-950 dark:border-green-800">
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="text-2xl">{getPlatformIcon(content.platform)}</span>
                <div>
                  <CardTitle className="text-lg">
                    {content.title || 'Generated Content'}
                  </CardTitle>
                  <CardDescription>
                    {content.contentType} • {getAudienceLabel(content.audience)}
                    {content.complianceScore && (
                      <span className="ml-2 text-green-600 dark:text-green-400">
                        • Compliance Score: {Math.round(content.complianceScore * 100)}%
                      </span>
                    )}
                  </CardDescription>
                </div>
              </div>
              <div className="flex gap-2">
                <Button variant="outline" size="sm" onClick={handleCopy}>
                  <Copy className="h-4 w-4 mr-1" />
                  Copy
                </Button>
                <Button variant="outline" size="sm" onClick={onSave}>
                  <Save className="h-4 w-4 mr-1" />
                  Save
                </Button>
                <Button variant="default" size="sm" onClick={onSubmitForReview}>
                  <Send className="h-4 w-4 mr-1" />
                  Submit for Review
                </Button>
              </div>
            </div>
          </CardHeader>
          <CardContent className="pt-0">
            {/* Generated content */}
            <div className="bg-white dark:bg-gray-900 rounded-md p-4 border mb-4">
              <pre className="whitespace-pre-wrap font-sans text-sm leading-relaxed">
                {content.content}
              </pre>
            </div>

            {/* Disclaimers if present */}
            {content.disclaimers && content.disclaimers.length > 0 && (
              <div className="text-xs text-muted-foreground space-y-1">
                <p className="font-medium">Required Disclaimers:</p>
                {content.disclaimers.map((disclaimer, index) => (
                  <p key={index} className="pl-2 border-l-2 border-muted">
                    {disclaimer}
                  </p>
                ))}
              </div>
            )}

            {/* Action buttons */}
            <div className="flex justify-between items-center mt-4 pt-4 border-t">
              <Button variant="ghost" size="sm" onClick={onRegenerate}>
                🔄 Regenerate
              </Button>
              <div className="text-xs text-muted-foreground">
                Ready for compliance review
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
