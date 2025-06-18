'use client'

import Link from 'next/link'
import { Button } from '@/components/ui/button'
import { PageHeader } from '@/components/layout'
import { ContentLibrary } from '@/components/library/ContentLibrary'

export default function LibraryPage() {
  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <PageHeader 
        title="Content Library"
        subtitle="Manage your compliant marketing content"
        actions={
          <Link href="/chat">
            <Button>
              New Content
            </Button>
          </Link>
        }
      />
      
      {/* Content Library Component */}
      <ContentLibrary />
    </div>
  )
}
