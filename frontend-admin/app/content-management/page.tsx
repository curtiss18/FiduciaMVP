'use client'

import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { 
  Database,
  FileText,
  Plus,
  Search,
  Filter,
  Edit,
  Trash2,
  Eye,
  Loader2,
  RefreshCw,
  CheckCircle,
  AlertCircle,
  ChevronLeft,
  ChevronRight,
  MoreVertical
} from 'lucide-react'
import { contentApi } from '@/lib/api'

interface ContentItem {
  id: number
  title: string
  content_text: string
  content_type: string
  audience_type: string
  approval_status: string
  tags: string
  source: string
  compliance_notes: string
  created_at: string
  updated_at: string
  is_vectorized: boolean
}

interface ContentStats {
  total_content: number
  by_type: Record<string, number>
  by_status: Record<string, number>
  vectorization_stats: {
    vectorized: number
    total: number
    percentage: number
  }
}

export default function ContentManagement() {
  const [content, setContent] = useState<ContentItem[]>([])
  const [stats, setStats] = useState<ContentStats | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [lastUpdated, setLastUpdated] = useState<Date>(new Date())
  const [searchTerm, setSearchTerm] = useState('')
  const [currentPage, setCurrentPage] = useState(1)
  const [pageSize, setPageSize] = useState(10)
  const [openDropdown, setOpenDropdown] = useState<number | null>(null)

  const fetchContentData = async () => {
    try {
      setIsLoading(true)
      
      // Fetch content list
      const contentResponse = await contentApi.getContent()
      setContent(contentResponse.data.content || [])
      
      // Fetch statistics
      const statsResponse = await contentApi.getContentStatistics()
      setStats(statsResponse.data.statistics || statsResponse.data)
      
      setLastUpdated(new Date())
      
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
    setCurrentPage(1) // Reset to first page when changing page size
  }

  const toggleDropdown = (id: number, event: React.MouseEvent) => {
    event.stopPropagation()
    setOpenDropdown(openDropdown === id ? null : id)
  }

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = () => {
      setOpenDropdown(null)
    }
    
    if (openDropdown !== null) {
      document.addEventListener('click', handleClickOutside)
      return () => document.removeEventListener('click', handleClickOutside)
    }
  }, [openDropdown])

  const getStatusBadgeColor = (status: string) => {
    switch (status.toLowerCase()) {
      case 'approved':
        return 'bg-green-50 text-green-700 border-green-200'
      case 'pending':
        return 'bg-yellow-50 text-yellow-700 border-yellow-200'
      case 'rejected':
        return 'bg-red-50 text-red-700 border-red-200'
      default:
        return 'bg-gray-50 text-gray-700 border-gray-200'
    }
  }

  const formatContentType = (type: string) => {
    return type.split('_').map(word => 
      word.charAt(0).toUpperCase() + word.slice(1)
    ).join(' ')
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
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <Card className="border-0 shadow-lg bg-gradient-to-br from-blue-500 to-blue-600 text-white">
            <CardHeader className="pb-2">
              <CardTitle className="text-lg flex items-center">
                <Database className="w-5 h-5 mr-2" />
                Total Content
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold">{stats?.total_content || content.length}</div>
              <p className="text-blue-100 text-sm">All content pieces</p>
            </CardContent>
          </Card>

          <Card className="border-0 shadow-lg bg-gradient-to-br from-green-500 to-green-600 text-white">
            <CardHeader className="pb-2">
              <CardTitle className="text-lg flex items-center">
                <CheckCircle className="w-5 h-5 mr-2" />
                Vectorized
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold">
                {stats?.vectorization_stats?.vectorized || 0}
              </div>
              <p className="text-green-100 text-sm">
                {stats?.vectorization_stats?.percentage || 0}% coverage
              </p>
            </CardContent>
          </Card>

          <Card className="border-0 shadow-lg bg-gradient-to-br from-purple-500 to-purple-600 text-white">
            <CardHeader className="pb-2">
              <CardTitle className="text-lg flex items-center">
                <FileText className="w-5 h-5 mr-2" />
                Approved
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold">
                {stats?.by_status?.approved || 0}
              </div>
              <p className="text-purple-100 text-sm">Ready to use</p>
            </CardContent>
          </Card>

          <Card className="border-0 shadow-lg bg-gradient-to-br from-orange-500 to-orange-600 text-white">
            <CardHeader className="pb-2">
              <CardTitle className="text-lg flex items-center">
                <AlertCircle className="w-5 h-5 mr-2" />
                Pending
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold">
                {stats?.by_status?.pending || 0}
              </div>
              <p className="text-orange-100 text-sm">Awaiting review</p>
            </CardContent>
          </Card>
        </div>

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
                
                <Button size="sm" className="bg-blue-600 hover:bg-blue-700">
                  Add Content
                </Button>
              </div>
            </div>
          </CardHeader>
          
          {/* Search and Filter Bar */}
          <div className="border-b border-gray-200 px-6 py-4">
            <div className="flex items-center justify-between space-x-4">
              <div className="flex-1 max-w-md">
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
                  <input
                    type="text"
                    placeholder="Search content..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                </div>
              </div>
              
              <div className="flex items-center space-x-2">
                <Button variant="outline" size="sm">
                  <Filter className="w-4 h-4 mr-2" />
                  Filter
                </Button>
                <span className="text-sm text-gray-600">
                  {filteredContent.length} of {content.length} items
                </span>
              </div>
            </div>
          </div>
          
          <CardContent>
            {isLoading ? (
              <div className="flex items-center justify-center py-12">
                <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
                <span className="ml-2 text-gray-600">Loading content...</span>
              </div>
            ) : filteredContent.length === 0 ? (
              <div className="text-center py-12">
                <FileText className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                <h3 className="text-lg font-medium text-gray-900 mb-2">No content found</h3>
                <p className="text-gray-600 mb-4">
                  {searchTerm ? 'No content matches your search.' : 'Start by adding your first content piece.'}
                </p>
                <Button>
                  Add Content
                </Button>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="border-b border-gray-200">
                      <th className="text-left py-3 px-4 font-medium text-gray-700">Title</th>
                      <th className="text-left py-3 px-4 font-medium text-gray-700">Type</th>
                      <th className="text-left py-3 px-4 font-medium text-gray-700">Status</th>
                      <th className="text-left py-3 px-4 font-medium text-gray-700">Vectorized</th>
                      <th className="text-left py-3 px-4 font-medium text-gray-700">Updated</th>
                      <th className="text-right py-3 px-4 font-medium text-gray-700">Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {paginatedContent.map((item) => (
                      <tr key={item.id} className="border-b border-gray-100 hover:bg-gray-50">
                        <td className="py-4 px-4">
                          <div className="font-medium text-gray-900">{item.title}</div>
                          <div className="text-sm text-gray-600 truncate max-w-xs">
                            {item.content_text}
                          </div>
                        </td>
                        <td className="py-4 px-4">
                          <Badge variant="outline" className="bg-blue-50 text-blue-700">
                            {formatContentType(item.content_type)}
                          </Badge>
                        </td>
                        <td className="py-4 px-4">
                          <Badge variant="outline" className={getStatusBadgeColor(item.approval_status)}>
                            {item.approval_status}
                          </Badge>
                        </td>
                        <td className="py-4 px-4">
                          {item.is_vectorized ? (
                            <CheckCircle className="w-5 h-5 text-green-500" />
                          ) : (
                            <AlertCircle className="w-5 h-5 text-yellow-500" />
                          )}
                        </td>
                        <td className="py-4 px-4 text-sm text-gray-600">
                          {new Date(item.updated_at).toLocaleDateString()}
                        </td>
                        <td className="py-4 px-4">
                          <div className="flex items-center justify-end">
                            <div className="relative">
                              <Button 
                                variant="outline" 
                                size="sm"
                                onClick={(e) => toggleDropdown(item.id, e)}
                                className="p-1"
                              >
                                <MoreVertical className="w-4 h-4" />
                              </Button>
                              
                              {openDropdown === item.id && (
                                <div className="absolute right-0 mt-1 w-32 bg-white border border-gray-200 rounded-md shadow-lg z-10">
                                  <div className="py-1">
                                    <button
                                      className="flex items-center w-full px-3 py-2 text-sm text-gray-700 hover:bg-gray-100"
                                      onClick={() => {
                                        // Handle view action
                                        setOpenDropdown(null)
                                      }}
                                    >
                                      <Eye className="w-4 h-4 mr-2" />
                                      View
                                    </button>
                                    <button
                                      className="flex items-center w-full px-3 py-2 text-sm text-gray-700 hover:bg-gray-100"
                                      onClick={() => {
                                        // Handle edit action
                                        setOpenDropdown(null)
                                      }}
                                    >
                                      <Edit className="w-4 h-4 mr-2" />
                                      Edit
                                    </button>
                                    <button
                                      className="flex items-center w-full px-3 py-2 text-sm text-red-600 hover:bg-red-50"
                                      onClick={() => {
                                        // Handle delete action
                                        setOpenDropdown(null)
                                      }}
                                    >
                                      <Trash2 className="w-4 h-4 mr-2" />
                                      Delete
                                    </button>
                                  </div>
                                </div>
                              )}
                            </div>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
            
            {/* Pagination Controls */}
            {filteredContent.length > 0 && (
              <div className="border-t border-gray-200 px-6 py-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-4">
                    <span className="text-sm text-gray-700">
                      Showing {startIndex + 1} to {Math.min(endIndex, filteredContent.length)} of {filteredContent.length} results
                    </span>
                    
                    <div className="flex items-center space-x-2">
                      <span className="text-sm text-gray-700">Show:</span>
                      <select
                        value={pageSize}
                        onChange={(e) => handlePageSizeChange(Number(e.target.value))}
                        className="border border-gray-300 rounded px-2 py-1 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                      >
                        <option value={10}>10</option>
                        <option value={50}>50</option>
                        <option value={100}>100</option>
                      </select>
                      <span className="text-sm text-gray-700">per page</span>
                    </div>
                  </div>

                  <div className="flex items-center space-x-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handlePageChange(currentPage - 1)}
                      disabled={currentPage === 1}
                    >
                      <ChevronLeft className="w-4 h-4 mr-1" />
                      Previous
                    </Button>
                    
                    <div className="flex items-center space-x-1">
                      {Array.from({ length: totalPages }, (_, i) => i + 1)
                        .filter(page => {
                          // Show first page, last page, current page, and pages around current
                          return (
                            page === 1 ||
                            page === totalPages ||
                            Math.abs(page - currentPage) <= 1
                          )
                        })
                        .map((page, index, array) => {
                          const prevPage = array[index - 1]
                          const showEllipsis = prevPage && page - prevPage > 1
                          
                          return (
                            <div key={page} className="flex items-center">
                              {showEllipsis && (
                                <span className="px-2 py-1 text-gray-500">...</span>
                              )}
                              <Button
                                variant={currentPage === page ? "default" : "outline"}
                                size="sm"
                                onClick={() => handlePageChange(page)}
                                className={currentPage === page ? "bg-blue-600 text-white" : ""}
                              >
                                {page}
                              </Button>
                            </div>
                          )
                        })}
                    </div>
                    
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handlePageChange(currentPage + 1)}
                      disabled={currentPage === totalPages}
                    >
                      Next
                      <ChevronRight className="w-4 h-4 ml-1" />
                    </Button>
                  </div>
                </div>
              </div>
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
    </div>
  )
}