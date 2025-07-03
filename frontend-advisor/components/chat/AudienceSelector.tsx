'use client'

import React, { useState, useEffect } from 'react'
import { Users, ChevronDown } from 'lucide-react'
import { audienceApi } from '@/lib/api'
import { Audience } from '@/lib/types'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { toast } from '@/components/ui/use-toast'

interface AudienceSelectorProps {
  selectedAudience: Audience | null
  onAudienceChange: (audience: Audience | null) => void
  disabled?: boolean
}

export const AudienceSelector: React.FC<AudienceSelectorProps> = ({
  selectedAudience,
  onAudienceChange,
  disabled = false
}) => {
  const [audiences, setAudiences] = useState<Audience[]>([])
  const [loading, setLoading] = useState(true)

  // Load audiences on component mount
  useEffect(() => {
    loadAudiences()
  }, [])

  const loadAudiences = async () => {
    try {
      setLoading(true)
      const response = await audienceApi.getAudiences('demo_advisor_001')
      setAudiences(response.audiences || [])
    } catch (error) {
      console.error('Failed to load audiences:', error)
      toast({
        title: "Error Loading Audiences",
        description: "Unable to load your audience list. Using general targeting.",
        variant: "destructive",
      })
    } finally {
      setLoading(false)
    }
  }

  const handleAudienceChange = (value: string) => {
    if (value === 'general') {
      onAudienceChange(null)
    } else {
      const audienceId = parseInt(value)
      const audience = audiences.find(a => a.id === audienceId)
      onAudienceChange(audience || null)
    }
  }

  const getDisplayValue = (): string => {
    if (selectedAudience) {
      return selectedAudience.name
    }
    return 'General/No Audience'
  }

  const getCurrentValue = (): string => {
    if (selectedAudience) {
      return selectedAudience.id.toString()
    }
    return 'general'
  }

  return (
    <div className="flex items-center gap-2 min-w-0">
      <Users className="h-4 w-4 text-muted-foreground flex-shrink-0" />
      <Select
        value={getCurrentValue()}
        onValueChange={handleAudienceChange}
        disabled={disabled || loading}
      >
        <SelectTrigger className="w-[200px] h-8 text-xs">
          <SelectValue>
            {loading ? 'Loading...' : getDisplayValue()}
          </SelectValue>
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="general">
            <span className="font-medium">General/No Audience</span>
          </SelectItem>
          {audiences.length > 0 && (
            <>
              <div className="px-2 py-1.5 text-xs font-medium text-muted-foreground border-t">
                Your Audiences
              </div>
              {audiences.map((audience) => (
                <SelectItem key={audience.id} value={audience.id.toString()}>
                  <div className="flex flex-col items-start gap-0.5 min-w-0">
                    <span className="font-medium truncate">{audience.name}</span>
                    {audience.occupation && (
                      <span className="text-xs text-muted-foreground truncate">
                        {audience.occupation} • {audience.contact_count || 0} contacts
                      </span>
                    )}
                  </div>
                </SelectItem>
              ))}
            </>
          )}
        </SelectContent>
      </Select>
    </div>
  )
}
