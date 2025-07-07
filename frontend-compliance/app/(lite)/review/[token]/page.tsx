'use client'

import { useEffect, useState } from 'react'
import { useParams } from 'next/navigation'
import { complianceLiteApi, handleApiError, validateToken } from '@/lib/api'
import { ContentReviewResponse } from '@/lib/types'
import { ReviewInterface } from '@/components/lite/ReviewInterface'
import { ErrorState } from '@/components/shared/ErrorState'
import { LoadingState } from '@/components/shared/LoadingState'

export default function ReviewPage() {
  const params = useParams()
  const token = params.token as string
  
  const [reviewData, setReviewData] = useState<ContentReviewResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const loadReviewData = async () => {
      try {
        // Validate token format
        if (!validateToken(token)) {
          setError('Invalid review token format')
          return
        }

        setLoading(true)
        const data = await complianceLiteApi.getContentForReview(token)
        setReviewData(data)
      } catch (err) {
        console.error('Failed to load review data:', err)
        setError(handleApiError(err))
      } finally {
        setLoading(false)
      }
    }

    if (token) {
      loadReviewData()
    }
  }, [token])

  if (loading) {
    return <LoadingState message="Loading content for review..." />
  }

  if (error || !reviewData) {
    return (
      <ErrorState 
        title="Unable to Load Content"
        message={error || 'The content you requested could not be found.'}
        showRetry
        onRetry={() => window.location.reload()}
      />
    )
  }

  return (
    <ReviewInterface 
      token={token}
      reviewData={reviewData}
    />
  )
}
