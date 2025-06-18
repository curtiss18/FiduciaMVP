'use client'

import React, { useState, useEffect } from 'react'
import { advisorApi } from '@/lib/api'
import { AdvisorContent } from '@/lib/types'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Copy, Send, Search, Filter, Calendar, User, RefreshCw, Edit } from 'lucide-react'
import Link from 'next/link'
import { cn } from '@/lib/utils'

export const ContentLibrary: React.FC = () => {
  const [content, setContent] = useState<AdvisorContent[]>([])
  const [filteredContent, setFilteredContent] = useState<AdvisorContent[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [searchQuery, setSearchQuery] = useState('')
  const [statusFilter, setStatusFilter] = useState<string>('all')
  const [typeFilter, setTypeFilter] = useState<string>('all')
  const advisorId = 'demo_advisor_001'

  // Fetch content from API
  const fetchContent = async () => {
    setIsLoading(true)
    try {
      const response = await advisorApi.getContentLibrary(advisorId)
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

  // Filter content based on search and filters
  useEffect(() => {
    let filtered = content

    // Search filter
    if (searchQuery.trim()) {
      filtered = filtered.filter(item =>
        item.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
        item.content_text.toLowerCase().includes(searchQuery.toLowerCase()) ||
        item.advisor_notes?.toLowerCase().includes(searchQuery.toLowerCase())
      )
    }

    // Status filter
    if (statusFilter !== 'all') {
      filtered = filtered.filter(item => item.status === statusFilter)
    }

    // Type filter
    if (typeFilter !== 'all') {
      filtered = filtered.filter(item => item.content_type === typeFilter)
    }

    setFilteredContent(filtered)
  }, [content, searchQuery, statusFilter, typeFilter])

  // Load content on mount
  useEffect(() => {
    fetchContent()
  }, [])

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
      blog_post: 'Blog Post'
    }
    return typeMap[type] || type
  }

  // Get platform icon
  const getPlatformIcon = (channels: string[]) => {
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
              return (
                <Card key={item.id} className="flex flex-col hover:shadow-md transition-shadow">
                  <CardHeader className="pb-3">
                    <div className="flex items-center gap-2 w-full">
                      <span className="text-lg">{getPlatformIcon(item.intended_channels)}</span>
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
                          item.status === 'distributed' && "bg-blue-500"
                        )} />
                        {statusBadge.label}
                      </span>
                    </div>
                  </CardHeader>

                  <CardContent className="flex-1 pb-3">
                    <p className="text-sm text-muted-foreground line-clamp-3 mb-4">
                      {item.content_text}
                    </p>

                    {/* Actions */}
                    <div className="flex gap-2">
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
                        </>
                      )}
                      
                      {item.status === 'approved' && (
                        <Button variant="default" size="sm">
                          <Send className="h-3 w-3 mr-1" />
                          Distribute
                        </Button>
                      )}
                    </div>
                  </CardContent>
                </Card>
              )
            })}
          </div>
        )}
      </div>
    </div>
  )
}
