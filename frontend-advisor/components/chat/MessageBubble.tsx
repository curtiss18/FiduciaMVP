import React from 'react'
import { Message } from '@/lib/types'
import { cn } from '@/lib/utils'
import { Card } from '@/components/ui/card'

interface MessageBubbleProps {
  message: Message
}

export const MessageBubble: React.FC<MessageBubbleProps> = ({ message }) => {
  const isAdvisor = message.role === 'advisor'
  const isWarren = message.role === 'warren'
  
  if (message.type === 'error') {
    return (
      <div className="flex justify-center mb-4">
        <Card className="bg-destructive/10 border-destructive/20 px-4 py-2">
          <p className="text-destructive text-sm">
            ⚠️ {message.content}
          </p>
        </Card>
      </div>
    )
  }

  return (
    <div className={cn(
      "flex mb-4",
      isAdvisor ? "justify-end" : "justify-start"
    )}>
      <div className={cn(
        "message-bubble rounded-lg px-4 py-3 shadow-sm",
        isAdvisor && "advisor-message",
        isWarren && "warren-message bg-card border"
      )}>
        {/* Role indicator */}
        <div className="flex items-center gap-2 mb-1">
          <div className={cn(
            "w-2 h-2 rounded-full",
            isAdvisor ? "bg-primary-foreground" : "bg-primary"
          )} />
          <span className="text-xs font-medium opacity-70">
            {isAdvisor ? "You" : "Warren"}
          </span>
          <span className="text-xs opacity-50">
            {message.timestamp.toLocaleTimeString([], { 
              hour: '2-digit', 
              minute: '2-digit' 
            })}
          </span>
        </div>
        
        {/* Message content */}
        <div className="whitespace-pre-wrap leading-relaxed">
          {message.content}
        </div>
        
        {/* Loading indicator for Warren's thinking */}
        {message.metadata?.isGenerating && (
          <div className="typing-indicator mt-2 text-sm opacity-70">
            <span className="mr-2">Warren is thinking</span>
            <div className="inline-flex gap-1">
              <div className="typing-dot" />
              <div className="typing-dot" />
              <div className="typing-dot" />
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
