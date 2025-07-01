import React, { useState, KeyboardEvent, useRef, useEffect } from 'react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Textarea } from '@/components/ui/textarea'
import { Send, Paperclip } from 'lucide-react'
import { cn } from '@/lib/utils'
import { AttachmentDropdown } from './AttachmentDropdown'

interface ChatInputProps {
  onSendMessage: (message: string) => void
  onFileUpload?: (files: FileList) => void
  onYouTubeUrl?: (url: string) => void
  disabled?: boolean
  placeholder?: string
  standalone?: boolean // New prop for centered layout
}

export const ChatInput: React.FC<ChatInputProps> = ({
  onSendMessage,
  onFileUpload,
  onYouTubeUrl,
  disabled = false,
  placeholder = "Ask Warren to create compliant content...",
  standalone = false
}) => {
  const [message, setMessage] = useState('')
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  // Auto-resize textarea as content changes
  const adjustTextareaHeight = () => {
    const textarea = textareaRef.current
    if (textarea) {
      textarea.style.height = 'auto'
      const scrollHeight = textarea.scrollHeight
      // Limit max height to about 6 lines (120px)
      const maxHeight = standalone ? 120 : 100
      const minHeight = standalone ? 48 : 40
      textarea.style.height = Math.max(minHeight, Math.min(scrollHeight, maxHeight)) + 'px'
    }
  }

  useEffect(() => {
    adjustTextareaHeight()
  }, [message])

  const handleSend = () => {
    if (message.trim() && !disabled) {
      onSendMessage(message.trim())
      setMessage('')
    }
  }

  const handleKeyPress = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  const handleChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setMessage(e.target.value)
  }

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && onFileUpload) {
      onFileUpload(e.target.files)
    }
  }

  return (
    <div className={cn(
      "bg-background p-4",
      !standalone && "border-t"
    )}>
      <div className="max-w-full space-y-3">
        {/* Message input - Full width at top */}
        <div className="w-full">
          <Textarea
            ref={textareaRef}
            value={message}
            onChange={handleChange}
            onKeyPress={handleKeyPress}
            placeholder={placeholder}
            disabled={disabled}
            className={cn(
              "resize-none overflow-hidden w-full",
              standalone ? "min-h-[48px] text-base border-input" : "min-h-[40px]",
              "leading-relaxed"
            )}
            rows={1}
          />
        </div>

        {/* Button row - File upload left, Send button right */}
        <div className="flex items-center justify-between">
          {/* Attachment dropdown - Bottom left */}
          <AttachmentDropdown
            onFileUpload={onFileUpload}
            onYouTubeUrl={onYouTubeUrl}
            disabled={disabled}
          />

          {/* Send button - Bottom right */}
          <Button
            onClick={handleSend}
            disabled={disabled || !message.trim()}
            size="icon"
            className="shrink-0"
          >
            <Send className="h-4 w-4" />
          </Button>
        </div>
      </div>
    </div>
  )
}
