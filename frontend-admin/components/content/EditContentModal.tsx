'use client'

import { useState, useEffect } from 'react'
import { Button } from '@/components/ui/button'
import { Loader2, Plus } from 'lucide-react'
import { contentApi } from '@/lib/api'
import { ContentItem } from './types'

interface EditContentModalProps {
  isOpen: boolean
  onClose: () => void
  onSuccess: () => void
  content: ContentItem | null
}

interface EnumData {
  content_types: string[]
  audience_types: string[]
  approval_statuses: string[]
  source_types: string[]
}

export default function EditContentModal({ isOpen, onClose, onSuccess, content }: EditContentModalProps) {
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
  
  // Track original values and changes
  const [originalData, setOriginalData] = useState({
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
  const [modifiedFields, setModifiedFields] = useState<Set<string>>(new Set())
  
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

  // Pre-populate form when content changes  
  useEffect(() => {
    if (content && isOpen) {
      const initialData = {
        title: content.title || '',
        content_text: content.content_text || '',
        content_type: content.content_type || 'email_template',
        audience_type: content.audience_type || 'general_education',
        approval_status: content.approval_status || 'approved',
        source_type: content.source || 'fiducia_created',
        tone: '', // These fields don't exist in ContentItem, keep empty
        topic_focus: '',
        target_demographics: '',
        tags: String(content.tags || ''), // Ensure string conversion
        original_source: '', // Not in ContentItem, keep empty
        compliance_score: '1.0'
      }
      
      setFormData(initialData)
      setOriginalData(initialData)
      setModifiedFields(new Set())
    }
  }, [content, isOpen])

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
    
    // Update form data (matching AddContentModal exactly)
    setFormData(prev => ({
      ...prev,
      [name]: value
    }))
    
    // Track if field has been modified 
    const originalValue = String(originalData[name as keyof typeof originalData] || '')
    const isModified = value !== originalValue
    setModifiedFields(prev => {
      const newSet = new Set(prev)
      if (isModified) {
        newSet.add(name)
      } else {
        newSet.delete(name)
      }
      return newSet
    })
  }

  // Helper function to get field styling based on modification status
  const getFieldClassName = (fieldName: string, baseClassName: string) => {
    const isModified = modifiedFields.has(fieldName)
    return `${baseClassName} ${isModified ? 'ring-2 ring-blue-500/50 border-blue-500 dark:ring-blue-400/50 dark:border-blue-400' : ''}`
  }

  // Helper function to render field label with change indicator
  const renderFieldLabel = (text: string, fieldName: string, required = false) => {
    const isModified = modifiedFields.has(fieldName)
    return (
      <label className="block text-sm font-medium text-foreground mb-1">
        {text}
        {required && <span className="text-red-500 dark:text-red-400">*</span>}
        {isModified && (
          <span className="ml-2 inline-flex items-center px-1.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-300">
            Modified
          </span>
        )}
      </label>
    )
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
    if (!content || !formData.title.trim() || !formData.content_text.trim()) {
      showNotification('error', 'Please fill in required fields (Title and Content)')
      return
    }

    try {
      setIsSubmitting(true)
      
      // Prepare the data with proper field mapping (matching AddContentModal exactly)
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
        tags: (typeof formData.tags === 'string' ? formData.tags : String(formData.tags || '')).trim() || null,
        original_source: formData.original_source.trim() || null,
        compliance_score: parseFloat(formData.compliance_score) || 1.0
      }
      
      await contentApi.updateContent(content.id, submitData)
      
      showNotification('success', 'Content updated successfully!')
      
      // Close modal after a brief delay to show success message
      setTimeout(() => {
        onSuccess()
        onClose()
      }, 1500)
      
    } catch (error: any) {
      console.error('Error updating content:', error)
      
      // Better error handling
      let errorMessage = 'Failed to update content. Please try again.'
      if (error.response?.data?.error) {
        errorMessage = `Error: ${error.response.data.error}`
      }
      showNotification('error', errorMessage)
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleClose = () => {
    setShowCustomEnum({
      content_type: false,
      audience_type: false
    })
    setCustomEnumValues({
      content_type: '',
      audience_type: ''
    })
    setNotification(null)
    setModifiedFields(new Set()) // Reset modified fields tracking
    onClose()
  }

  if (!isOpen || !content) return null

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
            <h2 className="text-xl font-bold text-card-foreground">Edit Content</h2>
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

          <form onSubmit={handleSubmit} className="space-y-4">            <div>
              {renderFieldLabel('Title', 'title', true)}
              <input
                type="text"
                name="title"
                value={formData.title}
                onChange={handleInputChange}
                className={getFieldClassName('title', 'w-full px-3 py-2 border border-input rounded-md bg-background text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring')}
                placeholder="Enter content title"
                required
              />
            </div>

            <div>
              {renderFieldLabel('Content', 'content_text', true)}
              <textarea
                name="content_text"
                value={formData.content_text}
                onChange={handleInputChange}
                rows={6}
                className={getFieldClassName('content_text', 'w-full px-3 py-2 border border-input rounded-md bg-background text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring')}
                placeholder="Enter content text"
                required
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                {renderFieldLabel('Content Type', 'content_type')}
                <div className="space-y-2">
                  <select
                    name="content_type"
                    value={formData.content_type}
                    onChange={handleInputChange}
                    className={getFieldClassName('content_type', 'w-full px-3 py-2 border border-input rounded-md bg-background text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring')}
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
                {renderFieldLabel('Audience Type', 'audience_type')}
                <div className="space-y-2">
                  <select
                    name="audience_type"
                    value={formData.audience_type}
                    onChange={handleInputChange}
                    className={getFieldClassName('audience_type', 'w-full px-3 py-2 border border-input rounded-md bg-background text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring')}
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
                {renderFieldLabel('Approval Status', 'approval_status')}
                <select
                  name="approval_status"
                  value={formData.approval_status}
                  onChange={handleInputChange}
                  className={getFieldClassName('approval_status', 'w-full px-3 py-2 border border-input rounded-md bg-background text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring')}
                >
                  {enums?.approval_statuses.map(status => (
                    <option key={status} value={status}>
                      {formatEnumLabel(status)}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                {renderFieldLabel('Source Type', 'source_type')}
                <select
                  name="source_type"
                  value={formData.source_type}
                  onChange={handleInputChange}
                  className={getFieldClassName('source_type', 'w-full px-3 py-2 border border-input rounded-md bg-background text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring')}
                >
                  {enums?.source_types.map(source => (
                    <option key={source} value={source}>
                      {formatEnumLabel(source)}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                {renderFieldLabel('Compliance Score', 'compliance_score')}
                <input
                  type="number"
                  name="compliance_score"
                  value={formData.compliance_score}
                  onChange={handleInputChange}
                  min="0"
                  max="1"
                  step="0.1"
                  className={getFieldClassName('compliance_score', 'w-full px-3 py-2 border border-input rounded-md bg-background text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring')}
                  placeholder="0.0 - 1.0"
                />
              </div>
            </div>

            <div className="grid grid-cols-3 gap-4">
              <div>
                {renderFieldLabel('Tone', 'tone')}
                <input
                  type="text"
                  name="tone"
                  value={formData.tone}
                  onChange={handleInputChange}
                  className={getFieldClassName('tone', 'w-full px-3 py-2 border border-input rounded-md bg-background text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring')}
                  placeholder="e.g., professional, casual, educational"
                />
              </div>

              <div>
                {renderFieldLabel('Topic Focus', 'topic_focus')}
                <input
                  type="text"
                  name="topic_focus"
                  value={formData.topic_focus}
                  onChange={handleInputChange}
                  className={getFieldClassName('topic_focus', 'w-full px-3 py-2 border border-input rounded-md bg-background text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring')}
                  placeholder="e.g., retirement, investing, tax planning"
                />
              </div>

              <div>
                {renderFieldLabel('Target Demographics', 'target_demographics')}
                <input
                  type="text"
                  name="target_demographics"
                  value={formData.target_demographics}
                  onChange={handleInputChange}
                  className={getFieldClassName('target_demographics', 'w-full px-3 py-2 border border-input rounded-md bg-background text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring')}
                  placeholder="e.g., millennials, boomers, high net worth"
                />
              </div>
            </div>

            <div>
              {renderFieldLabel('Tags', 'tags')}
              <input
                type="text"
                name="tags"
                value={formData.tags}
                onChange={handleInputChange}
                className={getFieldClassName('tags', 'w-full px-3 py-2 border border-input rounded-md bg-background text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring')}
                placeholder="Enter tags separated by commas"
              />
            </div>

            <div>
              {renderFieldLabel('Original Source', 'original_source')}
              <textarea
                name="original_source"
                value={formData.original_source}
                onChange={handleInputChange}
                rows={2}
                className={getFieldClassName('original_source', 'w-full px-3 py-2 border border-input rounded-md bg-background text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring')}
                placeholder="URL, file path, or description of the original source"
              />
            </div>

            {/* Modified Fields Summary */}
            {modifiedFields.size > 0 && (
              <div className="mt-4 p-3 bg-blue-50 border border-blue-200 rounded-md dark:bg-blue-900/20 dark:border-blue-800">
                <div className="flex items-center">
                  <div className="flex-shrink-0">
                    <svg className="w-5 h-5 text-blue-500 dark:text-blue-400" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
                    </svg>
                  </div>
                  <div className="ml-3">
                    <p className="text-sm font-medium text-blue-800 dark:text-blue-300">
                      {modifiedFields.size} field{modifiedFields.size !== 1 ? 's' : ''} modified
                    </p>
                    <p className="text-xs text-blue-600 dark:text-blue-400 mt-1">
                      {Array.from(modifiedFields).map(field => 
                        field.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())
                      ).join(', ')}
                    </p>
                  </div>
                </div>
              </div>
            )}

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
                    Updating...
                  </>
                ) : (
                  'Update Content'
                )}
              </Button>
            </div>
          </form>
        </div>
      </div>
    </div>
  )
}