'use client'

import React, { useState, useEffect } from 'react'
import { advisorApi } from '@/lib/api'
import { AdvisorContent } from '@/lib/types'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Copy, Send, Search, Filter, Calendar, User, RefreshCw, Edit, Archive, RotateCcw, AlertTriangle, X } from 'lucide-react'
import Link from 'next/link'
import { cn } from '@/lib/utils'

export const ContentLibrary: React.FC = () => {
  const [content, setContent] = useState<AdvisorContent[]>([])
  const [filteredContent, setFilteredContent] = useState<AdvisorContent[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [searchQuery, setSearchQuery] = useState('')
  const [statusFilter, setStatusFilter] = useState<string>('all')
  const [typeFilter, setTypeFilter] = useState<string>('all')
  const [itemToArchive, setItemToArchive] = useState<string | null>(null) // Store item ID instead of full item
  const advisorId = 'demo_advisor_001'

  // Fetch content from API
  const fetchContent = async () => {
    setIsLoading(true)
    try {
      // Build filters object
      const filters: any = {}
      if (statusFilter && statusFilter !== 'all') {
        filters.status = statusFilter
      }
      if (typeFilter && typeFilter !== 'all') {
        filters.content_type = typeFilter
      }

      const response = await advisorApi.getContentLibrary(advisorId, filters)
      console.log('Content library response:', response)
      setContent(response.content || [])
      setFilteredContent(response.content || [])
    } catch (error) {
      console.error('Failed to fetch content library:', error)
      setContent([])
      setFilteredContent([])
    } finally {
      setIsLoading(false)
    }
  }

  // Filter content based on search (other filters handled by backend)
  useEffect(() => {
    let filtered = content

    // Search filter (only client-side filtering needed)
    if (searchQuery.trim()) {
      filtered = filtered.filter(item =>
        item.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
        item.content_text.toLowerCase().includes(searchQuery.toLowerCase()) ||
        item.advisor_notes?.toLowerCase().includes(searchQuery.toLowerCase())
      )
    }

    setFilteredContent(filtered)
  }, [content, searchQuery])

  // Load content on mount and when filters change
  useEffect(() => {
    fetchContent()
  }, [statusFilter, typeFilter])

  // Handle copy content
  const handleCopyContent = async (item: AdvisorContent) => {
    try {
      await navigator.clipboard.writeText(item.content_text)
      console.log('Content copied to clipboard')
    } catch (error) {
      console.error('Failed to copy content:', error)
    }
  }

  // Handle edit in Warren - load content and chat history back to Warren
  const handleEditInWarren = async (item: AdvisorContent) => {
    try {
      // Store the content and session info for Warren to pick up
      const editContext = {
        contentId: item.id,
        sessionId: item.source_session_id,
        title: item.title,
        content: item.content_text,
        contentType: item.content_type,
        audienceType: item.audience_type,
        platform: item.intended_channels[0] || 'linkedin'
      }
      
      // Store in sessionStorage for Warren to retrieve
      sessionStorage.setItem('warrenEditContext', JSON.stringify(editContext))
      
      // Navigate to Warren chat
      window.location.href = '/chat'
    } catch (error) {
      console.error('Failed to load content in Warren:', error)
    }
  }

  // Handle resuming Warren session - load entire chat history
  const handleResumeSession = async (item: AdvisorContent) => {
    try {
      // Parse session data from content_text
      const sessionData = JSON.parse(item.content_text)
      
      // Store session info for Warren to restore complete conversation
      const sessionContext = {
        isSessionResume: true,
        sessionId: item.source_session_id,
        contentId: item.id,
        title: item.title,
        messages: sessionData.messages || [],
        generatedContent: sessionData.generatedContent,
        createdAt: sessionData.createdAt
      }
      
      // Store in sessionStorage for Warren to retrieve
      sessionStorage.setItem('warrenEditContext', JSON.stringify(sessionContext))
      
      // Navigate to Warren chat
      window.location.href = '/chat'
    } catch (error) {
      console.error('Failed to resume Warren session:', error)
      // Fallback to regular edit if session data is corrupted
      handleEditInWarren(item)
    }
  }

  // Handle submit for review
  const handleSubmitForReview = async (item: AdvisorContent) => {
    try {
      await advisorApi.updateContentStatus(item.id, advisorId, 'submitted', 'Submitted for compliance review')
      console.log('Content submitted for review')
      // Refresh content to show updated status
      fetchContent()
    } catch (error) {
      console.error('Failed to submit for review:', error)
    }
  }

  // Handle archive content - show inline confirmation
  const handleArchiveContent = async (item: AdvisorContent) => {
    setItemToArchive(item.id)
  }

  // Confirm archive action
  const confirmArchive = async (itemId: string) => {
    try {
      await advisorApi.archiveContent(itemId, advisorId)
      console.log('Content archived')
      setItemToArchive(null)
      // Refresh content to show updated status
      fetchContent()
    } catch (error) {
      console.error('Failed to archive content:', error)
    }
  }

  // Cancel archive action
  const cancelArchive = () => {
    setItemToArchive(null)
  }

  // Handle restore content
  const handleRestoreContent = async (item: AdvisorContent) => {
    try {
      await advisorApi.restoreContent(item.id, advisorId)
      console.log('Content restored')
      // Refresh content to show updated status
      fetchContent()
    } catch (error) {
      console.error('Failed to restore content:', error)
    }
  }

  // Get status badge styling
  const getStatusBadge = (status: string) => {
    const statusConfig = {
      draft: { 
        className: 'bg-slate-100 text-slate-700 border border-slate-200 dark:bg-slate-800 dark:text-slate-300 dark:border-slate-700', 
        label: 'Draft' 
      },
      submitted: { 
        className: 'bg-amber-50 text-amber-700 border border-amber-200 dark:bg-amber-900/20 dark:text-amber-300 dark:border-amber-800', 
        label: 'In Review' 
      },
      approved: { 
        className: 'bg-emerald-50 text-emerald-700 border border-emerald-200 dark:bg-emerald-900/20 dark:text-emerald-300 dark:border-emerald-800', 
        label: 'Approved' 
      },
      rejected: { 
        className: 'bg-red-50 text-red-700 border border-red-200 dark:bg-red-900/20 dark:text-red-300 dark:border-red-800', 
        label: 'Needs Revision' 
      },
      distributed: { 
        className: 'bg-blue-50 text-blue-700 border border-blue-200 dark:bg-blue-900/20 dark:text-blue-300 dark:border-blue-800', 
        label: 'Published' 
      },
      archived: { 
        className: 'bg-gray-50 text-gray-700 border border-gray-200 dark:bg-gray-900/20 dark:text-gray-400 dark:border-gray-800', 
        label: 'Archived' 
      }
    }
    return statusConfig[status as keyof typeof statusConfig] || { 
      className: 'bg-slate-100 text-slate-700 border border-slate-200 dark:bg-slate-800 dark:text-slate-300 dark:border-slate-700', 
      label: status 
    }
  }

  // Get content type display name
  const getContentTypeDisplay = (type: string) => {
    const typeMap: Record<string, string> = {
      linkedin_post: 'LinkedIn Post',
      email_template: 'Email Template',
      website_content: 'Website Content',
      newsletter: 'Newsletter',
      social_media: 'Social Media',
      blog_post: 'Blog Post',
      warren_session: 'Warren Session'
    }
    return typeMap[type] || type
  }

  // Get platform icon
  const getPlatformIcon = (channels: string[], item: AdvisorContent) => {
    // Check if this is a Warren session by metadata
    if (item.source_metadata?.isWarrenSession || channels.includes('warren_chat')) return '🛡️'
    if (channels.includes('linkedin')) return '💼'
    if (channels.includes('twitter')) return '🐦'
    if (channels.includes('email')) return '📧'
    if (channels.includes('website')) return '🌐'
    return '📄'
  }

  // Format date
  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric'
    })
  }

  if (isLoading) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <div className="text-center">
          <RefreshCw className="h-8 w-8 animate-spin text-primary mx-auto mb-4" />
          <p className="text-muted-foreground">Loading your content library...</p>
        </div>
      </div>
    )
  }

  if (content.length === 0) {
    return (
      <div className="flex-1 p-6">
        <div className="flex justify-center pt-16">
          <div className="text-center max-w-md">
            <div className="w-16 h-16 bg-muted rounded-full flex items-center justify-center mx-auto mb-6">
              <User className="h-8 w-8 text-muted-foreground" />
            </div>
            <h2 className="text-xl font-semibold mb-3">
              Your compliant content will live here
            </h2>
            <p className="text-muted-foreground text-sm leading-relaxed mb-6">
              Start creating content with Warren to build your personal library of SEC/FINRA compliant marketing materials.
            </p>
            <Link href="/chat">
              <Button>
                Create Your First Content
              </Button>
            </Link>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="flex-1 flex flex-col">
      {/* Search and Filters */}
      <div className="border-b border-border px-6 py-4 bg-background">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:gap-4">
          {/* Search */}
          <div className="relative flex-1 max-w-md">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <Input
              type="text"
              placeholder="Search content..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-10"
            />
          </div>

          {/* Simple Filters */}
          <div className="flex gap-2">
            <select 
              value={statusFilter} 
              onChange={(e) => setStatusFilter(e.target.value)}
              className="h-10 px-3 py-2 border border-input bg-background rounded-md text-sm"
            >
              <option value="all">All Status</option>
              <option value="draft">Draft</option>
              <option value="submitted">In Review</option>
              <option value="approved">Approved</option>
              <option value="rejected">Needs Revision</option>
              <option value="distributed">Published</option>
              <option value="archived">Archived</option>
            </select>

            <select 
              value={typeFilter} 
              onChange={(e) => setTypeFilter(e.target.value)}
              className="h-10 px-3 py-2 border border-input bg-background rounded-md text-sm"
            >
              <option value="all">All Types</option>
              <option value="linkedin_post">LinkedIn Post</option>
              <option value="email_template">Email Template</option>
              <option value="website_content">Website Content</option>
              <option value="newsletter">Newsletter</option>
              <option value="social_media">Social Media</option>
              <option value="blog_post">Blog Post</option>
            </select>
          </div>

          {/* Refresh button */}
          <Button variant="outline" onClick={fetchContent}>
            <RefreshCw className="h-4 w-4" />
          </Button>

          {/* Results count */}
          <div className="text-sm text-muted-foreground">
            {filteredContent.length} of {content.length} items
          </div>
        </div>
      </div>

      {/* Content Grid */}
      <div className="flex-1 p-6 overflow-y-auto">
        {filteredContent.length === 0 ? (
          <div className="text-center py-12">
            <Filter className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
            <h3 className="text-lg font-semibold mb-2">No content matches your filters</h3>
            <p className="text-muted-foreground mb-4">Try adjusting your search or filter criteria</p>
            <Button variant="outline" onClick={() => {
              setSearchQuery('')
              setStatusFilter('all')
              setTypeFilter('all')
            }}>
              Clear Filters
            </Button>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {filteredContent.map((item) => {
              const statusBadge = getStatusBadge(item.status)
              const isArchiveConfirm = itemToArchive === item.id
              
              return (
                <Card key={item.id} className={cn(
                  "flex flex-col hover:shadow-md transition-shadow",
                  item.status === 'archived' && "opacity-75",
                  isArchiveConfirm && "border-amber-300 bg-amber-50 dark:bg-amber-950 dark:border-amber-700"
                )}>
                  {isArchiveConfirm ? (
                    // Archive confirmation interface
                    <>
                      <CardHeader className="pb-3">
                        <div className="flex items-center gap-2 w-full">
                          <AlertTriangle className="h-5 w-5 text-amber-600 dark:text-amber-400" />
                          <h3 className="font-semibold text-sm flex-1">Archive Content</h3>
                          <Button variant="ghost" size="sm" onClick={cancelArchive}>
                            <X className="h-4 w-4" />
                          </Button>
                        </div>
                      </CardHeader>
                      <CardContent className="flex-1 pb-3">
                        <p className="text-sm text-muted-foreground mb-4">
                          This action will set the status to archived. The content will be removed from your active library but can be restored by filtering for content with the archived status.
                        </p>
                        <div className="flex gap-2">
                          <Button variant="outline" size="sm" onClick={cancelArchive}>
                            Cancel
                          </Button>
                          <Button variant="default" size="sm" onClick={() => confirmArchive(item.id)}>
                            <Archive className="h-3 w-3 mr-1" />
                            Archive
                          </Button>
                        </div>
                      </CardContent>
                    </>
                  ) : (
                    // Normal card content
                    <>
                      <CardHeader className="pb-3">
                        <div className="flex items-center gap-2 w-full">
                          <span className="text-lg">{getPlatformIcon(item.intended_channels, item)}</span>
                          <h3 className="font-semibold truncate text-sm flex-1">{item.title}</h3>
                        </div>
                        <div className="flex items-center justify-between gap-2">
                          <div className="flex items-center gap-4 text-xs text-muted-foreground">
                            <span>{getContentTypeDisplay(item.content_type)}</span>
                            <span className="flex items-center gap-1">
                              <Calendar className="h-3 w-3" />
                              {formatDate(item.created_at)}
                            </span>
                          </div>
                          <span className={cn(
                            "inline-flex items-center rounded-full px-2.5 py-1 text-xs font-medium gap-1.5 whitespace-nowrap flex-shrink-0",
                            statusBadge.className
                          )}>
                            {/* Status indicator dot */}
                            <span className={cn(
                              "w-1.5 h-1.5 rounded-full flex-shrink-0",
                              item.status === 'draft' && "bg-slate-400 dark:bg-slate-500",
                              item.status === 'submitted' && "bg-amber-500 animate-pulse",
                              item.status === 'approved' && "bg-emerald-500",
                              item.status === 'rejected' && "bg-red-500",
                              item.status === 'distributed' && "bg-blue-500",
                              item.status === 'archived' && "bg-gray-400 dark:bg-gray-600"
                            )} />
                            {statusBadge.label}
                          </span>
                        </div>
                      </CardHeader>

                      <CardContent className="flex-1 pb-3">
                        {item.source_metadata?.isWarrenSession ? (
                          // Special display for Warren sessions
                          <div className="space-y-2">
                            <p className="text-sm text-muted-foreground">
                              💬 {item.source_metadata?.messageCount || 0} messages
                              {item.source_metadata?.hasGeneratedContent && ' • Content generated'}
                            </p>
                            <p className="text-xs text-muted-foreground line-clamp-2">
                              Warren chat session - Click "Resume Chat" to continue the conversation
                            </p>
                          </div>
                        ) : (
                          // Regular content preview
                          <p className="text-sm text-muted-foreground line-clamp-3 mb-4">
                            {item.content_text}
                          </p>
                        )}

                        {/* Actions */}
                        <div className="flex gap-2">
                          {item.source_metadata?.isWarrenSession ? (
                            // Special actions for Warren sessions
                            <>
                              {item.status === 'archived' ? (
                                // Archived Warren session - only restore
                                <Button variant="outline" size="sm" onClick={() => handleRestoreContent(item)}>
                                  <RotateCcw className="h-3 w-3 mr-1" />
                                  Restore
                                </Button>
                              ) : (
                                // Active Warren session - normal actions + archive
                                <>
                                  <Button variant="outline" size="sm" onClick={() => handleResumeSession(item)}>
                                    <Edit className="h-3 w-3 mr-1" />
                                    Resume Chat
                                  </Button>
                                  {item.status === 'draft' && (
                                    <>
                                      <Button variant="outline" size="sm" onClick={() => handleSubmitForReview(item)}>
                                        <Send className="h-3 w-3 mr-1" />
                                        Submit
                                      </Button>
                                      <Button variant="outline" size="sm" onClick={() => handleArchiveContent(item)}>
                                        <Archive className="h-3 w-3 mr-1" />
                                        Archive
                                      </Button>
                                    </>
                                  )}
                                </>
                              )}
                            </>
                          ) : (
                            // Regular content actions
                            <>
                              {item.status === 'archived' ? (
                                // Archived content - only restore
                                <Button variant="outline" size="sm" onClick={() => handleRestoreContent(item)}>
                                  <RotateCcw className="h-3 w-3 mr-1" />
                                  Restore
                                </Button>
                              ) : (
                                // Active content - normal actions + archive
                                <>
                                  <Button variant="outline" size="sm" onClick={() => handleCopyContent(item)}>
                                    <Copy className="h-3 w-3 mr-1" />
                                    Copy
                                  </Button>
                                  
                                  {item.status === 'draft' && (
                                    <>
                                      <Button variant="outline" size="sm" onClick={() => handleEditInWarren(item)}>
                                        <Edit className="h-3 w-3 mr-1" />
                                        Edit
                                      </Button>
                                      <Button variant="outline" size="sm" onClick={() => handleSubmitForReview(item)}>
                                        <Send className="h-3 w-3 mr-1" />
                                        Submit
                                      </Button>
                                      <Button variant="outline" size="sm" onClick={() => handleArchiveContent(item)}>
                                        <Archive className="h-3 w-3 mr-1" />
                                        Archive
                                      </Button>
                                    </>
                                  )}
                                  
                                  {item.status === 'approved' && (
                                    <>
                                      <Button variant="default" size="sm">
                                        <Send className="h-3 w-3 mr-1" />
                                        Distribute
                                      </Button>
                                      <Button variant="outline" size="sm" onClick={() => handleArchiveContent(item)}>
                                        <Archive className="h-3 w-3 mr-1" />
                                        Archive
                                      </Button>
                                    </>
                                  )}

                                  {(item.status === 'submitted' || item.status === 'rejected' || item.status === 'distributed') && (
                                    <Button variant="outline" size="sm" onClick={() => handleArchiveContent(item)}>
                                      <Archive className="h-3 w-3 mr-1" />
                                      Archive
                                    </Button>
                                  )}
                                </>
                              )}
                            </>
                          )}
                        </div>
                      </CardContent>
                    </>
                  )}
                </Card>
              )
            })}
          </div>
        )}
      </div>
    </div>
  )
}
