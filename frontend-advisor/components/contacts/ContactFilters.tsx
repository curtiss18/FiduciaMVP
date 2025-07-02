'use client'

import React from 'react'
import { Input } from '@/components/ui/input'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Search, Filter } from 'lucide-react'

interface ContactFiltersProps {
  searchTerm: string
  onSearchChange: (value: string) => void
  statusFilter: string
  onStatusChange: (value: string) => void
}

export const ContactFilters: React.FC<ContactFiltersProps> = ({
  searchTerm,
  onSearchChange,
  statusFilter,
  onStatusChange
}) => {
  return (
    <div className="flex flex-col sm:flex-row gap-4 items-center">
      {/* Search Input */}
      <div className="relative flex-1 max-w-sm">
        <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground h-4 w-4" />
        <Input
          placeholder="Search contacts..."
          value={searchTerm}
          onChange={(e) => onSearchChange(e.target.value)}
          className="pl-9"
        />
      </div>

      {/* Status Filter */}
      <div className="flex items-center gap-2">
        <Filter className="h-4 w-4 text-muted-foreground" />
        <Select value={statusFilter} onValueChange={onStatusChange}>
          <SelectTrigger className="w-[150px]">
            <SelectValue placeholder="Filter by status" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Contacts</SelectItem>
            <SelectItem value="prospect">Prospects</SelectItem>
            <SelectItem value="client">Clients</SelectItem>
            <SelectItem value="referral_source">Referral Sources</SelectItem>
          </SelectContent>
        </Select>
      </div>
    </div>
  )
}