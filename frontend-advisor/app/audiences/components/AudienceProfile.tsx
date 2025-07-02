'use client'

import { Audience } from '@/lib/types'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent } from '@/components/ui/card'
import { Briefcase, Users, FileText, Tag } from 'lucide-react'

interface AudienceProfileProps {
  audience: Audience
}

export default function AudienceProfile({ audience }: AudienceProfileProps) {
  return (
    <div className="space-y-4">
      {/* Description */}
      {audience.description && (
        <Card>
          <CardContent className="p-4">
            <div className="flex items-start gap-3">
              <FileText className="h-5 w-5 text-muted-foreground mt-0.5" />
              <div>
                <h3 className="font-medium mb-2">Description</h3>
                <p className="text-sm text-muted-foreground leading-relaxed">
                  {audience.description}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Quick Info */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Occupation */}
        {audience.occupation && (
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center gap-3">
                <Briefcase className="h-5 w-5 text-muted-foreground" />
                <div>
                  <h3 className="font-medium text-sm">Occupation</h3>
                  <Badge variant="secondary" className="mt-1">
                    {audience.occupation}
                  </Badge>
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Relationship Type */}
        {audience.relationship_type && (
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center gap-3">
                <Users className="h-5 w-5 text-muted-foreground" />
                <div>
                  <h3 className="font-medium text-sm">Relationship Type</h3>
                  <Badge variant="outline" className="mt-1">
                    {audience.relationship_type}
                  </Badge>
                </div>
              </div>
            </CardContent>
          </Card>
        )}
      </div>

      {/* Characteristics */}
      {audience.characteristics && (
        <Card>
          <CardContent className="p-4">
            <div className="flex items-start gap-3">
              <Tag className="h-5 w-5 text-muted-foreground mt-0.5" />
              <div>
                <h3 className="font-medium mb-2">Characteristics</h3>
                <p className="text-sm text-muted-foreground leading-relaxed">
                  {audience.characteristics}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Created/Updated Info */}
      <Card>
        <CardContent className="p-4">
          <div className="flex items-center justify-between text-xs text-muted-foreground">
            <span>
              Created: {new Date(audience.created_at).toLocaleDateString()}
            </span>
            <span>
              Updated: {new Date(audience.updated_at).toLocaleDateString()}
            </span>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
