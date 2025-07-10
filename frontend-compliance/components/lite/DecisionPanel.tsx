import { CheckCircle, XCircle, Send } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'

interface DecisionPanelProps {
  decision: 'approved' | 'rejected' | null
  complianceScore: number
  confidence: number
  canSubmit: boolean
  onDecisionChange: (decision: 'approved' | 'rejected') => void
  onComplianceScoreChange: (score: number) => void
  onConfidenceChange: (confidence: number) => void
  onSubmit: () => void
}

export function DecisionPanel({
  decision,
  complianceScore,
  confidence,
  canSubmit,
  onDecisionChange,
  onComplianceScoreChange,
  onConfidenceChange,
  onSubmit
}: DecisionPanelProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Review Decision</CardTitle>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Decision Buttons */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-3">
            Decision *
          </label>
          <div className="grid grid-cols-2 gap-3">
            <Button
              type="button"
              variant={decision === 'approved' ? 'default' : 'outline'}
              className={`h-16 ${decision === 'approved' ? 'bg-green-600 hover:bg-green-700' : 'hover:bg-green-50'}`}
              onClick={() => onDecisionChange('approved')}
            >
              <CheckCircle className="h-6 w-6 mr-2" />
              Approve
            </Button>
            <Button
              type="button"
              variant={decision === 'rejected' ? 'default' : 'outline'}
              className={`h-16 ${decision === 'rejected' ? 'bg-red-600 hover:bg-red-700' : 'hover:bg-red-50'}`}
              onClick={() => onDecisionChange('rejected')}
            >
              <XCircle className="h-6 w-6 mr-2" />
              Reject
            </Button>
          </div>
        </div>

        {/* Compliance Score */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Compliance Score: {complianceScore}/100
          </label>
          <input
            type="range"
            min="0"
            max="100"
            value={complianceScore}
            onChange={(e) => onComplianceScoreChange(parseInt(e.target.value))}
            className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer"
          />
          <div className="flex justify-between text-xs text-gray-500 mt-1">
            <span>Non-compliant</span>
            <span>Fully compliant</span>
          </div>
        </div>

        {/* Confidence Level */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Confidence in Decision: {confidence}%
          </label>
          <input
            type="range"
            min="1"
            max="100"
            value={confidence}
            onChange={(e) => onConfidenceChange(parseInt(e.target.value))}
            className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer"
          />
          <div className="flex justify-between text-xs text-gray-500 mt-1">
            <span>Low confidence</span>
            <span>High confidence</span>
          </div>
        </div>

        {/* Submit Button */}
        <div className="pt-4 border-t">
          <Button
            type="button"
            className="w-full h-12"
            onClick={onSubmit}
            disabled={!canSubmit}
          >
            <Send className="h-5 w-5 mr-2" />
            Submit Review
          </Button>
          
          {!canSubmit && decision === 'rejected' && (
            <p className="mt-2 text-sm text-red-600">
              Rejected content requires detailed feedback (at least 10 characters)
            </p>
          )}
          
          {!canSubmit && !decision && (
            <p className="mt-2 text-sm text-gray-500">
              Please select a decision to continue
            </p>
          )}
        </div>
      </CardContent>
    </Card>
  )
}
