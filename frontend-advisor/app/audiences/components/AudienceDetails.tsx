'use client'

import { useState, useCallback } from 'react'
import { ArrowLeft, Users, Edit, Trash2, Plus, UserMinus } from 'lucide-react'
import { Audience, Contact } from '@/lib/types'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import AudienceProfile from './AudienceProfile'
import AudienceMemberTable from './AudienceMemberTable'
import EditAudienceModal from './EditAudienceModal'
import DeleteAudienceModal from './DeleteAudienceModal'
import AddContactsModal from './AddContactsModal'
import RemoveContactsModal from './RemoveContactsModal'

interface AudienceDetailsProps {
  audience: Audience | null
  loading: boolean
  onUpdate: () => void
  onDelete: () => void
  onBack?: () => void
  showBackButton: boolean
}

export default function AudienceDetails({
  audience,
  loading,
  onUpdate,
  onDelete,
  onBack,
  showBackButton
}: AudienceDetailsProps) {
  const [showEditModal, setShowEditModal] = useState(false)
  const [showDeleteModal, setShowDeleteModal] = useState(false)
  const [showAddContactsModal, setShowAddContactsModal] = useState(false)
  const [showRemoveContactsModal, setShowRemoveContactsModal] = useState(false)
  const [selectedContacts, setSelectedContacts] = useState<Contact[]>([])

  const handleRemoveContacts = () => {
    if (selectedContacts.length > 0) {
      setShowRemoveContactsModal(true)
    }
  }

  const handleContactSelectionChange = useCallback((contacts: Contact[]) => {
    setSelectedContacts(contacts)
  }, [])

  if (loading) {
    return (
      <div className="h-full flex flex-col">
        {/* Header skeleton */}
        <div className="p-6 border-b border-border">
          <div className="flex items-center justify-between mb-4">
            <Skeleton className="h-8 w-48" />
            <div className="flex gap-2">
              <Skeleton className="h-10 w-20" />
              <Skeleton className="h-10 w-20" />
            </div>
          </div>
          <Skeleton className="h-4 w-full mb-2" />
          <Skeleton className="h-4 w-3/4" />
        </div>
        
        {/* Content skeleton */}
        <div className="flex-1 p-6">
          <Skeleton className="h-64 w-full" />
        </div>
      </div>
    )
  }

  if (!audience) {
    return (
      <div className="h-full flex items-center justify-center">
        <div className="text-center">
          <Users className="h-16 w-16 text-muted-foreground mx-auto mb-4" />
          <h3 className="text-lg font-medium text-muted-foreground mb-2">
            Select an audience
          </h3>
          <p className="text-sm text-muted-foreground">
            Choose an audience from the list to view details and manage members
          </p>
        </div>
      </div>
    )
  }

  return (
    <div className="h-full flex flex-col">
      {/* Header with audience name and actions */}
      <div className="p-6 border-b border-border">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-3">
            {showBackButton && (
              <Button
                variant="ghost"
                size="sm"
                onClick={onBack}
                className="p-2"
              >
                <ArrowLeft className="h-4 w-4" />
              </Button>
            )}
            <div>
              <h1 className="text-2xl font-bold">{audience.name}</h1>
              <p className="text-sm text-muted-foreground">
                {audience.contact_count || 0} {(audience.contact_count || 0) === 1 ? 'contact' : 'contacts'}
              </p>
            </div>
          </div>
          
          <div className="flex gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setShowEditModal(true)}
              className="gap-2"
            >
              <Edit className="h-4 w-4" />
              Edit
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => setShowDeleteModal(true)}
              className="gap-2 text-destructive hover:text-destructive"
            >
              <Trash2 className="h-4 w-4" />
              Delete
            </Button>
          </div>
        </div>
      </div>

      {/* Main content area */}
      <div className="flex-1 overflow-y-auto">
        {/* Audience Profile Section */}
        <div className="p-6 border-b border-border">
          <AudienceProfile audience={audience} />
        </div>

        {/* Members Section */}
        <div className="p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold">Members</h2>
            <div className="flex gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={handleRemoveContacts}
                disabled={selectedContacts.length === 0}
                className="gap-2"
              >
                <UserMinus className="h-4 w-4" />
                Remove Selected ({selectedContacts.length})
              </Button>
              <Button
                size="sm"
                onClick={() => setShowAddContactsModal(true)}
                className="gap-2"
              >
                <Plus className="h-4 w-4" />
                Add Contacts
              </Button>
            </div>
          </div>

          <AudienceMemberTable
            audience={audience}
            onSelectionChange={handleContactSelectionChange}
            onUpdate={onUpdate}
          />
        </div>
      </div>

      {/* Modals */}
      <EditAudienceModal
        open={showEditModal}
        onClose={() => setShowEditModal(false)}
        audience={audience}
        onSuccess={() => {
          setShowEditModal(false)
          onUpdate()
        }}
      />

      <DeleteAudienceModal
        open={showDeleteModal}
        onClose={() => setShowDeleteModal(false)}
        audience={audience}
        onSuccess={() => {
          setShowDeleteModal(false)
          onDelete()
        }}
      />

      <AddContactsModal
        open={showAddContactsModal}
        onClose={() => setShowAddContactsModal(false)}
        audience={audience}
        onSuccess={() => {
          setShowAddContactsModal(false)
          onUpdate()
        }}
      />

      <RemoveContactsModal
        open={showRemoveContactsModal}
        onClose={() => setShowRemoveContactsModal(false)}
        audience={audience}
        contacts={selectedContacts}
        onSuccess={() => {
          setShowRemoveContactsModal(false)
          setSelectedContacts([])
          onUpdate()
        }}
      />
    </div>
  )
}
