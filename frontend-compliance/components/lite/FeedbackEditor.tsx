import { useState } from 'react'
import { SectionFeedback, ViolationType } from '@/lib/types'
import { getSeverityColor } from '@/lib/utils'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Textarea } from '@/components/ui/textarea'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { MessageSquare, Plus, X, AlertTriangle } from 'lucide-react'

interface FeedbackEditorProps {
  sectionFeedback: SectionFeedback[]
  overallFeedback: string
  violationTypes: ViolationType[]
  onOverallFeedbackChange: (feedback: string) => void
  onAddSectionFeedback: (feedback: SectionFeedback) => void
  onRemoveSectionFeedback: (index: number) => void
}

export function FeedbackEditor({ 
  sectionFeedback, 
  overallFeedback, 
  violationTypes,
  onOverallFeedbackChange,
  onAddSectionFeedback,
  onRemoveSectionFeedback
}: FeedbackEditorProps) {
  const [showAddFeedback, setShowAddFeedback] = useState(false)
  const [newFeedback, setNewFeedback] = useState({
    sectionText: '',
    violationType: '',
    comment: '',
    suggestedFix: '',
    severity: 'medium' as 'low' | 'medium' | 'high' | 'critical'
  })

  const handleAddFeedback = () => {
    if (!newFeedback.sectionText || !newFeedback.comment || !newFeedback.violationType) {
      return
    }

    const feedback: SectionFeedback = {
      sectionText: newFeedback.sectionText,
      startPosition: 0, // Would be calculated from text selection
      endPosition: newFeedback.sectionText.length,
      violationType: newFeedback.violationType,
      comment: newFeedback.comment,
      suggestedFix: newFeedback.suggestedFix || undefined,
      severity: newFeedback.severity,
      aiAssisted: false
    }

    onAddSectionFeedback(feedback)
    setNewFeedback({
      sectionText: '',
      violationType: '',
      comment: '',
      suggestedFix: '',
      severity: 'medium'
    })
    setShowAddFeedback(false)
  }

  return (
    <Card className="feedback-editor">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <MessageSquare className="h-5 w-5" />
          Review Feedback
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Overall Feedback */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Overall Feedback
          </label>
          <Textarea
            placeholder="Provide overall feedback about this content..."
            value={overallFeedback}
            onChange={(e) => onOverallFeedbackChange(e.target.value)}
            rows={4}
          />
          <p className="mt-1 text-xs text-gray-500">
            {overallFeedback.length < 10 && overallFeedback.length > 0 && 
              "Rejections require at least 10 characters of feedback"
            }
          </p>
        </div>

        {/* Section-Specific Feedback */}
        <div>
          <div className="flex items-center justify-between mb-3">
            <label className="block text-sm font-medium text-gray-700">
              Section-Specific Issues
            </label>
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={() => setShowAddFeedback(true)}
            >
              <Plus className="h-4 w-4 mr-2" />
              Add Issue
            </Button>
          </div>

          {/* Existing Feedback Items */}
          <div className="space-y-3">
            {sectionFeedback.map((feedback, index) => (
              <div key={index} className="border rounded-lg p-3 bg-gray-50">
                <div className="flex items-start justify-between mb-2">
                  <span className={`violation-badge ${getSeverityColor(feedback.severity)}`}>
                    {feedback.violationType.replace('_', ' ')}
                  </span>
                  <Button
                    type="button"
                    variant="ghost"
                    size="sm"
                    onClick={() => onRemoveSectionFeedback(index)}
                  >
                    <X className="h-4 w-4" />
                  </Button>
                </div>
                <p className="text-sm text-gray-600 mb-2 italic">
                  "{feedback.sectionText}"
                </p>
                <p className="text-sm text-gray-900">
                  {feedback.comment}
                </p>
                {feedback.suggestedFix && (
                  <div className="mt-2 p-2 bg-green-50 rounded text-sm">
                    <span className="font-medium text-green-800">Suggested fix:</span>
                    <p className="text-green-700">{feedback.suggestedFix}</p>
                  </div>
                )}
              </div>
            ))}
          </div>

          {/* Add New Feedback Form */}
          {showAddFeedback && (
            <div className="border rounded-lg p-4 bg-white mt-3">
              <div className="space-y-3">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Section Text
                  </label>
                  <Input
                    placeholder="Enter the specific text section..."
                    value={newFeedback.sectionText}
                    onChange={(e) => setNewFeedback(prev => ({ ...prev, sectionText: e.target.value }))}
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Violation Type
                  </label>
                  <select
                    className="w-full p-2 border border-gray-300 rounded-md"
                    value={newFeedback.violationType}
                    onChange={(e) => setNewFeedback(prev => ({ ...prev, violationType: e.target.value }))}
                  >
                    <option value="">Select violation type...</option>
                    {violationTypes.map((type) => (
                      <option key={type.id} value={type.id}>
                        {type.name}
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Comment
                  </label>
                  <Textarea
                    placeholder="Explain the issue and compliance concern..."
                    value={newFeedback.comment}
                    onChange={(e) => setNewFeedback(prev => ({ ...prev, comment: e.target.value }))}
                    rows={3}
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Suggested Fix (Optional)
                  </label>
                  <Input
                    placeholder="Suggest how to improve this section..."
                    value={newFeedback.suggestedFix}
                    onChange={(e) => setNewFeedback(prev => ({ ...prev, suggestedFix: e.target.value }))}
                  />
                </div>

                <div className="flex justify-end gap-2">
                  <Button
                    type="button"
                    variant="outline"
                    size="sm"
                    onClick={() => setShowAddFeedback(false)}
                  >
                    Cancel
                  </Button>
                  <Button
                    type="button"
                    size="sm"
                    onClick={handleAddFeedback}
                    disabled={!newFeedback.sectionText || !newFeedback.comment || !newFeedback.violationType}
                  >
                    Add Issue
                  </Button>
                </div>
              </div>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  )
}
