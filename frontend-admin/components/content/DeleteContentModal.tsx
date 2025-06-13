'use client'

import { useState, useEffect } from 'react'
import { Button } from '@/components/ui/button'
import { Loader2, AlertTriangle } from 'lucide-react'
import { contentApi } from '@/lib/api'

interface DeleteContentModalProps {
  isOpen: boolean
  onClose: () => void
  onSuccess: () => void
  content: {
    id: number
    title: string
    content_type: string
  } | null
}

export default function DeleteContentModal({ 
  isOpen, 
  onClose, 
  onSuccess, 
  content 
}: DeleteContentModalProps) {
  const [isDeleting, setIsDeleting] = useState(false)
  const [notification, setNotification] = useState<{
    type: 'success' | 'error'
    message: string
  } | null>(null)

  // Auto-hide notifications and close modal on success
  useEffect(() => {
    if (notification?.type === 'success') {
      const timer = setTimeout(() => {
        onSuccess()
        onClose()
        setNotification(null)
      }, 1500)
      return () => clearTimeout(timer)
    } else if (notification?.type === 'error') {
      const timer = setTimeout(() => {
        setNotification(null)
      }, 4000)
      return () => clearTimeout(timer)
    }
  }, [notification, onSuccess, onClose])

  const showNotification = (type: 'success' | 'error', message: string) => {
    setNotification({ type, message })
  }

  const handleDelete = async () => {
    if (!content) return

    try {
      setIsDeleting(true)
      console.log('Attempting to delete content:', content.id)
      
      const response = await contentApi.deleteContent(content.id)
      console.log('Delete response:', response)
      
      // Check if the response indicates success
      if (response.data && response.data.status === 'success') {
        showNotification('success', 'Content deleted successfully!')
      } else {
        // Handle unexpected response format
        console.error('Unexpected response format:', response)
        showNotification('error', 'Delete may have failed - please check if record was removed')
      }
    } catch (error: any) {
      console.error('Error deleting content:', error)
      console.error('Error response:', error.response)
      
      let errorMessage = 'Failed to delete content. Please try again.'
      if (error.response?.data?.error) {
        errorMessage = `Error: ${error.response.data.error}`
      } else if (error.response?.data?.message) {
        errorMessage = `Error: ${error.response.data.message}`
      }
      showNotification('error', errorMessage)
    } finally {
      setIsDeleting(false)
    }
  }

  const handleClose = () => {
    setNotification(null)
    onClose()
  }

  if (!isOpen || !content) return null

  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center p-4 z-50">
      <div className="bg-card rounded-lg shadow-xl max-w-md w-full border border-border">
        <div className="p-6">
          <div className="flex items-center space-x-3 mb-4">
            <div className="flex-shrink-0">
              <AlertTriangle className="w-8 h-8 text-destructive" />
            </div>
            <div>
              <h3 className="text-lg font-semibold text-card-foreground">
                Delete Content
              </h3>
              <p className="text-sm text-muted-foreground">
                This action cannot be undone
              </p>
            </div>
          </div>

          {/* Notification */}
          {notification && (
            <div className={`mb-4 p-3 rounded-md border ${
              notification.type === 'success' 
                ? 'bg-green-50 border-green-200 dark:bg-green-900/20 dark:border-green-800' 
                : 'bg-red-50 border-red-200 dark:bg-red-900/20 dark:border-red-800'
            }`}>
              <div className="flex items-center">
                <div className={`flex-shrink-0 ${
                  notification.type === 'success' ? 'text-green-500 dark:text-green-400' : 'text-red-500 dark:text-red-400'
                }`}>
                  {notification.type === 'success' ? (
                    <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                    </svg>
                  ) : (
                    <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                    </svg>
                  )}
                </div>
                <div className="ml-3">
                  <p className={`text-sm font-medium ${
                    notification.type === 'success' 
                      ? 'text-green-800 dark:text-green-300' 
                      : 'text-red-800 dark:text-red-300'
                  }`}>
                    {notification.message}
                  </p>
                </div>
              </div>
            </div>
          )}

          <div className="mb-6">
            <p className="text-card-foreground">
              Are you sure you want to delete this content?
            </p>
            <div className="mt-3 p-3 bg-muted/50 rounded-md border border-border">
              <p className="font-medium text-card-foreground">
                "{content.title}"
              </p>
              <p className="text-sm text-muted-foreground mt-1">
                Type: {content.content_type.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}
              </p>
              <p className="text-sm text-muted-foreground">
                ID: {content.id}
              </p>
            </div>
          </div>

          <div className="flex justify-end space-x-3">
            <Button
              type="button"
              variant="outline"
              onClick={handleClose}
              disabled={isDeleting}
            >
              Cancel
            </Button>
            <Button
              type="button"
              onClick={handleDelete}
              disabled={isDeleting}
              className="bg-destructive hover:bg-destructive/90 text-destructive-foreground"
            >
              {isDeleting ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  Deleting...
                </>
              ) : (
                'Delete Content'
              )}
            </Button>
          </div>
        </div>
      </div>
    </div>
  )
}
