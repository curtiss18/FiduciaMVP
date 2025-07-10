'use client'

import React, { useState, useCallback, useRef } from 'react'
import { Button } from '@/components/ui/button'
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { FileText, Upload, CheckCircle, XCircle, AlertCircle, X, FileIcon } from 'lucide-react'
import { cn } from '@/lib/utils'
import { advisorApi } from '@/lib/api'
import { BatchUploadResponse, DocumentUploadResult } from '@/lib/types'

interface MultiFileUploadModalProps {
  isOpen: boolean
  onClose: () => void
  sessionId: string | null
  onUploadComplete?: (results: BatchUploadResponse) => void
  onSessionCreated?: (sessionId: string) => void // New callback for session creation
}

interface FileWithMetadata {
  file: File
  id: string
  title: string
  status: 'pending' | 'uploading' | 'success' | 'failed'
  result?: DocumentUploadResult
  error?: string
}

const ACCEPTED_FILE_TYPES = {
  'application/pdf': '.pdf',
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document': '.docx',
  'text/plain': '.txt'
}

const MAX_FILE_SIZE = 10 * 1024 * 1024 // 10MB
const MAX_FILES = 10

export const MultiFileUploadModal: React.FC<MultiFileUploadModalProps> = ({
  isOpen,
  onClose,
  sessionId,
  onUploadComplete,
  onSessionCreated
}) => {
  const [files, setFiles] = useState<FileWithMetadata[]>([])
  const [isUploading, setIsUploading] = useState(false)
  const [isDragOver, setIsDragOver] = useState(false)
  const [uploadResults, setUploadResults] = useState<BatchUploadResponse | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  // Generate unique ID for files
  const generateFileId = () => `file_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`

  // Generate title from filename
  const generateTitleFromFilename = (filename: string): string => {
    // Remove extension and clean up the name
    const nameWithoutExt = filename.replace(/\.[^/.]+$/, '')
    
    // Replace underscores and hyphens with spaces
    const cleanName = nameWithoutExt
      .replace(/[_-]/g, ' ')
      .replace(/([a-z])([A-Z])/g, '$1 $2') // Add space before capital letters
      .trim()
    
    // Capitalize first letter of each word
    return cleanName
      .split(' ')
      .map(word => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase())
      .join(' ')
  }

  // Validate file type and size
  const validateFile = (file: File): string | null => {
    // Check file type
    if (!Object.keys(ACCEPTED_FILE_TYPES).includes(file.type)) {
      return `File type ${file.type} not supported. Please use PDF, DOCX, or TXT files.`
    }

    // Check file size
    if (file.size > MAX_FILE_SIZE) {
      return `File size (${(file.size / 1024 / 1024).toFixed(1)}MB) exceeds maximum allowed size of 10MB.`
    }

    return null
  }

  // Add files to the list
  const addFiles = useCallback((newFiles: File[]) => {
    const validFiles: FileWithMetadata[] = []
    const errors: string[] = []

    // Check total file limit
    if (files.length + newFiles.length > MAX_FILES) {
      errors.push(`Cannot add ${newFiles.length} files. Maximum ${MAX_FILES} files allowed.`)
      return
    }

    newFiles.forEach(file => {
      // Check for duplicates
      const isDuplicate = files.some(f => f.file.name === file.name && f.file.size === file.size)
      if (isDuplicate) {
        errors.push(`File "${file.name}" is already selected.`)
        return
      }

      // Validate file
      const validationError = validateFile(file)
      if (validationError) {
        errors.push(`${file.name}: ${validationError}`)
        return
      }

      // Add valid file
      validFiles.push({
        file,
        id: generateFileId(),
        title: generateTitleFromFilename(file.name),
        status: 'pending'
      })
    })

    if (errors.length > 0) {
      console.error('File validation errors:', errors)
      // TODO: Show toast notifications for errors
    }

    if (validFiles.length > 0) {
      setFiles(prev => [...prev, ...validFiles])
    }
  }, [files])

  // Handle file selection
  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      const fileArray = Array.from(e.target.files)
      addFiles(fileArray)
    }
    // Reset the input
    if (fileInputRef.current) {
      fileInputRef.current.value = ''
    }
  }

  // Handle drag and drop
  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragOver(true)
  }, [])

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragOver(false)
  }, [])

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragOver(false)
    
    const droppedFiles = Array.from(e.dataTransfer.files)
    addFiles(droppedFiles)
  }, [addFiles])

  // Remove file from list
  const removeFile = (fileId: string) => {
    setFiles(prev => prev.filter(f => f.id !== fileId))
  }

  // Update file title
  const updateFileTitle = (fileId: string, newTitle: string) => {
    setFiles(prev => prev.map(f => 
      f.id === fileId ? { ...f, title: newTitle } : f
    ))
  }

  // Upload files
  const handleUpload = async () => {
    if (files.length === 0) {
      return
    }

    setIsUploading(true)
    setUploadResults(null)

    try {
      // Update all files to uploading status
      setFiles(prev => prev.map(f => ({ ...f, status: 'uploading' as const })))

      // Ensure we have a session - create one if needed
      let uploadSessionId = sessionId
      if (!uploadSessionId) {
        console.log('No session ID provided, creating new session for document upload...')
        try {
          const sessionResponse = await advisorApi.createSession(
            'demo_advisor_001', // Default advisor ID
            `Document Upload Session - ${new Date().toLocaleDateString()}`
          )
          uploadSessionId = sessionResponse.session.session_id
          console.log('Created new session for document upload:', uploadSessionId)
          
          // Notify parent component about the new session
          onSessionCreated?.(uploadSessionId)
        } catch (error) {
          console.error('Failed to create session for document upload:', error)
          throw new Error('Failed to create session for document upload')
        }
      }

      // Prepare files and titles for upload
      const filesToUpload = files.map(f => f.file)
      const titles = files.map(f => f.title)

      // Call the batch upload API
      const response = await advisorApi.uploadDocuments(uploadSessionId, filesToUpload, titles)
      
      setUploadResults(response)

      // Update file statuses based on results
      setFiles(prev => prev.map(fileWithMeta => {
        const result = response.batch_results.successful_uploads.find(
          r => r.filename === fileWithMeta.file.name
        ) || response.batch_results.failed_uploads.find(
          r => r.filename === fileWithMeta.file.name
        )

        if (result) {
          return {
            ...fileWithMeta,
            status: result.status === 'success' ? 'success' : 'failed',
            result,
            error: result.error
          }
        }

        return { ...fileWithMeta, status: 'failed', error: 'No result found' }
      }))

      // Notify parent component
      onUploadComplete?.(response)

    } catch (error) {
      console.error('Batch upload failed:', error)
      
      // Update all files to failed status
      setFiles(prev => prev.map(f => ({ 
        ...f, 
        status: 'failed', 
        error: error instanceof Error ? error.message : 'Upload failed. Please try again.' 
      })))
    } finally {
      setIsUploading(false)
    }
  }

  // Reset modal state
  const handleClose = () => {
    if (!isUploading) {
      setFiles([])
      setUploadResults(null)
      onClose()
    }
  }

  // Get file icon based on type
  const getFileIcon = (file: File) => {
    if (file.type === 'application/pdf') return '📄'
    if (file.type === 'application/vnd.openxmlformats-officedocument.wordprocessingml.document') return '📝'
    if (file.type === 'text/plain') return '📋'
    return '📁'
  }

  // Get status icon
  const getStatusIcon = (status: FileWithMetadata['status']) => {
    switch (status) {
      case 'pending':
        return <FileIcon className="h-4 w-4 text-muted-foreground" />
      case 'uploading':
        return <div className="h-4 w-4 animate-spin rounded-full border-2 border-primary border-t-transparent" />
      case 'success':
        return <CheckCircle className="h-4 w-4 text-green-600" />
      case 'failed':
        return <XCircle className="h-4 w-4 text-red-600" />
      default:
        return <FileIcon className="h-4 w-4 text-muted-foreground" />
    }
  }

  // Format file size
  const formatFileSize = (bytes: number): string => {
    if (bytes < 1024) return `${bytes} B`
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
    return `${(bytes / 1024 / 1024).toFixed(1)} MB`
  }

  return (
    <Dialog open={isOpen} onOpenChange={handleClose}>
      <DialogContent className="max-w-2xl max-h-[80vh] flex flex-col">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Upload className="h-5 w-5" />
            Upload Multiple Documents
          </DialogTitle>
        </DialogHeader>

        <div className="flex-1 flex flex-col gap-4 min-h-0">
          {/* File Selection Area */}
          {!uploadResults && (
            <div
              className={cn(
                "border-2 border-dashed rounded-lg p-8 text-center transition-colors",
                isDragOver ? "border-primary bg-primary/5" : "border-muted-foreground/25",
                isUploading && "pointer-events-none opacity-50"
              )}
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              onDrop={handleDrop}
            >
              <div className="flex flex-col items-center gap-3">
                <div className="w-12 h-12 bg-muted rounded-full flex items-center justify-center">
                  <Upload className="h-6 w-6 text-muted-foreground" />
                </div>
                <div>
                  <p className="font-medium">Drop files here or click to browse</p>
                  <p className="text-sm text-muted-foreground">
                    PDF, DOCX, and TXT files up to 10MB each
                  </p>
                </div>
                <Button
                  variant="outline"
                  onClick={() => fileInputRef.current?.click()}
                  disabled={isUploading}
                >
                  Select Files
                </Button>
              </div>

              <input
                ref={fileInputRef}
                type="file"
                multiple
                accept=".pdf,.docx,.txt"
                className="hidden"
                onChange={handleFileSelect}
                disabled={isUploading}
              />
            </div>
          )}

          {/* File List */}
          {files.length > 0 && (
            <div className="flex-1 min-h-0">
              <div className="flex items-center justify-between mb-3">
                <Label className="text-sm font-medium">
                  Selected Files ({files.length}/{MAX_FILES})
                </Label>
                {!isUploading && !uploadResults && (
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => setFiles([])}
                  >
                    Clear All
                  </Button>
                )}
              </div>

              <div className="space-y-2 max-h-60 overflow-y-auto">
                {files.map((fileWithMeta) => (
                  <div
                    key={fileWithMeta.id}
                    className="flex items-center gap-3 p-3 border rounded-lg bg-background"
                  >
                    {/* File Icon & Status */}
                    <div className="flex items-center gap-2 flex-shrink-0">
                      <span className="text-lg">{getFileIcon(fileWithMeta.file)}</span>
                      {getStatusIcon(fileWithMeta.status)}
                    </div>

                    {/* File Info */}
                    <div className="flex-1 min-w-0">
                      <div className="font-medium text-sm truncate">
                        {fileWithMeta.file.name}
                      </div>
                      <div className="text-xs text-muted-foreground">
                        {formatFileSize(fileWithMeta.file.size)}
                        {fileWithMeta.result?.processing_results && (
                          <span className="ml-2">
                            • {fileWithMeta.result.processing_results.word_count} words
                            {fileWithMeta.result.processing_results.summary_tokens && (
                              <span> • {fileWithMeta.result.processing_results.summary_tokens} summary tokens</span>
                            )}
                          </span>
                        )}
                      </div>
                      {fileWithMeta.error && (
                        <div className="text-xs text-red-600 mt-1">
                          {fileWithMeta.error}
                        </div>
                      )}
                      {fileWithMeta.result?.processing_results?.summary_preview && (
                        <div className="text-xs text-muted-foreground mt-1 italic">
                          "{fileWithMeta.result.processing_results.summary_preview}..."
                        </div>
                      )}
                    </div>

                    {/* Remove Button */}
                    {!isUploading && fileWithMeta.status === 'pending' && (
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => removeFile(fileWithMeta.id)}
                        className="flex-shrink-0"
                      >
                        <X className="h-4 w-4" />
                      </Button>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Upload Results Summary */}
          {uploadResults && (
            <div className="border rounded-lg p-4 bg-muted/20">
              <h4 className="font-medium mb-2 flex items-center gap-2">
                {uploadResults.status === 'success' ? (
                  <CheckCircle className="h-4 w-4 text-green-600" />
                ) : uploadResults.status === 'partial_success' ? (
                  <AlertCircle className="h-4 w-4 text-yellow-600" />
                ) : (
                  <XCircle className="h-4 w-4 text-red-600" />
                )}
                Upload Results
              </h4>
              <p className="text-sm text-muted-foreground mb-2">
                {uploadResults.message}
              </p>
              <div className="text-xs text-muted-foreground">
                {uploadResults.batch_results.successful_count} of {uploadResults.batch_results.total_files} files uploaded successfully
                ({Math.round(uploadResults.batch_results.success_rate * 100)}% success rate)
              </div>
            </div>
          )}
        </div>

        {/* Action Buttons */}
        <div className="flex justify-between pt-4 border-t">
          <Button
            variant="outline"
            onClick={handleClose}
            disabled={isUploading}
          >
            {uploadResults ? 'Close' : 'Cancel'}
          </Button>

          {!uploadResults && (
            <Button
              onClick={handleUpload}
              disabled={files.length === 0 || isUploading}
              className="min-w-[120px]"
            >
              {isUploading ? (
                <>
                  <div className="w-4 h-4 animate-spin rounded-full border-2 border-background border-t-transparent mr-2" />
                  Uploading...
                </>
              ) : (
                <>
                  <Upload className="h-4 w-4 mr-2" />
                  Upload {files.length} File{files.length !== 1 ? 's' : ''}
                </>
              )}
            </Button>
          )}

          {uploadResults && (
            <Button
              variant="outline"
              onClick={() => {
                setFiles([])
                setUploadResults(null)
              }}
            >
              Upload More Files
            </Button>
          )}
        </div>
      </DialogContent>
    </Dialog>
  )
}
