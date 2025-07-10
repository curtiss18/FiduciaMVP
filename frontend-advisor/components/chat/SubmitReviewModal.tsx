'use client'

import React, { useState } from 'react'
import { 
  Dialog, 
  DialogContent, 
  DialogDescription, 
  DialogFooter, 
  DialogHeader, 
  DialogTitle 
} from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { Badge } from '@/components/ui/badge'
import { Send, Mail, AlertCircle } from 'lucide-react'

interface SubmitReviewModalProps {
  isOpen: boolean
  onClose: () => void
  onSubmit: (ccoEmail: string, notes: string) => Promise<void>
  contentTitle: string
  isSubmitting?: boolean
}

export const SubmitReviewModal: React.FC<SubmitReviewModalProps> = ({
  isOpen,
  onClose,
  onSubmit,
  contentTitle,
  isSubmitting = false
}) => {
  const [ccoEmail, setCcoEmail] = useState('curtis@fiduciaapp.com')
  const [notes, setNotes] = useState('')
  const [emailError, setEmailError] = useState('')

  // Reset form when modal opens/closes
  React.useEffect(() => {
    if (!isOpen) {
      setCcoEmail('curtis@fiduciaapp.com')
      setNotes('')
      setEmailError('')
    }
  }, [isOpen])

  // Email validation
  const validateEmail = (email: string) => {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
    return emailRegex.test(email)
  }

  const handleEmailChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const email = e.target.value
    setCcoEmail(email)
    
    if (email && !validateEmail(email)) {
      setEmailError('Please enter a valid email address')
    } else {
      setEmailError('')
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    // Validate email before submission
    if (!ccoEmail) {
      setEmailError('CCO email is required')
      return
    }
    
    if (!validateEmail(ccoEmail)) {
      setEmailError('Please enter a valid email address')
      return
    }

    try {
      await onSubmit(ccoEmail, notes)
      onClose()
    } catch (error) {
      // Error handling is done in the parent component
      console.error('Submit failed:', error)
    }
  }

  const handleCancel = () => {
    if (!isSubmitting) {
      onClose()
    }
  }

  return (
    <Dialog open={isOpen} onOpenChange={handleCancel}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Send className="h-5 w-5 text-primary" />
            Submit for Compliance Review
          </DialogTitle>
          <DialogDescription>
            Send your content to your Chief Compliance Officer for review and approval.
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Content Preview */}
          <div className="border rounded-lg p-3 bg-muted/20">
            <div className="flex items-center gap-2 mb-2">
              <Badge variant="outline" className="text-xs">Content</Badge>
            </div>
            <p className="text-sm font-medium text-foreground truncate">
              {contentTitle}
            </p>
          </div>

          {/* CCO Email Input */}
          <div className="space-y-2">
            <Label htmlFor="cco-email" className="flex items-center gap-2">
              <Mail className="h-4 w-4" />
              Chief Compliance Officer Email
            </Label>
            <Input
              id="cco-email"
              type="email"
              value={ccoEmail}
              onChange={handleEmailChange}
              placeholder="cco@yourfirm.com"
              className={emailError ? 'border-red-500' : ''}
              disabled={isSubmitting}
              required
            />
            {emailError && (
              <div className="flex items-center gap-1 text-sm text-red-600">
                <AlertCircle className="h-3 w-3" />
                {emailError}
              </div>
            )}
          </div>

          {/* Optional Notes */}
          <div className="space-y-2">
            <Label htmlFor="review-notes">
              Notes for CCO <span className="text-muted-foreground">(optional)</span>
            </Label>
            <Textarea
              id="review-notes"
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder="Add any specific instructions or context for the compliance review..."
              rows={3}
              disabled={isSubmitting}
              className="resize-none"
            />
          </div>

          {/* Compliance Notice */}
          <div className="border border-amber-200 bg-amber-50 dark:bg-amber-950/20 dark:border-amber-800 rounded-lg p-3">
            <div className="flex items-start gap-2">
              <AlertCircle className="h-4 w-4 text-amber-600 dark:text-amber-400 mt-0.5 flex-shrink-0" />
              <div className="text-xs text-amber-800 dark:text-amber-200">
                <p className="font-medium mb-1">Compliance Review Process</p>
                <p>Your CCO will receive an email with a secure link to review your content. 
                You'll be notified once the review is complete.</p>
              </div>
            </div>
          </div>

          <DialogFooter className="flex gap-2">
            <Button 
              type="button" 
              variant="outline" 
              onClick={handleCancel}
              disabled={isSubmitting}
            >
              Cancel
            </Button>
            <Button 
              type="submit" 
              disabled={isSubmitting || !!emailError || !ccoEmail}
              className="min-w-[120px]"
            >
              {isSubmitting ? (
                <div className="flex items-center gap-2">
                  <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                  Submitting...
                </div>
              ) : (
                <div className="flex items-center gap-2">
                  <Send className="h-4 w-4" />
                  Submit for Review
                </div>
              )}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}
