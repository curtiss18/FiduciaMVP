'use client'

import React, { useState, useCallback, useEffect } from 'react'
import { Message, Conversation, GeneratedContent, WarrenResponse, ExtractedContent } from '@/lib/types'
import { warrenChatApi } from '@/lib/api'
import { ChatHeader } from './ChatHeader'
import { MessageHistory } from './MessageHistory'
import { ChatInput } from './ChatInput'
import { Button } from '@/components/ui/button'
import { Copy, Save, Send } from 'lucide-react'
import { cn } from '@/lib/utils'

export const ChatInterface: React.FC = () => {
  const [conversation, setConversation] = useState<Conversation>({
    id: `conv_${Date.now()}`,
    messages: [],
    status: 'active'
  })
  
  const [isLoading, setIsLoading] = useState(false)
  const [generatedContent, setGeneratedContent] = useState<GeneratedContent | null>(null)
  
  // Resize state for dynamic panel widths
  const [chatWidth, setChatWidth] = useState(30) // Default: 30% chat, 70% content
  const [isResizing, setIsResizing] = useState(false)

  // Generate unique message ID
  const generateMessageId = () => `msg_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`

  // Parse Warren's response for delimited content
  const parseWarrenResponse = (response: string): ExtractedContent => {
    const delimiter = '##MARKETINGCONTENT##';
    const startIndex = response.indexOf(delimiter);
    const endIndex = response.lastIndexOf(delimiter);
    
    if (startIndex !== -1 && endIndex !== -1 && startIndex !== endIndex) {
      // Extract the marketing content between delimiters
      const marketingContent = response.substring(
        startIndex + delimiter.length, 
        endIndex
      ).trim();
      
      // Remove the delimited section from the conversational response
      const beforeDelimiter = response.substring(0, startIndex).trim();
      const afterDelimiter = response.substring(endIndex + delimiter.length).trim();
      
      // Combine the non-marketing parts for chat display
      const conversationalParts = [beforeDelimiter, afterDelimiter]
        .filter(part => part.length > 0);
      const conversationalResponse = conversationalParts.join('\n\n').trim();
      
      // Extract title (first line of marketing content)
      const lines = marketingContent.split('\n').filter(line => line.trim());
      const title = lines[0]?.trim() || 'Generated Content';
      
      return {
        marketingContent,
        conversationalResponse: conversationalResponse || 'Content generated successfully!',
        hasMarketingContent: true,
        title
      };
    }
    
    // No delimited content found - return original response
    return {
      marketingContent: null,
      conversationalResponse: response,
      hasMarketingContent: false
    };
  }

  // Add message to conversation
  const addMessage = useCallback((message: Omit<Message, 'id' | 'timestamp'>) => {
    const newMessage: Message = {
      ...message,
      id: generateMessageId(),
      timestamp: new Date()
    }

    setConversation(prev => ({
      ...prev,
      messages: [...prev.messages, newMessage]
    }))

    return newMessage
  }, [])

  // Send message to Warren
  const sendMessageToWarren = useCallback(async (userMessage: string) => {
    // Add user message
    addMessage({
      role: 'advisor',
      content: userMessage,
      type: 'text'
    })

    setIsLoading(true)

    try {
      // Determine if this is a refinement request
      const isRefinement = generatedContent !== null;
      const currentContent = generatedContent?.content;
      
      // Log refinement detection for debugging
      console.log('Refinement Detection:', {
        isRefinement,
        hasGeneratedContent: !!generatedContent,
        currentContentLength: currentContent?.length || 0,
        userMessage: userMessage.substring(0, 50) + (userMessage.length > 50 ? '...' : '')
      });
      
      // Prepare context for Warren (backend will use its own prompts)
      const context = {
        conversation_history: conversation.messages,
        contentType: conversation.context?.contentType || generatedContent?.contentType,
        audience: conversation.context?.audience || generatedContent?.audience,
        platform: conversation.context?.platform || generatedContent?.platform,
        current_content: currentContent,
        is_refinement: isRefinement
      }

      // Call Warren API
      const response: WarrenResponse = await warrenChatApi.sendMessage(
        userMessage,
        conversation.id,
        context
      )

      if (response.status === 'success' && response.content) {
        // Parse Warren's response for delimited content
        const extractedContent = parseWarrenResponse(response.content);
        
        // Add Warren's conversational response to chat (without marketing content)
        addMessage({
          role: 'warren',
          content: extractedContent.conversationalResponse,
          type: 'text',
          metadata: {
            contentType: response.metadata?.contentType,
            audience: response.metadata?.audience,
            platform: response.metadata?.platform
          }
        })

        // If marketing content was found, set it for preview
        if (extractedContent.hasMarketingContent && extractedContent.marketingContent) {
          const content: GeneratedContent = {
            title: extractedContent.title || 'Generated Content',
            content: extractedContent.marketingContent,
            contentType: response.metadata?.contentType || 'general',
            audience: response.metadata?.audience || 'general_education',
            platform: response.metadata?.platform || 'general',
            complianceScore: response.context_quality_score
          }
          
          setGeneratedContent(content)
          setConversation(prev => ({
            ...prev,
            status: 'content_ready',
            generatedContent: content
          }))
        }
      } else {
        // Add error message
        addMessage({
          role: 'warren',
          content: response.error || 'Sorry, I encountered an error. Please try again.',
          type: 'error'
        })
      }
    } catch (error) {
      console.error('Error sending message to Warren:', error)
      addMessage({
        role: 'warren',
        content: 'I apologize, but I\'m having trouble connecting right now. Please check that the backend is running and try again.',
        type: 'error'
      })
    } finally {
      setIsLoading(false)
    }
  }, [conversation, addMessage, generatedContent])

  // Helper functions for content preview
  const getPlatformIcon = (platform: string) => {
    switch (platform.toLowerCase()) {
      case 'linkedin': return '💼'
      case 'twitter': case 'x': return '🐦'
      case 'email': return '📧'
      case 'website': return '🌐'
      case 'newsletter': return '📰'
      default: return '📄'
    }
  }

  const getAudienceLabel = (audience: string) => {
    return audience.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())
  }

  // Event handlers
  const handleRefresh = () => {
    setConversation({
      id: `conv_${Date.now()}`,
      messages: [],
      status: 'active'
    })
    setGeneratedContent(null)
  }

  const handleFileUpload = (files: FileList) => {
    // TODO: Implement file upload in Phase 2
    console.log('Files uploaded:', files)
    addMessage({
      role: 'warren',
      content: 'File upload feature will be available in the next update! For now, you can describe your content needs and I\'ll help you create compliant content.',
      type: 'text'
    })
  }

  const handleCopyContent = () => {
    if (generatedContent?.content) {
      navigator.clipboard.writeText(generatedContent.content).then(() => {
        addMessage({
          role: 'warren',
          content: '✅ Content copied to clipboard! You can now paste it into your preferred platform.',
          type: 'text'
        })
      }).catch(() => {
        addMessage({
          role: 'warren',
          content: '❌ Failed to copy content. Please try selecting and copying manually.',
          type: 'text'
        })
      })
    }
  }

  const handleSaveContent = () => {
    if (generatedContent) {
      // Save to localStorage for now (Phase 3 will add database persistence)
      const savedContent = JSON.parse(localStorage.getItem('warrenSavedContent') || '[]')
      savedContent.push({
        ...generatedContent,
        savedAt: new Date().toISOString(),
        conversationId: conversation.id
      })
      localStorage.setItem('warrenSavedContent', JSON.stringify(savedContent))
      
      addMessage({
        role: 'warren',
        content: '✅ Content saved! You can access your saved content from the library.',
        type: 'text'
      })
    }
  }

  const handleSubmitForReview = () => {
    addMessage({
      role: 'warren',
      content: '📋 Content submitted for compliance review! Your compliance officer will be notified. (Full review workflow coming in next update)',
      type: 'text'
    })
    
    setConversation(prev => ({
      ...prev,
      status: 'submitted'
    }))
  }

  const handleRegenerate = () => {
    if (generatedContent) {
      sendMessageToWarren(`Please regenerate this ${generatedContent.contentType} with any improvements you can suggest.`)
      setGeneratedContent(null)
    } else {
      sendMessageToWarren('Please regenerate the content with any improvements you can suggest.')
    }
  }

  // Resize handlers for dynamic panel widths
  const handleMouseDown = useCallback((e: React.MouseEvent) => {
    e.preventDefault()
    setIsResizing(true)
    document.body.style.cursor = 'col-resize'
    document.body.style.userSelect = 'none'
  }, [])

  const handleMouseMove = useCallback((e: MouseEvent) => {
    if (!isResizing) return
    
    const containerRect = document.querySelector('.resize-container')?.getBoundingClientRect()
    if (!containerRect) return
    
    const mouseX = e.clientX - containerRect.left
    const newChatWidth = (mouseX / containerRect.width) * 100
    
    // Constrain between 20% and 80%
    const constrainedWidth = Math.max(20, Math.min(80, newChatWidth))
    setChatWidth(constrainedWidth)
  }, [isResizing])

  const handleMouseUp = useCallback(() => {
    if (isResizing) {
      setIsResizing(false)
      document.body.style.cursor = ''
      document.body.style.userSelect = ''
      
      // Save to localStorage for persistence
      localStorage.setItem('warrenChatWidth', chatWidth.toString())
    }
  }, [isResizing, chatWidth])

  // Load saved chat width on mount
  React.useEffect(() => {
    const savedWidth = localStorage.getItem('warrenChatWidth')
    if (savedWidth) {
      setChatWidth(Number(savedWidth))
    }
  }, [])

  // Scroll to bottom when content preview opens
  React.useEffect(() => {
    if (generatedContent) {
      // Small delay to allow layout to settle before scrolling
      setTimeout(() => {
        const messagesContainer = document.querySelector('.messages-container')
        if (messagesContainer) {
          messagesContainer.scrollTop = messagesContainer.scrollHeight
        }
      }, 100)
    }
  }, [generatedContent])

  // Add/remove mouse event listeners
  React.useEffect(() => {
    if (isResizing) {
      document.addEventListener('mousemove', handleMouseMove)
      document.addEventListener('mouseup', handleMouseUp)
      
      return () => {
        document.removeEventListener('mousemove', handleMouseMove)
        document.removeEventListener('mouseup', handleMouseUp)
      }
    }
  }, [isResizing, handleMouseMove, handleMouseUp])

  return (
    <div className="h-screen flex flex-col">
      <ChatHeader 
        onRefresh={handleRefresh}
        advisorName="Demo Advisor"
      />
      
      {/* Main Content Area - Dynamic Layout with Resizer */}
      <div className="flex-1 flex flex-col lg:flex-row overflow-hidden resize-container">
        {/* Chat Panel - Mobile Bottom, Desktop Left */}
        <div 
          className="order-2 lg:order-1 flex flex-col transition-all duration-300 ease-in-out w-full"
          style={{
            width: generatedContent ? `${chatWidth}%` : '100%'
          }}
        >
          {/* Show welcome only if no messages AND no content */}
          {conversation.messages.length === 0 && !generatedContent ? (
            /* Centered welcome layout for first-time users */
            <div className="flex flex-col h-full max-w-4xl w-full mx-auto px-6">
              <div className="flex-1 flex items-center justify-center">
                <div className="text-center max-w-2xl w-full">
                  <div className="w-16 h-16 bg-primary/10 rounded-full flex items-center justify-center mx-auto mb-6">
                    <span className="text-3xl">🛡️</span>
                  </div>
                  <h2 className="text-2xl font-semibold mb-3">
                    Hi! I'm Warren
                  </h2>
                  <p className="text-muted-foreground text-base leading-relaxed mb-8">
                    I help financial advisors create SEC/FINRA compliant marketing content. 
                    Tell me what you'd like to create!
                  </p>
                  <div className="text-sm text-muted-foreground mb-8">
                    <p>💡 Try: "Create a LinkedIn post about retirement planning"</p>
                  </div>
                  
                  {/* Input Section - Right after welcome text */}
                  <div className="w-full">
                    <div className="border border-border rounded-lg bg-background shadow-sm">
                      <ChatInput
                        onSendMessage={sendMessageToWarren}
                        onFileUpload={handleFileUpload}
                        disabled={isLoading}
                        placeholder="Tell Warren what content you'd like to create..."
                        standalone={true}
                      />
                    </div>
                  </div>
                </div>
              </div>
            </div>
          ) : (
            /* Normal chat layout for active conversations - maintain centered width when no content */
            <div className={cn(
              "flex flex-col h-full",
              !generatedContent && "max-w-4xl w-full mx-auto px-6"
            )}>
              <MessageHistory 
                messages={conversation.messages}
                isLoading={isLoading}
              />
              
              <div className={cn(
                !generatedContent && "border border-border rounded-lg bg-background shadow-sm"
              )}>
                <ChatInput
                  onSendMessage={sendMessageToWarren}
                  onFileUpload={handleFileUpload}
                  disabled={isLoading}
                  placeholder="Continue your conversation with Warren..."
                  standalone={!generatedContent}
                />
              </div>
            </div>
          )}
        </div>

        {/* Resize Divider - Only show on desktop when content exists */}
        {generatedContent && (
          <div 
            className="
              hidden lg:block
              w-1 bg-border hover:bg-primary/20 
              cursor-col-resize 
              transition-colors duration-200
              relative group
              order-2 lg:order-2
            "
            onMouseDown={handleMouseDown}
          >
            {/* Visual indicator */}
            <div className="
              absolute inset-y-0 left-1/2 transform -translate-x-1/2
              w-0.5 bg-border group-hover:bg-primary/40
              transition-colors duration-200
            " />
            {/* Invisible wider hover area for easier interaction */}
            <div className="absolute inset-y-0 -left-1 -right-1" />
          </div>
        )}

        {/* Content Preview Panel - Mobile Top, Desktop Right */}
        {generatedContent && (
          <div 
            className="
              order-1 lg:order-3
              flex flex-col 
              bg-muted/20 
              border-b lg:border-b-0 lg:border-l-0 border-border
              animate-in slide-in-from-right-full lg:slide-in-from-right-full
              duration-300 ease-in-out
              max-h-[40vh] lg:max-h-none
              w-full
            "
            style={{
              width: `${100 - chatWidth}%`
            }}
          >
            <div className="flex-1 flex flex-col">
              {/* Content Preview Header */}
              <div className="border-b border-border p-4 bg-background">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="text-2xl">{getPlatformIcon(generatedContent.platform)}</span>
                    <div>
                      <h3 className="font-semibold">
                        {generatedContent.title || 'Generated Content'}
                      </h3>
                      <p className="text-sm text-muted-foreground">
                        {generatedContent.contentType} • {getAudienceLabel(generatedContent.audience)}
                        {generatedContent.complianceScore && (
                          <span className="ml-2 text-green-600 dark:text-green-400">
                            • Compliance Score: {Math.round(generatedContent.complianceScore * 100)}%
                          </span>
                        )}
                      </p>
                    </div>
                  </div>
                  
                  {/* Action Buttons */}
                  <div className="flex gap-2">
                    <Button variant="outline" size="sm" onClick={handleCopyContent}>
                      <Copy className="h-4 w-4 mr-1" />
                      Copy
                    </Button>
                    <Button variant="outline" size="sm" onClick={handleSaveContent}>
                      <Save className="h-4 w-4 mr-1" />
                      Save
                    </Button>
                    <Button variant="default" size="sm" onClick={handleSubmitForReview}>
                      <Send className="h-4 w-4 mr-1" />
                      Submit for Review
                    </Button>
                  </div>
                </div>
              </div>
              
              {/* Content Display Area */}
              <div className="flex-1 p-4 lg:p-6 overflow-y-auto">
                <div className="bg-background rounded-lg border p-4 lg:p-6 shadow-sm">
                  <pre className="whitespace-pre-wrap font-sans text-sm leading-relaxed">
                    {generatedContent.content}
                  </pre>
                </div>
                
                {/* Disclaimers if present */}
                {generatedContent.disclaimers && generatedContent.disclaimers.length > 0 && (
                  <div className="mt-4 lg:mt-6 text-xs text-muted-foreground space-y-1">
                    <p className="font-medium">Required Disclaimers:</p>
                    {generatedContent.disclaimers.map((disclaimer, index) => (
                      <p key={index} className="pl-2 border-l-2 border-muted">
                        {disclaimer}
                      </p>
                    ))}
                  </div>
                )}
              </div>
              
              {/* Bottom Actions */}
              <div className="border-t border-border p-3 lg:p-4 bg-background">
                <div className="flex justify-between items-center">
                  <Button variant="ghost" size="sm" onClick={handleRegenerate}>
                    🔄 Regenerate
                  </Button>
                  <div className="text-xs text-muted-foreground">
                    Ready for compliance review
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
