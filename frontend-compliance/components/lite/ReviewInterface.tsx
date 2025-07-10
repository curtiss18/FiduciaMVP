'use client'

import { useState } from 'react'
import { ContentReviewResponse, ReviewSubmission, SectionFeedback } from '@/lib/types'
import { complianceLiteApi, handleApiError } from '@/lib/api'
import { Header } from '@/components/shared/Header'
import { ContentViewer } from '@/components/lite/ContentViewer'
import { AdvisorInfo } from '@/components/lite/AdvisorInfo'
import { FeedbackEditor } from '@/components/lite/FeedbackEditor'
import { DecisionPanel } from '@/components/lite/DecisionPanel'
import { UpgradePrompt } from '@/components/lite/UpgradePrompt'
import { SuccessState } from '@/components/shared/SuccessState'
import { LoadingState } from '@/components/shared/LoadingState'
import { ErrorState } from '@/components/shared/ErrorState'

interface ReviewInterfaceProps {
  token: string
  reviewData: ContentReviewResponse
}

export function ReviewInterface({ token, reviewData }: ReviewInterfaceProps) {
  const [decision, setDecision] = useState<'approved' | 'rejected' | null>(null)
  const [overallFeedback, setOverallFeedback] = useState('')
  const [sectionFeedback, setSectionFeedback] = useState<SectionFeedback[]>([])
  const [complianceScore, setComplianceScore] = useState<number>(85)
  const [confidence, setConfidence] = useState<number>(90)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [submitSuccess, setSubmitSuccess] = useState(false)
  const [submitError, setSubmitError] = useState<string | null>(null)

  const handleSubmitReview = async () => {
    if (!decision) return

    try {
      setIsSubmitting(true)
      setSubmitError(null)

      const reviewSubmission: ReviewSubmission = {
        token,
        decision,
        overallFeedback: overallFeedback.trim() || undefined,
        complianceScore,
        sectionFeedback,
        confidence
      }

      const response = await complianceLiteApi.submitReview(reviewSubmission)
      
      if (response.success) {
        setSubmitSuccess(true)
      }
    } catch (error) {
      console.error('Failed to submit review:', error)
      setSubmitError(handleApiError(error))
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleTextSelection = (selectedText: string, startPos: number, endPos: number) => {
    // Handle text selection for inline commenting
    console.log('Text selected:', { selectedText, startPos, endPos })
  }

  const addSectionFeedback = (feedback: SectionFeedback) => {
    setSectionFeedback(prev => [...prev, feedback])
  }

  const removeSectionFeedback = (index: number) => {
    setSectionFeedback(prev => prev.filter((_, i) => i !== index))
  }

  if (isSubmitting) {
    return <LoadingState message="Submitting your review..." />
  }

  if (submitSuccess) {
    return (
      <SuccessState 
        title="Review Submitted Successfully"
        message="The advisor has been notified of your decision and will receive your feedback."
        showUpgrade={reviewData.upgrade.showPrompt}
      />
    )
  }

  if (submitError) {
    return (
      <ErrorState 
        title="Submission Failed"
        message={submitError}
        showRetry
        onRetry={() => setSubmitError(null)}
      />
    )
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <Header />
      
      <main className="container mx-auto px-4 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Content Viewer */}
          <ContentViewer 
            content={reviewData.content}
            advisor={reviewData.advisor}
            onTextSelection={handleTextSelection}
          />
          
          {/* Review Tools */}
          <div className="space-y-6">
            <AdvisorInfo 
              advisor={reviewData.advisor}
              review={reviewData.review}
            />
            
            <FeedbackEditor 
              sectionFeedback={sectionFeedback}
              overallFeedback={overallFeedback}
              violationTypes={reviewData.compliance.violationTypes}
              onOverallFeedbackChange={setOverallFeedback}
              onAddSectionFeedback={addSectionFeedback}
              onRemoveSectionFeedback={removeSectionFeedback}
            />
            
            <DecisionPanel 
              decision={decision}
              complianceScore={complianceScore}
              confidence={confidence}
              canSubmit={!!decision && (decision === 'approved' || overallFeedback.trim().length >= 10)}
              onDecisionChange={setDecision}
              onComplianceScoreChange={setComplianceScore}
              onConfidenceChange={setConfidence}
              onSubmit={handleSubmitReview}
            />
          </div>
        </div>
      </main>
      
      <UpgradePrompt upgradeInfo={reviewData.upgrade} />
    </div>
  )
}
