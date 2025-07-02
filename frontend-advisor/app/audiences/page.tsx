'use client'

import { useState, useEffect } from 'react'
import { Users, Plus } from 'lucide-react'
import { audienceApi } from '@/lib/api'
import { Audience, Contact } from '@/lib/types'
import { Button } from '@/components/ui/button'
import { toast } from '@/components/ui/use-toast'
import { PageHeader } from '@/components/layout/PageHeader'
import AudienceList from './components/AudienceList'
import AudienceDetails from './components/AudienceDetails'
import CreateAudienceModal from './components/CreateAudienceModal'

const DEMO_ADVISOR_ID = 'demo_advisor_001'

export default function AudiencesPage() {
  const [audiences, setAudiences] = useState<Audience[]>([])
  const [selectedAudienceId, setSelectedAudienceId] = useState<number | null>(null)
  const [selectedAudience, setSelectedAudience] = useState<Audience | null>(null)
  const [loading, setLoading] = useState(true)
  const [detailsLoading, setDetailsLoading] = useState(false)
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [isMobile, setIsMobile] = useState(false)
  const [showDetails, setShowDetails] = useState(false) // For mobile navigation

  // Check if mobile viewport
  useEffect(() => {
    const checkMobile = () => {
      setIsMobile(window.innerWidth < 768)
    }
    
    checkMobile()
    window.addEventListener('resize', checkMobile)
    return () => window.removeEventListener('resize', checkMobile)
  }, [])

  // Load audiences on component mount
  useEffect(() => {
    loadAudiences()
  }, [])

  // Auto-select first audience when audiences load
  useEffect(() => {
    if (audiences.length > 0 && !selectedAudienceId) {
      const firstAudience = audiences[0]
      setSelectedAudienceId(firstAudience.id)
      loadAudienceDetails(firstAudience.id)
    }
  }, [audiences, selectedAudienceId])

  const loadAudiences = async () => {
    try {
      setLoading(true)
      const response = await audienceApi.getAudiences(DEMO_ADVISOR_ID)
      setAudiences(response.audiences || [])
    } catch (error) {
      console.error('Error loading audiences:', error)
      toast({
        title: "Error",
        description: "Failed to load audiences. Please try again.",
        variant: "destructive",
      })
    } finally {
      setLoading(false)
    }
  }

  const loadAudienceDetails = async (audienceId: number) => {
    try {
      setDetailsLoading(true)
      const response = await audienceApi.getAudience(audienceId.toString(), DEMO_ADVISOR_ID)
      setSelectedAudience(response)
    } catch (error) {
      console.error('Error loading audience details:', error)
      toast({
        title: "Error",
        description: "Failed to load audience details. Please try again.",
        variant: "destructive",
      })
    } finally {
      setDetailsLoading(false)
    }
  }

  const handleAudienceSelect = (audienceId: number) => {
    setSelectedAudienceId(audienceId)
    loadAudienceDetails(audienceId)
    
    // On mobile, show details panel
    if (isMobile) {
      setShowDetails(true)
    }
  }

  const handleCreateAudience = async (audienceData: {
    name: string
    description?: string
    characteristics?: string
    occupation?: string
    relationshipType?: string
  }) => {
    try {
      await audienceApi.createAudience({
        advisorId: DEMO_ADVISOR_ID,
        ...audienceData
      })
      
      toast({
        title: "Success",
        description: "Audience created successfully!",
      })
      
      setShowCreateModal(false)
      await loadAudiences() // Refresh the list
    } catch (error) {
      console.error('Error creating audience:', error)
      toast({
        title: "Error",
        description: "Failed to create audience. Please try again.",
        variant: "destructive",
      })
    }
  }

  const handleAudienceUpdate = async () => {
    // Refresh audiences list and current details
    await loadAudiences()
    if (selectedAudienceId) {
      await loadAudienceDetails(selectedAudienceId)
    }
  }

  const handleAudienceDelete = async () => {
    // Refresh audiences list and clear selection
    await loadAudiences()
    setSelectedAudienceId(null)
    setSelectedAudience(null)
    setShowDetails(false)
  }

  const handleBackToList = () => {
    setShowDetails(false)
  }

  const pageActions = (
    <Button onClick={() => setShowCreateModal(true)} className="gap-2">
      <Plus className="h-4 w-4" />
      Create Audience
    </Button>
  )

  return (
    <div className="flex flex-col h-full">
      <PageHeader
        title="Audiences"
        subtitle="Organize contacts into targeted groups for content creation"
        icon={Users}
        actions={pageActions}
      />
      
      <div className="flex-1 flex overflow-hidden">
        {/* Mobile: Single panel navigation */}
        {isMobile ? (
          <>
            {!showDetails ? (
              <div className="flex-1">
                <AudienceList
                  audiences={audiences}
                  selectedAudienceId={selectedAudienceId}
                  onAudienceSelect={handleAudienceSelect}
                  loading={loading}
                />
              </div>
            ) : (
              <div className="flex-1">
                <AudienceDetails
                  audience={selectedAudience}
                  loading={detailsLoading}
                  onUpdate={handleAudienceUpdate}
                  onDelete={handleAudienceDelete}
                  onBack={handleBackToList}
                  showBackButton={true}
                />
              </div>
            )}
          </>
        ) : (
          /* Desktop: Split-screen layout */
          <>
            <div className="w-80 border-r border-border">
              <AudienceList
                audiences={audiences}
                selectedAudienceId={selectedAudienceId}
                onAudienceSelect={handleAudienceSelect}
                loading={loading}
              />
            </div>
            <div className="flex-1">
              <AudienceDetails
                audience={selectedAudience}
                loading={detailsLoading}
                onUpdate={handleAudienceUpdate}
                onDelete={handleAudienceDelete}
                showBackButton={false}
              />
            </div>
          </>
        )}
      </div>

      {/* Create Audience Modal */}
      <CreateAudienceModal
        open={showCreateModal}
        onClose={() => setShowCreateModal(false)}
        onSubmit={handleCreateAudience}
      />
    </div>
  )
}
