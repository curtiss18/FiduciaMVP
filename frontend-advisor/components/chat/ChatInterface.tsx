'use client'

import React, { useState, useCallback, useEffect } from 'react'
import { Message, Conversation, GeneratedContent, WarrenResponse, ExtractedContent, SourceInformation } from '@/lib/types'
import { warrenChatApi, advisorApi } from '@/lib/api'
import { PageHeader } from '@/components/layout'
import { MessageHistory } from './MessageHistory'
import { ChatInput } from './ChatInput'
import { SourceInfoBadges } from '@/components/content'
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
  
  // Enhanced session management for API integration
  const [advisorSession, setAdvisorSession] = useState<string | null>(null)
  const [sessionContentId, setSessionContentId] = useState<string | null>(null) // Content ID for session in library
  const [sessionTitle, setSessionTitle] = useState<string>('') // Smart title for session
  const [isSessionSaved, setIsSessionSaved] = useState(false) // Track if session is persisted
  const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false) // Track unsaved content
  const advisorId = 'demo_advisor_001'
  
  // Edit context for loading existing content
  const [editContext, setEditContext] = useState<any>(null)
  const [isLoadingHistory, setIsLoadingHistory] = useState(false)
  
  // Resize state for dynamic panel widths
  const [chatWidth, setChatWidth] = useState(30) // Default: 30% chat, 70% content
  const [isResizing, setIsResizing] = useState(false)

  // Generate unique message ID
  const generateMessageId = () => `msg_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`

  // Session management functions
  const ensureSession = async (): Promise<string> => {
    if (advisorSession) return advisorSession

    try {
      // Create new session
      const sessionResponse = await advisorApi.createSession(
        advisorId, 
        sessionTitle || `Warren Chat - ${new Date().toLocaleDateString()}`
      )
      const newSessionId = sessionResponse.session.session_id
      setAdvisorSession(newSessionId)
      setHasUnsavedChanges(true) // Mark as having unsaved changes
      console.log('Created new session:', newSessionId)
      return newSessionId
    } catch (error) {
      console.error('Failed to create session:', error)
      // Graceful degradation - continue with local session
      const localSessionId = `local_${Date.now()}`
      setAdvisorSession(localSessionId)
      return localSessionId
    }
  }

  // Persist message to database
  const persistMessage = async (
    sessionId: string,
    messageType: 'user' | 'warren',
    content: string,
    metadata?: any
  ) => {
    try {
      await advisorApi.saveMessage(sessionId, messageType, content, metadata)
      console.log(`Persisted ${messageType} message to session ${sessionId}`)
    } catch (error) {
      console.warn('Message persistence failed (graceful degradation):', error)
      // Continue without breaking chat experience
      setHasUnsavedChanges(true) // Mark as having unsaved changes
    }
  }

  // Generate smart session title from Warren's first response
  const generateSessionTitle = (warrenResponse: string, userMessage: string): string => {
    // Try to extract meaningful title from Warren's response or user message
    const responseLines = warrenResponse.split('\n').filter(line => line.trim())
    const userWords = userMessage.toLowerCase()
    
    // Look for content type keywords
    if (userWords.includes('linkedin')) return 'LinkedIn Content Session'
    if (userWords.includes('email')) return 'Email Content Session'
    if (userWords.includes('website')) return 'Website Content Session'
    if (userWords.includes('retirement')) return 'Retirement Planning Content'
    if (userWords.includes('investment')) return 'Investment Content Session'
    if (userWords.includes('financial planning')) return 'Financial Planning Content'
    
    // Extract first meaningful line from Warren's response
    const meaningfulLine = responseLines.find(line => 
      line.length > 10 && 
      !line.startsWith('I') && 
      !line.includes('Warren') &&
      !line.includes('compliance')
    )
    
    if (meaningfulLine && meaningfulLine.length < 50) {
      return meaningfulLine.trim()
    }
    
    // Fallback to date-based title
    return `Warren Chat - ${new Date().toLocaleDateString()}`
  }

  // Save session as content in library
  const saveSessionToLibrary = async () => {
    if (!advisorSession) return

    try {
      // Clean up messages before saving - remove delimited content from Warren messages
      const cleanMessages = conversation.messages.map(msg => {
        if (msg.role === 'warren' && msg.content.includes('##MARKETINGCONTENT##')) {
          // Extract only the conversational part for storage
          const extractedContent = parseWarrenResponse(msg.content)
          return {
            ...msg,
            content: extractedContent.conversationalResponse
          }
        }
        return msg
      })

      const sessionData = {
        title: sessionTitle,
        messages: cleanMessages, // Use cleaned messages
        generatedContent,
        createdAt: new Date().toISOString()
      }

      const contentData = {
        advisorId,
        title: sessionTitle,
        contentText: JSON.stringify(sessionData), // Store session data as JSON
        contentType: 'website_blog', // Use valid backend value - lowercase for advisor_content table
        audienceType: 'general_education', // Use valid backend value - lowercase
        sourceSessionId: advisorSession,
        advisorNotes: `Warren chat session with ${conversation.messages.length} messages - Session Data`,
        intendedChannels: ['warren_chat'],
        sourceMetadata: {
          sessionId: advisorSession,
          messageCount: conversation.messages.length,
          hasGeneratedContent: !!generatedContent,
          lastActivity: new Date().toISOString(),
          isWarrenSession: true // Flag to identify this as a session
        }
      }

      let saveResponse

      if (sessionContentId) {
        // Update existing session using the proper update endpoint
        console.log('Updating existing session:', sessionContentId)
        
        const updateData = {
          title: sessionTitle,
          contentText: JSON.stringify(sessionData),
          advisorNotes: `Warren chat session with ${conversation.messages.length} messages - Updated: ${new Date().toLocaleString()}`
          // Note: sourceMetadata not included as advisor_content table doesn't have this column
        }
        
        saveResponse = await advisorApi.updateContent(sessionContentId, advisorId, updateData)
        setIsSessionSaved(true)
        setHasUnsavedChanges(false)
        
        console.log('Session updated successfully:', sessionContentId)
        return sessionContentId
      } else {
        // Create new session
        console.log('Creating new session')
        saveResponse = await advisorApi.saveContent(contentData)
        setSessionContentId(saveResponse.content.id)
        setIsSessionSaved(true)
        setHasUnsavedChanges(false)
        
        console.log('Session saved to library:', saveResponse.content.id)
        return saveResponse.content.id
      }
    } catch (error) {
      console.error('Failed to save session to library:', error)
      setHasUnsavedChanges(true)
      throw error
    }
  }

  // Build source information from Warren response
  const buildSourceInformation = (response: WarrenResponse): SourceInformation => {
    // Calculate source breakdown from available data
    const totalSources = response.total_knowledge_sources || 0
    const vectorResults = response.vector_results_found || 0
    const textResults = response.text_results_found || 0
    
    // Try to get specific breakdown if available from backend
    const marketingExamples = response.marketing_examples_count || Math.floor(vectorResults * 0.7) // Estimate if not provided
    const complianceRules = response.compliance_rules_count || Math.floor(totalSources - marketingExamples) // Remainder
    
    return {
      totalSources,
      marketingExamples: Math.max(0, marketingExamples),
      complianceRules: Math.max(0, complianceRules),
      searchStrategy: response.search_strategy || 'vector',
      fallbackUsed: response.fallback_used || false
    }
  }

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

    // Mark session as having unsaved changes when new messages are added
    if (sessionContentId && !hasUnsavedChanges) {
      setHasUnsavedChanges(true)
    }

    return newMessage
  }, [sessionContentId, hasUnsavedChanges])

  // Send message to Warren
  const sendMessageToWarren = useCallback(async (userMessage: string) => {
    try {
      // 1. Ensure session exists before sending any messages
      const sessionId = await ensureSession()

      // 2. Add user message to UI
      const userMessageObj = addMessage({
        role: 'advisor',
        content: userMessage,
        type: 'text'
      })

      // 3. Persist user message immediately (graceful degradation)
      await persistMessage(sessionId, 'user', userMessage, {
        timestamp: new Date().toISOString(),
        messageId: userMessageObj.id
      })

      setIsLoading(true)
      setHasUnsavedChanges(true) // Mark session as having unsaved changes

      // 4. Determine if this is a refinement request
      const isRefinement = generatedContent !== null;
      const currentContent = generatedContent?.content;
      
      // Log refinement detection for debugging
      console.log('Refinement Detection:', {
        isRefinement,
        hasGeneratedContent: !!generatedContent,
        currentContentLength: currentContent?.length || 0,
        userMessage: userMessage.substring(0, 50) + (userMessage.length > 50 ? '...' : '')
      });
      
      // 5. Prepare context for Warren (backend will use its own prompts)
      const context = {
        conversation_history: conversation.messages,
        contentType: conversation.context?.contentType || generatedContent?.contentType,
        audience: conversation.context?.audience || generatedContent?.audience,
        platform: conversation.context?.platform || generatedContent?.platform,
        current_content: currentContent,
        is_refinement: isRefinement
      }

      // 6. Call Warren API
      const response: WarrenResponse = await warrenChatApi.sendMessage(
        userMessage,
        sessionId, // Use actual session ID instead of conversation.id
        context
      )

      if (response.status === 'success' && response.content) {
        // 7. Parse Warren's response for delimited content
        const extractedContent = parseWarrenResponse(response.content);
        
        // 8. Generate smart session title on first response if not set
        if (!sessionTitle && conversation.messages.length <= 1) {
          const smartTitle = generateSessionTitle(response.content, userMessage)
          setSessionTitle(smartTitle)
        }
        
        // 9. Add Warren's conversational response to chat (without marketing content)
        const warrenMessageObj = addMessage({
          role: 'warren',
          content: extractedContent.conversationalResponse,
          type: 'text',
          metadata: {
            contentType: response.metadata?.contentType,
            audience: response.metadata?.audience,
            platform: response.metadata?.platform
          }
        })

        // 10. Persist Warren message with clean conversational content (graceful degradation)
        await persistMessage(sessionId, 'warren', extractedContent.conversationalResponse, {
          sourceInfo: buildSourceInformation(response),
          searchStrategy: response.search_strategy,
          contextQuality: response.context_quality_score,
          extractedContent: extractedContent,
          fullResponse: response.content, // Store full response in metadata if needed
          timestamp: new Date().toISOString(),
          messageId: warrenMessageObj.id
        })

        // If marketing content was found, set it for preview
        if (extractedContent.hasMarketingContent && extractedContent.marketingContent) {
          // Build source information from Warren's response
          const sourceInfo = buildSourceInformation(response)
          
          const content: GeneratedContent = {
            title: extractedContent.title || 'Generated Content',
            content: extractedContent.marketingContent,
            contentType: response.metadata?.contentType || 'general',
            audience: response.metadata?.audience || 'general_education',
            platform: response.metadata?.platform || 'general',
            complianceScore: response.context_quality_score,
            sourceInfo
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

  const handleSaveContent = async () => {
    if (generatedContent) {
      try {
        // Ensure we have a session (this should already exist)
        const sessionId = await ensureSession()

        // Map content type to valid backend values (lowercase for advisor_content table)
        const mapContentType = (type: string) => {
          const typeMap: Record<string, string> = {
            'general': 'linkedin_post',
            'social_media': 'linkedin_post', 
            'linkedin': 'linkedin_post',
            'twitter': 'x_post',
            'email': 'email_template',
            'website': 'website_copy',
            'newsletter': 'newsletter',
            'blog': 'website_blog'
          }
          return typeMap[type.toLowerCase()] || 'linkedin_post'
        }

        // Map audience type to valid backend values (lowercase for advisor_content table)
        const mapAudienceType = (type: string) => {
          const audienceMap: Record<string, string> = {
            'general_education': 'general_education',
            'high_net_worth': 'existing_clients',
            'retirees': 'existing_clients',
            'young_professionals': 'new_prospects',
            'institutional': 'existing_clients',
            'prospects': 'new_prospects'
          }
          return audienceMap[type.toLowerCase()] || 'general_education'
        }

        // Save content to database via API
        const contentData = {
          advisorId,
          title: generatedContent.title || 'Generated Content',
          contentText: generatedContent.content,
          contentType: mapContentType(generatedContent.contentType),
          audienceType: mapAudienceType(generatedContent.audience || 'general_education'),
          sourceSessionId: sessionId,
          advisorNotes: 'Generated via Warren chat',
          intendedChannels: [generatedContent.platform.toLowerCase()],
          sourceMetadata: generatedContent.sourceInfo
        }

        console.log('Saving content with data:', contentData)
        const saveResponse = await advisorApi.saveContent(contentData)
        
        addMessage({
          role: 'warren',
          content: `✅ Content saved to your library! (ID: ${saveResponse.content.id})\n\nYou can access your saved content from the Library page.`,
          type: 'text'
        })
      } catch (error) {
        console.error('Failed to save content:', error)
        addMessage({
          role: 'warren',
          content: '❌ Failed to save content to library. Please try again.',
          type: 'error'
        })
      }
    }
  }

  const handleSaveSession = async () => {
    try {
      const contentId = await saveSessionToLibrary()
      const isUpdate = sessionContentId !== null
      
      addMessage({
        role: 'warren',
        content: isUpdate 
          ? `✅ Chat session updated in your library! (ID: ${contentId})\n\nYour latest conversation has been saved.`
          : `✅ Chat session saved to your library! (ID: ${contentId})\n\nYou can continue this conversation later from the Library page.`,
        type: 'text'
      })
    } catch (error) {
      console.error('Failed to save session:', error)
      addMessage({
        role: 'warren',
        content: sessionContentId 
          ? '❌ Failed to update session in library. Please try again.'
          : '❌ Failed to save session to library. Please copy your content manually if needed.',
        type: 'error'
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

  // Check for edit context and load chat history on mount
  React.useEffect(() => {
    const loadEditContext = async () => {
      const editContextData = sessionStorage.getItem('warrenEditContext')
      if (editContextData) {
        try {
          const context = JSON.parse(editContextData)
          setEditContext(context)
          
          // Clear the context from sessionStorage
          sessionStorage.removeItem('warrenEditContext')
          
          if (context.isSessionResume) {
            // Handle full session resume with complete conversation history
            console.log('Resuming Warren session:', context.sessionId)
            
            setAdvisorSession(context.sessionId)
            setSessionContentId(context.contentId)
            setSessionTitle(context.title)
            setIsSessionSaved(true) // Already saved session
            setIsLoadingHistory(true)
            
            // Restore messages from saved session data
            const savedMessages = context.messages || []
            
            // Convert saved messages to UI format and ensure proper timestamps
            const uiMessages = savedMessages.map((msg: any) => ({
              id: msg.id || generateMessageId(),
              role: msg.role,
              content: msg.content,
              timestamp: msg.timestamp ? new Date(msg.timestamp) : new Date(),
              type: msg.type || 'text',
              metadata: msg.metadata || {}
            }))
            
            // Update conversation with restored messages
            setConversation(prev => ({
              ...prev,
              id: context.sessionId,
              messages: uiMessages
            }))
            
            // Restore generated content if it exists and is properly formatted
            if (context.generatedContent && typeof context.generatedContent === 'object') {
              // Ensure the generated content has all required fields
              const restoredContent: GeneratedContent = {
                title: context.generatedContent.title || 'Restored Content',
                content: context.generatedContent.content || '',
                contentType: context.generatedContent.contentType || 'general',
                audience: context.generatedContent.audience || 'general_education',
                platform: context.generatedContent.platform || 'general',
                complianceScore: context.generatedContent.complianceScore,
                sourceInfo: context.generatedContent.sourceInfo
              }
              setGeneratedContent(restoredContent)
            }
            
            setIsLoadingHistory(false)
            
            // Add a Warren message indicating the session was resumed
            addMessage({
              role: 'warren',
              content: `✅ Welcome back! I've restored your previous chat session "${context.title}". You can continue our conversation from where we left off.`,
              type: 'text'
            })
          } else {
            // Handle regular edit context (single content editing)
            if (context.sessionId) {
              setAdvisorSession(context.sessionId)
              setIsLoadingHistory(true)
              
              // Load chat history from API
              const historyResponse = await advisorApi.getSessionMessages(context.sessionId, advisorId)
              const messages = historyResponse.messages || []
              
              // Convert database messages to UI format
              const uiMessages = messages.map((msg: any) => ({
                id: msg.id,
                role: msg.message_type === 'user' ? 'advisor' : 'warren',
                content: msg.content,
                timestamp: new Date(msg.created_at),
                type: 'text',
                metadata: msg.metadata
              }))
              
              // Update conversation with loaded messages
              setConversation(prev => ({
                ...prev,
                id: context.sessionId,
                messages: uiMessages
              }))
              
              // Set the generated content for preview
              const generatedContent: GeneratedContent = {
                title: context.title,
                content: context.content,
                contentType: context.contentType,
                audience: context.audienceType,
                platform: context.platform,
                sourceInfo: context.sourceMetadata
              }
              
              setGeneratedContent(generatedContent)
              setIsLoadingHistory(false)
              
              // Add a Warren message indicating the content was loaded
              addMessage({
                role: 'warren',
                content: `✅ Content loaded! I've restored our previous conversation and your draft content. You can continue editing or ask me to make changes.`,
                type: 'text'
              })
            }
          }
        } catch (error) {
          console.error('Failed to load edit context:', error)
          setIsLoadingHistory(false)
        }
      }
    }
    
    loadEditContext()
  }, [])

  // Scroll to bottom when content preview opens or new messages arrive
  React.useEffect(() => {
    const scrollToBottom = () => {
      const messagesContainer = document.querySelector('.messages-container')
      if (messagesContainer) {
        messagesContainer.scrollTop = messagesContainer.scrollHeight
      }
    }

    // Scroll when new messages are added
    if (conversation.messages.length > 0) {
      // Small delay to allow DOM to update
      setTimeout(scrollToBottom, 100)
    }

    // Scroll when content preview opens
    if (generatedContent) {
      setTimeout(scrollToBottom, 100)
    }
  }, [conversation.messages.length, generatedContent])

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

  // Navigation protection for unsaved changes
  React.useEffect(() => {
    const handleBeforeUnload = (e: BeforeUnloadEvent) => {
      if (hasUnsavedChanges && !isSessionSaved) {
        const message = 'You have unsaved changes in your Warren chat session. Are you sure you want to leave?'
        e.returnValue = message
        return message
      }
    }

    const handlePopState = (e: PopStateEvent) => {
      if (hasUnsavedChanges && !isSessionSaved) {
        const shouldLeave = window.confirm(
          'You have unsaved changes in your Warren chat session. Would you like to save it to your library before leaving?\n\nClick OK to save and continue, or Cancel to stay on this page.'
        )
        
        if (shouldLeave) {
          // Try to save session before leaving
          saveSessionToLibrary().catch(error => {
            console.error('Failed to save session before navigation:', error)
            alert('Failed to save session. Please copy your content manually before leaving.')
          })
        } else {
          // Prevent navigation
          window.history.pushState(null, '', window.location.pathname)
          e.preventDefault()
        }
      }
    }

    if (hasUnsavedChanges) {
      window.addEventListener('beforeunload', handleBeforeUnload)
      window.addEventListener('popstate', handlePopState)
    }

    return () => {
      window.removeEventListener('beforeunload', handleBeforeUnload)
      window.removeEventListener('popstate', handlePopState)
    }
  }, [hasUnsavedChanges, isSessionSaved, saveSessionToLibrary])

  return (
    <div className="h-full flex flex-col">
      <PageHeader 
        title="Warren AI"
        subtitle={sessionTitle || "Compliance-focused content assistant"}
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
              <div className="flex justify-center pt-16">
                <div className="text-center max-w-2xl w-full">
                  <div className="w-16 h-16 bg-muted rounded-full flex items-center justify-center mx-auto mb-6">
                    <span className="text-2xl">🛡️</span>
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
                        disabled={isLoading || isLoadingHistory}
                        placeholder={isLoadingHistory ? "Loading chat history..." : "Tell Warren what content you'd like to create..."}
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
                  disabled={isLoading || isLoadingHistory}
                  placeholder={isLoadingHistory ? "Loading chat history..." : "Continue your conversation with Warren..."}
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
                      <div className="space-y-1">
                        <div className="text-sm text-muted-foreground">
                          {generatedContent.contentType} • {getAudienceLabel(generatedContent.audience)}
                          {generatedContent.complianceScore && (
                            <span className="ml-2 text-green-600 dark:text-green-400">
                              • Compliance Score: {Math.round(generatedContent.complianceScore * 100)}%
                            </span>
                          )}
                        </div>
                        
                        {/* Source Information Badges */}
                        {generatedContent.sourceInfo && (
                          <SourceInfoBadges sourceInfo={generatedContent.sourceInfo} />
                        )}
                      </div>
                    </div>
                  </div>
                  
                  {/* Action Buttons */}
                  <div className="flex gap-2">
                    <Button variant="outline" size="sm" onClick={handleCopyContent}>
                      <Copy className="h-4 w-4 mr-1" />
                      Copy
                    </Button>
                    <Button variant="outline" size="sm" onClick={handleSaveSession}>
                      <Save className="h-4 w-4 mr-1" />
                      {sessionContentId ? 'Update Session' : 'Save Session'}
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