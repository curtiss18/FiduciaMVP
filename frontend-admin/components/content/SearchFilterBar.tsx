'use client'

import { Button } from '@/components/ui/button'
import { Search, Filter } from 'lucide-react'

interface SearchFilterBarProps {
  searchTerm: string
  onSearchChange: (value: string) => void
  filteredCount: number
  totalCount: number
}

export default function SearchFilterBar({ 
  searchTerm, 
  onSearchChange, 
  filteredCount, 
  totalCount 
}: SearchFilterBarProps) {
  return (
    <div className="border-b border-gray-200 px-6 py-4">
      <div className="flex items-center justify-between space-x-4">
        <div className="flex-1 max-w-md">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground w-4 h-4" />
            <input
              type="text"
              placeholder="Search content..."
              value={searchTerm}
              onChange={(e) => onSearchChange(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border border-input rounded-lg bg-background text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring focus:border-transparent"
            />
          </div>
        </div>
        
        <div className="flex items-center space-x-2">
          <Button variant="outline" size="sm">
            <Filter className="w-4 h-4 mr-2" />
            Filter
          </Button>
          <span className="text-sm text-muted-foreground">
            {filteredCount} of {totalCount} items
          </span>
        </div>
      </div>
    </div>
  )
}