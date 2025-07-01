import React, { useRef, useEffect, useState } from 'react'
import { Message } from '@/lib/types'
import { MessageBubble } from './MessageBubble'
import { Button } from '@/components/ui/button'
import { ChevronDown } from 'lucide-react'
import { cn } from '@/lib/utils'

interface MessageHistoryProps {
  messages: Message[]
  isLoading?: boolean
}

export const MessageHistory: React.FC<MessageHistoryProps> = ({ 
  messages, 
  isLoading = false 
}) => {
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const containerRef = useRef<HTMLDivElement>(null)
  const [showScrollButton, setShowScrollButton] = useState(false)

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  // Enhanced scroll to bottom function for external use
  useEffect(() => {
    if (containerRef.current) {
      containerRef.current.scrollTop = containerRef.current.scrollHeight
    }
  }, [messages.length, isLoading])

  // Handle scroll to detect if user scrolled up
  const handleScroll = () => {
    if (containerRef.current) {
      const { scrollTop, scrollHeight, clientHeight } = containerRef.current
      const isNearBottom = scrollHeight - scrollTop - clientHeight < 100
      setShowScrollButton(!isNearBottom && messages.length > 3)
    }
  }

  // Scroll to bottom function
  const scrollToBottom = () => {
    if (containerRef.current) {
      containerRef.current.scrollTo({
        top: containerRef.current.scrollHeight,
        behavior: 'smooth'
      })
    }
  }

  return (
    <div className="relative flex-1">
      <div 
        ref={containerRef}
        className="messages-container flex-1 p-4 overflow-y-auto scroll-smooth"
        onScroll={handleScroll}
        style={{ 
          maxHeight: 'calc(100vh - 200px)', // Ensure scrollable area
          minHeight: '300px' // Minimum height for better UX
        }}
      >
        <div className="max-w-full mx-auto"> {/* Removed max-w-4xl for split layout */}
          {/* Welcome message when no messages */}
          {messages.length === 0 && (
            <div className="flex flex-col items-center justify-center h-full text-center py-8"> {/* Reduced padding */}
              <div className="w-12 h-12 bg-primary/10 rounded-full flex items-center justify-center mb-3"> {/* Smaller icon */}
                <span className="text-xl">🛡️</span>
              </div>
              <h2 className="text-lg font-semibold mb-2"> {/* Smaller heading */}
                Hi! I'm Warren
              </h2>
              <p className="text-muted-foreground text-sm max-w-xs"> {/* Smaller text and width */}
                I help financial advisors create SEC/FINRA compliant marketing content. 
                Tell me what you'd like to create!
              </p>
              <div className="mt-4 text-xs text-muted-foreground">
                <p>💡 Try: "Create a LinkedIn post about retirement planning"</p>
              </div>
            </div>
          )}

          {/* Message list */}
          {messages.map((message) => (
            <MessageBubble key={message.id} message={message} />
          ))}

          {/* Loading indicator */}
          {isLoading && (
            <div className="flex justify-start mb-4">
              <div className="warren-message bg-card border rounded-lg px-4 py-3 shadow-sm max-w-xs">
                <div className="flex items-center gap-2 mb-1">
                  <div className="w-2 h-2 rounded-full bg-primary" />
                  <span className="text-xs font-medium opacity-70">Warren</span>
                </div>
                <div className="typing-indicator">
                  <span className="mr-2 text-sm">Thinking...</span>
                  <div className="inline-flex gap-1">
                    <div className="typing-dot" />
                    <div className="typing-dot" />
                    <div className="typing-dot" />
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Scroll anchor with padding to ensure full scroll */}
          <div ref={messagesEndRef} className="h-4" />
        </div>
      </div>

      {/* Scroll to bottom button */}
      {showScrollButton && (
        <div className="absolute bottom-4 right-4">
          <Button
            variant="outline"
            size="sm"
            className="rounded-full shadow-lg"
            onClick={scrollToBottom}
          >
            <ChevronDown className="h-4 w-4" />
          </Button>
        </div>
      )}
    </div>
  )
}
