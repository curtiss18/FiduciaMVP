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
import AddContentModal from '@/components/content/AddContentModal'

export default function ContentManagement() {
  const [content, setContent] = useState<ContentItem[]>([])
  const [stats, setStats] = useState<ContentStats | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [searchTerm, setSearchTerm] = useState('')
  const [currentPage, setCurrentPage] = useState(1)
  const [pageSize, setPageSize] = useState(10)
  const [isAddModalOpen, setIsAddModalOpen] = useState(false)

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

  const filteredContent = content.filter(item =>
    item.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
    item.content_type.toLowerCase().includes(searchTerm.toLowerCase()) ||
    item.tags.toLowerCase().includes(searchTerm.toLowerCase())
  )

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
    setIsAddModalOpen(true)
  }

  const handleCloseModal = () => {
    setIsAddModalOpen(false)
  }

  const handleContentSuccess = () => {
    fetchContentData()
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50">
      {/* Header */}
      <div className="border-b bg-white/80 backdrop-blur-sm">
        <div className="container mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <FileText className="h-8 w-8 text-blue-600" />
              <div>
                <h1 className="text-2xl font-bold text-gray-900">Content Management</h1>
                <p className="text-sm text-gray-600">Manage compliance & regulatory content</p>
              </div>
            </div>
            
            <div className="flex items-center space-x-3">
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
        <Card className="shadow-lg border-0">
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle className="flex items-center">
                  <Database className="w-6 h-6 mr-2 text-blue-600" />
                  Content Database
                </CardTitle>
                <CardDescription>
                  Manage your compliance and regulatory content
                </CardDescription>
              </div>
              
              <div className="flex items-center space-x-3">
                {isLoading ? (
                  <Badge variant="outline" className="bg-gray-50 text-gray-700 border-gray-200">
                    <Loader2 className="w-4 h-4 mr-1 animate-spin" />
                    Loading...
                  </Badge>
                ) : (
                  <Badge variant="outline" className="bg-green-50 text-green-700 border-green-200">
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
                
                <Button size="sm" className="bg-blue-600 hover:bg-blue-700" onClick={handleAddContent}>
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
            <ContentTable content={paginatedContent} isLoading={isLoading} />
            
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

      {/* Add Content Modal */}
      <AddContentModal
        isOpen={isAddModalOpen}
        onClose={handleCloseModal}
        onSuccess={handleContentSuccess}
      />
    </div>
  )
}
