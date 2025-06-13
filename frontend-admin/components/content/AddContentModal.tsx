'use client'

import { useState, useEffect } from 'react'
import { Button } from '@/components/ui/button'
import { Loader2, Plus } from 'lucide-react'
import { contentApi } from '@/lib/api'

interface AddContentModalProps {
  isOpen: boolean
  onClose: () => void
  onSuccess: () => void
}

interface EnumData {
  content_types: string[]
  audience_types: string[]
  approval_statuses: string[]
  source_types: string[]
}

export default function AddContentModal({ isOpen, onClose, onSuccess }: AddContentModalProps) {
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [isLoadingEnums, setIsLoadingEnums] = useState(false)
  const [enums, setEnums] = useState<EnumData | null>(null)
  const [notification, setNotification] = useState<{
    type: 'success' | 'error' | 'info'
    message: string
  } | null>(null)
  const [showCustomEnum, setShowCustomEnum] = useState({
    content_type: false,
    audience_type: false
  })
  const [customEnumValues, setCustomEnumValues] = useState({
    content_type: '',
    audience_type: ''
  })
  
  const [formData, setFormData] = useState({
    title: '',
    content_text: '',
    content_type: 'email_template',
    audience_type: 'general_education',
    approval_status: 'approved',
    source_type: 'fiducia_created',
    tone: '',
    topic_focus: '',
    target_demographics: '',
    tags: '',
    original_source: '',
    compliance_score: '1.0'
  })

  // Load enums when modal opens
  useEffect(() => {
    if (isOpen && !enums) {
      loadEnums()
    }
  }, [isOpen])

  // Auto-hide notifications
  useEffect(() => {
    if (notification) {
      const timer = setTimeout(() => {
        setNotification(null)
      }, 4000) // Hide after 4 seconds
      return () => clearTimeout(timer)
    }
  }, [notification])

  const showNotification = (type: 'success' | 'error' | 'info', message: string) => {
    setNotification({ type, message })
  }

  const loadEnums = async () => {
    try {
      setIsLoadingEnums(true)
      const response = await contentApi.getContentEnums()
      if (response.data.status === 'success') {
        setEnums(response.data.enums)
      }
    } catch (error) {
      console.error('Error loading enums:', error)
      showNotification('error', 'Failed to load form options. Please refresh and try again.')
    } finally {
      setIsLoadingEnums(false)
    }
  }

  // Helper function to format enum values for display
  const formatEnumLabel = (value: string) => {
    return value
      .split('_')
      .map(word => word.charAt(0).toUpperCase() + word.slice(1))
      .join(' ')
  }

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
    const { name, value } = e.target
    setFormData(prev => ({
      ...prev,
      [name]: value
    }))
  }

  const handleCustomEnumToggle = (enumType: 'content_type' | 'audience_type') => {
    setShowCustomEnum(prev => ({
      ...prev,
      [enumType]: !prev[enumType]
    }))
  }

  const handleCustomEnumChange = (enumType: 'content_type' | 'audience_type', value: string) => {
    setCustomEnumValues(prev => ({
      ...prev,
      [enumType]: value
    }))
  }

  const handleCustomEnumSubmit = (enumType: 'content_type' | 'audience_type') => {
    const customValue = customEnumValues[enumType].trim()
    if (!customValue) return
    
    // Convert to snake_case
    const snakeCaseValue = customValue.toLowerCase().replace(/\s+/g, '_')
    
    // Update form data
    setFormData(prev => ({
      ...prev,
      [enumType]: snakeCaseValue
    }))
    
    // Reset custom input
    setCustomEnumValues(prev => ({
      ...prev,
      [enumType]: ''
    }))
    setShowCustomEnum(prev => ({
      ...prev,
      [enumType]: false
    }))
    
    showNotification('info', `Custom ${enumType.replace(/_/g, ' ')} "${customValue}" will be submitted. Note: This may require admin approval.`)
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!formData.title.trim() || !formData.content_text.trim()) {
      showNotification('error', 'Please fill in required fields (Title and Content)')
      return
    }

    try {
      setIsSubmitting(true)
      
      // Prepare the data with proper field mapping
      const submitData = {
        title: formData.title.trim(),
        content_text: formData.content_text.trim(),
        content_type: formData.content_type,
        audience_type: formData.audience_type,
        approval_status: formData.approval_status,
        source_type: formData.source_type,
        tone: formData.tone.trim() || null,
        topic_focus: formData.topic_focus.trim() || null,
        target_demographics: formData.target_demographics.trim() || null,
        tags: formData.tags.trim() || null,
        original_source: formData.original_source.trim() || null,
        compliance_score: parseFloat(formData.compliance_score) || 1.0
      }
      
      await contentApi.createContent(submitData)
      
      // Reset form
      setFormData({
        title: '',
        content_text: '',
        content_type: 'email_template',
        audience_type: 'general_education',
        approval_status: 'approved',
        source_type: 'fiducia_created',
        tone: '',
        topic_focus: '',
        target_demographics: '',
        tags: '',
        original_source: '',
        compliance_score: '1.0'
      })
      
      showNotification('success', 'Content created successfully!')
      
      // Close modal after a brief delay to show success message
      setTimeout(() => {
        onSuccess()
        onClose()
      }, 1500)
      
    } catch (error: any) {
      console.error('Error creating content:', error)
      
      // Better error handling
      let errorMessage = 'Failed to create content. Please try again.'
      if (error.response?.data?.error) {
        errorMessage = `Error: ${error.response.data.error}`
      }
      showNotification('error', errorMessage)
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleClose = () => {
    setFormData({
      title: '',
      content_text: '',
      content_type: 'email_template',
      audience_type: 'general_education',
      approval_status: 'approved',
      source_type: 'fiducia_created',
      tone: '',
      topic_focus: '',
      target_demographics: '',
      tags: '',
      original_source: '',
      compliance_score: '1.0'
    })
    setShowCustomEnum({
      content_type: false,
      audience_type: false
    })
    setCustomEnumValues({
      content_type: '',
      audience_type: ''
    })
    setNotification(null)
    onClose()
  }

  if (!isOpen) return null

  if (isLoadingEnums) {
    return (
      <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center p-4 z-50">
        <div className="bg-card rounded-lg shadow-xl p-6 border border-border">
          <div className="flex items-center space-x-3">
            <Loader2 className="w-5 h-5 animate-spin text-primary" />
            <span className="text-card-foreground">Loading form options...</span>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center p-4 z-50">
      <div className="bg-card rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto border border-border">
        <div className="p-6">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-xl font-bold text-card-foreground">Add New Content</h2>
            <button
              onClick={handleClose}
              className="text-muted-foreground hover:text-foreground transition-colors"
            >
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          {/* Notification */}
          {notification && (
            <div className={`mb-4 p-3 rounded-md border ${
              notification.type === 'success' 
                ? 'bg-green-50 border-green-200 dark:bg-green-900/20 dark:border-green-800' :
              notification.type === 'error' 
                ? 'bg-red-50 border-red-200 dark:bg-red-900/20 dark:border-red-800' :
                'bg-blue-50 border-blue-200 dark:bg-blue-900/20 dark:border-blue-800'
            }`}>
              <div className="flex items-center">
                <div className={`flex-shrink-0 ${
                  notification.type === 'success' ? 'text-green-500 dark:text-green-400' :
                  notification.type === 'error' ? 'text-red-500 dark:text-red-400' :
                  'text-blue-500 dark:text-blue-400'
                }`}>
                  {notification.type === 'success' ? (
                    <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                    </svg>
                  ) : notification.type === 'error' ? (
                    <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                    </svg>
                  ) : (
                    <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
                    </svg>
                  )}
                </div>
                <div className="ml-3">
                  <p className={`text-sm font-medium ${
                    notification.type === 'success' ? 'text-green-800 dark:text-green-300' :
                    notification.type === 'error' ? 'text-red-800 dark:text-red-300' :
                    'text-blue-800 dark:text-blue-300'
                  }`}>
                    {notification.message}
                  </p>
                </div>
                <div className="ml-auto pl-3">
                  <button
                    onClick={() => setNotification(null)}
                    className={`inline-flex ${
                      notification.type === 'success' ? 'text-green-400 hover:text-green-600' :
                      notification.type === 'error' ? 'text-red-400 hover:text-red-600' :
                      'text-blue-400 hover:text-blue-600'
                    }`}
                  >
                    <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
                    </svg>
                  </button>
                </div>
              </div>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-foreground mb-1">
                Title <span className="text-red-500 dark:text-red-400">*</span>
              </label>
              <input
                type="text"
                name="title"
                value={formData.title}
                onChange={handleInputChange}
                className="w-full px-3 py-2 border border-input rounded-md bg-background text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring"
                placeholder="Enter content title"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-foreground mb-1">
                Content <span className="text-red-500 dark:text-red-400">*</span>
              </label>
              <textarea
                name="content_text"
                value={formData.content_text}
                onChange={handleInputChange}
                rows={6}
                className="w-full px-3 py-2 border border-input rounded-md bg-background text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring"
                placeholder="Enter content text"
                required
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-foreground mb-1">
                  Content Type
                </label>
                <div className="space-y-2">
                  <select
                    name="content_type"
                    value={formData.content_type}
                    onChange={handleInputChange}
                    className="w-full px-3 py-2 border border-input rounded-md bg-background text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring"
                  >
                    {enums?.content_types.map(type => (
                      <option key={type} value={type}>
                        {formatEnumLabel(type)}
                      </option>
                    ))}
                  </select>
                  
                  {!showCustomEnum.content_type && (
                    <button
                      type="button"
                      onClick={() => handleCustomEnumToggle('content_type')}
                      className="flex items-center space-x-1 text-sm text-blue-600 hover:text-blue-800"
                    >
                      <Plus className="w-4 h-4" />
                      <span>Add custom type</span>
                    </button>
                  )}
                  
                  {showCustomEnum.content_type && (
                    <div className="flex space-x-2">
                      <input
                        type="text"
                        value={customEnumValues.content_type}
                        onChange={(e) => handleCustomEnumChange('content_type', e.target.value)}
                        placeholder="Enter custom content type"
                        className="flex-1 px-2 py-1 text-sm border border-input rounded bg-background text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-ring"
                      />
                      <button
                        type="button"
                        onClick={() => handleCustomEnumSubmit('content_type')}
                        className="px-3 py-1 text-sm bg-primary text-primary-foreground rounded hover:bg-primary/90"
                      >
                        Add
                      </button>
                      <button
                        type="button"
                        onClick={() => handleCustomEnumToggle('content_type')}
                        className="px-3 py-1 text-sm bg-secondary text-secondary-foreground rounded hover:bg-secondary/80"
                      >
                        Cancel
                      </button>
                    </div>
                  )}
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-foreground mb-1">
                  Audience Type
                </label>
                <div className="space-y-2">
                  <select
                    name="audience_type"
                    value={formData.audience_type}
                    onChange={handleInputChange}
                    className="w-full px-3 py-2 border border-input rounded-md bg-background text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring"
                  >
                    {enums?.audience_types.map(type => (
                      <option key={type} value={type}>
                        {formatEnumLabel(type)}
                      </option>
                    ))}
                  </select>
                  
                  {!showCustomEnum.audience_type && (
                    <button
                      type="button"
                      onClick={() => handleCustomEnumToggle('audience_type')}
                      className="flex items-center space-x-1 text-sm text-blue-600 hover:text-blue-800"
                    >
                      <Plus className="w-4 h-4" />
                      <span>Add custom audience</span>
                    </button>
                  )}
                  
                  {showCustomEnum.audience_type && (
                    <div className="flex space-x-2">
                      <input
                        type="text"
                        value={customEnumValues.audience_type}
                        onChange={(e) => handleCustomEnumChange('audience_type', e.target.value)}
                        placeholder="Enter custom audience type"
                        className="flex-1 px-2 py-1 text-sm border border-input rounded bg-background text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-ring"
                      />
                      <button
                        type="button"
                        onClick={() => handleCustomEnumSubmit('audience_type')}
                        className="px-3 py-1 text-sm bg-primary text-primary-foreground rounded hover:bg-primary/90"
                      >
                        Add
                      </button>
                      <button
                        type="button"
                        onClick={() => handleCustomEnumToggle('audience_type')}
                        className="px-3 py-1 text-sm bg-secondary text-secondary-foreground rounded hover:bg-secondary/80"
                      >
                        Cancel
                      </button>
                    </div>
                  )}
                </div>
              </div>
            </div>

            <div className="grid grid-cols-3 gap-4">
              <div>
                <label className="block text-sm font-medium text-foreground mb-1">
                  Approval Status
                </label>
                <select
                  name="approval_status"
                  value={formData.approval_status}
                  onChange={handleInputChange}
                  className="w-full px-3 py-2 border border-input rounded-md bg-background text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring"
                >
                  {enums?.approval_statuses.map(status => (
                    <option key={status} value={status}>
                      {formatEnumLabel(status)}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-foreground mb-1">
                  Source Type
                </label>
                <select
                  name="source_type"
                  value={formData.source_type}
                  onChange={handleInputChange}
                  className="w-full px-3 py-2 border border-input rounded-md bg-background text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring"
                >
                  {enums?.source_types.map(source => (
                    <option key={source} value={source}>
                      {formatEnumLabel(source)}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-foreground mb-1">
                  Compliance Score
                </label>
                <input
                  type="number"
                  name="compliance_score"
                  value={formData.compliance_score}
                  onChange={handleInputChange}
                  min="0"
                  max="1"
                  step="0.1"
                  className="w-full px-3 py-2 border border-input rounded-md bg-background text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring"
                  placeholder="0.0 - 1.0"
                />
              </div>
            </div>

            <div className="grid grid-cols-3 gap-4">
              <div>
                <label className="block text-sm font-medium text-foreground mb-1">
                  Tone
                </label>
                <input
                  type="text"
                  name="tone"
                  value={formData.tone}
                  onChange={handleInputChange}
                  className="w-full px-3 py-2 border border-input rounded-md bg-background text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring"
                  placeholder="e.g., professional, casual, educational"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-foreground mb-1">
                  Topic Focus
                </label>
                <input
                  type="text"
                  name="topic_focus"
                  value={formData.topic_focus}
                  onChange={handleInputChange}
                  className="w-full px-3 py-2 border border-input rounded-md bg-background text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring"
                  placeholder="e.g., retirement, investing, tax planning"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-foreground mb-1">
                  Target Demographics
                </label>
                <input
                  type="text"
                  name="target_demographics"
                  value={formData.target_demographics}
                  onChange={handleInputChange}
                  className="w-full px-3 py-2 border border-input rounded-md bg-background text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring"
                  placeholder="e.g., millennials, boomers, high net worth"
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-foreground mb-1">
                Tags
              </label>
              <input
                type="text"
                name="tags"
                value={formData.tags}
                onChange={handleInputChange}
                className="w-full px-3 py-2 border border-input rounded-md bg-background text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring"
                placeholder="Enter tags separated by commas"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-foreground mb-1">
                Original Source
              </label>
              <textarea
                name="original_source"
                value={formData.original_source}
                onChange={handleInputChange}
                rows={2}
                className="w-full px-3 py-2 border border-input rounded-md bg-background text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring"
                placeholder="URL, file path, or description of the original source"
              />
            </div>

            <div className="flex justify-end space-x-3 pt-4">
              <Button
                type="button"
                variant="outline"
                onClick={handleClose}
                disabled={isSubmitting}
              >
                Cancel
              </Button>
              <Button
                type="submit"
                className="bg-primary hover:bg-primary/90 text-primary-foreground"
                disabled={isSubmitting}
              >
                {isSubmitting ? (
                  <>
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    Creating...
                  </>
                ) : (
                  'Create Content'
                )}
              </Button>
            </div>
          </form>
        </div>
      </div>
    </div>
  )
}