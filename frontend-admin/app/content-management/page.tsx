'use client'

import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { 
  Database,
  FileText,
  RefreshCw,
  CheckCircle,
  Loader2
} from 'lucide-react'
import { contentApi } from '@/lib/api'
import { ContentItem, ContentStats } from '@/components/content/types'
import ContentStatsCards from '@/components/content/ContentStatsCards'
import SearchFilterBar from '@/components/content/SearchFilterBar'
import ContentTable from '@/components/content/ContentTable'
import Pagination from '@/components/content/Pagination'
import ContentModal from '@/components/content/ContentModal'
import DeleteContentModal from '@/components/content/DeleteContentModal'
import { ThemeToggle } from '@/shared-ui/components/theme'

export default function ContentManagement() {
  const [content, setContent] = useState<ContentItem[]>([])
  const [stats, setStats] = useState<ContentStats | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [searchTerm, setSearchTerm] = useState('')
  const [currentPage, setCurrentPage] = useState(1)
  const [pageSize, setPageSize] = useState(10)
  const [modalMode, setModalMode] = useState<'create' | 'edit'>('create')
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [editingContent, setEditingContent] = useState<ContentItem | null>(null)
  const [deleteModal, setDeleteModal] = useState<{
    isOpen: boolean
    content: ContentItem | null
  }>({
    isOpen: false,
    content: null
  })

  const fetchContentData = async () => {
    try {
      setIsLoading(true)
      
      // Fetch content list
      const contentResponse = await contentApi.getContent()
      setContent(contentResponse.data.content || [])
      
      // Fetch statistics
      const statsResponse = await contentApi.getContentStatistics()
      setStats(statsResponse.data.statistics || statsResponse.data)
      
    } catch (error) {
      console.error('Error fetching content data:', error)
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    fetchContentData()
  }, [])

  const handleRefresh = () => {
    fetchContentData()
  }

  const filteredContent = content.filter(item => {
    const tagsString = Array.isArray(item.tags) ? item.tags.join(' ') : (item.tags || '')
    return (
      item.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
      item.content_type.toLowerCase().includes(searchTerm.toLowerCase()) ||
      tagsString.toLowerCase().includes(searchTerm.toLowerCase())
    )
  })

  // Pagination calculations
  const totalPages = Math.ceil(filteredContent.length / pageSize)
  const startIndex = (currentPage - 1) * pageSize
  const endIndex = startIndex + pageSize
  const paginatedContent = filteredContent.slice(startIndex, endIndex)

  // Reset to first page when search changes
  useEffect(() => {
    setCurrentPage(1)
  }, [searchTerm])

  const handlePageChange = (page: number) => {
    setCurrentPage(page)
  }

  const handlePageSizeChange = (newPageSize: number) => {
    setPageSize(newPageSize)
    setCurrentPage(1)
  }

  const handleAddContent = () => {
    setModalMode('create')
    setEditingContent(null)
    setIsModalOpen(true)
  }

  const handleCloseModal = () => {
    setIsModalOpen(false)
    setEditingContent(null)
  }

  const handleContentSuccess = () => {
    fetchContentData()
  }

  const handleEditContent = (content: ContentItem) => {
    setModalMode('edit')
    setEditingContent(content)
    setIsModalOpen(true)
  }

  const handleDeleteContent = (content: ContentItem) => {
    setDeleteModal({
      isOpen: true,
      content: content
    })
  }

  const handleDeleteSuccess = () => {
    setDeleteModal({
      isOpen: false,
      content: null
    })
    
    // Add a small delay to ensure backend processing is complete
    setTimeout(() => {
      fetchContentData()
    }, 100)
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-background via-background to-muted/20">
      {/* Header */}
      <div className="border-b bg-card/80 backdrop-blur-sm">
        <div className="container mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <FileText className="h-8 w-8 text-primary" />
              <div>
                <h1 className="text-2xl font-bold text-foreground">Content Management</h1>
                <p className="text-sm text-muted-foreground">Manage compliance & regulatory content</p>
              </div>
            </div>
            
            <div className="flex items-center space-x-3">
              <ThemeToggle />
              
              {isLoading ? (
                <Badge variant="outline" className="bg-gray-50 text-gray-700 border-gray-200">
                  <Loader2 className="w-4 h-4 mr-1 animate-spin" />
                  Loading...
                </Badge>
              ) : (
                <Badge variant="outline" className="bg-green-50 text-green-700 border-green-200">
                  <CheckCircle className="w-4 h-4 mr-1" />
                  System Healthy
                </Badge>
              )}
            </div>
          </div>
        </div>
      </div>

      <div className="container mx-auto px-6 py-8">
        {/* Stats Cards */}
        <ContentStatsCards stats={stats} contentLength={content.length} />

        {/* Content Table */}
        <Card className="shadow-lg border border-border">
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle className="flex items-center">
                  <Database className="w-6 h-6 mr-2 text-primary" />
                  Content Database
                </CardTitle>
                <CardDescription>
                  Manage your compliance and regulatory content
                </CardDescription>
              </div>
              
              <div className="flex items-center space-x-3">
                {isLoading ? (
                  <Badge variant="outline" className="bg-muted text-muted-foreground border-border">
                    <Loader2 className="w-4 h-4 mr-1 animate-spin" />
                    Loading...
                  </Badge>
                ) : (
                  <Badge variant="outline" className="bg-green-50 text-green-700 border-green-200 dark:bg-green-900/20 dark:text-green-300 dark:border-green-800">
                    <CheckCircle className="w-4 h-4 mr-1" />
                    {content.length} Items
                  </Badge>
                )}
                
                <Button variant="outline" size="sm" onClick={handleRefresh} disabled={isLoading}>
                  {isLoading ? (
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  ) : (
                    <RefreshCw className="w-4 h-4 mr-2" />
                  )}
                  {isLoading ? 'Refreshing...' : 'Refresh'}
                </Button>
                
                <div className="h-6 w-px bg-border"></div>
                
                <Button 
                  className="bg-primary hover:bg-primary/90 text-primary-foreground font-medium shadow-sm px-4 py-2 h-9"
                  onClick={handleAddContent}
                >
                  Add Content
                </Button>
              </div>
            </div>
          </CardHeader>
          
          {/* Search and Filter Bar */}
          <SearchFilterBar
            searchTerm={searchTerm}
            onSearchChange={setSearchTerm}
            filteredCount={filteredContent.length}
            totalCount={content.length}
          />
          
          <CardContent>
            <ContentTable 
              content={paginatedContent} 
              isLoading={isLoading}
              onEdit={handleEditContent}
              onRefresh={fetchContentData}
            />
            
            {/* Pagination Controls */}
            {filteredContent.length > 0 && (
              <Pagination
                currentPage={currentPage}
                totalPages={totalPages}
                pageSize={pageSize}
                totalItems={filteredContent.length}
                startIndex={startIndex}
                endIndex={endIndex}
                onPageChange={handlePageChange}
                onPageSizeChange={handlePageSizeChange}
              />
            )}
          </CardContent>
        </Card>

        {/* Footer Stats */}
        <div className="mt-8 text-center text-sm text-gray-500">
          <div className="flex justify-center items-center space-x-6">
            <div>Content API: Connected</div>
            <div>•</div>
            <div>Items Loaded: {content.length}</div>
            <div>•</div>
            <div>Status: {isLoading ? 'Loading...' : 'Ready'}</div>
          </div>
        </div>
      </div>

      {/* Unified Content Modal */}
      <ContentModal
        mode={modalMode}
        isOpen={isModalOpen}
        onClose={handleCloseModal}
        onSuccess={handleContentSuccess}
        onDelete={handleDeleteContent}
        content={editingContent}
      />

      {/* Delete Content Modal */}
      <DeleteContentModal
        isOpen={deleteModal.isOpen}
        onClose={() => setDeleteModal({ isOpen: false, content: null })}
        onSuccess={handleDeleteSuccess}
        content={deleteModal.content}
      />
    </div>
  )
}
