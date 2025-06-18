'use client'

import Link from 'next/link'
import { Card } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { PageHeader } from '@/components/layout'
import { Library, Filter, Search } from 'lucide-react'

export default function LibraryPage() {
  // For now, we'll simulate an empty library. In the future, this will come from API
  const hasContent = false
  
  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <PageHeader 
        title="Content Library"
        actions={
          <Link href="/chat">
            <Button>
              New Content
            </Button>
          </Link>
        }
      />
        
      {/* Search and Filters - Only show when there's content */}
      {hasContent && (
        <div className="border-b border-border px-6 py-4">
          <div className="flex items-center gap-4">
            <div className="relative flex-1 max-w-md">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <input
                type="text"
                placeholder="Search content..."
                className="w-full pl-10 pr-4 py-2 border border-border rounded-lg bg-background focus:outline-none focus:ring-2 focus:ring-ring"
              />
            </div>
            <Button variant="outline">
              <Filter className="h-4 w-4 mr-2" />
              Filter
            </Button>
          </div>
        </div>
      )}

      {/* Content Area */}
      {hasContent ? (
        // Content grid will go here when we have content
        <div className="flex-1 p-6">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {/* Content cards will be rendered here */}
          </div>
        </div>
      ) : (
        // Empty state
        <div className="flex-1 p-6">
          <div className="flex justify-center pt-16">
            <div className="text-center max-w-md">
              <div className="w-16 h-16 bg-muted rounded-full flex items-center justify-center mx-auto mb-6">
                <Library className="h-8 w-8 text-muted-foreground" />
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
      )}
    </div>
  )
}