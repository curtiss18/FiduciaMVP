import React, { useState, useRef, useEffect } from 'react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Plus, Paperclip, Youtube, Upload } from 'lucide-react'
import { cn } from '@/lib/utils'
import { MultiFileUploadModal } from './MultiFileUploadModal'
import { BatchUploadResponse } from '@/lib/types'

interface AttachmentDropdownProps {
  onFileUpload?: (files: FileList) => void
  onYouTubeUrl?: (url: string) => void
  onMultiFileUpload?: (results: BatchUploadResponse) => void
  onSessionCreated?: (sessionId: string) => void
  sessionId?: string | null
  disabled?: boolean
}

export const AttachmentDropdown: React.FC<AttachmentDropdownProps> = ({
  onFileUpload,
  onYouTubeUrl,
  onMultiFileUpload,
  onSessionCreated,
  sessionId,
  disabled = false
}) => {
  const [isOpen, setIsOpen] = useState(false)
  const [showYouTubeInput, setShowYouTubeInput] = useState(false)
  const [showMultiFileModal, setShowMultiFileModal] = useState(false)
  const [youtubeUrl, setYoutubeUrl] = useState('')
  const dropdownRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false)
        setShowYouTubeInput(false)
        setYoutubeUrl('')
      }
    }

    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  // Focus input when YouTube option is clicked
  useEffect(() => {
    if (showYouTubeInput && inputRef.current) {
      inputRef.current.focus()
    }
  }, [showYouTubeInput])

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && onFileUpload) {
      onFileUpload(e.target.files)
      setIsOpen(false)
    }
  }

  const handleYouTubeClick = () => {
    setShowYouTubeInput(true)
  }

  const handleMultiFileClick = () => {
    setShowMultiFileModal(true)
    setIsOpen(false)
  }

  const handleMultiFileUploadComplete = (results: BatchUploadResponse) => {
    onMultiFileUpload?.(results)
    setShowMultiFileModal(false)
  }

  const handleYouTubeSubmit = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && youtubeUrl.trim()) {
      onYouTubeUrl?.(youtubeUrl.trim())
      setYoutubeUrl('')
      setShowYouTubeInput(false)
      setIsOpen(false)
    }
  }

  const handleYouTubeChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setYoutubeUrl(e.target.value)
  }

  return (
    <div className="relative" ref={dropdownRef}>
      {/* Hidden file input */}
      <input
        type="file"
        id="file-upload-hidden"
        className="hidden"
        multiple
        accept=".txt,.pdf,.docx,.md"
        onChange={handleFileUpload}
        disabled={disabled}
      />

      {/* Plus button */}
      <Button
        variant="outline"
        size="icon"
        className="shrink-0"
        onClick={() => setIsOpen(!isOpen)}
        disabled={disabled}
        title="Add attachment"
      >
        <Plus className="h-4 w-4" />
      </Button>

      {/* Dropdown menu */}
      {isOpen && (
        <div className="absolute bottom-full left-0 mb-2 w-64 bg-popover border rounded-md shadow-lg z-50">
          <div className="p-1">
            {/* Upload Single Document option */}
            <button
              className="flex items-center w-full px-3 py-2 text-sm text-left hover:bg-accent hover:text-accent-foreground rounded-sm"
              onClick={() => document.getElementById('file-upload-hidden')?.click()}
              disabled={disabled}
            >
              <Paperclip className="h-4 w-4 mr-3" />
              Upload a file
            </button>

            {/* Upload Multiple Documents option */}
            <button
              className="flex items-center w-full px-3 py-2 text-sm text-left hover:bg-accent hover:text-accent-foreground rounded-sm"
              onClick={handleMultiFileClick}
              disabled={disabled}
              title="Upload multiple files at once"
            >
              <Upload className="h-4 w-4 mr-3" />
              Upload multiple files
            </button>

            {/* YouTube Video option */}
            <div className="relative">
              <button
                className="flex items-center w-full px-3 py-2 text-sm text-left hover:bg-accent hover:text-accent-foreground rounded-sm"
                onClick={handleYouTubeClick}
                disabled={disabled}
              >
                <Youtube className="h-4 w-4 mr-3" />
                YouTube Video
              </button>

              {/* Inline YouTube URL input */}
              {showYouTubeInput && (
                <div className="px-3 pb-2">
                  <Input
                    ref={inputRef}
                    value={youtubeUrl}
                    onChange={handleYouTubeChange}
                    onKeyPress={handleYouTubeSubmit}
                    placeholder="Paste URL here"
                    className="mt-2 text-sm"
                    disabled={disabled}
                  />
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Multi-File Upload Modal */}
      <MultiFileUploadModal
        isOpen={showMultiFileModal}
        onClose={() => setShowMultiFileModal(false)}
        sessionId={sessionId}
        onUploadComplete={handleMultiFileUploadComplete}
        onSessionCreated={onSessionCreated}
      />
    </div>
  )
}
