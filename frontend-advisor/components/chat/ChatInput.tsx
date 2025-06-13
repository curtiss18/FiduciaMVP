import React, { useState, KeyboardEvent } from 'react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Send, Paperclip } from 'lucide-react'
import { cn } from '@/lib/utils'

interface ChatInputProps {
  onSendMessage: (message: string) => void
  onFileUpload?: (files: FileList) => void
  disabled?: boolean
  placeholder?: string
}

export const ChatInput: React.FC<ChatInputProps> = ({
  onSendMessage,
  onFileUpload,
  disabled = false,
  placeholder = "Ask Warren to create compliant content..."
}) => {
  const [message, setMessage] = useState('')

  const handleSend = () => {
    if (message.trim() && !disabled) {
      onSendMessage(message.trim())
      setMessage('')
    }
  }

  const handleKeyPress = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && onFileUpload) {
      onFileUpload(e.target.files)
    }
  }

  return (
    <div className="border-t bg-background p-3">
      <div className="flex items-end gap-2 max-w-full">
        {/* File upload button */}
        <div className="relative">
          <input
            type="file"
            id="file-upload"
            className="hidden"
            multiple
            accept=".txt,.pdf,.docx,.md"
            onChange={handleFileUpload}
            disabled={disabled}
          />
          <Button
            variant="outline"
            size="icon"
            className="shrink-0"
            onClick={() => document.getElementById('file-upload')?.click()}
            disabled={disabled}
            title="Upload documents for context"
          >
            <Paperclip className="h-4 w-4" />
          </Button>
        </div>

        {/* Message input */}
        <div className="flex-1 relative">
          <Input
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder={placeholder}
            disabled={disabled}
            className="pr-12 min-h-[40px] resize-none"
          />
        </div>

        {/* Send button */}
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
  )
}
