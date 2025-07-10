'use client'

import { useState } from 'react'
import { Search, Users, Star } from 'lucide-react'
import { Audience } from '@/lib/types'
import { Input } from '@/components/ui/input'
import { Card, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'

interface AudienceListProps {
  audiences: Audience[]
  selectedAudienceId: number | null
  onAudienceSelect: (audienceId: number) => void
  loading: boolean
}

export default function AudienceList({
  audiences,
  selectedAudienceId,
  onAudienceSelect,
  loading
}: AudienceListProps) {
  const [searchTerm, setSearchTerm] = useState('')

  // Filter audiences based on search term
  const filteredAudiences = audiences.filter(audience =>
    audience.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    audience.description?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    audience.characteristics?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    audience.occupation?.toLowerCase().includes(searchTerm.toLowerCase())
  )

  if (loading) {
    return (
      <div className="h-full flex flex-col">
        {/* Search skeleton */}
        <div className="p-4 border-b">
          <Skeleton className="h-10 w-full" />
        </div>
        
        {/* Card skeletons */}
        <div className="flex-1 overflow-y-auto p-4 space-y-3">
          {[...Array(5)].map((_, i) => (
            <Skeleton key={i} className="h-24 w-full" />
          ))}
        </div>
      </div>
    )
  }

  return (
    <div className="h-full flex flex-col">
      {/* Search Bar */}
      <div className="p-4 border-b border-border">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Search audiences..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="pl-10"
          />
        </div>
      </div>

      {/* Audiences List */}
      <div className="flex-1 overflow-y-auto p-4 space-y-3">
        {filteredAudiences.length === 0 ? (
          <div className="text-center py-8">
            <Users className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
            <h3 className="text-lg font-medium text-muted-foreground mb-2">
              {searchTerm ? 'No audiences found' : 'No audiences yet'}
            </h3>
            <p className="text-sm text-muted-foreground">
              {searchTerm 
                ? 'Try adjusting your search terms'
                : 'Create your first audience to get started'
              }
            </p>
          </div>
        ) : (
          filteredAudiences.map((audience) => (
            <AudienceCard
              key={audience.id}
              audience={audience}
              isSelected={selectedAudienceId === audience.id}
              onClick={() => onAudienceSelect(audience.id)}
            />
          ))
        )}
      </div>
    </div>
  )
}

interface AudienceCardProps {
  audience: Audience
  isSelected: boolean
  onClick: () => void
}

function AudienceCard({ audience, isSelected, onClick }: AudienceCardProps) {
  return (
    <Card 
      className={`cursor-pointer transition-all duration-200 hover:shadow-md ${
        isSelected 
          ? 'ring-2 ring-primary shadow-md bg-primary/5' 
          : 'hover:bg-muted/50'
      }`}
      onClick={onClick}
    >
      <CardContent className="p-4">
        <div className="flex items-start justify-between gap-3">
          <div className="flex-1 min-w-0">
            {/* Audience Name */}
            <div className="flex items-center gap-2 mb-2">
              <h3 className="font-medium text-sm truncate">
                {audience.name}
              </h3>
              {/* Future: Add favorite star */}
              {/* <Star className="h-3 w-3 text-muted-foreground" /> */}
            </div>

            {/* Occupation/Relationship Type */}
            <div className="flex flex-wrap gap-1 mb-2">
              {audience.occupation && (
                <Badge variant="secondary" className="text-xs">
                  {audience.occupation}
                </Badge>
              )}
              {audience.relationship_type && (
                <Badge variant="outline" className="text-xs">
                  {audience.relationship_type}
                </Badge>
              )}
            </div>

            {/* Description */}
            {audience.description && (
              <p className="text-xs text-muted-foreground line-clamp-2 mb-2">
                {audience.description}
              </p>
            )}
          </div>

          {/* Contact Count */}
          <div className="flex flex-col items-center gap-1">
            <div className="flex items-center gap-1">
              <Users className="h-3 w-3 text-muted-foreground" />
              <span className="text-xs font-medium">
                {audience.contact_count || 0}
              </span>
            </div>
            <span className="text-xs text-muted-foreground">
              {audience.contact_count === 1 ? 'contact' : 'contacts'}
            </span>
          </div>
        </div>

        {/* Characteristics (if available) */}
        {audience.characteristics && (
          <div className="mt-2 pt-2 border-t border-border">
            <p className="text-xs text-muted-foreground line-clamp-1">
              <span className="font-medium">Characteristics:</span> {audience.characteristics}
            </p>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
