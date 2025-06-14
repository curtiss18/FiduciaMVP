'use client'

import React, { useState, useCallback } from 'react'
import { Message, Conversation, GeneratedContent, WarrenResponse, ExtractedContent } from '@/lib/types'
import { warrenChatApi } from '@/lib/api'
import { getWarrenPrompt } from '@/lib/prompts/warren-prompts'
import { ChatHeader } from './ChatHeader'
import { MessageHistory } from './MessageHistory'
import { ChatInput } from './ChatInput'
import { Button } from '@/components/ui/button'
import { Copy, Save, Send } from 'lucide-react'

export const ChatInterface: React.FC = () => {
  const [conversation, setConversation] = useState<Conversation>({
    id: `conv_${Date.now()}`,
    messages: [],
    status: 'active'
  })
  
  const [isLoading, setIsLoading] = useState(false)
  const [generatedContent, setGeneratedContent] = useState<GeneratedContent | null>(null)

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
      // Get the appropriate system prompt
      const systemPrompt = getWarrenPrompt('main', conversation.context?.platform);
      
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
      
      // Prepare context for Warren
      const context = {
        system_prompt: systemPrompt,
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
  }, [conversation, addMessage])

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

  return (
    <div className="h-screen flex flex-col">
      <ChatHeader 
        onRefresh={handleRefresh}
        advisorName="Demo Advisor"
      />
      
      {/* Main Content Area - Split Layout */}
      <div className="flex-1 flex overflow-hidden">
        {/* Left Panel - Chat */}
        <div className="w-1/2 flex flex-col border-r border-border">
          <MessageHistory 
            messages={conversation.messages}
            isLoading={isLoading}
          />
          
          <ChatInput
            onSendMessage={sendMessageToWarren}
            onFileUpload={handleFileUpload}
            disabled={isLoading}
            placeholder={
              conversation.messages.length === 0 
                ? "Tell Warren what content you'd like to create..."
                : "Continue your conversation with Warren..."
            }
          />
        </div>
        
        {/* Right Panel - Content Preview */}
        <div className="w-1/2 flex flex-col bg-muted/20">
          {generatedContent ? (
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
              <div className="flex-1 p-6 overflow-y-auto">
                <div className="bg-background rounded-lg border p-6 shadow-sm">
                  <pre className="whitespace-pre-wrap font-sans text-sm leading-relaxed">
                    {generatedContent.content}
                  </pre>
                </div>
                
                {/* Disclaimers if present */}
                {generatedContent.disclaimers && generatedContent.disclaimers.length > 0 && (
                  <div className="mt-6 text-xs text-muted-foreground space-y-1">
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
              <div className="border-t border-border p-4 bg-background">
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
          ) : (
            /* Empty State - No Content Generated Yet */
            <div className="flex-1 flex items-center justify-center p-8">
              <div className="text-center max-w-md">
                <div className="w-16 h-16 bg-muted rounded-full flex items-center justify-center mx-auto mb-4">
                  <span className="text-2xl">📄</span>
                </div>
                <h3 className="text-lg font-semibold mb-2">Content Preview</h3>
                <p className="text-muted-foreground text-sm leading-relaxed">
                  Start a conversation with Warren to generate compliant content. 
                  Your generated content will appear here for review and editing.
                </p>
                <div className="mt-4 text-xs text-muted-foreground">
                  💡 Try: "Create a LinkedIn post about retirement planning"
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
