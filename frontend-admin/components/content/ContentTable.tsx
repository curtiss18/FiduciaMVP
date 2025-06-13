'use client'

import { useState, useEffect } from 'react'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { 
  Edit,
  Trash2,
  Eye,
  CheckCircle,
  AlertCircle,
  MoreVertical
} from 'lucide-react'
import DeleteContentModal from './DeleteContentModal'

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

interface ContentTableProps {
  content: ContentItem[]
  isLoading: boolean
}

export default function ContentTable({ content, isLoading }: ContentTableProps) {
  const [openDropdown, setOpenDropdown] = useState<number | null>(null)
  const [deleteModal, setDeleteModal] = useState<{
    isOpen: boolean
    content: ContentItem | null
  }>({
    isOpen: false,
    content: null
  })

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

  const toggleDropdown = (id: number, event: React.MouseEvent) => {
    event.stopPropagation()
    setOpenDropdown(openDropdown === id ? null : id)
  }

  const handleDeleteClick = (item: ContentItem) => {
    setDeleteModal({
      isOpen: true,
      content: item
    })
    setOpenDropdown(null) // Close the dropdown
  }

  const handleDeleteSuccess = () => {
    // Temporarily disable auto-refresh for debugging
    console.log('Delete completed - check if record was actually deleted')
    // window.location.reload()
    
    // Alternative: You could manually refresh the data here
    // by calling a prop function from the parent component
  }

  const getStatusBadgeColor = (status: string) => {
    switch (status.toLowerCase()) {
      case 'approved':
        return 'bg-green-50 text-green-700 border-green-200 dark:bg-green-900/20 dark:text-green-300 dark:border-green-800'
      case 'pending':
        return 'bg-yellow-50 text-yellow-700 border-yellow-200 dark:bg-yellow-900/20 dark:text-yellow-300 dark:border-yellow-800'
      case 'rejected':
        return 'bg-red-50 text-red-700 border-red-200 dark:bg-red-900/20 dark:text-red-300 dark:border-red-800'
      case 'needs_revision':
        return 'bg-orange-50 text-orange-700 border-orange-200 dark:bg-orange-900/20 dark:text-orange-300 dark:border-orange-800'
      default:
        return 'bg-muted text-muted-foreground border-border'
    }
  }

  const formatContentType = (type: string) => {
    return type.split('_').map(word => 
      word.charAt(0).toUpperCase() + word.slice(1)
    ).join(' ')
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="w-8 h-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
        <span className="ml-2 text-muted-foreground">Loading content...</span>
      </div>
    )
  }

  if (content.length === 0) {
    return (
      <div className="text-center py-12">
        <div className="w-12 h-12 text-muted-foreground mx-auto mb-4">
          <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
        </div>
        <h3 className="text-lg font-medium text-foreground mb-2">No content found</h3>
        <p className="text-muted-foreground mb-4">Start by adding your first content piece.</p>
        <Button className="bg-primary hover:bg-primary/90 text-primary-foreground font-medium">
          Add Content
        </Button>
      </div>
    )
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full">
        <thead>
          <tr className="border-b border-border">
            <th className="text-left py-3 px-4 font-medium text-foreground">Title</th>
            <th className="text-left py-3 px-4 font-medium text-foreground">Type</th>
            <th className="text-left py-3 px-4 font-medium text-foreground">Status</th>
            <th className="text-left py-3 px-4 font-medium text-foreground">Vectorized</th>
            <th className="text-left py-3 px-4 font-medium text-foreground">Updated</th>
            <th className="text-right py-3 px-4 font-medium text-foreground">Actions</th>
          </tr>
        </thead>
        <tbody>
          {content.map((item) => (
            <tr key={item.id} className="border-b border-border hover:bg-muted/50">
              <td className="py-4 px-4">
                <div className="font-medium text-foreground">{item.title}</div>
                <div className="text-sm text-muted-foreground truncate max-w-xs">
                  {item.content_text}
                </div>
              </td>
              <td className="py-4 px-4">
                <Badge variant="outline" className="bg-blue-50 text-blue-700 dark:bg-blue-900/20 dark:text-blue-300">
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
                  <CheckCircle className="w-5 h-5 text-green-500 dark:text-green-400" />
                ) : (
                  <AlertCircle className="w-5 h-5 text-yellow-500 dark:text-yellow-400" />
                )}
              </td>
              <td className="py-4 px-4 text-sm text-muted-foreground">
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
                      <div className="absolute right-0 mt-1 w-32 bg-popover border border-border rounded-md shadow-lg z-10">
                        <div className="py-1">
                          <button
                            className="flex items-center w-full px-3 py-2 text-sm text-popover-foreground hover:bg-accent hover:text-accent-foreground"
                            onClick={() => {
                              // Handle view action
                              setOpenDropdown(null)
                            }}
                          >
                            <Eye className="w-4 h-4 mr-2" />
                            View
                          </button>
                          <button
                            className="flex items-center w-full px-3 py-2 text-sm text-popover-foreground hover:bg-accent hover:text-accent-foreground"
                            onClick={() => {
                              // Handle edit action
                              setOpenDropdown(null)
                            }}
                          >
                            <Edit className="w-4 h-4 mr-2" />
                            Edit
                          </button>
                          <button
                            className="flex items-center w-full px-3 py-2 text-sm text-destructive hover:bg-destructive/10"
                            onClick={() => handleDeleteClick(item)}
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